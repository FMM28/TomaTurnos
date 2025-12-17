from app.extensions import db
from .base import BaseModel

class Ventanilla(BaseModel):
    __tablename__ = "ventanilla"

    id_ventanilla = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(45), nullable=False)

    id_area = db.Column(
        db.Integer,
        db.ForeignKey("area.id_area"),
        nullable=True
    )

    area = db.relationship("Area", back_populates="ventanillas")
    atenciones = db.relationship("Atencion", back_populates="ventanilla")
