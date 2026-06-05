from app import create_app
from models import db
from models.user import User
from models.game import Game
from models.achievement import Achievement
from models.shop import ShopItem, DailyChallenge, GameEvent
from models.lottery import Lottery, LotteryPrize
from models.badge import Badge
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import pymysql

def init_database():
    app = create_app()
    
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            if "Unknown database" in str(e):
                print("数据库不存在，正在创建...")
                db_uri = app.config['SQLALCHEMY_DATABASE_URI']
                parts = db_uri.replace('mysql+pymysql://', '').split('/')
                credentials = parts[0].split('@')[0]
                host = parts[0].split('@')[1]
                db_name = parts[1].split('?')[0]
                
                user, password = credentials.split(':')
                
                conn = pymysql.connect(host=host, user=user, password=password)
                cursor = conn.cursor()
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                cursor.close()
                conn.close()
                
                db.create_all()
            else:
                raise

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
            {'name': '初来乍到', 'description': '完成第一次游戏', 'category': 'play_count', 'target_value': 1, 'coin_reward': 10, 'game_id': None, 'icon': '🎮'},
            {'name': '游戏达人', 'description': '累计完成10次游戏', 'category': 'play_count', 'target_value': 10, 'coin_reward': 20, 'game_id': None, 'icon': '🏅'},
            {'name': '游戏大师', 'description': '累计完成50次游戏', 'category': 'play_count', 'target_value': 50, 'coin_reward': 50, 'game_id': None, 'icon': '🏆'},
            # Snake achievements
            {'name': '贪吃蛇新手', 'description': '贪吃蛇得分超过50', 'category': 'total_score', 'target_value': 50, 'coin_reward': 15, 'game_id': 1, 'icon': '🐍'},
            {'name': '贪吃蛇高手', 'description': '贪吃蛇得分超过200', 'category': 'total_score', 'target_value': 200, 'coin_reward': 30, 'game_id': 1, 'icon': '🔥'},
            # 2048 achievements
            {'name': '2048达人', 'description': '2048得分超过1000', 'category': 'total_score', 'target_value': 1000, 'coin_reward': 25, 'game_id': 2, 'icon': '🔢'},
            {'name': '2048大师', 'description': '2048得分超过5000', 'category': 'total_score', 'target_value': 5000, 'coin_reward': 50, 'game_id': 2, 'icon': '💎'},
            # Minesweeper achievements
            {'name': '扫雷专家', 'description': '扫雷初级通关（得分超过71）', 'category': 'total_score', 'target_value': 71, 'coin_reward': 20, 'game_id': 3, 'icon': '💣'},
            {'name': '扫雷大师', 'description': '扫雷中级通关（得分超过216）', 'category': 'total_score', 'target_value': 216, 'coin_reward': 40, 'game_id': 3, 'icon': '🏆'},
            # Tetris achievements
            {'name': '俄罗斯方块新手', 'description': '俄罗斯方块消除10行', 'category': 'total_score', 'target_value': 10, 'coin_reward': 15, 'game_id': 4, 'icon': '🧱'},
            {'name': '俄罗斯方块高手', 'description': '俄罗斯方块消除50行', 'category': 'total_score', 'target_value': 50, 'coin_reward': 35, 'game_id': 4, 'icon': '✨'},
            # Memory achievements
            {'name': '记忆达人', 'description': '记忆翻牌完美通关（步数等于配对数）', 'category': 'total_score', 'target_value': 100, 'coin_reward': 25, 'game_id': 5, 'icon': '🃏'},
            # Breakout achievements
            {'name': '打砖块高手', 'description': '打砖块得分超过500', 'category': 'total_score', 'target_value': 500, 'coin_reward': 25, 'game_id': 6, 'icon': '🏓'},
            # General collection achievement
            {'name': '全能玩家', 'description': '在所有游戏中都有得分记录', 'category': 'games_played', 'target_value': 6, 'coin_reward': 100, 'game_id': None, 'icon': '🌟'},
        ]

        for ad in achievements_data:
            ach = Achievement.query.filter_by(name=ad['name']).first()
            if not ach:
                ach = Achievement(**ad)
                db.session.add(ach)

        # Create shop items
        shop_items_data = [
            # ========== 皮肤类 ==========
            # 俄罗斯方块皮肤 (game_id=4)
            {'name': '经典方块', 'description': '经典俄罗斯方块配色，简约大方', 'icon': '🟫', 'item_type': 'skin', 'price': 50, 'game_id': 4, 'rarity': 'common', 'skin_config': '{"block_color": "#8B4513", "pattern": "classic", "effect": "none", "game_name": "俄罗斯方块"}'},
            {'name': '霓虹方块', 'description': '炫酷霓虹灯光效果，让方块闪耀', 'icon': '🔮', 'item_type': 'skin', 'price': 150, 'game_id': 4, 'rarity': 'epic', 'skin_config': '{"block_color": "#FF00FF", "pattern": "neon", "effect": "glow", "game_name": "俄罗斯方块"}'},
            {'name': '水彩方块', 'description': '柔和的水彩渐变，文艺清新', 'icon': '🎨', 'item_type': 'skin', 'price': 120, 'game_id': 4, 'rarity': 'rare', 'skin_config': '{"block_color": "#FFB6C1", "pattern": "watercolor", "effect": "gradient", "game_name": "俄罗斯方块"}'},
            {'name': '暗黑方块', 'description': '神秘暗黑风格，炫酷到底', 'icon': '🖤', 'item_type': 'skin', 'price': 100, 'game_id': 4, 'rarity': 'rare', 'skin_config': '{"block_color": "#2C2C2C", "pattern": "dark", "effect": "shadow", "game_name": "俄罗斯方块"}'},
            {'name': '彩虹方块', 'description': '彩虹七色变换，绚丽多彩', 'icon': '🌈', 'item_type': 'skin', 'price': 200, 'game_id': 4, 'rarity': 'legendary', 'skin_config': '{"block_color": "#FF0000", "pattern": "rainbow", "effect": "shimmer", "game_name": "俄罗斯方块"}'},
            {'name': '金色方块', 'description': '尊贵的金色方块，身份的象征', 'icon': '🟡', 'item_type': 'skin', 'price': 180, 'game_id': 4, 'rarity': 'legendary', 'skin_config': '{"block_color": "#FFD700", "pattern": "metallic", "effect": "shine", "game_name": "俄罗斯方块"}'},
            {'name': '海洋方块', 'description': '清凉海洋蓝，如同置身海底', 'icon': '🌊', 'item_type': 'skin', 'price': 130, 'game_id': 4, 'rarity': 'rare', 'skin_config': '{"block_color": "#00CED1", "pattern": "ocean", "effect": "wave", "game_name": "俄罗斯方块"}'},
            {'name': '森林方块', 'description': '自然森林绿，清新自然', 'icon': '🌲', 'item_type': 'skin', 'price': 110, 'game_id': 4, 'rarity': 'rare', 'skin_config': '{"block_color": "#228B22", "pattern": "forest", "effect": "leaf", "game_name": "俄罗斯方块"}'},
            
            # 贪吃蛇皮肤 (game_id=1)
            {'name': '绿色蛇身', 'description': '经典绿色小蛇，童年的回忆', 'icon': '🐍', 'item_type': 'skin', 'price': 50, 'game_id': 1, 'rarity': 'common', 'skin_config': '{"block_color": "#32CD32", "pattern": "classic", "effect": "none", "game_name": "贪吃蛇"}'},
            {'name': '蓝色蛇身', 'description': '蓝色冷酷风格，冷静应对', 'icon': '💎', 'item_type': 'skin', 'price': 80, 'game_id': 1, 'rarity': 'rare', 'skin_config': '{"block_color": "#4169E1", "pattern": "cool", "effect": "glow", "game_name": "贪吃蛇"}'},
            {'name': '粉色蛇身', 'description': '可爱粉红风格，少女心满满', 'icon': '💗', 'item_type': 'skin', 'price': 90, 'game_id': 1, 'rarity': 'rare', 'skin_config': '{"block_color": "#FF69B4", "pattern": "cute", "effect": "sparkle", "game_name": "贪吃蛇"}'},
            {'name': '金色蛇身', 'description': '金色炫酷小蛇，光芒四射', 'icon': '🌟', 'item_type': 'skin', 'price': 150, 'game_id': 1, 'rarity': 'epic', 'skin_config': '{"block_color": "#FFD700", "pattern": "golden", "effect": "shine", "game_name": "贪吃蛇"}'},
            {'name': '彩虹蛇身', 'description': '彩虹渐变小蛇，绚丽夺目', 'icon': '🦄', 'item_type': 'skin', 'price': 200, 'game_id': 1, 'rarity': 'legendary', 'skin_config': '{"block_color": "#FF0000", "pattern": "rainbow", "effect": "shimmer", "game_name": "贪吃蛇"}'},
            {'name': '暗黑蛇身', 'description': '神秘暗黑风格，霸气侧漏', 'icon': '🖤', 'item_type': 'skin', 'price': 100, 'game_id': 1, 'rarity': 'rare', 'skin_config': '{"block_color": "#1a1a1a", "pattern": "dark", "effect": "shadow", "game_name": "贪吃蛇"}'},
            {'name': '火焰蛇身', 'description': '烈焰般的红色，热情如火', 'icon': '🔥', 'item_type': 'skin', 'price': 160, 'game_id': 1, 'rarity': 'epic', 'skin_config': '{"block_color": "#FF4500", "pattern": "fire", "effect": "flame", "game_name": "贪吃蛇"}'},
            {'name': '冰霜蛇身', 'description': '冰晶般的蓝色，寒气逼人', 'icon': '❄️', 'item_type': 'skin', 'price': 160, 'game_id': 1, 'rarity': 'epic', 'skin_config': '{"block_color": "#00FFFF", "pattern": "ice", "effect": "crystal", "game_name": "贪吃蛇"}'},
            
            # 打砖块皮肤 (game_id=6)
            {'name': '霓虹球', 'description': '炫酷霓虹球效果，发光闪烁', 'icon': '✨', 'item_type': 'skin', 'price': 120, 'game_id': 6, 'rarity': 'rare', 'skin_config': '{"block_color": "#FF00FF", "pattern": "neon", "effect": "glow", "game_name": "打砖块"}'},
            {'name': '火焰球', 'description': '烈焰包裹的球，燃烧一切', 'icon': '🔥', 'item_type': 'skin', 'price': 140, 'game_id': 6, 'rarity': 'epic', 'skin_config': '{"block_color": "#FF4500", "pattern": "fire", "effect": "trail", "game_name": "打砖块"}'},
            {'name': '星光球', 'description': '星星点点的球，璀璨夺目', 'icon': '⭐', 'item_type': 'skin', 'price': 130, 'game_id': 6, 'rarity': 'epic', 'skin_config': '{"block_color": "#FFD700", "pattern": "star", "effect": "sparkle", "game_name": "打砖块"}'},
            {'name': '彩虹球', 'description': '彩虹色的球，七彩斑斓', 'icon': '🌈', 'item_type': 'skin', 'price': 180, 'game_id': 6, 'rarity': 'legendary', 'skin_config': '{"block_color": "#FF0000", "pattern": "rainbow", "effect": "shimmer", "game_name": "打砖块"}'},
            {'name': '经典球', 'description': '经典白色球，简约不简单', 'icon': '⚪', 'item_type': 'skin', 'price': 50, 'game_id': 6, 'rarity': 'common', 'skin_config': '{"block_color": "#FFFFFF", "pattern": "classic", "effect": "none", "game_name": "打砖块"}'},
            
            # 2048皮肤 (game_id=2)
            {'name': '经典2048', 'description': '经典橙色风格，简约大方', 'icon': '🟧', 'item_type': 'skin', 'price': 50, 'game_id': 2, 'rarity': 'common', 'skin_config': '{"block_color": "#ED9121", "pattern": "classic", "effect": "none", "game_name": "2048"}'},
            {'name': '霓虹2048', 'description': '霓虹灯光效果，炫酷潮流', 'icon': '🔮', 'item_type': 'skin', 'price': 150, 'game_id': 2, 'rarity': 'epic', 'skin_config': '{"block_color": "#FF00FF", "pattern": "neon", "effect": "glow", "game_name": "2048"}'},
            {'name': '暗黑2048', 'description': '暗黑风格护眼，高端大气', 'icon': '🖤', 'item_type': 'skin', 'price': 100, 'game_id': 2, 'rarity': 'rare', 'skin_config': '{"block_color": "#2C2C2C", "pattern": "dark", "effect": "shadow", "game_name": "2048"}'},
            {'name': '彩虹2048', 'description': '彩虹渐变风格，绚丽多彩', 'icon': '🌈', 'item_type': 'skin', 'price': 200, 'game_id': 2, 'rarity': 'legendary', 'skin_config': '{"block_color": "#FF0000", "pattern": "rainbow", "effect": "shimmer", "game_name": "2048"}'},
            
            # ========== 主题类 ==========
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

        # Create new achievements (achievement.py models)
        # game_id: None = any game, 1-6 = specific game
        # 俄罗斯方块 id=4, 2048 id=2
        new_achievements_data = [
            # 游戏次数类
            {'name': '初次游戏', 'description': '第一次玩游戏', 'icon': '🎮', 'category': 'play_count', 'target_value': 1, 'coin_reward': 10, 'game_id': None},
            {'name': '游戏达人', 'description': '游戏次数达到100', 'icon': '🏆', 'category': 'play_count', 'target_value': 100, 'coin_reward': 100, 'game_id': None},
            {'name': '游戏大师', 'description': '游戏次数达到500', 'icon': '👑', 'category': 'play_count', 'target_value': 500, 'coin_reward': 200, 'game_id': None},
            # 连续登录类
            {'name': '连登3天', 'description': '连续登录3天', 'icon': '🔥', 'category': 'login_streak', 'target_value': 3, 'coin_reward': 30, 'game_id': None},
            {'name': '连登7天', 'description': '连续登录7天', 'icon': '⭐', 'category': 'login_streak', 'target_value': 7, 'coin_reward': 70, 'game_id': None},
            {'name': '连登30天', 'description': '连续登录30天', 'icon': '💎', 'category': 'login_streak', 'target_value': 30, 'coin_reward': 300, 'game_id': None},
            # 达到分数类 - 2048
            {'name': '2048达人', 'description': '2048达到5000分', 'icon': '🔢', 'category': 'reach_score', 'target_value': 5000, 'coin_reward': 50, 'game_id': 2},
            {'name': '2048大师', 'description': '2048达到10000分', 'icon': '🌟', 'category': 'reach_score', 'target_value': 10000, 'coin_reward': 100, 'game_id': 2},
            # 达到分数类 - 俄罗斯方块
            {'name': '俄罗斯方块新手', 'description': '俄罗斯方块达到5000分', 'icon': '🧱', 'category': 'reach_score', 'target_value': 5000, 'coin_reward': 50, 'game_id': 4},
            {'name': '俄罗斯大师', 'description': '俄罗斯方块达到10000分', 'icon': '🏅', 'category': 'reach_score', 'target_value': 10000, 'coin_reward': 100, 'game_id': 4},
            {'name': '俄罗斯之王', 'description': '俄罗斯方块达到50000分', 'icon': '👑', 'category': 'reach_score', 'target_value': 50000, 'coin_reward': 300, 'game_id': 4},
            # 累计分数类
            {'name': '积分积累', 'description': '累计分数达到10000', 'icon': '📊', 'category': 'total_score', 'target_value': 10000, 'coin_reward': 100, 'game_id': None},
            {'name': '积分达人', 'description': '累计分数达到100000', 'icon': '🔥', 'category': 'total_score', 'target_value': 100000, 'coin_reward': 500, 'game_id': None},
        ]

        for nad in new_achievements_data:
            ach = Achievement.query.filter_by(name=nad['name']).first()
            if not ach:
                ach = Achievement(**nad)
                db.session.add(ach)

        # Create lottery (幸运转盘)
        lottery = Lottery.query.filter_by(name='幸运转盘').first()
        if not lottery:
            lottery = Lottery(
                name='幸运转盘',
                description='花费金币转动转盘，赢取稀有皮肤、金币奖励！',
                cost=100,
                is_active=True
            )
            db.session.add(lottery)
            db.session.commit()

            # Create lottery prizes
            prizes_data = [
                {'name': '谢谢参与', 'prize_type': 'none', 'prize_value': 0, 'probability': 0.40, 'stock': -1, 'icon': '😢'},
                {'name': '50金币', 'prize_type': 'coins', 'prize_value': 50, 'probability': 0.30, 'stock': -1, 'icon': '💰'},
                {'name': '100金币', 'prize_type': 'coins', 'prize_value': 100, 'probability': 0.15, 'stock': -1, 'icon': '💰💰'},
                {'name': '稀有皮肤', 'prize_type': 'skin', 'prize_value': 1, 'probability': 0.10, 'stock': 10, 'icon': '🎁'},
                {'name': '传说皮肤', 'prize_type': 'skin', 'prize_value': 2, 'probability': 0.05, 'stock': 3, 'icon': '👑'},
            ]

            for pd in prizes_data:
                prize = LotteryPrize(
                    lottery_id=lottery.id,
                    name=pd['name'],
                    prize_type=pd['prize_type'],
                    prize_value=pd['prize_value'],
                    probability=pd['probability'],
                    stock=pd['stock'],
                    icon=pd['icon']
                )
                db.session.add(prize)

        # Create badges (champion badges + achievement badges)
        # game_id: None = global, 1-6 = specific game
        badges_data = [
            # Global champion badges
            {'name': '全站周冠军', 'description': '全站上周积分榜冠军', 'icon': '👑', 'badge_type': 'weekly_champion', 'game_id': None, 'valid_days': 7},
            {'name': '全站月冠军', 'description': '全站上月积分榜冠军', 'icon': '🏆', 'badge_type': 'monthly_champion', 'game_id': None, 'valid_days': 30},
            # Game-specific champion badges
            {'name': '贪吃蛇周冠军', 'description': '贪吃蛇上周排行榜冠军', 'icon': '🐍', 'badge_type': 'weekly_champion', 'game_id': 1, 'valid_days': 7},
            {'name': '贪吃蛇月冠军', 'description': '贪吃蛇上月排行榜冠军', 'icon': '🏅', 'badge_type': 'monthly_champion', 'game_id': 1, 'valid_days': 30},
            {'name': '2048周冠军', 'description': '2048上周排行榜冠军', 'icon': '🔢', 'badge_type': 'weekly_champion', 'game_id': 2, 'valid_days': 7},
            {'name': '2048月冠军', 'description': '2048上月排行榜冠军', 'icon': '🎯', 'badge_type': 'monthly_champion', 'game_id': 2, 'valid_days': 30},
            {'name': '扫雷周冠军', 'description': '扫雷上周排行榜冠军', 'icon': '💣', 'badge_type': 'weekly_champion', 'game_id': 3, 'valid_days': 7},
            {'name': '扫雷月冠军', 'description': '扫雷上月排行榜冠军', 'icon': '💥', 'badge_type': 'monthly_champion', 'game_id': 3, 'valid_days': 30},
            {'name': '俄罗斯方块周冠军', 'description': '俄罗斯方块上周排行榜冠军', 'icon': '🧱', 'badge_type': 'weekly_champion', 'game_id': 4, 'valid_days': 7},
            {'name': '俄罗斯方块月冠军', 'description': '俄罗斯方块上月排行榜冠军', 'icon': '🏰', 'badge_type': 'monthly_champion', 'game_id': 4, 'valid_days': 30},
            {'name': '记忆翻牌周冠军', 'description': '记忆翻牌上周排行榜冠军', 'icon': '🃏', 'badge_type': 'weekly_champion', 'game_id': 5, 'valid_days': 7},
            {'name': '记忆翻牌月冠军', 'description': '记忆翻牌上月排行榜冠军', 'icon': '🎴', 'badge_type': 'monthly_champion', 'game_id': 5, 'valid_days': 30},
            {'name': '打砖块周冠军', 'description': '打砖块上周排行榜冠军', 'icon': '🏓', 'badge_type': 'weekly_champion', 'game_id': 6, 'valid_days': 7},
            {'name': '打砖块月冠军', 'description': '打砖块上月排行榜冠军', 'icon': '🎱', 'badge_type': 'monthly_champion', 'game_id': 6, 'valid_days': 30},
            # Achievement badges (earned through achievements)
            {'name': '初出茅庐', 'description': '完成第一次游戏', 'icon': '🌱', 'badge_type': 'special', 'game_id': None, 'valid_days': 0},
            {'name': '游戏达人', 'description': '游戏次数达到100', 'icon': '🎮', 'badge_type': 'special', 'game_id': None, 'valid_days': 0},
            {'name': '连胜将军', 'description': '连续登录7天', 'icon': '🔥', 'badge_type': 'special', 'game_id': None, 'valid_days': 0},
            {'name': '2048大师', 'description': '2048达到10000分', 'icon': '💎', 'badge_type': 'special', 'game_id': 2, 'valid_days': 0},
            {'name': '俄罗斯之王', 'description': '俄罗斯方块达到50000分', 'icon': '👑', 'badge_type': 'special', 'game_id': 4, 'valid_days': 0},
        ]

        for bd in badges_data:
            badge = Badge.query.filter_by(name=bd['name']).first()
            if not badge:
                badge = Badge(**bd)
                db.session.add(badge)

        db.session.commit()

        # Link achievements to badges
        achievement_badge_map = {
            '初次游戏': '初出茅庐',
            '游戏达人': '游戏达人',
            '连登7天': '连胜将军',
            '2048大师': '2048大师',
            '俄罗斯之王': '俄罗斯之王',
        }

        for ach_name, badge_name in achievement_badge_map.items():
            ach = Achievement.query.filter_by(name=ach_name).first()
            badge = Badge.query.filter_by(name=badge_name).first()
            if ach and badge:
                ach.badge_reward = badge.id

        db.session.commit()
        print('数据库初始化完成！')
        print('管理员账号: admin / admin123')
        print('已添加商城商品、每日挑战、活动数据、成就系统、幸运转盘和徽章系统')

if __name__ == '__main__':
    init_database()