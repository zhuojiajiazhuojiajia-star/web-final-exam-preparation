import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'game-platform-secret-key-2024'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:123456@localhost:3306/game_platform?charset=utf8mb4'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'app/static/img/uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
