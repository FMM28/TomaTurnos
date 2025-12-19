from flask import Blueprint, render_template
from app.auth.decorators import login_required, role_required

ventanilla_bp = Blueprint("ventanilla", __name__, url_prefix="/ventanilla")

@ventanilla_bp.route("/")
@login_required
@role_required("ventanilla")
def dashboard():
    return render_template("ventanilla/dashboard.html")
