from app.models import Tramite
from app.extensions import db
from typing import List, Optional


class TramiteService:
    
    @staticmethod
    def get_all_tramites() -> List[Tramite]:
        return Tramite.query.all()
    
    @staticmethod
    def get_tramites_by_area(area_id: int) -> List[Tramite]:

        return Tramite.query.filter_by(id_area=area_id).order_by(Tramite.id_tramite).all()
    
    @staticmethod
    def get_tramite_by_id(tramite_id: int) -> Optional[Tramite]:
        return Tramite.query.get(tramite_id)
    
    @staticmethod
    def get_tramite_by_id_or_404(tramite_id: int) -> Tramite:
        return Tramite.query.get_or_404(tramite_id)
    
    @staticmethod
    def create_tramite(area_id: int, name: str) -> Tramite:

        name = name.strip()
        
        if not name:
            raise ValueError("El nombre del trámite es requerido")
        
        tramite = Tramite(id_area=area_id, name=name)
        
        try:
            db.session.add(tramite)
            db.session.commit()
            return tramite
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error al crear el trámite: {str(e)}")
    
    @staticmethod
    def update_tramite(tramite_id: int, name: str) -> Tramite:

        tramite = Tramite.query.get_or_404(tramite_id)
        name = name.strip()
        
        if not name:
            raise ValueError("El nombre del trámite es requerido")
        
        tramite.name = name
        
        try:
            db.session.commit()
            return tramite
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error al actualizar el trámite: {str(e)}")
    
    @staticmethod
    def delete_tramite(tramite_id: int) -> int:

        tramite = Tramite.query.get_or_404(tramite_id)
        id_area = tramite.id_area
        
        try:
            db.session.delete(tramite)
            db.session.commit()
            return id_area
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error al eliminar el trámite: {str(e)}")