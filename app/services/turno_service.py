from sqlalchemy import func
from app.models import Ticket
from app.extensions import db
from flask import current_app

class TurnoService:

    @staticmethod
    def obtener_siguiente_turno() -> int:
        max_turno = current_app.config["MAX_TURNO"]

        ultimo = db.session.query(
            func.max(Ticket.id_ticket)
        ).scalar()

        if not ultimo or ultimo.turno >= max_turno:
            return 1

        return ultimo.turno + 1