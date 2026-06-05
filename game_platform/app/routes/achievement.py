from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from models import db
from models.achievement import Achievement, UserAchievement
from models.user import User
from models.game import Game
from datetime import datetime

achievement_bp = Blueprint('achievement', __name__)


@achievement_bp.route('/')
@login_required
def index():
    """用户成就页面"""
    achievements = Achievement.query.filter_by(is_active=True).all()
    
    # 获取用户成就进度
    user_achievements = {}
    for ua in UserAchievement.query.filter_by(user_id=current_user.id).all():
        user_achievements[ua.achievement_id] = ua
    
    # 按分类分组
    categories = {
        'play_count': {'name': '游戏次数', 'achievements': []},
        'total_score': {'name': '累计分数', 'achievements': []},
        'login_streak': {'name': '连续登录', 'achievements': []},
        'win_games': {'name': '获胜次数', 'achievements': []},
        'reach_score': {'name': '达到分数', 'achievements': []},
    }
    
    for ach in achievements:
        if ach.category in categories:
            user_ach = user_achievements.get(ach.id)
            categories[ach.category]['achievements'].append({
                'achievement': ach,
                'user_achievement': user_ach
            })
    
    # 统计
    total_count = len(achievements)
    completed_count = sum(1 for ua in user_achievements.values() if ua.is_completed)
    claimed_count = sum(1 for ua in user_achievements.values() if ua.claimed_at)
    
    return render_template('achievement/index.html',
                           categories=categories,
                           total_count=total_count,
                           completed_count=completed_count,
                           claimed_count=claimed_count)


@achievement_bp.route('/api/list')
@login_required
def api_list():
    """获取用户成就列表 API"""
    achievements = Achievement.query.filter_by(is_active=True).all()
    user_achievements = {
        ua.achievement_id: ua 
        for ua in UserAchievement.query.filter_by(user_id=current_user.id).all()
    }
    
    result = []
    for ach in achievements:
        user_ach = user_achievements.get(ach.id)
        result.append({
            'id': ach.id,
            'name': ach.name,
            'description': ach.description,
            'icon': ach.icon,
            'category': ach.category,
            'target_value': ach.target_value,
            'coin_reward': ach.coin_reward,
            'game_id': ach.game_id,
            'progress': user_ach.progress if user_ach else 0,
            'is_completed': user_ach.is_completed if user_ach else False,
            'completed_at': user_ach.completed_at.isoformat() if user_ach and user_ach.completed_at else None,
            'claimed_at': user_ach.claimed_at.isoformat() if user_ach and user_ach.claimed_at else None,
        })
    
    return jsonify({'code': 200, 'data': result})


@achievement_bp.route('/api/progress', methods=['POST'])
@login_required
def api_progress():
    """更新成就进度 API"""
    data = request.get_json()
    if not data:
        return jsonify({'code': 400, 'msg': '无效的数据'})
    
    category = data.get('category')
    value = data.get('value', 0)
    game_id = data.get('game_id')
    
    if not category:
        return jsonify({'code': 400, 'msg': '缺少category参数'})
    
    # 查找需要更新的成就
    query = Achievement.query.filter_by(category=category, is_active=True)
    if category == 'reach_score' and game_id:
        # 对于reach_score，需要匹配特定游戏或通用成就
        query = query.filter(db.or_(
            Achievement.game_id == game_id,
            Achievement.game_id == None
        ))
    elif category != 'reach_score':
        query = query.filter_by(game_id=None)  # 非特定游戏的成就
    
    achievements = query.all()
    
    updated = []
    for ach in achievements:
        # 获取或创建用户成就
        user_ach = UserAchievement.query.filter_by(
            user_id=current_user.id,
            achievement_id=ach.id
        ).first()
        
        if not user_ach:
            user_ach = UserAchievement(
                user_id=current_user.id,
                achievement_id=ach.id,
                progress=0
            )
            db.session.add(user_ach)
        
        # 如果已领取，跳过
        if user_ach.claimed_at:
            continue
        
        # 更新进度
        if category == 'win_games':
            # 获胜次数需要检查value是否为真
            if value:
                user_ach.progress += 1
        else:
            user_ach.progress = max(user_ach.progress, value)
        
        # 检查是否完成
        if not user_ach.is_completed and user_ach.progress >= ach.target_value:
            user_ach.is_completed = True
            user_ach.completed_at = datetime.now()
        
        updated.append({
            'achievement_id': ach.id,
            'achievement_name': ach.name,
            'progress': user_ach.progress,
            'target_value': ach.target_value,
            'is_completed': user_ach.is_completed
        })
    
    db.session.commit()
    
    return jsonify({'code': 200, 'msg': '进度更新成功', 'updated': updated})


@achievement_bp.route('/api/claim', methods=['POST'])
@login_required
def api_claim():
    """领取成就奖励 API"""
    data = request.get_json()
    if not data:
        return jsonify({'code': 400, 'msg': '无效的数据'})
    
    achievement_id = data.get('achievement_id')
    if not achievement_id:
        return jsonify({'code': 400, 'msg': '缺少achievement_id'})
    
    achievement = Achievement.query.get(achievement_id)
    if not achievement:
        return jsonify({'code': 404, 'msg': '成就不存在'})
    
    user_ach = UserAchievement.query.filter_by(
        user_id=current_user.id,
        achievement_id=achievement_id
    ).first()
    
    if not user_ach:
        return jsonify({'code': 400, 'msg': '成就未解锁'})
    
    if not user_ach.is_completed:
        return jsonify({'code': 400, 'msg': '成就未完成'})
    
    if user_ach.claimed_at:
        return jsonify({'code': 400, 'msg': '奖励已领取'})
    
    # 领取奖励
    user_ach.claimed_at = datetime.now()
    
    # 添加金币奖励
    from models.shop import UserCurrency, CoinTransaction
    currency = UserCurrency.query.filter_by(user_id=current_user.id).first()
    if not currency:
        currency = UserCurrency(user_id=current_user.id, coins=0)
        db.session.add(currency)
        db.session.flush()
    
    currency.coins += achievement.coin_reward
    
    transaction = CoinTransaction(
        user_id=current_user.id,
        amount=achievement.coin_reward,
        transaction_type='achievement',
        description=f'成就奖励: {achievement.name}'
    )
    db.session.add(transaction)
    
    # 奖励徽章
    from models.badge import Badge, UserBadge
    if achievement.badge_reward:
        badge = Badge.query.get(achievement.badge_reward)
        if badge:
            existing_badge = UserBadge.query.filter_by(user_id=current_user.id, badge_id=badge.id).first()
            if not existing_badge:
                user_badge = UserBadge(
                    user_id=current_user.id,
                    badge_id=badge.id,
                    earned_at=datetime.now(),
                    expires_at=None  # 永久有效
                )
                db.session.add(user_badge)
    
    db.session.commit()
    
    return jsonify({
        'code': 200, 
        'msg': f'领取成功！获得 {achievement.coin_reward} 金币',
        'coins': currency.coins
    })
