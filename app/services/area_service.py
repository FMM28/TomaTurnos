from app.models import Area
from app.extensions import db
from typing import List, Optional, Tuple
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from app.services.tramite_service import TramiteService

class AreaService:

    @staticmethod
    def get_all_areas(include_deleted: bool = False) -> List[Area]:
        """Obtiene todas las áreas activas"""
        try:
            query = Area.query

            if not include_deleted:
                query = query.filter(Area.deleted_at.is_(None))

            return query.order_by(Area.id_area).all()
        except SQLAlchemyError as e:
            print(f"Error al obtener áreas: {e}")
            return []

    @staticmethod
    def get_area_by_id(area_id: int, include_deleted: bool = False) -> Optional[Area]:
        """Obtiene un área por ID"""
        try:
            query = Area.query.filter(Area.id_area == area_id)

            if not include_deleted:
                query = query.filter(Area.deleted_at.is_(None))

            return query.first()
        except SQLAlchemyError as e:
            print(f"Error al obtener área {area_id}: {e}")
            return None

    @staticmethod
    def area_exists_by_name(name: str, exclude_id: Optional[int] = None) -> bool:
        """Verifica si existe un área activa con el nombre dado"""
        try:
            query = Area.query.filter(
                Area.name == name,
                Area.deleted_at.is_(None)
            )

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
            return None, f"Error al crear el área: {e}"

    @staticmethod
    def update_area(area_id: int, name: str) -> Tuple[Optional[Area], Optional[str]]:
        """Actualiza un área existente"""
        try:
            area = Area.query.filter(
                Area.id_area == area_id,
                Area.deleted_at.is_(None)
            ).first()

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
            return None, f"Error al actualizar el área: {e}"

    @staticmethod
    def delete_area(area_id: int) -> Tuple[bool, Optional[str]]:
        """Elimina un área"""
        try:
            area = Area.query.filter(
                Area.id_area == area_id,
                Area.deleted_at.is_(None)
            ).first()

            if not area:
                return False, "Área no encontrada o ya eliminada"

            tramites = TramiteService.get_tramites_by_area(area_id)
            for tramite in tramites:
                TramiteService.delete_tramite(tramite.id_tramite)

            area.deleted_at = datetime.utcnow()
            db.session.commit()
            return True, None

        except SQLAlchemyError as e:
            db.session.rollback()
            return False, f"Error al eliminar el área: {e}"
