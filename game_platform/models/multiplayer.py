from models import db
from datetime import datetime

class GameRoom(db.Model):
    __tablename__ = 'game_rooms'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=False)
    room_name = db.Column(db.String(100), nullable=False)
    player1_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    player2_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    player1_score = db.Column(db.Integer, default=0)
    player2_score = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='waiting')  # waiting, playing, finished
    winner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    game = db.relationship('Game', backref='rooms')
    player1 = db.relationship('User', foreign_keys=[player1_id], backref='rooms_as_player1')
    player2 = db.relationship('User', foreign_keys=[player2_id], backref='rooms_as_player2')
    winner = db.relationship('User', foreign_keys=[winner_id])


class GameInvite(db.Model):
    __tablename__ = 'game_invites'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    from_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    to_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, rejected
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    from_user = db.relationship('User', foreign_keys=[from_user_id], backref='sent_invites')
    to_user = db.relationship('User', foreign_keys=[to_user_id], backref='received_invites')
    game = db.relationship('Game', backref='invites')
