from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from flask_socketio import emit
from app.extensions import socketio
from app.auth.decorators import role_required
from app.services.ticket_tramite_service import TicketTramiteService
from app.services.atencion_service import AtencionService
from app.services.turno_service import TurnoService
from app.services.speak_service import AudioService

ventanilla_bp = Blueprint("ventanilla", __name__, url_prefix="/ventanilla")

@ventanilla_bp.route("/")
@login_required
@role_required("ventanilla")
def dashboard():
    turnos_en_espera = TicketTramiteService.get_cola_para_usuario(current_user.id_usuario)
    turno_actual = AtencionService.get_atencion_activa_por_usuario(current_user.id_usuario)

    return render_template(
        "ventanilla/dashboard.html",
        turnos_en_espera=turnos_en_espera,
        turno_actual=turno_actual,
        usuario=current_user,
    )


@ventanilla_bp.post("/llamar-siguiente")
@login_required
@role_required("ventanilla")
def llamar_siguiente():
    sigiente = TicketTramiteService.get_siguiente_para_usuario(current_user.id_usuario)
    if not sigiente:
        flash("No hay turnos esperando", "warning")
        return redirect(url_for("ventanilla.dashboard"))
    atencion, error = AtencionService.iniciar_atencion(
        ticket_tramite=sigiente,
        id_usuario=current_user.id_usuario
    )

    socketio.emit("turnos_en_espera", TurnoService.get_turnos_en_espera())
    socketio.emit("turnos_en_llamado", TurnoService.get_turnos_en_llamado())
    socketio.sleep(0.1)
    
    AudioService.anunciar_turno(sigiente.ticket.turno, sigiente.tramite.ventanilla.name)


    if error:
        flash(f"Error al llamar el turno: {error}", "error")
        return redirect(url_for("ventanilla.dashboard"))
    
    flash("Turno llamado", "success")
    return redirect(url_for("ventanilla.dashboard",turno_actual=atencion))


@ventanilla_bp.post("/rellamar")
@login_required
@role_required("ventanilla")
def rellamar():
    atencion = AtencionService.get_atencion_activa_por_usuario(current_user.id_usuario)

    if not atencion:
        flash("No hay turno activo para volver a llamar", "warning")
        return redirect(url_for("ventanilla.dashboard"))

    tiempo_transcurrido = AtencionService.tiempo_desde_ultimo_llamado(atencion)
    
    if tiempo_transcurrido is not None and tiempo_transcurrido < 5:
        tiempo_restante = 5 - int(tiempo_transcurrido)
        flash(f"Debes esperar {tiempo_restante} segundo(s) antes de volver a llamar", "warning")
        return redirect(url_for("ventanilla.dashboard"))

    AtencionService.rellamar(atencion)
    AudioService.anunciar_turno(atencion.ticket_tramite.ticket.turno, atencion.ventanilla.name)

    flash("Turno vuelto a llamar", "success")
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
    atencion = AtencionService.get_atencion_activa_por_usuario(current_user.id_usuario)

    descripcion = request.form.get("descripcion")

    AtencionService.finalizar_atencion(atencion, descripcion)

    flash("Turno finalizado", "success")
    return redirect(url_for("ventanilla.dashboard"))


@ventanilla_bp.route("/ventanilla/cancelar", methods=["POST"])
@login_required
@role_required("ventanilla")
def cancelar():
    atencion = AtencionService.get_atencion_activa_por_usuario(current_user.id_usuario)
    
    motivo = request.form.get("motivo_cancelacion")
    motivo_otro = request.form.get("motivo_otro")

    if motivo == "otro":
        descripcion = motivo_otro
    elif motivo == "trabajador_no_acudio":
        descripcion = "El trabajador no acudió al llamado"
    elif motivo == "error_registro":
        descripcion = "Error de registro"
    else:
        descripcion = None

    AtencionService.cancelar_atencion(atencion, descripcion)

    flash("Trámite cancelado correctamente", "warning")
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
                "id_ticket_tramite": tt.id_ticket_tramite,
                "estado": tt.estado
            }
            for tt in cola
        ]
    }
