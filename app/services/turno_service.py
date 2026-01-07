from typing import List
from sqlalchemy import func
from app.models import Ticket
from app.extensions import db
from flask import current_app

class TurnoService:

    @staticmethod
    def obtener_siguiente_turno() -> int:
        max_turno = current_app.config["MAX_TURNO"]

        ultimo = db.session.query(Ticket).order_by(Ticket.turno.desc()).first()

        if not ultimo or ultimo.turno >= max_turno:
            return 1

        return ultimo.turno + 1
    
    @staticmethod
    def get_turnos_en_espera() -> List[dict]:
        turnos = (
            Ticket.query
            .filter(Ticket.estado == "activo")
            .order_by(Ticket.fecha_hora.asc())
            .all()
        )

        return [
            {
                "turno": t.turno,
                "fecha_hora": t.fecha_hora.strftime("%H:%M")
            }
            for t in turnos
        ]