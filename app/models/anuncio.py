from app.extensions import db
from .base import BaseModel

class Anuncio(BaseModel):
    __tablename__ = "anuncio"
    
    id_anuncio = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    enlace = db.Column(db.String(500), nullable=False)
    duracion = db.Column(db.Integer, nullable=False)
    tipo = db.Column(db.String(20), nullable=False, default='video')
    activo = db.Column(db.Boolean, default=True, nullable=False)
