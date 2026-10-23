import os

from dotenv import load_dotenv
from flask import Flask

from app.auth.login_manager import load_user
from app.commands import activate
from app.licensing import LicenseClient, init_flask
from app.services.audio_service import AudioService

from .config import Config
from .extensions import bcrypt, csrf, db, login_manager, migrate, socketio

__all__ = ["create_app"]


def create_app():
    load_dotenv()

    app = Flask(__name__.split(".")[0])
    app.config.from_object(Config)

    app.cli.add_command(activate)

    csrf.init_app(app)

    lic = LicenseClient(
        server_url=os.getenv("LICENSE_SERVER_URL"),
        product="tomaturnos",
        public_key=os.getenv("LICENSE_PUBLIC_KEY"),
        storage_path=os.getenv("LICENSE_STORAGE_PATH")
    )
    app.extensions["license_client"] = lic
    init_flask(app, csrf, lic)

    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db.session.remove()

    from .routes import register_blueprints
    register_blueprints(app)

    socketio.init_app(
        app,
        cors_allowed_origins="*",
        async_mode="threading"
    )

    AudioService.start(app)

    return app