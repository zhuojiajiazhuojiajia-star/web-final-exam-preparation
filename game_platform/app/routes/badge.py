from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from models import db
from models.badge import Badge, UserBadge
from models.game import Game, GameScore
from models.user import User
from datetime import datetime, timedelta
from sqlalchemy import func, extract
import calendar

badge_bp = Blueprint('badge', __name__)

@badge_bp.route('/')
def index():
    """徽章页面"""
    return render_template('badge/index.html')

@badge_bp.route('/api/list')
@login_required
def api_list():
    """获取用户徽章列表"""
    user_badges = UserBadge.query.filter_by(user_id=current_user.id).order_by(UserBadge.earned_at.desc()).all()
    
    badges_data = []
    for ub in user_badges:
        badge = ub.badge
        badges_data.append({
            'id': badge.id,
            'name': badge.name,
            'description': badge.description,
            'icon': badge.icon,
            'badge_type': badge.badge_type,
            'game_id': badge.game_id,
            'game_name': badge.game.name if badge.game else '全局',
            'earned_at': ub.earned_at.strftime('%Y-%m-%d') if ub.earned_at else None,
            'expires_at': ub.expires_at.strftime('%Y-%m-%d') if ub.expires_at else None,
            'is_expired': ub.expires_at < datetime.now() if ub.expires_at else False
        })
    
    return jsonify({'code': 200, 'data': badges_data})

@badge_bp.route('/api/leaderboard')
@login_required
def api_leaderboard():
    """获取排行榜信息，支持weekly/monthly"""
    period = request.args.get('period', 'weekly')  # weekly or monthly
    game_id = request.args.get('game_id', type=int)
    
    now = datetime.now()
    
    if period == 'weekly':
        # 本周开始（周一）
        start_date = now - timedelta(days=now.weekday())
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    else:  # monthly
        # 本月开始
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # 查询该期间的最高分
    query = db.session.query(
        GameScore.user_id,
        func.max(GameScore.score).label('best_score')
    ).filter(GameScore.created_at >= start_date)
    
    if game_id:
        query = query.filter(GameScore.game_id == game_id)
    
    query = query.group_by(GameScore.user_id).order_by(func.max(GameScore.score).desc()).limit(10)
    results = query.all()
    
    leaderboard_data = []
    for rank, result in enumerate(results, 1):
        user = User.query.get(result.user_id)
        game = Game.query.get(game_id) if game_id else None
        
        # 检查用户是否有对应的冠军徽章
        badge_type = 'weekly_champion' if period == 'weekly' else 'monthly_champion'
        champion_badge = Badge.query.filter_by(badge_type=badge_type, game_id=game_id).first()
        
        has_badge = False
        if champion_badge:
            user_badge = UserBadge.query.filter_by(user_id=user.id, badge_id=champion_badge.id).first()
            has_badge = user_badge is not None
        
        leaderboard_data.append({
            'rank': rank,
            'user_id': user.id,
            'username': user.nickname or user.username,
            'avatar': user.avatar,
            'best_score': result.best_score,
            'game_name': game.name if game else '全平台',
            'has_champion_badge': has_badge,
            'is_current_champion': rank == 1
        })
    
    return jsonify({
        'code': 200, 
        'data': leaderboard_data,
        'period': period,
        'game_name': game.name if game else '全平台'
    })

@badge_bp.route('/api/check_champions')
def api_check_champions():
    """定时任务：检查并颁发冠军徽章"""
    now = datetime.now()
    
    # 检查是否需要颁发周冠军徽章（每周一凌晨）
    if now.weekday() == 0 and now.hour == 0:
        award_weekly_champions()
    
    # 检查是否需要颁发月冠军徽章（每月1号凌晨）
    if now.day == 1 and now.hour == 0:
        award_monthly_champions()
    
    return jsonify({'code': 200, 'msg': '检查完成'})

