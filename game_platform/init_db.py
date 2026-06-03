from app import create_app
from models import db
from models.user import User
from models.game import Game, Achievement
from werkzeug.security import generate_password_hash
from datetime import datetime

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

        db.session.commit()
        print('数据库初始化完成！')
        print('管理员账号: admin / admin123')

if __name__ == '__main__':
    init_database()