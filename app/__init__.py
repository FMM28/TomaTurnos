from flask import Flask
from dotenv import load_dotenv
from .config import Config
from .extensions import db, migrate, bcrypt, login_manager, socketio, csrf
from app.auth.login_manager import load_user
from .routes import register_blueprints
import app.sockets
from app import models
from app.services.audio_service import AudioService
from app.licensing import LicenseClient,init_flask
import os

def create_app():
    load_dotenv() 
    
    app = Flask(__name__)
    app.config.from_object(Config)
    
    csrf.init_app(app)
    
    lic = LicenseClient(
        server_url=os.getenv("LICENSE_SERVER_URL"),
        product="tomaturnos",
        public_key=os.getenv("LICENSE_PUBLIC_KEY"),
        storage_path=os.getenv("LICENSE_STORAGE_PATH")
    )
    init_flask(app, csrf, lic)

    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db.session.remove()

    register_blueprints(app)

    socketio.init_app(
        app,
        cors_allowed_origins="*",
        async_mode="threading"
    )

    AudioService.start(app)

    return app
