from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.auth.decorators import role_required
from app.services.anuncio_service import AnuncioService
from app.services.user_service import UserService
from app.services.area_service import AreaService
from app.services.tramite_service import TramiteService
from app.services.ventanilla_service import VentanillaService
from app.services.asignacion_service import AsignacionService
from app.services.suplente_service import SuplenteService

admin_area_bp = Blueprint("admin_area", __name__, url_prefix="/admin_area")

@admin_area_bp.route("/")
@login_required
@role_required("admin_area")
def dashboard():
    return render_template("admin_area/dashboard.html")