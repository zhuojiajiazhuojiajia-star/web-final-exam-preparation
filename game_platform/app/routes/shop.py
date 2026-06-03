from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db
from models.shop import (
    UserCurrency, CoinTransaction, ShopItem, UserItem,
    DailyChallenge, UserDailyChallenge, GameEvent
)
from models.game import Game, GameScore
from models.user import User
from datetime import datetime, date, timedelta
import random

shop_bp = Blueprint('shop', __name__)


# ========== 货币系统辅助函数 ==========

def get_or_create_currency(user_id):
    """获取或创建用户货币账户"""
    currency = UserCurrency.query.filter_by(user_id=user_id).first()
    if not currency:
        currency = UserCurrency(user_id=user_id, coins=100)  # 新用户赠送100金币
        db.session.add(currency)
        db.session.commit()
        
        # 记录交易
        transaction = CoinTransaction(
            user_id=user_id,
            amount=100,
            transaction_type='admin',
            description='新用户注册奖励'
        )
        db.session.add(transaction)
        db.session.commit()
    return currency


def add_coins(user_id, amount, transaction_type, description='', related_id=None):
    """添加金币"""
    currency = get_or_create_currency(user_id)
    if currency.add_coins(amount):
        transaction = CoinTransaction(
            user_id=user_id,
            amount=amount,
            transaction_type=transaction_type,
            description=description,
            related_id=related_id
        )
        db.session.add(transaction)
        db.session.commit()
        return True
    return False


def spend_coins(user_id, amount, transaction_type, description='', related_id=None):
    """消费金币"""
    currency = get_or_create_currency(user_id)
    if currency.spend_coins(amount):
        transaction = CoinTransaction(
            user_id=user_id,
            amount=-amount,
            transaction_type=transaction_type,
            description=description,
            related_id=related_id
        )
        db.session.add(transaction)
        db.session.commit()
        return True
    return False


