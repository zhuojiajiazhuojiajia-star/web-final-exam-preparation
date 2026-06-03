from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db
from models.lottery import Lottery, LotteryPrize, UserLotteryRecord
from models.shop import UserCurrency, CoinTransaction
from datetime import datetime
import random

lottery_bp = Blueprint('lottery', __name__)


def get_or_create_currency(user_id):
    """获取或创建用户货币账户"""
    currency = UserCurrency.query.filter_by(user_id=user_id).first()
    if not currency:
        currency = UserCurrency(user_id=user_id, coins=100)
        db.session.add(currency)
        db.session.commit()
    return currency


def spend_coins(user_id, amount, description=''):
    """消费金币"""
    currency = get_or_create_currency(user_id)
    if currency.spend_coins(amount):
        transaction = CoinTransaction(
            user_id=user_id,
            amount=-amount,
            transaction_type='lottery',
            description=description
        )
        db.session.add(transaction)
        db.session.commit()
        return True
    return False


def add_coins(user_id, amount, description=''):
    """添加金币"""
    currency = get_or_create_currency(user_id)
    if currency.add_coins(amount):
        transaction = CoinTransaction(
            user_id=user_id,
            amount=amount,
            transaction_type='lottery_reward',
            description=description
        )
        db.session.add(transaction)
        db.session.commit()
        return True
    return False


@lottery_bp.route('/')
def index():
    """抽奖页面"""
    lottery = Lottery.query.filter_by(is_active=True).first()
    currency = get_or_create_currency(current_user.id) if current_user.is_authenticated else None

    # 获取最近的抽奖记录
    recent_records = []
    if current_user.is_authenticated:
        recent_records = UserLotteryRecord.query.filter_by(user_id=current_user.id)\
            .order_by(UserLotteryRecord.created_at.desc()).limit(10).all()

    return render_template('lottery/index.html',
                          lottery=lottery,
                          user_coins=currency.coins if currency else 0,
                          recent_records=recent_records)


@lottery_bp.route('/api/info')
@login_required
def api_info():
    """获取抽奖信息"""
    lottery = Lottery.query.filter_by(is_active=True).first()

    if not lottery:
        return jsonify({'code': 404, 'msg': '暂无可用抽奖活动'})

    # 获取奖品列表（前端展示用）
    prizes = []
    for prize in lottery.prizes:
        prizes.append({
            'id': prize.id,
            'name': prize.name,
            'icon': prize.icon,
            'prize_type': prize.prize_type,
            'stock': prize.stock,
            'probability': prize.probability
        })

    currency = get_or_create_currency(current_user.id)

    return jsonify({
        'code': 200,
        'data': {
            'lottery_id': lottery.id,
            'name': lottery.name,
            'description': lottery.description,
            'cost': lottery.cost,
            'prizes': prizes,
            'user_coins': currency.coins
        }
    })


@lottery_bp.route('/api/draw', methods=['POST'])
@login_required
def api_draw():
    """执行抽奖"""
    lottery = Lottery.query.filter_by(is_active=True).first()

    if not lottery:
        return jsonify({'code': 404, 'msg': '暂无可用抽奖活动'})

    # 检查金币
    currency = get_or_create_currency(current_user.id)
    if currency.coins < lottery.cost:
        return jsonify({'code': 400, 'msg': f'金币不足，需要 {lottery.cost} 金币'})

    # 扣费
    if not spend_coins(current_user.id, lottery.cost, f'参与抽奖: {lottery.name}'):
        return jsonify({'code': 500, 'msg': '扣费失败'})

    # 根据概率抽取奖品
    prize = draw_prize(lottery)

    # 记录抽奖
    record = UserLotteryRecord(
        user_id=current_user.id,
        lottery_id=lottery.id,
        prize_id=prize.id if prize else None
    )
    db.session.add(record)

    # 处理奖品发放
    prize_info = None
    if prize:
        prize_info = {
            'id': prize.id,
            'name': prize.name,
            'icon': prize.icon,
            'prize_type': prize.prize_type
        }

        # 发放奖品
        if prize.prize_type == 'coins' and prize.prize_value > 0:
            add_coins(current_user.id, prize.prize_value, f'抽奖获得: {prize.name}')
            prize_info['coins_added'] = prize.prize_value

        # 减少库存
        if prize.stock != -1:
            prize.stock -= 1

    db.session.commit()

    # 更新用户金币
    currency = get_or_create_currency(current_user.id)

    return jsonify({
        'code': 200,
        'msg': '抽奖成功',
        'prize': prize_info,
        'user_coins': currency.coins
    })


def draw_prize(lottery):
    """根据概率抽取奖品"""
    prizes = list(lottery.prizes)

    # 过滤掉库存为0的奖品
    available_prizes = [p for p in prizes if p.stock != 0]

    if not available_prizes:
        return None

    # 计算总概率
    total_prob = sum(p.probability for p in available_prizes)

    # 随机抽取
    rand = random.random() * total_prob

    cumulative = 0
    for prize in available_prizes:
        cumulative += prize.probability
        if rand <= cumulative:
            return prize

    # 兜底：返回谢谢参与
    return None


@lottery_bp.route('/api/history')
@login_required
def api_history():
    """获取抽奖历史"""
    page = request.args.get('page', 1, type=int)
    per_page = 20

    records = UserLotteryRecord.query.filter_by(user_id=current_user.id)\
        .order_by(UserLotteryRecord.created_at.desc())\
        .paginate(page=page, per_page=per_page)

    history = []
    for record in records.items:
        history.append({
            'id': record.id,
            'lottery_name': record.lottery.name if record.lottery else '未知',
            'prize_name': record.prize.name if record.prize else '谢谢参与',
            'prize_icon': record.prize.icon if record.prize else '😢',
            'created_at': record.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })

    return jsonify({
        'code': 200,
        'data': {
            'records': history,
            'total': records.total,
            'pages': records.pages,
            'current_page': records.page
        }
    })
