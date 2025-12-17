from app.extensions import db
from .base import BaseModel

class Area(BaseModel):
    __tablename__ = "area"

    id_area = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(45), unique=True, nullable=False)

    tramites = db.relationship("Tramite", back_populates="area")
    ventanillas = db.relationship("Ventanilla", back_populates="area")
