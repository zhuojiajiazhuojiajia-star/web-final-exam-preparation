from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models.game import Game, GameScore
from models import db
from sqlalchemy import func

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    games = Game.query.filter_by(is_active=True).all()
    # Get popular games (most played)
    popular_games = Game.query.filter_by(is_active=True).order_by(Game.play_count.desc()).limit(4).all()
    # Get latest scores
    latest_scores = GameScore.query.order_by(GameScore.created_at.desc()).limit(10).all()
    return render_template('index.html', games=games, popular_games=popular_games, latest_scores=latest_scores)

@main_bp.route('/about')
def about():
    return render_template('about.html')
