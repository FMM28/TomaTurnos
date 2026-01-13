from app.extensions import db
from .base import BaseModel

class Tramite(BaseModel):
    __tablename__ = "tramite"

    id_tramite = db.Column(db.Integer, primary_key=True)
    id_area = db.Column(
        db.Integer,
        db.ForeignKey("area.id_area"),
        nullable=False
    )
    name = db.Column(db.String(255), nullable=False, unique=True)
    id_ventanilla = db.Column(
        db.Integer,
        db.ForeignKey("ventanilla.id_ventanilla"),
        nullable=True
    )

    area = db.relationship("Area", back_populates="tramites")
    asignaciones = db.relationship("Asignacion", back_populates="tramite")
    ticket_tramites = db.relationship("TicketTramite", back_populates="tramite")
    ventanilla = db.relationship("Ventanilla", back_populates="tramites")
