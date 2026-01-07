from .login import auth_bp
from .root import main_bp
from .admin import admin_bp
from .ventanilla import ventanilla_bp
from .kiosco import kiosco_bp
from .anuncios import anuncios_bp

def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(ventanilla_bp)
    app.register_blueprint(kiosco_bp)
    app.register_blueprint(anuncios_bp)
