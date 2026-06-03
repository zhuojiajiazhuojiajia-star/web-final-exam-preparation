from models import db
from datetime import datetime

class Badge(db.Model):
    __tablename__ = 'badges'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200))
    icon = db.Column(db.String(100))
    badge_type = db.Column(db.String(30))  # weekly_champion, monthly_champion, all_time, special
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=True)  # null = global
    valid_days = db.Column(db.Integer, default=0)  # 0 = permanent
    created_at = db.Column(db.DateTime, default=datetime.now)

    user_badges = db.relationship('UserBadge', backref='badge', lazy='dynamic')

class UserBadge(db.Model):
    __tablename__ = 'user_badges'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    badge_id = db.Column(db.Integer, db.ForeignKey('badges.id'), nullable=False)
    earned_at = db.Column(db.DateTime, default=datetime.now)
    expires_at = db.Column(db.DateTime, nullable=True)

    __table_args__ = (db.UniqueConstraint('user_id', 'badge_id', 'earned_at'),)
