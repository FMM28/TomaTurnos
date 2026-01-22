from app.extensions import db
from .base import BaseModel

class Tramite(BaseModel):
    __tablename__ = "tramite"

    id_tramite = db.Column(db.Integer, primary_key=True)

    id_area = db.Column(
        db.Integer,
        db.ForeignKey("area.id_area", ondelete="CASCADE"),
        nullable=False
    )

    name = db.Column(db.String(255), nullable=False)

    id_ventanilla = db.Column(
        db.Integer,
        db.ForeignKey("ventanilla.id_ventanilla", ondelete="SET NULL"),
        nullable=True
    )
    
    requerimientos = db.Column(db.String(255), nullable = True)
    
    deleted_at = db.Column(db.DateTime, nullable=True)

    area = db.relationship(
        "Area",
        back_populates="tramites",
        passive_deletes=True
    )

    asignaciones = db.relationship(
        "Asignacion",
        back_populates="tramite",
        passive_deletes=True
    )

    ticket_tramites = db.relationship(
        "TicketTramite",
        back_populates="tramite",
        passive_deletes=True
    )

    ventanilla = db.relationship(
        "Ventanilla",
        back_populates="tramites"
    )
