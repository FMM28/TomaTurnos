from app.extensions import db
from .base import BaseModel

class Asignacion(BaseModel):
    __tablename__ = "asignacion"

    id_asignacion = db.Column(db.Integer, primary_key=True)

    id_usuario = db.Column(
        db.Integer,
        db.ForeignKey("usuario.id_usuario"),
        nullable=False
    )

    id_tramite = db.Column(
        db.Integer,
        db.ForeignKey("tramite.id_tramite"),
        nullable=False
    )

    usuario = db.relationship("Usuario", back_populates="asignaciones")
    tramite = db.relationship("Tramite", back_populates="asignaciones")
