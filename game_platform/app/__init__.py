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

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(game_bp, url_prefix='/game')
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    return app
