from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from models.game import Game, GameScore, GameFavorite
from models.user import User
from models.game import Achievement, UserAchievement
from models import db
from datetime import datetime
from functools import wraps

game_bp = Blueprint('game', __name__)

def check_achievement(user_id, game_id, score):
    """Check and unlock achievements after a game"""
    user = User.query.get(user_id)
    if not user:
        return []

    newly_unlocked = []

    # Check play count achievements (game_id is None = any game)
    play_count = user.games_played
    achievements = Achievement.query.filter_by(condition_type='play_count', game_id=None).all()
    for ach in achievements:
        if play_count >= ach.condition_value:
            existing = UserAchievement.query.filter_by(user_id=user_id, achievement_id=ach.id).first()
            if not existing:
                ua = UserAchievement(user_id=user_id, achievement_id=ach.id)
                db.session.add(ua)
                newly_unlocked.append(ach.name)

    # Check high score achievements for current game
    # Get achievements that match current game OR are for any game (game_id=None)
    achievements = Achievement.query.filter_by(condition_type='high_score').filter(
        (Achievement.game_id == game_id) | (Achievement.game_id == None)
    ).all()
    for ach in achievements:
        if score >= ach.condition_value:
            existing = UserAchievement.query.filter_by(user_id=user_id, achievement_id=ach.id).first()
            if not existing:
                ua = UserAchievement(user_id=user_id, achievement_id=ach.id)
                db.session.add(ua)
                newly_unlocked.append(ach.name)

    # Check games played achievements (game_id is None = any game)
    games_with_scores = GameScore.query.filter_by(user_id=user_id).distinct(GameScore.game_id).count()
    achievements = Achievement.query.filter_by(condition_type='games_played', game_id=None).all()
    for ach in achievements:
        if games_with_scores >= ach.condition_value:
            existing = UserAchievement.query.filter_by(user_id=user_id, achievement_id=ach.id).first()
            if not existing:
                ua = UserAchievement(user_id=user_id, achievement_id=ach.id)
                db.session.add(ua)
                newly_unlocked.append(ach.name)

    return newly_unlocked

@game_bp.route('/play/<int:game_id>')
@login_required
def play(game_id):
    game = Game.query.get_or_404(game_id)
    # Increment play count
    game.play_count += 1
    db.session.commit()

    template_map = {
        1: 'games/snake.html',
        2: 'games/game2048.html',
        3: 'games/minesweeper.html',
        4: 'games/tetris.html',
        5: 'games/memory.html',
        6: 'games/breakout.html',
    }
    template = template_map.get(game_id, 'games/snake.html')
    return render_template(template, game=game)

@game_bp.route('/submit_score', methods=['POST'])
@login_required
def submit_score():
    data = request.get_json()
    game_id = data.get('game_id')
    score = data.get('score', 0)
    duration = data.get('duration', 0)
    difficulty = data.get('difficulty', 'normal')

    if not game_id or score is None:
        return jsonify({'code': 400, 'msg': '参数错误'})

    game_score = GameScore(
        user_id=current_user.id,
        game_id=game_id,
        score=int(score),
        duration=int(duration),
        difficulty=difficulty
    )
    db.session.add(game_score)

    # Update user stats
    current_user.games_played += 1
    current_user.total_score += int(score)

    # Check achievements
    newly_unlocked = check_achievement(current_user.id, game_id, int(score))

    db.session.commit()

    # Get best score for this game
    best = GameScore.query.filter_by(user_id=current_user.id, game_id=game_id).order_by(GameScore.score.desc()).first()

    response = {
        'code': 200,
        'msg': '成绩已提交',
        'data': {
            'score': int(score),
            'best_score': best.score if best else int(score),
            'total_games': current_user.games_played,
            'new_achievements': newly_unlocked
        }
    }
    return jsonify(response)

@game_bp.route('/leaderboard/<int:game_id>')
def leaderboard(game_id):
    game = Game.query.get_or_404(game_id)
    page = request.args.get('page', 1, type=int)
    per_page = 20

    scores = GameScore.query.filter_by(game_id=game_id).order_by(GameScore.score.desc()).paginate(page=page, per_page=per_page)

    return render_template('game/leaderboard.html', game=game, scores=scores)

@game_bp.route('/favorite/<int:game_id>', methods=['POST'])
@login_required
def favorite(game_id):
    existing = GameFavorite.query.filter_by(user_id=current_user.id, game_id=game_id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify({'code': 200, 'msg': '已取消收藏', 'favorited': False})
    else:
        fav = GameFavorite(user_id=current_user.id, game_id=game_id)
        db.session.add(fav)
        db.session.commit()
        return jsonify({'code': 200, 'msg': '已收藏', 'favorited': True})

@game_bp.route('/history')
@login_required
def history():
    page = request.args.get('page', 1, type=int)
    per_page = 15
    scores = GameScore.query.filter_by(user_id=current_user.id).order_by(GameScore.created_at.desc()).paginate(page=page, per_page=per_page)
    return render_template('game/history.html', scores=scores)