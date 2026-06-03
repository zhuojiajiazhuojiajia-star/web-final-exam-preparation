from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from models.user import User
from models.game import GameScore, GameFavorite
from models.achievement import UserAchievement, Achievement
from models.shop import UserCurrency, UserItem, ShopItem
from models import db
from werkzeug.utils import secure_filename
import os
import time

user_bp = Blueprint('user', __name__)

@user_bp.route('/profile')
@login_required
def profile():
    favorites = GameFavorite.query.filter_by(user_id=current_user.id).all()
    achievements = UserAchievement.query.filter_by(user_id=current_user.id).all()
    all_achievements = Achievement.query.all()
    achievement_dict = {a.achievement_id: a for a in achievements}

    # Get best scores per game
    from sqlalchemy import func
    best_scores = db.session.query(
        GameScore.game_id, func.max(GameScore.score).label('best_score')
    ).filter_by(user_id=current_user.id).group_by(GameScore.game_id).all()
    
    # 获取用户金币信息
    currency = UserCurrency.query.filter_by(user_id=current_user.id).first()
    if not currency:
        currency = UserCurrency(user_id=current_user.id, coins=100)
        db.session.add(currency)
        db.session.commit()
    
    # 获取用户拥有的物品
    user_items = UserItem.query.filter_by(user_id=current_user.id).all()
    items_with_details = []
    for ui in user_items:
        item = ShopItem.query.get(ui.item_id)
        if item:
            items_with_details.append({
                'user_item': ui,
                'item': item
            })

    return render_template('user/profile.html',
                          favorites=favorites,
                          achievements=achievements,
                          all_achievements=all_achievements,
                          achievement_dict=achievement_dict,
                          best_scores=best_scores,
                          currency=currency,
                          items_with_details=items_with_details)

@user_bp.route('/edit_profile', methods=['POST'])
@login_required
def edit_profile():
    nickname = request.form.get('nickname', '').strip()
    bio = request.form.get('bio', '').strip()

    if nickname:
        current_user.nickname = nickname
    if bio:
        current_user.bio = bio[:200]

    db.session.commit()
    flash('资料更新成功！', 'success')
    return redirect(url_for('user.profile'))

@user_bp.route('/change_password', methods=['POST'])
@login_required
def change_password():
    old_password = request.form.get('old_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')

    if not current_user.check_password(old_password):
        flash('原密码错误', 'error')
        return redirect(url_for('user.profile'))

    if new_password != confirm_password:
        flash('两次密码不一致', 'error')
        return redirect(url_for('user.profile'))

    if len(new_password) < 6:
        flash('新密码长度至少6位', 'error')
        return redirect(url_for('user.profile'))

    current_user.set_password(new_password)
    db.session.commit()
    flash('密码修改成功！', 'success')
    return redirect(url_for('user.profile'))

@user_bp.route('/upload_avatar', methods=['POST'])
@login_required
def upload_avatar():
    if 'avatar' not in request.files:
        flash('请选择头像文件', 'error')
        return redirect(url_for('user.profile'))

    file = request.files['avatar']
    if file.filename == '':
        flash('请选择头像文件', 'error')
        return redirect(url_for('user.profile'))

    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''

    if ext not in allowed_extensions:
        flash('仅支持 png/jpg/jpeg/gif 格式', 'error')
        return redirect(url_for('user.profile'))

    filename = secure_filename(f'{current_user.id}_{int(time.time())}.{ext}')
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    current_user.avatar = filename
    db.session.commit()
    flash('头像更新成功！', 'success')
    return redirect(url_for('user.profile'))
