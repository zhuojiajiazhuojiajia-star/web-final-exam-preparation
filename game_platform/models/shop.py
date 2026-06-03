from models import db
from datetime import datetime, date

# ========== 货币系统 ==========

class UserCurrency(db.Model):
    """用户货币账户"""
    __tablename__ = 'user_currency'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    coins = db.Column(db.Integer, default=0)  # 金币余额
    total_earned = db.Column(db.Integer, default=0)  # 累计获得
    total_spent = db.Column(db.Integer, default=0)  # 累计消费
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def add_coins(self, amount):
        """增加金币"""
        if amount > 0:
            self.coins += amount
            self.total_earned += amount
            return True
        return False
    
    def spend_coins(self, amount):
        """消费金币"""
        if amount > 0 and self.coins >= amount:
            self.coins -= amount
            self.total_spent += amount
            return True
        return False


class CoinTransaction(db.Model):
    """金币交易记录"""
    __tablename__ = 'coin_transactions'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)  # 正数为获得，负数为消费
    transaction_type = db.Column(db.String(30), nullable=False)  # game_reward, daily_task, purchase, admin
    description = db.Column(db.String(200))
    related_id = db.Column(db.Integer)  # 关联ID（游戏ID、任务ID、商品ID等）
    created_at = db.Column(db.DateTime, default=datetime.now)


# ========== 商城系统 ==========

class ShopItem(db.Model):
    """商城商品"""
    __tablename__ = 'shop_items'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200))
    icon = db.Column(db.String(100))  # emoji或图片路径
    item_type = db.Column(db.String(30), nullable=False)  # skin, theme, effect, badge, boost
    price = db.Column(db.Integer, nullable=False)  # 金币价格
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=True)  # null表示通用物品
    rarity = db.Column(db.String(20), default='common')  # common, rare, epic, legendary
    is_active = db.Column(db.Boolean, default=True)
    stock = db.Column(db.Integer, default=-1)  # -1表示无限库存
    sold_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 物品效果配置（JSON格式存储）
    effect_config = db.Column(db.Text)  # 如: {"color": "#ff0000", "speed_boost": 1.5}
    
    # 皮肤配置（JSON格式存储：颜色、图案、特效等）
    skin_config = db.Column(db.Text)  # 如: {"block_color": "#ff0000", "pattern": "neon", "effect": "glow"}


class UserItem(db.Model):
    """用户拥有的物品"""
    __tablename__ = 'user_items'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('shop_items.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)  # 物品数量，用于堆叠
    item_category = db.Column(db.String(30), default='skin')  # skin, badge, title, effect
    is_equipped = db.Column(db.Boolean, default=False)  # 是否装备中
    purchased_at = db.Column(db.DateTime, default=datetime.now)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'item_id', name='uix_user_item'),)


# ========== 每日挑战系统 ==========

class DailyChallenge(db.Model):
    """每日挑战任务配置"""
    __tablename__ = 'daily_challenges'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200))
    icon = db.Column(db.String(50))
    
    # 任务类型
    challenge_type = db.Column(db.String(30), nullable=False)
    # play_game: 玩指定游戏
    # reach_score: 达到指定分数
    # play_count: 游玩次数
    # win_games: 赢得游戏（达到一定分数）
    # total_score: 累计总分
    
    target_value = db.Column(db.Integer, nullable=False)  # 目标值
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=True)  # null表示任意游戏
    
    # 奖励
    coin_reward = db.Column(db.Integer, default=10)
    exp_reward = db.Column(db.Integer, default=0)
    
    is_active = db.Column(db.Boolean, default=True)
    difficulty = db.Column(db.String(20), default='normal')  # easy, normal, hard
    created_at = db.Column(db.DateTime, default=datetime.now)


class UserDailyChallenge(db.Model):
    """用户每日挑战进度"""
    __tablename__ = 'user_daily_challenges'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('daily_challenges.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)  # 任务日期
    
    current_progress = db.Column(db.Integer, default=0)  # 当前进度
    is_completed = db.Column(db.Boolean, default=False)
    is_claimed = db.Column(db.Boolean, default=False)  # 是否已领取奖励
    completed_at = db.Column(db.DateTime)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'challenge_id', 'date'),)


# ========== 活动系统 ==========

class GameEvent(db.Model):
    """游戏活动"""
    __tablename__ = 'game_events'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(50))
    
    # 活动类型
    event_type = db.Column(db.String(30), nullable=False)
    # double_coins: 双倍金币
    # double_score: 双倍分数
    # special_challenge: 特别挑战
    # limited_item: 限时商品
    
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    
    # 奖励配置
    coin_bonus = db.Column(db.Integer, default=0)
    score_multiplier = db.Column(db.Float, default=1.0)
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
