from flask import Blueprint, render_template
from app.auth.decorators import login_required, role_required

kiosco_bp = Blueprint("kiosco", __name__, url_prefix="/kiosco")

@kiosco_bp.route("/")
@login_required
@role_required("kiosco")
def dashboard():
    return render_template("kiosco/dashboard.html")
