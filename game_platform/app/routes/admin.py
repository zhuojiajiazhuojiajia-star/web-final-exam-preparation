from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models.user import User
from models.game import Game, GameScore, Achievement
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

    stats = {
        'total_users': total_users,
        'total_games_played': total_games_played,
        'total_games': total_games,
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
