from app.extensions import db
from .base import BaseModel

class Suplente(BaseModel):
    __tablename__ = "suplente"

    id_suplente = db.Column(db.Integer, primary_key=True)

    id_usuario = db.Column(
        db.Integer,
        db.ForeignKey("usuario.id_usuario", ondelete="CASCADE"),
        nullable=False
    )

    id_suplente_usuario = db.Column(
        db.Integer,
        db.ForeignKey("usuario.id_usuario", ondelete="CASCADE"),
        nullable=False
    )

    activo = db.Column(db.Boolean, default=False, nullable=False)

    usuario = db.relationship("Usuario", foreign_keys=[id_usuario], back_populates="suplentes_asignados")
    suplente_usuario = db.relationship("Usuario",foreign_keys=[id_suplente_usuario],back_populates="suplencias")