def award_weekly_champions():
    """颁发上周冠军徽章"""
    # 计算上周时间范围
    now = datetime.now()
    last_week_end = now - timedelta(days=now.weekday() + 1)
    last_week_start = last_week_end - timedelta(days=6)
    last_week_start = last_week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    last_week_end = last_week_end.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    # 获取所有游戏
    games = Game.query.all()
    
    for game in games:
        # 查询该游戏上周最高分
        top_score = GameScore.query.filter(
            GameScore.game_id == game.id,
            GameScore.created_at >= last_week_start,
            GameScore.created_at <= last_week_end
        ).order_by(GameScore.score.desc()).first()
        
        if top_score:
            # 查找或创建周冠军徽章
            badge = Badge.query.filter_by(badge_type='weekly_champion', game_id=game.id).first()
            if not badge:
                badge = Badge(
                    name=f'{game.name}周冠军',
                    description=f'{game.name}上周排行榜冠军',
                    icon='🏆',
                    badge_type='weekly_champion',
                    game_id=game.id,
                    valid_days=7
                )
                db.session.add(badge)
                db.session.commit()
            
            # 检查用户是否已有该徽章
            existing = UserBadge.query.filter_by(user_id=top_score.user_id, badge_id=badge.id).first()
            if not existing:
                user_badge = UserBadge(
                    user_id=top_score.user_id,
                    badge_id=badge.id,
                    earned_at=now,
                    expires_at=now + timedelta(days=7)
                )
                db.session.add(user_badge)
    
    # 全局周冠军
    global_top = db.session.query(
        GameScore.user_id,
        func.sum(GameScore.score).label('total_score')
    ).filter(
        GameScore.created_at >= last_week_start,
        GameScore.created_at <= last_week_end
    ).group_by(GameScore.user_id).order_by(func.sum(GameScore.score).desc()).first()
    
    if global_top:
        badge = Badge.query.filter_by(badge_type='weekly_champion', game_id=None).first()
        if not badge:
            badge = Badge(
                name='全站周冠军',
                description='全站上周积分榜冠军',
                icon='👑',
                badge_type='weekly_champion',
                game_id=None,
                valid_days=7
            )
            db.session.add(badge)
            db.session.commit()
        
        existing = UserBadge.query.filter_by(user_id=global_top.user_id, badge_id=badge.id).first()
        if not existing:
            user_badge = UserBadge(
                user_id=global_top.user_id,
                badge_id=badge.id,
                earned_at=now,
                expires_at=now + timedelta(days=7)
            )
            db.session.add(user_badge)
    
    db.session.commit()

def award_monthly_champions():
    """颁发上月冠军徽章"""
    now = datetime.now()
    # 上个月
    if now.month == 1:
        last_month_start = datetime(now.year - 1, 12, 1)
    else:
        last_month_start = datetime(now.year, now.month - 1, 1)
    
    last_month_end = datetime(now.year, now.month, 1) - timedelta(seconds=1)
    
    games = Game.query.all()
    
    for game in games:
        top_score = GameScore.query.filter(
            GameScore.game_id == game.id,
            GameScore.created_at >= last_month_start,
            GameScore.created_at <= last_month_end
        ).order_by(GameScore.score.desc()).first()
        
        if top_score:
            badge = Badge.query.filter_by(badge_type='monthly_champion', game_id=game.id).first()
            if not badge:
                badge = Badge(
                    name=f'{game.name}月冠军',
                    description=f'{game.name}上月排行榜冠军',
                    icon='🏅',
                    badge_type='monthly_champion',
                    game_id=game.id,
                    valid_days=30
                )
                db.session.add(badge)
                db.session.commit()
            
            existing = UserBadge.query.filter_by(user_id=top_score.user_id, badge_id=badge.id).first()
            if not existing:
                user_badge = UserBadge(
                    user_id=top_score.user_id,
                    badge_id=badge.id,
                    earned_at=now,
                    expires_at=now + timedelta(days=30)
                )
                db.session.add(user_badge)
    
    # 全局月冠军
    global_top = db.session.query(
        GameScore.user_id,
        func.sum(GameScore.score).label('total_score')
    ).filter(
        GameScore.created_at >= last_month_start,
        GameScore.created_at <= last_month_end
    ).group_by(GameScore.user_id).order_by(func.sum(GameScore.score).desc()).first()
    
    if global_top:
        badge = Badge.query.filter_by(badge_type='monthly_champion', game_id=None).first()
        if not badge:
            badge = Badge(
                name='全站月冠军',
                description='全站上月积分榜冠军',
                icon='👑',
                badge_type='monthly_champion',
                game_id=None,
                valid_days=30
            )
            db.session.add(badge)
            db.session.commit()
        
        existing = UserBadge.query.filter_by(user_id=global_top.user_id, badge_id=badge.id).first()
        if not existing:
            user_badge = UserBadge(
                user_id=global_top.user_id,
                badge_id=badge.id,
                earned_at=now,
                expires_at=now + timedelta(days=30)
            )
            db.session.add(user_badge)
    
    db.session.commit()

@badge_bp.route('/api/all')
@login_required
def api_all_badges():
    """获取所有徽章（用于徽章商城）"""
    badges = Badge.query.all()
    badges_data = []
    
    for badge in badges:
        # 检查用户是否已有该徽章
        user_has = UserBadge.query.filter_by(user_id=current_user.id, badge_id=badge.id).first() is not None
        
        badges_data.append({
            'id': badge.id,
            'name': badge.name,
            'description': badge.description,
            'icon': badge.icon,
            'badge_type': badge.badge_type,
            'game_id': badge.game_id,
            'game_name': badge.game.name if badge.game else '全局',
            'valid_days': badge.valid_days,
            'user_has': user_has
        })
    
    return jsonify({'code': 200, 'data': badges_data})
