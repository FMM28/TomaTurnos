from app.models import Area, Tramite
from app.extensions import db
from typing import List, Optional


class AreaService:
    
    @staticmethod
    def get_all_areas() -> List[Area]:
        return Area.query.all()
    
    @staticmethod
    def get_area_by_id(area_id: int) -> Optional[Area]:
        return Area.query.get(area_id)
    
    @staticmethod
    def get_area_by_id_or_404(area_id: int) -> Area:
        return Area.query.get_or_404(area_id)
    
    @staticmethod
    def get_area_by_name(name: str) -> Optional[Area]:
        return Area.query.filter_by(name=name).first()
    
    @staticmethod
    def area_exists_by_name(name: str, exclude_id: Optional[int] = None) -> bool:

        query = Area.query.filter(Area.name == name)
        
        if exclude_id is not None:
            query = query.filter(Area.id_area != exclude_id)
        
        return query.first() is not None
    
    @staticmethod
    def create_area(name: str) -> Area:

        name = name.strip()
        
        if not name:
            raise ValueError("El nombre del área es requerido")
        
        if AreaService.area_exists_by_name(name):
            raise ValueError("Ya existe un área con ese nombre")
        
        area = Area(name=name)
        
        try:
            db.session.add(area)
            db.session.commit()
            return area
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error al crear el área: {str(e)}")
    
    @staticmethod
    def update_area(area_id: int, name: str) -> Area:

        area = Area.query.get_or_404(area_id)
        name = name.strip()
        
        if not name:
            raise ValueError("El nombre del área es requerido")
        
        if AreaService.area_exists_by_name(name, exclude_id=area_id):
            raise ValueError("Ya existe un área con ese nombre")
        
        area.name = name
        
        try:
            db.session.commit()
            return area
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error al actualizar el área: {str(e)}")
    
    @staticmethod
    def delete_area(area_id: int) -> None:

        area = Area.query.get_or_404(area_id)
        
        try:
            # Eliminar trámites asociados
            Tramite.query.filter_by(id_area=area_id).delete()
            db.session.delete(area)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error al eliminar el área: {str(e)}")