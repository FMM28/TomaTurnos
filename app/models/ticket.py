from app.extensions import db
from .base import BaseModel

class Ticket(BaseModel):
    __tablename__ = "ticket"

    id_ticket = db.Column(db.Integer, primary_key=True)
    fecha_hora = db.Column(db.DateTime, nullable=False)
    turno = db.Column(db.Integer, nullable=False)

    estado = db.Column(
        db.String(20),
        nullable=False,
        default="activo"
    )

    ticket_tramites = db.relationship(
        "TicketTramite",
        back_populates="ticket"
    )
