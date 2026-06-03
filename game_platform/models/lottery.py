from models import db
from datetime import datetime


class Lottery(db.Model):
    """抽奖活动"""
    __tablename__ = 'lotteries'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200))
    cost = db.Column(db.Integer, default=100)  # 每次抽奖消耗金币
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    # 关联奖品
    prizes = db.relationship('LotteryPrize', backref='lottery', lazy='dynamic')


class LotteryPrize(db.Model):
    """抽奖奖品"""
    __tablename__ = 'lottery_prizes'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    lottery_id = db.Column(db.Integer, db.ForeignKey('lotteries.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    prize_type = db.Column(db.String(20), nullable=False)  # skin, coins, badge, none
    prize_value = db.Column(db.Integer, default=0)  # 奖品具体值（金币数量、物品ID等）
    probability = db.Column(db.Float, default=0)  # 概率（0-1之间）
    stock = db.Column(db.Integer, default=-1)  # 库存，-1表示无限
    icon = db.Column(db.String(50))  # emoji或图片路径


class UserLotteryRecord(db.Model):
    """用户抽奖记录"""
    __tablename__ = 'user_lottery_records'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    lottery_id = db.Column(db.Integer, db.ForeignKey('lotteries.id'), nullable=False)
    prize_id = db.Column(db.Integer, db.ForeignKey('lottery_prizes.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    # 关联用户
    user = db.relationship('User', backref=db.backref('lottery_records', lazy='dynamic'))
    # 关联抽奖
    lottery = db.relationship('Lottery', backref=db.backref('records', lazy='dynamic'))
    # 关联奖品
    prize = db.relationship('LotteryPrize', backref=db.backref('records', lazy='dynamic'))
