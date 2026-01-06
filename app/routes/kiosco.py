from flask import Blueprint, render_template,request, session, redirect, url_for, flash
from app.services.area_service import AreaService
from app.services.tramite_service import TramiteService
from app.services.ticket_service import TicketService
from app.services.ticket_tramite_service import TicketTramiteService
from app.services.turno_service import TurnoService
from app.services.impresion_service import ImpresionService
from app.extensions import db

kiosco_bp = Blueprint("kiosco", __name__, url_prefix="/kiosco")

@kiosco_bp.route("/")
def selector_area():
    areas = AreaService.get_all_areas()
    return render_template("kiosco/selector_area.html", areas=areas)


@kiosco_bp.route("/area/<int:id_area>")
def selector_tramite(id_area):
    area = AreaService.get_area_by_id_or_404(id_area)
    areas = AreaService.get_all_areas()
    tramites = TramiteService.get_tramites_by_area(id_area)
    ticket = session.get("kiosk_ticket", {"tramites": []})
    return render_template("kiosco/selector_tramite.html", area=area, tramites=tramites, ticket=ticket, areas=areas)


@kiosco_bp.route("/ticket/add/<int:id_area>", methods=["POST"])
def kiosco_add_tramite(id_area):
    tramite_id = request.form.get("id_tramite")
    ticket = session.get("kiosk_ticket", {"tramites": []})

    if len(ticket["tramites"]) >= 3:
        flash("No se pueden agregar más de 3 trámites por ticket", "error")
        return redirect(url_for("kiosco.selector_tramite", id_area=id_area))

    tramite = TramiteService.get_tramite_by_id(tramite_id)

    if not tramite:
        flash("Trámite no encontrado", "error")
        return redirect(url_for("kiosco.selector_tramite", id_area=id_area))

    for t in ticket["tramites"]:
        if t["id_tramite"] == tramite.id_tramite:
            flash("Trámite ya agregado al ticket", "warning")
            return redirect(url_for("kiosco.selector_tramite", id_area=id_area))

    ticket["tramites"].append({
        "id_tramite": tramite.id_tramite,
        "nombre": tramite.name,
        "id_area": tramite.id_area
    })

    session["kiosk_ticket"] = ticket
    session.modified = True

    flash("Trámite agregado exitosamente", "success")
    return redirect(url_for("kiosco.selector_tramite", id_area=id_area))


@kiosco_bp.route("/ticket/remove/<int:id_area>", methods=["POST"])
def kiosco_remove_tramite(id_area):
    tramite_id = request.form.get("id_tramite")

    ticket = session.get("kiosk_ticket", {"tramites": []})
    ticket["tramites"] = [
        t for t in ticket["tramites"] if t["id_tramite"] != int(tramite_id)
    ]

    session["kiosk_ticket"] = ticket
    session.modified = True

    flash("Trámite removido exitosamente", "success")
    return redirect(url_for("kiosco.selector_tramite", id_area=id_area))


@kiosco_bp.route("/ticket/checkout", methods=["GET", "POST"])
def kiosco_checkout():
    ticket_session = session.get("kiosk_ticket", {"tramites": []})

    if not ticket_session.get("tramites"):
        flash("No hay trámites seleccionados.", "warning")
        return redirect(url_for("kiosco.selector_area"))

    if request.method == "POST":
        try:
            db.session.begin_nested()
            
            turno = TurnoService.obtener_siguiente_turno()
            nuevo_ticket, error = TicketService.create_ticket(turno=turno)
            
            if error or not nuevo_ticket:
                db.session.rollback()
                flash(f"Error al crear el ticket: {error}", "error")
                return redirect(url_for("kiosco.selector_area"))

            tramites_ids = [t["id_tramite"] for t in ticket_session["tramites"]]
            registros, error = TicketTramiteService.create_multiple(
                id_ticket=nuevo_ticket.id_ticket,
                tramites=tramites_ids
            )

            if error:
                db.session.rollback()
                flash(f"Error al asignar trámites: {error}", "error")
                return redirect(url_for("kiosco.selector_area"))

            db.session.commit()
            session.pop("kiosk_ticket", None)

            return redirect(url_for("kiosco.kiosco_print_ticket", id_ticket=nuevo_ticket.id_ticket))

        except Exception as e:
            db.session.rollback()
            flash(f"Error inesperado: {str(e)}", "error")
            return redirect(url_for("kiosco.selector_area"))

    return render_template("kiosco/checkout_confirm.html", tramites=ticket_session["tramites"])

@kiosco_bp.route("/ticket/print/<int:id_ticket>")
def kiosco_print_ticket(id_ticket):
    ticket = TicketService.get_ticket_by_id_or_404(id_ticket)
    print(ticket)
    tramites = TicketTramiteService.get_tramites_by_ticket(id_ticket)


    ticket_data = {
        "turno": ticket.turno,
        "tramites": [t.name for t in tramites],
        "fecha_hora": ticket.fecha_hora.strftime("%d/%m/%Y %H:%M:%S")
    }

    impresora = ImpresionService()
    impresora.print_ticket(ticket_data)

    return redirect(url_for("kiosco.selector_area"))