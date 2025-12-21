from app.models import Area, Tramite
from app.extensions import db
from typing import List, Optional, Tuple
from sqlalchemy.exc import SQLAlchemyError


class AreaService:
    
    @staticmethod
    def get_all_areas() -> List[Area]:
        """Obtiene todas las áreas"""
        try:
            return Area.query.order_by(Area.id_area).all()
        except SQLAlchemyError as e:
            print(f"Error al obtener áreas: {e}")
            return []
    
    @staticmethod
    def get_area_by_id(area_id: int) -> Optional[Area]:
        """Obtiene un área por su ID"""
        try:
            return Area.query.get(area_id)
        except SQLAlchemyError as e:
            print(f"Error al obtener área {area_id}: {e}")
            return None
    
    @staticmethod
    def get_area_by_id_or_404(area_id: int) -> Area:
        """Obtiene un área por su ID o retorna 404"""
        return Area.query.get_or_404(area_id)
    
    @staticmethod
    def get_area_by_name(name: str) -> Optional[Area]:
        """Obtiene un área por su nombre"""
        try:
            return Area.query.filter_by(name=name).first()
        except SQLAlchemyError as e:
            print(f"Error al buscar área por nombre: {e}")
            return None
    
    @staticmethod
    def area_exists_by_name(name: str, exclude_id: Optional[int] = None) -> bool:
        """Verifica si existe un área con el nombre dado"""
        try:
            query = Area.query.filter(Area.name == name)
            
            if exclude_id is not None:
                query = query.filter(Area.id_area != exclude_id)
            
            return query.first() is not None
        except SQLAlchemyError as e:
            print(f"Error al verificar existencia de área: {e}")
            return False
    
    @staticmethod
    def create_area(name: str) -> Tuple[Optional[Area], Optional[str]]:
        """Crea una nueva área"""
        try:
            name = name.strip()
            
            if not name:
                return None, "El nombre del área es requerido"
            
            if AreaService.area_exists_by_name(name):
                return None, "Ya existe un área con ese nombre"
            
            area = Area(name=name)
            db.session.add(area)
            db.session.commit()
            return area, None
        except SQLAlchemyError as e:
            db.session.rollback()
            error_msg = f"Error al crear el área: {str(e)}"
            print(error_msg)
            return None, error_msg
    
    @staticmethod
    def update_area(area_id: int, name: str) -> Tuple[Optional[Area], Optional[str]]:
        """Actualiza un área existente"""
        try:
            area = Area.query.get(area_id)
            if not area:
                return None, "Área no encontrada"
            
            name = name.strip()
            
            if not name:
                return None, "El nombre del área es requerido"
            
            if AreaService.area_exists_by_name(name, exclude_id=area_id):
                return None, "Ya existe un área con ese nombre"
            
            area.name = name
            db.session.commit()
            return area, None
        except SQLAlchemyError as e:
            db.session.rollback()
            error_msg = f"Error al actualizar el área: {str(e)}"
            print(error_msg)
            return None, error_msg
    
    @staticmethod
    def delete_area(area_id: int) -> Tuple[bool, Optional[str]]:
        """Elimina un área"""
        try:
            area = Area.query.get(area_id)
            if not area:
                return False, "Área no encontrada"
            
            # Eliminar trámites asociados
            Tramite.query.filter_by(id_area=area_id).delete()
            db.session.delete(area)
            db.session.commit()
            return True, None
        except SQLAlchemyError as e:
            db.session.rollback()
            error_msg = f"Error al eliminar el área: {str(e)}"
            print(error_msg)
            return False, error_msg