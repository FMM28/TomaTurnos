from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import current_user, login_required
from app.auth.decorators import role_required
from app.services.ventanilla_service import VentanillaService
from app.services.ticket_tramite_service import TicketTramiteService

ventanilla_bp = Blueprint("ventanilla", __name__, url_prefix="/ventanilla")

@ventanilla_bp.route("/")
@login_required
@role_required("ventanilla")
def dashboard():
    turnos_en_espera = TicketTramiteService.get_cola_para_usuario(current_user.id_usuario)
    turno_actual = None

    return render_template(
        "ventanilla/dashboard.html",
        turnos_en_espera=turnos_en_espera,
        turno_actual=turno_actual,
        usuario=current_user,
        ventanilla=VentanillaService.get_ventanilla_by_usuario(current_user.id),
    )


@ventanilla_bp.post("/llamar-siguiente")
@login_required
@role_required("ventanilla")
def llamar_siguiente():
    flash("Turno llamado", "success")
    return redirect(url_for("ventanilla.dashboard"))


@ventanilla_bp.post("/rellamar")
@login_required
@role_required("ventanilla")
def rellamar():
    flash("Turno vuelto a llamar")
    return redirect(url_for("ventanilla.dashboard"))


@ventanilla_bp.post("/reasignar")
@login_required
@role_required("ventanilla")
def reasignar():
    flash("Turno reasignado")
    return redirect(url_for("ventanilla.dashboard"))


@ventanilla_bp.post("/finalizar")
@login_required
@role_required("ventanilla")
def finalizar():
    flash("Turno finalizado")
    return redirect(url_for("ventanilla.dashboard"))


@ventanilla_bp.route("/cola")
@login_required
@role_required("ventanilla")
def cola():
    cola = TicketTramiteService.get_cola_para_usuario(
        current_user.id_usuario
    )

    return {
        "total": len(cola),
        "cola": [
            {
                "ticket": tt.ticket.turno,
                "tramite": tt.tramite.name,
                "id_ticket_tramite": tt.id_ticket_tramite
            }
            for tt in cola
        ]
    }
