from app.extensions import db
from .base import BaseModel

class Usuario(BaseModel):
    __tablename__ = "usuario"

    id_usuario = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(45), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(45), nullable=False)

    asignaciones = db.relationship("Asignacion", back_populates="usuario")
    atenciones = db.relationship("Atencion", back_populates="usuario")
