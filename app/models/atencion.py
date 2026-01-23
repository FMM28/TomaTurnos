from app.extensions import db
from .base import BaseModel

class Atencion(BaseModel):
    __tablename__ = "atencion"

    id_atencion = db.Column(db.Integer, primary_key=True)

    id_ticket_tramite = db.Column(
        db.Integer,
        db.ForeignKey("ticket_tramite.id_ticket_tramite"),
        nullable=False
    )

    id_ventanilla = db.Column(
        db.Integer,
        db.ForeignKey("ventanilla.id_ventanilla"),
        nullable=False
    )

    id_usuario = db.Column(
        db.Integer,
        db.ForeignKey("usuario.id_usuario"),
        nullable=False
    )

    estado = db.Column(db.String(20))
    descripcion_estado = db.Column(db.String(100))
    hora_inicio = db.Column(db.DateTime)
    hora_fin = db.Column(db.DateTime)

    ticket_tramite = db.relationship("TicketTramite", back_populates="atenciones")
    ventanilla = db.relationship("Ventanilla", back_populates="atenciones")
    usuario = db.relationship("Usuario", back_populates="atenciones")
