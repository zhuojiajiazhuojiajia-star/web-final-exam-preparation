from flask import Flask
from config import Config
from models import db, login_manager
import os

def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config.from_object(Config)

    # ensure upload folder exists
    os.makedirs(app.config.get('UPLOAD_FOLDER', 'static/img/uploads'), exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)

    # register blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.game import game_bp
    from app.routes.user import user_bp
    from app.routes.admin import admin_bp
    from app.routes.shop import shop_bp
    from app.routes.backpack import backpack_bp
    from app.routes.lottery import lottery_bp
    from app.routes.achievement import achievement_bp
    from app.routes.badge import badge_bp
    from app.routes.multiplayer import multiplayer_bp
    from app.routes.friend import friend_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(game_bp, url_prefix='/game')
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(shop_bp, url_prefix='/shop')
    app.register_blueprint(backpack_bp, url_prefix='/backpack')
    app.register_blueprint(lottery_bp, url_prefix='/lottery')
    app.register_blueprint(achievement_bp, url_prefix='/achievement')
    app.register_blueprint(multiplayer_bp, url_prefix='/multiplayer')
    app.register_blueprint(badge_bp, url_prefix='/badge')
    app.register_blueprint(friend_bp, url_prefix='/friend')

    return app
