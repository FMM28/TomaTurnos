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
    def get_tramites_by_ventanilla(ventanilla_id: int) -> List[Tramite]:
        """Obtiene todos los trámites asignados a una ventanilla específica"""
        try:
            return Tramite.query.filter_by(id_ventanilla=ventanilla_id).order_by(Tramite.id_tramite).all()
        except SQLAlchemyError as e:
            print(f"Error al obtener trámites de la ventanilla {ventanilla_id}: {e}")
            return []
        
    @staticmethod
    def get_tramites_by_area_excluyendo(area_id: int, excluir_ids: set[int]) -> List[Tramite]:
        """Obtiene todos los trámites de un área específica excluyendo ciertos IDs"""
        try:
            query = Tramite.query.filter(Tramite.id_area == area_id)
            
            if excluir_ids:
                query = query.filter(~Tramite.id_tramite.in_(excluir_ids))
            
            return query.order_by(Tramite.id_tramite).all()
        except SQLAlchemyError as e:
            print(f"Error al obtener trámites del área {area_id} excluyendo IDs {excluir_ids}: {e}")
            return []
    
    @staticmethod
    def create_tramite(area_id: int, name: str) -> Tuple[Optional[Tramite], Optional[str]]:
        """Crea un nuevo trámite"""
        try:
            name = name.strip()
            
            if not name:
                return None, "El nombre del trámite es requerido"
            
            if TramiteService.tramite_exists_by_name(name):
                return None, "Ya existe un trámite con ese nombre"
            
            tramite = Tramite(
                id_area=area_id,
                name=name,
                id_ventanilla=None
            )

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
    def asignar_tramite_a_ventanilla(tramite_id: int, ventanilla_id: int) -> Tuple[Optional[Tramite], Optional[str]]:
        """Asigna un trámite a una ventanilla"""
        try:
            tramite = Tramite.query.get(tramite_id)
            if not tramite:
                return None, "Trámite no encontrado"
            
            tramite.id_ventanilla = ventanilla_id
            db.session.commit()
            return tramite, None
        except SQLAlchemyError as e:
            db.session.rollback()
            error_msg = f"Error al asignar el trámite a la ventanilla: {str(e)}"
            print(error_msg)
            return None, error_msg
        
    @staticmethod
    def desasignar_tramite_de_ventanilla(tramite_id: int) -> Tuple[Optional[Tramite], Optional[str]]:
        """Desasigna un trámite de su ventanilla"""
        try:
            tramite = Tramite.query.get(tramite_id)
            if not tramite:
                return None, "Trámite no encontrado"
            
            tramite.id_ventanilla = None
            db.session.commit()
            return tramite, None
        except SQLAlchemyError as e:
            db.session.rollback()
            error_msg = f"Error al desasignar el trámite de la ventanilla: {str(e)}"
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