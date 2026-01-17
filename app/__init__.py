from flask import Flask
from .config import Config
from .extensions import db,migrate, bcrypt, login_manager, socketio
from app.auth.login_manager import load_user
from .routes import register_blueprints
import app.sockets
from app import models
from app.services.speak_service import AudioService

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    register_blueprints(app)

    socketio.init_app(app, cors_allowed_origins="*", async_mode='eventlet')
    
    AudioService.start()

    return app
