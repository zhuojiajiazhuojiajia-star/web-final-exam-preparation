from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models.user import User
from models.game import Game, GameScore, Achievement
from models.shop import ShopItem, DailyChallenge, GameEvent, UserCurrency
from models import db
from functools import wraps

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('需要管理员权限', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    total_users = User.query.count()
    total_games_played = GameScore.query.count()
    total_games = Game.query.count()
    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
    recent_scores = GameScore.query.order_by(GameScore.created_at.desc()).limit(10).all()
    
    # 商城统计
    total_shop_items = ShopItem.query.count()
    total_coins_in_circulation = db.session.query(db.func.sum(UserCurrency.coins)).scalar() or 0

    stats = {
        'total_users': total_users,
        'total_games_played': total_games_played,
        'total_games': total_games,
        'total_shop_items': total_shop_items,
        'total_coins': total_coins_in_circulation,
    }

    return render_template('admin/dashboard.html', stats=stats, recent_users=recent_users, recent_scores=recent_scores)

@admin_bp.route('/users')
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('admin/users.html', users=users)

@admin_bp.route('/games')
@admin_required
def games():
    games = Game.query.all()
    return render_template('admin/games.html', games=games)

@admin_bp.route('/toggle_game/<int:game_id>', methods=['POST'])
@admin_required
def toggle_game(game_id):
    game = Game.query.get_or_404(game_id)
    game.is_active = not game.is_active
    db.session.commit()
    return jsonify({'code': 200, 'msg': f'游戏已{"上架" if game.is_active else "下架"}'})

# ========== 商城管理 ==========

@admin_bp.route('/shop')
@admin_required
def shop_items():
    """商城商品管理"""
    items = ShopItem.query.order_by(ShopItem.created_at.desc()).all()
    return render_template('admin/shop.html', items=items)

@admin_bp.route('/shop/add', methods=['GET', 'POST'])
@admin_required
def add_shop_item():
    """添加商品"""
    if request.method == 'POST':
        item = ShopItem(
            name=request.form.get('name'),
            description=request.form.get('description'),
            icon=request.form.get('icon'),
            item_type=request.form.get('item_type'),
            price=int(request.form.get('price', 0)),
            rarity=request.form.get('rarity', 'common'),
            stock=int(request.form.get('stock', -1)),
            game_id=request.form.get('game_id') or None
        )
        db.session.add(item)
        db.session.commit()
        flash('商品添加成功', 'success')
        return redirect(url_for('admin.shop_items'))
    
    games = Game.query.all()
    return render_template('admin/shop_form.html', games=games, item=None)

@admin_bp.route('/shop/edit/<int:item_id>', methods=['GET', 'POST'])
@admin_required
def edit_shop_item(item_id):
    """编辑商品"""
    item = ShopItem.query.get_or_404(item_id)
    
    if request.method == 'POST':
        item.name = request.form.get('name')
        item.description = request.form.get('description')
        item.icon = request.form.get('icon')
        item.item_type = request.form.get('item_type')
        item.price = int(request.form.get('price', 0))
        item.rarity = request.form.get('rarity', 'common')
        item.stock = int(request.form.get('stock', -1))
        item.game_id = request.form.get('game_id') or None
        item.is_active = request.form.get('is_active') == 'on'
        
        db.session.commit()
        flash('商品更新成功', 'success')
        return redirect(url_for('admin.shop_items'))
    
    games = Game.query.all()
    return render_template('admin/shop_form.html', games=games, item=item)

@admin_bp.route('/shop/toggle/<int:item_id>', methods=['POST'])
@admin_required
def toggle_shop_item(item_id):
    """上架/下架商品"""
    item = ShopItem.query.get_or_404(item_id)
    item.is_active = not item.is_active
    db.session.commit()
    return jsonify({'code': 200, 'msg': f'商品已{"上架" if item.is_active else "下架"}'})

@admin_bp.route('/shop/delete/<int:item_id>', methods=['POST'])
@admin_required
def delete_shop_item(item_id):
    """删除商品"""
    item = ShopItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({'code': 200, 'msg': '商品已删除'})

# ========== 每日挑战管理 ==========

@admin_bp.route('/challenges')
@admin_required
def challenges():
    """每日挑战管理"""
    challenges = DailyChallenge.query.order_by(DailyChallenge.created_at.desc()).all()
    return render_template('admin/challenges.html', challenges=challenges)

@admin_bp.route('/challenges/add', methods=['GET', 'POST'])
@admin_required
def add_challenge():
    """添加每日挑战"""
    if request.method == 'POST':
        challenge = DailyChallenge(
            name=request.form.get('name'),
            description=request.form.get('description'),
            icon=request.form.get('icon'),
            challenge_type=request.form.get('challenge_type'),
            target_value=int(request.form.get('target_value', 1)),
            coin_reward=int(request.form.get('coin_reward', 10)),
            difficulty=request.form.get('difficulty', 'normal'),
            game_id=request.form.get('game_id') or None
        )
        db.session.add(challenge)
        db.session.commit()
        flash('挑战添加成功', 'success')
        return redirect(url_for('admin.challenges'))
    
    games = Game.query.all()
    return render_template('admin/challenge_form.html', games=games, challenge=None)

@admin_bp.route('/challenges/edit/<int:challenge_id>', methods=['GET', 'POST'])
@admin_required
def edit_challenge(challenge_id):
    """编辑每日挑战"""
    challenge = DailyChallenge.query.get_or_404(challenge_id)
    
    if request.method == 'POST':
        challenge.name = request.form.get('name')
        challenge.description = request.form.get('description')
        challenge.icon = request.form.get('icon')
        challenge.challenge_type = request.form.get('challenge_type')
        challenge.target_value = int(request.form.get('target_value', 1))
        challenge.coin_reward = int(request.form.get('coin_reward', 10))
        challenge.difficulty = request.form.get('difficulty', 'normal')
        challenge.game_id = request.form.get('game_id') or None
        challenge.is_active = request.form.get('is_active') == 'on'
        
        db.session.commit()
        flash('挑战更新成功', 'success')
        return redirect(url_for('admin.challenges'))
    
    games = Game.query.all()
    return render_template('admin/challenge_form.html', games=games, challenge=challenge)

@admin_bp.route('/challenges/toggle/<int:challenge_id>', methods=['POST'])
@admin_required
def toggle_challenge(challenge_id):
    """启用/禁用挑战"""
    challenge = DailyChallenge.query.get_or_404(challenge_id)
    challenge.is_active = not challenge.is_active
    db.session.commit()
    return jsonify({'code': 200, 'msg': f'挑战已{"启用" if challenge.is_active else "禁用"}'})

# ========== 活动管理 ==========

@admin_bp.route('/events')
@admin_required
def events():
    """活动管理"""
    from datetime import datetime
    events = GameEvent.query.order_by(GameEvent.start_time.desc()).all()
    return render_template('admin/events.html', events=events, now=datetime.now())

@admin_bp.route('/events/add', methods=['GET', 'POST'])
@admin_required
def add_event():
    """添加活动"""
    if request.method == 'POST':
        from datetime import datetime
        event = GameEvent(
            name=request.form.get('name'),
            description=request.form.get('description'),
            icon=request.form.get('icon'),
            event_type=request.form.get('event_type'),
            start_time=datetime.strptime(request.form.get('start_time'), '%Y-%m-%d %H:%M'),
            end_time=datetime.strptime(request.form.get('end_time'), '%Y-%m-%d %H:%M'),
            coin_bonus=int(request.form.get('coin_bonus', 0)),
            score_multiplier=float(request.form.get('score_multiplier', 1.0))
        )
        db.session.add(event)
        db.session.commit()
        flash('活动添加成功', 'success')
        return redirect(url_for('admin.events'))
    
    return render_template('admin/event_form.html', event=None)

@admin_bp.route('/events/toggle/<int:event_id>', methods=['POST'])
@admin_required
def toggle_event(event_id):
    """启用/禁用活动"""
    event = GameEvent.query.get_or_404(event_id)
    event.is_active = not event.is_active
    db.session.commit()
    return jsonify({'code': 200, 'msg': f'活动已{"启用" if event.is_active else "禁用"}'})
