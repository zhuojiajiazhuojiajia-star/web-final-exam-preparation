from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db
from models.shop import UserItem, ShopItem, UserCurrency, CoinTransaction
from models.user import User
from datetime import datetime

backpack_bp = Blueprint('backpack', __name__)


def get_or_create_currency(user_id):
    """获取或创建用户货币账户"""
    currency = UserCurrency.query.filter_by(user_id=user_id).first()
    if not currency:
        currency = UserCurrency(user_id=user_id, coins=0)
        db.session.add(currency)
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


@backpack_bp.route('/')
@login_required
def index():
    """背包页面"""
    currency = get_or_create_currency(current_user.id)
    return render_template('backpack/index.html', currency=currency)


@backpack_bp.route('/api/list')
@login_required
def api_list():
    """获取背包物品列表"""
    category = request.args.get('category', 'all')
    
    query = UserItem.query.filter_by(user_id=current_user.id)
    
    if category != 'all':
        query = query.filter_by(item_category=category)
    
    user_items = query.order_by(UserItem.purchased_at.desc()).all()
    
    items_data = []
    for ui in user_items:
        item = ShopItem.query.get(ui.item_id)
        if item:
            items_data.append({
                'id': ui.id,
                'item_id': item.id,
                'name': item.name,
                'icon': item.icon,
                'description': item.description,
                'item_type': item.item_type,
                'item_category': ui.item_category,
                'rarity': item.rarity,
                'quantity': ui.quantity,
                'is_equipped': ui.is_equipped,
                'price': item.price,
                'purchased_at': ui.purchased_at.strftime('%Y-%m-%d %H:%M') if ui.purchased_at else ''
            })
    
    return jsonify({
        'code': 200,
        'items': items_data
    })


@backpack_bp.route('/api/equip', methods=['POST'])
@login_required
def api_equip():
    """装备物品"""
    data = request.get_json()
    item_id = data.get('item_id')
    
    if not item_id:
        return jsonify({'code': 400, 'msg': '缺少物品ID'})
    
    user_item = UserItem.query.filter_by(user_id=current_user.id, item_id=item_id).first()
    if not user_item:
        return jsonify({'code': 404, 'msg': '物品不存在'})
    
    item = ShopItem.query.get(item_id)
    
    if user_item.is_equipped:
        user_item.is_equipped = False
        db.session.commit()
        return jsonify({'code': 200, 'msg': '已卸下', 'equipped': False})
    else:
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


@backpack_bp.route('/api/unequip', methods=['POST'])
@login_required
def api_unequip():
    """卸下物品"""
    data = request.get_json()
    item_id = data.get('item_id')
    
    if not item_id:
        return jsonify({'code': 400, 'msg': '缺少物品ID'})
    
    user_item = UserItem.query.filter_by(user_id=current_user.id, item_id=item_id).first()
    if not user_item:
        return jsonify({'code': 404, 'msg': '物品不存在'})
    
    if not user_item.is_equipped:
        return jsonify({'code': 400, 'msg': '物品未装备'})
    
    user_item.is_equipped = False
    db.session.commit()
    
    return jsonify({'code': 200, 'msg': '已卸下'})


@backpack_bp.route('/api/use', methods=['POST'])
@login_required
def api_use():
    """使用物品（消耗品）"""
    data = request.get_json()
    item_id = data.get('item_id')
    use_count = data.get('use_count', 1)
    
    if not item_id:
        return jsonify({'code': 400, 'msg': '缺少物品ID'})
    
    user_item = UserItem.query.filter_by(user_id=current_user.id, item_id=item_id).first()
    if not user_item:
        return jsonify({'code': 404, 'msg': '物品不存在'})
    
    item = ShopItem.query.get(item_id)
    
    if user_item.quantity < use_count:
        return jsonify({'code': 400, 'msg': '物品数量不足'})
    
    if item.item_type not in ['boost', 'effect']:
        return jsonify({'code': 400, 'msg': '该物品不可使用'})
    
    user_item.quantity -= use_count
    
    if user_item.quantity <= 0:
        db.session.delete(user_item)
    
    db.session.commit()
    
    reward_coins = item.price // 2
    if reward_coins > 0:
        add_coins(current_user.id, reward_coins, 'use_item', f'使用物品获得: {item.name}', item_id)
    
    return jsonify({
        'code': 200, 
        'msg': f'使用成功，获得 {reward_coins} 金币',
        'remaining': user_item.quantity if user_item.quantity > 0 else 0
    })


@backpack_bp.route('/api/sell', methods=['POST'])
@login_required
def api_sell():
    """出售物品"""
    data = request.get_json()
    item_id = data.get('item_id')
    sell_count = data.get('sell_count', 1)
    
    if not item_id:
        return jsonify({'code': 400, 'msg': '缺少物品ID'})
    
    user_item = UserItem.query.filter_by(user_id=current_user.id, item_id=item_id).first()
    if not user_item:
        return jsonify({'code': 404, 'msg': '物品不存在'})
    
    item = ShopItem.query.get(item_id)
    
    if user_item.quantity < sell_count:
        return jsonify({'code': 400, 'msg': '物品数量不足'})
    
    sell_price = (item.price // 2) * sell_count
    
    user_item.quantity -= sell_count
    
    if user_item.quantity <= 0:
        db.session.delete(user_item)
    
    add_coins(current_user.id, sell_price, 'sell_item', f'出售物品: {item.name}', item_id)
    
    db.session.commit()
    
    currency = get_or_create_currency(current_user.id)
    
    return jsonify({
        'code': 200, 
        'msg': f'出售成功，获得 {sell_price} 金币',
        'coins': currency.coins,
        'remaining': user_item.quantity if user_item.quantity > 0 else 0
    })


@backpack_bp.route('/api/discard', methods=['DELETE'])
@login_required
def api_discard():
    """丢弃物品"""
    data = request.get_json()
    item_id = data.get('item_id')
    discard_count = data.get('discard_count', 1)
    
    if not item_id:
        return jsonify({'code': 400, 'msg': '缺少物品ID'})
    
    user_item = UserItem.query.filter_by(user_id=current_user.id, item_id=item_id).first()
    if not user_item:
        return jsonify({'code': 404, 'msg': '物品不存在'})
    
    if user_item.is_equipped:
        return jsonify({'code': 400, 'msg': '请先卸下装备再丢弃'})
    
    if user_item.quantity < discard_count:
        return jsonify({'code': 400, 'msg': '物品数量不足'})
    
    user_item.quantity -= discard_count
    
    if user_item.quantity <= 0:
        db.session.delete(user_item)
    
    db.session.commit()
    
    return jsonify({
        'code': 200, 
        'msg': '丢弃成功',
        'remaining': user_item.quantity if user_item.quantity > 0 else 0
    })
