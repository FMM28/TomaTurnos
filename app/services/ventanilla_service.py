from app.models.ventanilla import Ventanilla
from app.extensions import db
from typing import List, Optional, Tuple
from sqlalchemy.exc import SQLAlchemyError


class VentanillaService:
    
    @staticmethod
    def get_all_ventanillas() -> List[Ventanilla]:
        """Obtiene todas las ventanillas"""
        try:
            return Ventanilla.query.order_by(Ventanilla.id_ventanilla).all()
        except SQLAlchemyError as e:
            print(f"Error al obtener ventanillas: {e}")
            return []
    
    @staticmethod
    def get_ventanilla_by_id(id_ventanilla: int) -> Optional[Ventanilla]:
        """Obtiene una ventanilla por su ID"""
        try:
            return Ventanilla.query.get(id_ventanilla)
        except SQLAlchemyError as e:
            print(f"Error al obtener ventanilla {id_ventanilla}: {e}")
            return None
    
    @staticmethod
    def get_ventanillas_by_area(id_area: int) -> List[Ventanilla]:
        """Obtiene todas las ventanillas de un área específica"""
        try:
            return Ventanilla.query.filter_by(id_area=id_area).order_by(Ventanilla.id_ventanilla).all()
        except SQLAlchemyError as e:
            print(f"Error al obtener ventanillas del área {id_area}: {e}")
            return []
    
    @staticmethod
    def ventanilla_exists_by_name(name: str, exclude_id: Optional[int] = None) -> bool:
        """Verifica si existe una ventanilla con el nombre dado"""
        try:
            query = Ventanilla.query.filter(Ventanilla.name == name)
            
            if exclude_id is not None:
                query = query.filter(Ventanilla.id_ventanilla != exclude_id)
            
            return query.first() is not None
        except SQLAlchemyError as e:
            print(f"Error al verificar existencia de ventanilla: {e}")
            return False
    
    @staticmethod
    def create_ventanilla(name: str, id_area: Optional[int] = None) -> Tuple[Optional[Ventanilla], Optional[str]]:
        """Crea una nueva ventanilla"""
        try:
            name = name.strip()
            
            if not name:
                return None, "El nombre de la ventanilla es requerido"
            
            if VentanillaService.ventanilla_exists_by_name(name):
                return None, "Ya existe una ventanilla con ese nombre"
            
            ventanilla = Ventanilla(
                name=name,
                id_area=id_area if id_area else None
            )
            db.session.add(ventanilla)
            db.session.commit()
            return ventanilla, None
        except SQLAlchemyError as e:
            db.session.rollback()
            error_msg = f"Error al crear ventanilla: {str(e)}"
            print(error_msg)
            return None, error_msg
    
    @staticmethod
    def update_ventanilla(id_ventanilla: int, name: str, id_area: Optional[int] = None) -> Tuple[Optional[Ventanilla], Optional[str]]:
        """Actualiza una ventanilla existente"""
        try:
            ventanilla = Ventanilla.query.get(id_ventanilla)
            if not ventanilla:
                return None, "Ventanilla no encontrada"
            
            name = name.strip()
            
            if not name:
                return None, "El nombre de la ventanilla es requerido"
            
            if VentanillaService.ventanilla_exists_by_name(name, exclude_id=id_ventanilla):
                return None, "Ya existe una ventanilla con ese nombre"
            
            ventanilla.name = name
            ventanilla.id_area = id_area if id_area else None
            
            db.session.commit()
            return ventanilla, None
        except SQLAlchemyError as e:
            db.session.rollback()
            error_msg = f"Error al actualizar ventanilla: {str(e)}"
            print(error_msg)
            return None, error_msg
    
    @staticmethod
    def delete_ventanilla(id_ventanilla: int) -> Tuple[bool, Optional[str]]:
        """Elimina una ventanilla"""
        try:
            ventanilla = Ventanilla.query.get(id_ventanilla)
            if not ventanilla:
                return False, "Ventanilla no encontrada"
            
            db.session.delete(ventanilla)
            db.session.commit()
            return True, None
        except SQLAlchemyError as e:
            db.session.rollback()
            error_msg = f"Error al eliminar ventanilla: {str(e)}"
            print(error_msg)
            return False, error_msg