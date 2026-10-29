from app.extensions import db
from .base import BaseModel

class TicketTramite(BaseModel):
    __tablename__ = "ticket_tramite"

    id_ticket_tramite = db.Column(db.Integer, primary_key=True)

    id_ticket = db.Column(
        db.Integer,
        db.ForeignKey("ticket.id_ticket"),
        nullable=False
    )

    id_tramite = db.Column(
        db.Integer,
        db.ForeignKey("tramite.id_tramite"),
        nullable=False
    )

    estado = db.Column(
        db.String(20),
        default="espera"
    )

    prioridad = db.Column(db.Integer, default=0)
    fecha_creacion = db.Column(db.DateTime, nullable=False)

    ticket = db.relationship("Ticket", back_populates="ticket_tramites")
    tramite = db.relationship("Tramite", back_populates="ticket_tramites")
    atenciones = db.relationship("Atencion", back_populates="ticket_tramite")
