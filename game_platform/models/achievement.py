from models import db
from datetime import datetime

class Achievement(db.Model):
    __tablename__ = 'achievements_new'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200))
    icon = db.Column(db.String(100))
    category = db.Column(db.String(30))  # play_count, total_score, login_streak, win_games, reach_score
    target_value = db.Column(db.Integer, nullable=False)
    coin_reward = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 关联特定游戏，null表示通用成就
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=True)
    
    user_achievements = db.relationship('UserAchievement', backref='achievement', lazy='dynamic')


class UserAchievement(db.Model):
    __tablename__ = 'user_achievements_new'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    achievement_id = db.Column(db.Integer, db.ForeignKey('achievements_new.id'), nullable=False)
    progress = db.Column(db.Integer, default=0)
    is_completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    claimed_at = db.Column(db.DateTime, nullable=True)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'achievement_id'),)