def calculate_game_reward(score, game_id):
    """计算游戏奖励金币"""
    # 基础奖励 + 分数奖励
    base_reward = 5
    score_reward = min(score // 100, 50)  # 每100分得1金币，最多50
    
    # 检查是否有双倍金币活动
    event = GameEvent.query.filter(
        GameEvent.event_type == 'double_coins',
        GameEvent.is_active == True,
        GameEvent.start_time <= datetime.now(),
        GameEvent.end_time >= datetime.now()
    ).first()
    
    total = base_reward + score_reward
    if event:
        total *= 2
    
    return total


# ========== 商城路由 ==========

@shop_bp.route('/')
def index():
    """商城首页"""
    items = ShopItem.query.filter_by(is_active=True).order_by(ShopItem.rarity, ShopItem.price).all()
    
    # 按类型分组
    items_by_type = {}
    for item in items:
        if item.item_type not in items_by_type:
            items_by_type[item.item_type] = []
        items_by_type[item.item_type].append(item)
    
    # 用户已拥有的物品
    owned_items = []
    if current_user.is_authenticated:
        owned_items = [ui.item_id for ui in UserItem.query.filter_by(user_id=current_user.id).all()]
    
    # 用户金币
    user_coins = 0
    if current_user.is_authenticated:
        currency = get_or_create_currency(current_user.id)
        user_coins = currency.coins
    
    return render_template('shop/index.html', 
                          items_by_type=items_by_type, 
                          owned_items=owned_items,
                          user_coins=user_coins)


@shop_bp.route('/buy/<int:item_id>', methods=['POST'])
@login_required
def buy(item_id):
    """购买商品"""
    item = ShopItem.query.get_or_404(item_id)
    
    # 检查库存
    if item.stock != -1 and item.stock <= 0:
        return jsonify({'code': 400, 'msg': '商品已售罄'})
    
    # 检查金币
    currency = get_or_create_currency(current_user.id)
    if currency.coins < item.price:
        return jsonify({'code': 400, 'msg': '金币不足'})
    
    # 扣款并添加物品
    if spend_coins(current_user.id, item.price, 'purchase', f'购买 {item.name}', item_id):
        existing = UserItem.query.filter_by(user_id=current_user.id, item_id=item_id).first()
        if existing:
            existing.quantity += 1
        else:
            user_item = UserItem(
                user_id=current_user.id,
                item_id=item_id,
                quantity=1,
                item_category=item.item_type
            )
            db.session.add(user_item)
        
        # 更新销量和库存
        item.sold_count += 1
        if item.stock != -1:
            item.stock -= 1
        
        db.session.commit()
        return jsonify({'code': 200, 'msg': '购买成功', 'coins': currency.coins})
    
    return jsonify({'code': 500, 'msg': '购买失败'})


@shop_bp.route('/my_items')
@login_required
def my_items():
    """我的物品"""
    user_items = UserItem.query.filter_by(user_id=current_user.id).all()
    currency = get_or_create_currency(current_user.id)
    
    # 获取物品详情
    items_with_details = []
    for ui in user_items:
        item = ShopItem.query.get(ui.item_id)
        if item:
            items_with_details.append({
                'user_item': ui,
                'item': item
            })
    
    return render_template('shop/my_items.html', 
                          items_with_details=items_with_details,
                          currency=currency)


@shop_bp.route('/equip/<int:item_id>', methods=['POST'])
@login_required
def equip(item_id):
    """装备/卸下物品"""
    user_item = UserItem.query.filter_by(user_id=current_user.id, item_id=item_id).first_or_404()
    item = ShopItem.query.get(item_id)
    
    if user_item.is_equipped:
        user_item.is_equipped = False
        db.session.commit()
        return jsonify({'code': 200, 'msg': '已卸下', 'equipped': False})
    else:
        # 卸下同类型的其他物品
        same_type_items = db.session.query(UserItem).join(ShopItem).filter(
            UserItem.user_id == current_user.id,
            ShopItem.item_type == item.item_type,
            UserItem.is_equipped == True
        ).all()
        
        for sti in same_type_items:
            sti.is_equipped = False
        
        user_item.is_equipped = True
        db.session.commit()
        return jsonify({'code': 200, 'msg': '已装备', 'equipped': True})


# ========== 每日挑战路由 ==========

@shop_bp.route('/daily')
@login_required
def daily_challenges():
    """每日挑战页面"""
    today = date.today()
    
    # 获取所有活跃的每日挑战
    challenges = DailyChallenge.query.filter_by(is_active=True).all()
    
    # 获取用户今日的挑战进度
    user_challenges = []
    for challenge in challenges:
        uc = UserDailyChallenge.query.filter_by(
            user_id=current_user.id,
            challenge_id=challenge.id,
            date=today
        ).first()
        
        if not uc:
            # 创建今日进度
            uc = UserDailyChallenge(
                user_id=current_user.id,
                challenge_id=challenge.id,
                date=today
            )
            db.session.add(uc)
            db.session.commit()
        
        user_challenges.append({
            'challenge': challenge,
            'progress': uc
        })
    
    currency = get_or_create_currency(current_user.id)
    
    return render_template('shop/daily.html', 
                          user_challenges=user_challenges,
                          currency=currency)


def update_daily_challenge_progress(user_id, game_id, score):
    """更新每日挑战进度（在提交分数时调用）"""
    today = date.today()
    
    # 获取所有活跃的每日挑战
    challenges = DailyChallenge.query.filter_by(is_active=True).all()
    
    for challenge in challenges:
        uc = UserDailyChallenge.query.filter_by(
            user_id=user_id,
            challenge_id=challenge.id,
            date=today
        ).first()
        
        if not uc or uc.is_completed:
            continue
        
        progress_made = False
        
        if challenge.challenge_type == 'play_game':
            # 玩指定游戏
            if challenge.game_id is None or challenge.game_id == game_id:
                uc.current_progress += 1
                progress_made = True
        
        elif challenge.challenge_type == 'reach_score':
            # 达到指定分数
            if score >= challenge.target_value:
                if challenge.game_id is None or challenge.game_id == game_id:
                    uc.current_progress = challenge.target_value
                    progress_made = True
        
        elif challenge.challenge_type == 'play_count':
            # 游玩次数
            uc.current_progress += 1
            progress_made = True
        
        elif challenge.challenge_type == 'total_score':
            # 累计总分
            uc.current_progress += score
            progress_made = True
        
        if progress_made:
            # 检查是否完成
            if uc.current_progress >= challenge.target_value:
                uc.is_completed = True
                uc.completed_at = datetime.now()
    
    db.session.commit()


@shop_bp.route('/claim_reward/<int:challenge_id>', methods=['POST'])
@login_required
def claim_reward(challenge_id):
    """领取每日挑战奖励"""
    today = date.today()
    
    uc = UserDailyChallenge.query.filter_by(
        user_id=current_user.id,
        challenge_id=challenge_id,
        date=today
    ).first_or_404()
    
    if not uc.is_completed:
        return jsonify({'code': 400, 'msg': '任务未完成'})
    
    if uc.is_claimed:
        return jsonify({'code': 400, 'msg': '奖励已领取'})
    
    challenge = DailyChallenge.query.get(challenge_id)
    
    # 发放奖励
    add_coins(current_user.id, challenge.coin_reward, 'daily_task', 
              f'完成每日挑战: {challenge.name}', challenge_id)
    
    uc.is_claimed = True
    db.session.commit()
    
    currency = get_or_create_currency(current_user.id)
    
    return jsonify({
        'code': 200, 
        'msg': f'领取成功！获得 {challenge.coin_reward} 金币',
        'coins': currency.coins
    })


# ========== 活动路由 ==========

@shop_bp.route('/events')
def events():
    """活动列表"""
    now = datetime.now()
    
    # 进行中的活动
    active_events = GameEvent.query.filter(
        GameEvent.is_active == True,
        GameEvent.start_time <= now,
        GameEvent.end_time >= now
    ).all()
    
    # 即将开始的活动
    upcoming_events = GameEvent.query.filter(
        GameEvent.is_active == True,
        GameEvent.start_time > now
    ).all()
    
    return render_template('shop/events.html', 
                          active_events=active_events,
                          upcoming_events=upcoming_events)


# ========== 金币交易记录 ==========

@shop_bp.route('/transactions')
@login_required
def transactions():
    """金币交易记录"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    transactions = CoinTransaction.query.filter_by(user_id=current_user.id)\
        .order_by(CoinTransaction.created_at.desc())\
        .paginate(page=page, per_page=per_page)
    
    currency = get_or_create_currency(current_user.id)
    
    return render_template('shop/transactions.html', 
                          transactions=transactions,
                          currency=currency)


# ========== 皮肤系统 API ==========

@shop_bp.route('/api/skins')
def api_skins():
    """获取所有皮肤"""
    # 获取所有皮肤类物品
    skins = ShopItem.query.filter_by(item_type='skin', is_active=True).all()
    
    # 用户已拥有的皮肤
    owned_skin_ids = []
    if current_user.is_authenticated:
        owned_skin_ids = [ui.item_id for ui in UserItem.query.filter_by(
            user_id=current_user.id, 
            item_category='skin'
        ).all()]
    
    # 用户已装备的皮肤
    equipped_skin_ids = []
    if current_user.is_authenticated:
        equipped_skin_ids = [ui.item_id for ui in UserItem.query.filter_by(
            user_id=current_user.id, 
            item_category='skin',
            is_equipped=True
        ).all()]
    
    skins_data = []
    for skin in skins:
        import json
        skin_config = json.loads(skin.skin_config) if skin.skin_config else {}
        skins_data.append({
            'id': skin.id,
            'name': skin.name,
            'description': skin.description,
            'icon': skin.icon,
            'price': skin.price,
            'rarity': skin.rarity,
            'game_id': skin.game_id,
            'skin_config': skin_config,
            'is_owned': skin.id in owned_skin_ids,
            'is_equipped': skin.id in equipped_skin_ids
        })
    
    return jsonify({'code': 200, 'skins': skins_data})


@shop_bp.route('/api/my-skins')
@login_required
def api_my_skins():
    """获取我的皮肤"""
    user_skins = UserItem.query.filter_by(
        user_id=current_user.id, 
        item_category='skin'
    ).all()
    
    skins_data = []
    for us in user_skins:
        skin = ShopItem.query.get(us.item_id)
        if skin:
            import json
            skin_config = json.loads(skin.skin_config) if skin.skin_config else {}
            skins_data.append({
                'id': skin.id,
                'name': skin.name,
                'description': skin.description,
                'icon': skin.icon,
                'rarity': skin.rarity,
                'game_id': skin.game_id,
                'skin_config': skin_config,
                'is_equipped': us.is_equipped,
                'quantity': us.quantity
            })
    
    return jsonify({'code': 200, 'skins': skins_data})


@shop_bp.route('/api/preview', methods=['POST'])
@login_required
def api_preview():
    """预览皮肤效果（临时应用皮肤到游戏）"""
    data = request.get_json()
    skin_id = data.get('skin_id')
    
    if not skin_id:
        return jsonify({'code': 400, 'msg': '缺少皮肤ID'})
    
    skin = ShopItem.query.get(skin_id)
    if not skin:
        return jsonify({'code': 404, 'msg': '皮肤不存在'})
    
    if skin.item_type != 'skin':
        return jsonify({'code': 400, 'msg': '该物品不是皮肤'})
    
    import json
    skin_config = json.loads(skin.skin_config) if skin.skin_config else {}
    
    return jsonify({
        'code': 200, 
        'msg': '预览成功',
        'preview': {
            'skin_id': skin.id,
            'name': skin.name,
            'icon': skin.icon,
            'skin_config': skin_config
        }
    })


# ========== API: 获取用户金币 ==========

@shop_bp.route('/api/coins')
@login_required
def api_coins():
    """获取用户金币余额"""
    currency = get_or_create_currency(current_user.id)
    return jsonify({
        'code': 200,
        'coins': currency.coins,
        'total_earned': currency.total_earned,
        'total_spent': currency.total_spent
    })
