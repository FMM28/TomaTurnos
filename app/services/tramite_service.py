from app.models import Tramite
from app.extensions import db
from typing import List, Optional, Tuple
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

class TramiteService:

    @staticmethod
    def get_all_tramites(include_deleted: bool = False) -> List[Tramite]:
        try:
            query = Tramite.query

            if not include_deleted:
                query = query.filter(Tramite.deleted_at.is_(None))

            return query.order_by(Tramite.id_tramite).all()
        except SQLAlchemyError as e:
            print(f"Error al obtener trámites: {e}")
            return []

    @staticmethod
    def get_tramites_by_area(area_id: int) -> List[Tramite]:
        try:
            return (
                Tramite.query
                .filter(
                    Tramite.id_area == area_id,
                    Tramite.deleted_at.is_(None)
                )
                .order_by(Tramite.id_tramite)
                .all()
            )
        except SQLAlchemyError as e:
            print(f"Error al obtener trámites del área {area_id}: {e}")
            return []
        
    @staticmethod
    def get_tramites_by_ventanilla(ventanilla_id: int):
        try:
            return (
                Tramite.query
                .filter(
                    Tramite.id_ventanilla == ventanilla_id,
                    Tramite.deleted_at.is_(None)
                )
                .order_by(Tramite.id_tramite)
                .all()
            )
        except SQLAlchemyError as e:
            print(f"Error al obtener trámites de la ventanilla {ventanilla_id}: {e}")
            return []
        
    @staticmethod
    def get_tramites_by_area_excluyendo(area_id: int, excluir_ids: set[int]) -> List[Tramite]:
        """Obtiene todos los trámites de un área específica excluyendo ciertos IDs"""
        try:
            query = Tramite.query.filter(
                Tramite.id_area == area_id,
                Tramite.deleted_at.is_(None)
            )

            if excluir_ids:
                query = query.filter(~Tramite.id_tramite.in_(excluir_ids))

            return query.order_by(Tramite.id_tramite).all()

        except SQLAlchemyError as e:
            print(
                f"Error al obtener trámites del área {area_id} "
                f"excluyendo IDs {excluir_ids}: {e}"
            )
            return []


    @staticmethod
    def get_tramite_by_id(tramite_id: int, include_deleted: bool = False) -> Optional[Tramite]:
        try:
            query = Tramite.query.filter(Tramite.id_tramite == tramite_id)

            if not include_deleted:
                query = query.filter(Tramite.deleted_at.is_(None))

            return query.first()
        except SQLAlchemyError as e:
            print(f"Error al obtener trámite {tramite_id}: {e}")
            return None

    @staticmethod
    def tramite_exists_by_name(name: str, exclude_id: Optional[int] = None) -> bool:
        try:
            query = Tramite.query.filter(
                Tramite.name == name,
                Tramite.deleted_at.is_(None)
            )

            if exclude_id:
                query = query.filter(Tramite.id_tramite != exclude_id)

            return query.first() is not None
        except SQLAlchemyError as e:
            print(f"Error al verificar trámite: {e}")
            return False

    @staticmethod
    def create_tramite(area_id: int, name: str) -> Tuple[Optional[Tramite], Optional[str]]:
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
            return None, f"Error al crear el trámite: {e}"

    @staticmethod
    def update_tramite(tramite_id: int, name: str) -> Tuple[Optional[Tramite], Optional[str]]:
        try:
            tramite = Tramite.query.filter(
                Tramite.id_tramite == tramite_id,
                Tramite.deleted_at.is_(None)
            ).first()

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
            return None, f"Error al actualizar el trámite: {e}"

    @staticmethod
    def asignar_tramite_a_ventanilla(tramite_id: int, ventanilla_id: int):
        try:
            tramite = Tramite.query.filter(
                Tramite.id_tramite == tramite_id,
                Tramite.deleted_at.is_(None)
            ).first()

            if not tramite:
                return None, "Trámite no encontrado"

            tramite.id_ventanilla = ventanilla_id
            db.session.commit()
            return tramite, None

        except SQLAlchemyError as e:
            db.session.rollback()
            return None, f"Error al asignar ventanilla: {e}"

    @staticmethod
    def desasignar_tramite_de_ventanilla(tramite_id: int):
        try:
            tramite = Tramite.query.filter(
                Tramite.id_tramite == tramite_id,
                Tramite.deleted_at.is_(None)
            ).first()

            if not tramite:
                return None, "Trámite no encontrado"

            tramite.id_ventanilla = None
            db.session.commit()
            return tramite, None

        except SQLAlchemyError as e:
            db.session.rollback()
            return None, f"Error al desasignar ventanilla: {e}"

    @staticmethod
    def delete_tramite(tramite_id: int) -> Tuple[bool, Optional[str]]:
        try:
            tramite = Tramite.query.filter(
                Tramite.id_tramite == tramite_id,
                Tramite.deleted_at.is_(None)
            ).first()

            if not tramite:
                return False, "Trámite no encontrado o ya eliminado"

            tramite.deleted_at = datetime.utcnow()
            db.session.commit()
            return True, None

        except SQLAlchemyError as e:
            db.session.rollback()
            return False, f"Error al eliminar el trámite: {e}"

    @staticmethod
    def restore_tramite(tramite_id: int) -> Tuple[bool, Optional[str]]:
        try:
            tramite = Tramite.query.filter_by(id_tramite=tramite_id).first()

            if not tramite or tramite.deleted_at is None:
                return False, "Trámite no eliminado"

            tramite.deleted_at = None
            db.session.commit()
            return True, None

        except SQLAlchemyError as e:
            db.session.rollback()
            return False, f"Error al restaurar el trámite: {e}"
