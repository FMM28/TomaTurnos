from typing import List

from flask import current_app
from sqlalchemy import func

from app.extensions import db
from app.licensing import licensed
from app.models import Ticket, TicketTramite


class TurnoService:

    @staticmethod
    @licensed
    def obtener_siguiente_turno() -> int:
        max_turno = current_app.config["MAX_TURNO"]

        ultimo = db.session.query(Ticket).order_by(Ticket.id_ticket.desc()).first()

        return 1 if not ultimo or ultimo.turno >= max_turno else ultimo.turno + 1
    
    @staticmethod
    @licensed
    def get_turnos_en_espera() -> List[dict]:
        turnos = (
            TicketTramite.query
            .filter(TicketTramite.estado == "espera")
            .order_by(TicketTramite.fecha_creacion.asc())
            .all()
        )

        return [t.ticket.turno for t in turnos]
    
    @staticmethod
    @licensed
    def get_turnos_en_llamado() -> List[dict]:
        turnos = (
            TicketTramite.query
            .filter(TicketTramite.estado == "llamado")
            .order_by(TicketTramite.fecha_creacion.asc())
            .all()
        )

        return [
            {
                "turno": t.ticket.turno,
                "ventanilla": t.tramite.ventanilla.name
            }
            for t in turnos
        ]