from app.models import Tramite
from app.extensions import db
from typing import List, Optional, Tuple
from sqlalchemy.exc import SQLAlchemyError


class TramiteService:
    
    @staticmethod
    def get_all_tramites() -> List[Tramite]:
        """Obtiene todos los trámites"""
        try:
            return Tramite.query.order_by(Tramite.id_tramite).all()
        except SQLAlchemyError as e:
            print(f"Error al obtener trámites: {e}")
            return []
    
    @staticmethod
    def get_tramites_by_area(area_id: int) -> List[Tramite]:
        """Obtiene todos los trámites de un área específica"""
        try:
            return Tramite.query.filter_by(id_area=area_id).order_by(Tramite.id_tramite).all()
        except SQLAlchemyError as e:
            print(f"Error al obtener trámites del área {area_id}: {e}")
            return []
    
    @staticmethod
    def get_tramite_by_id(tramite_id: int) -> Optional[Tramite]:
        """Obtiene un trámite por su ID"""
        try:
            return Tramite.query.get(tramite_id)
        except SQLAlchemyError as e:
            print(f"Error al obtener trámite {tramite_id}: {e}")
            return None
    
    @staticmethod
    def get_tramite_by_id_or_404(tramite_id: int) -> Tramite:
        """Obtiene un trámite por su ID o retorna 404"""
        return Tramite.query.get_or_404(tramite_id)
    
    @staticmethod
    def tramite_exists_by_name(name: str, exclude_id: Optional[int] = None) -> bool:
        """Verifica si existe un trámite con el nombre dado"""
        try:
            query = Tramite.query.filter(Tramite.name == name)
            
            if exclude_id is not None:
                query = query.filter(Tramite.id_tramite != exclude_id)
            
            return query.first() is not None
        except SQLAlchemyError as e:
            print(f"Error al verificar existencia de trámite: {e}")
            return False
    
    @staticmethod
    def create_tramite(area_id: int, name: str) -> Tuple[Optional[Tramite], Optional[str]]:
        """Crea un nuevo trámite"""
        try:
            name = name.strip()
            
            if not name:
                return None, "El nombre del trámite es requerido"
            
            if TramiteService.tramite_exists_by_name(name):
                return None, "Ya existe un trámite con ese nombre"
            
            tramite = Tramite(id_area=area_id, name=name)
            db.session.add(tramite)
            db.session.commit()
            return tramite, None
        except SQLAlchemyError as e:
            db.session.rollback()
            error_msg = f"Error al crear el trámite: {str(e)}"
            print(error_msg)
            return None, error_msg
    
    @staticmethod
    def update_tramite(tramite_id: int, name: str) -> Tuple[Optional[Tramite], Optional[str]]:
        """Actualiza un trámite existente"""
        try:
            tramite = Tramite.query.get(tramite_id)
            if not tramite:
                return None, "Trámite no encontrado"
            
            name = name.strip()
            
            if not name:
                return None, "El nombre del trámite es requerido"
            
            if TramiteService.tramite_exists_by_name(name, exclude_id=tramite_id):
                return None, "Ya existe un trámite con ese nombre"
            
            tramite.name = name
            db.session.commit()
            return tramite, None
        except SQLAlchemyError as e:
            db.session.rollback()
            error_msg = f"Error al actualizar el trámite: {str(e)}"
            print(error_msg)
            return None, error_msg
    
    @staticmethod
    def delete_tramite(tramite_id: int) -> Tuple[Optional[int], Optional[str]]:
        """Elimina un trámite y retorna el ID del área"""
        try:
            tramite = Tramite.query.get(tramite_id)
            if not tramite:
                return None, "Trámite no encontrado"
            
            id_area = tramite.id_area
            db.session.delete(tramite)
            db.session.commit()
            return id_area, None
        except SQLAlchemyError as e:
            db.session.rollback()
            error_msg = f"Error al eliminar el trámite: {str(e)}"
            print(error_msg)
            return None, error_msg