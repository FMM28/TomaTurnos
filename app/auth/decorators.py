from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user

def role_required(role):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("auth.login"))

            if current_user.role != role:
                flash(
                    "No tienes permisos para acceder a esta sección.",
                    "warning"
                )
                return redirect(url_for(f"{current_user.role}.dashboard"))

            return f(*args, **kwargs)
        return wrapper
    return decorator
