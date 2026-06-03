from app import create_app
from models import db
from models.user import User
from models.game import Game, Achievement
from models.shop import ShopItem, DailyChallenge, GameEvent
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

def init_database():
    app = create_app()

    with app.app_context():
        db.create_all()

        # Create admin user if not exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@game.com',
                nickname='管理员',
                password_hash=generate_password_hash('admin123'),
                is_admin=True,
                bio='系统管理员'
            )
            db.session.add(admin)

        # Create games if not exist
        games_data = [
            {'name': '贪吃蛇', 'description': '经典贪吃蛇游戏，控制蛇吃食物不断变长，避免撞墙和自身。', 'icon': '🐍', 'category': '经典'},
            {'name': '2048', 'description': '数字合并益智游戏，滑动合并相同数字，挑战2048！', 'icon': '🔢', 'category': '益智'},
            {'name': '扫雷', 'description': '经典扫雷游戏，根据数字提示找出所有地雷。', 'icon': '💣', 'category': '策略'},
            {'name': '俄罗斯方块', 'description': '经典俄罗斯方块，消除整行得分，方块下落速度逐渐加快。', 'icon': '🧱', 'category': '经典'},
            {'name': '记忆翻牌', 'description': '记忆力挑战游戏，翻牌配对，用最少步数找到所有配对。', 'icon': '🃏', 'category': '益智'},
            {'name': '打砖块', 'description': '经典打砖块游戏，控制挡板反弹球消除所有砖块。', 'icon': '🏓', 'category': '动作'},
        ]

        for gd in games_data:
            game = Game.query.filter_by(name=gd['name']).first()
            if not game:
                game = Game(**gd)
                db.session.add(game)

        # Create achievements
        # game_id: null = any game, 1-6 = specific game
        achievements_data = [
            # General achievements
            {'name': '初来乍到', 'description': '完成第一次游戏', 'condition_type': 'play_count', 'condition_value': 1, 'points': 10, 'game_id': None},
            {'name': '游戏达人', 'description': '累计完成10次游戏', 'condition_type': 'play_count', 'condition_value': 10, 'points': 20, 'game_id': None},
            {'name': '游戏大师', 'description': '累计完成50次游戏', 'condition_type': 'play_count', 'condition_value': 50, 'points': 50, 'game_id': None},
            # Snake achievements
            {'name': '贪吃蛇新手', 'description': '贪吃蛇得分超过50', 'condition_type': 'high_score', 'condition_value': 50, 'points': 15, 'game_id': 1},
            {'name': '贪吃蛇高手', 'description': '贪吃蛇得分超过200', 'condition_type': 'high_score', 'condition_value': 200, 'points': 30, 'game_id': 1},
            # 2048 achievements
            {'name': '2048达人', 'description': '2048得分超过1000', 'condition_type': 'high_score', 'condition_value': 1000, 'points': 25, 'game_id': 2},
            {'name': '2048大师', 'description': '2048得分超过5000', 'condition_type': 'high_score', 'condition_value': 5000, 'points': 50, 'game_id': 2},
            # Minesweeper achievements
            {'name': '扫雷专家', 'description': '扫雷初级通关（得分超过71）', 'condition_type': 'high_score', 'condition_value': 71, 'points': 20, 'game_id': 3},
            {'name': '扫雷大师', 'description': '扫雷中级通关（得分超过216）', 'condition_type': 'high_score', 'condition_value': 216, 'points': 40, 'game_id': 3},
            # Tetris achievements
            {'name': '俄罗斯方块新手', 'description': '俄罗斯方块消除10行', 'condition_type': 'high_score', 'condition_value': 10, 'points': 15, 'game_id': 4},
            {'name': '俄罗斯方块高手', 'description': '俄罗斯方块消除50行', 'condition_type': 'high_score', 'condition_value': 50, 'points': 35, 'game_id': 4},
            # Memory achievements
            {'name': '记忆达人', 'description': '记忆翻牌完美通关（步数等于配对数）', 'condition_type': 'high_score', 'condition_value': 100, 'points': 25, 'game_id': 5},
            # Breakout achievements
            {'name': '打砖块高手', 'description': '打砖块得分超过500', 'condition_type': 'high_score', 'condition_value': 500, 'points': 25, 'game_id': 6},
            # General collection achievement
            {'name': '全能玩家', 'description': '在所有游戏中都有得分记录', 'condition_type': 'games_played', 'condition_value': 6, 'points': 100, 'game_id': None},
        ]

        for ad in achievements_data:
            ach = Achievement.query.filter_by(name=ad['name']).first()
            if not ach:
                ach = Achievement(**ad)
                db.session.add(ach)

        # Create shop items
        shop_items_data = [
            # 皮肤类
            {'name': '金色蛇身', 'description': '贪吃蛇专属金色皮肤', 'icon': '🌟', 'item_type': 'skin', 'price': 100, 'game_id': 1, 'rarity': 'rare'},
            {'name': '彩虹方块', 'description': '俄罗斯方块彩虹主题', 'icon': '🌈', 'item_type': 'skin', 'price': 150, 'game_id': 4, 'rarity': 'epic'},
            {'name': '霓虹球', 'description': '打砖块霓虹球效果', 'icon': '✨', 'item_type': 'skin', 'price': 120, 'game_id': 6, 'rarity': 'rare'},
            
            # 主题类
            {'name': '暗黑主题', 'description': '全局暗黑模式主题', 'icon': '🌙', 'item_type': 'theme', 'price': 200, 'game_id': None, 'rarity': 'epic'},
            {'name': '复古主题', 'description': '经典复古像素风格', 'icon': '👾', 'item_type': 'theme', 'price': 180, 'game_id': None, 'rarity': 'rare'},
            {'name': '樱花主题', 'description': '粉色樱花飘落效果', 'icon': '🌸', 'item_type': 'theme', 'price': 250, 'game_id': None, 'rarity': 'legendary'},
            
            # 特效类
            {'name': '粒子爆炸', 'description': '消除时的粒子爆炸特效', 'icon': '💥', 'item_type': 'effect', 'price': 80, 'game_id': None, 'rarity': 'common'},
            {'name': '星光闪烁', 'description': '得分时的星光闪烁效果', 'icon': '⭐', 'item_type': 'effect', 'price': 100, 'game_id': None, 'rarity': 'rare'},
            
            # 徽章类
            {'name': '新手徽章', 'description': '显示在个人主页的新手徽章', 'icon': '🔰', 'item_type': 'badge', 'price': 50, 'game_id': None, 'rarity': 'common'},
            {'name': '高手徽章', 'description': '显示在个人主页的高手徽章', 'icon': '🏆', 'item_type': 'badge', 'price': 300, 'game_id': None, 'rarity': 'legendary'},
            {'name': '爱心徽章', 'description': '可爱的爱心徽章', 'icon': '❤️', 'item_type': 'badge', 'price': 150, 'game_id': None, 'rarity': 'rare'},
            
            # 增益类
            {'name': '双倍金币卡', 'description': '30分钟内金币获取翻倍', 'icon': '💰', 'item_type': 'boost', 'price': 500, 'game_id': None, 'rarity': 'epic'},
            {'name': '幸运加成', 'description': '增加10%分数加成', 'icon': '🍀', 'item_type': 'boost', 'price': 200, 'game_id': None, 'rarity': 'rare'},
        ]
        
        for sid in shop_items_data:
            item = ShopItem.query.filter_by(name=sid['name']).first()
            if not item:
                item = ShopItem(**sid)
                db.session.add(item)
        
        # Create daily challenges
        daily_challenges_data = [
            {'name': '每日登录', 'description': '登录游戏平台', 'icon': '👋', 'challenge_type': 'play_count', 'target_value': 1, 'coin_reward': 10, 'difficulty': 'easy'},
            {'name': '游戏玩家', 'description': '完成3局游戏', 'icon': '🎮', 'challenge_type': 'play_count', 'target_value': 3, 'coin_reward': 20, 'difficulty': 'normal'},
            {'name': '游戏达人', 'description': '完成5局游戏', 'icon': '🎯', 'challenge_type': 'play_count', 'target_value': 5, 'coin_reward': 35, 'difficulty': 'normal'},
            {'name': '高分挑战', 'description': '任意游戏得分超过100', 'icon': '💯', 'challenge_type': 'reach_score', 'target_value': 100, 'coin_reward': 25, 'difficulty': 'normal'},
            {'name': '高分达人', 'description': '任意游戏得分超过500', 'icon': '🔥', 'challenge_type': 'reach_score', 'target_value': 500, 'coin_reward': 50, 'difficulty': 'hard'},
            {'name': '总分积累', 'description': '累计总分达到1000', 'icon': '📊', 'challenge_type': 'total_score', 'target_value': 1000, 'coin_reward': 40, 'difficulty': 'normal'},
        ]
        
        for dcd in daily_challenges_data:
            challenge = DailyChallenge.query.filter_by(name=dcd['name']).first()
            if not challenge:
                challenge = DailyChallenge(**dcd)
                db.session.add(challenge)
        
        # Create sample events
        now = datetime.now()
        events_data = [
            {
                'name': '周末双倍金币',
                'description': '周末期间所有游戏金币奖励翻倍！',
                'icon': '🎉',
                'event_type': 'double_coins',
                'start_time': now - timedelta(hours=1),
                'end_time': now + timedelta(days=2),
                'coin_bonus': 100,
                'score_multiplier': 1.0
            },
        ]
        
        for ed in events_data:
            event = GameEvent.query.filter_by(name=ed['name']).first()
            if not event:
                event = GameEvent(**ed)
                db.session.add(event)

        db.session.commit()
        print('数据库初始化完成！')
        print('管理员账号: admin / admin123')
        print('已添加商城商品、每日挑战和活动数据')

if __name__ == '__main__':
    init_database()