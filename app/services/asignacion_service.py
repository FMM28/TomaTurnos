from app.models import Asignacion
from app.extensions import db
from typing import List, Optional, Tuple
from sqlalchemy.exc import SQLAlchemyError

class AsignacionService:
    
    @staticmethod
    def get_asignaciones_by_tramite(tramite_id: int) -> List[Asignacion]:
        """Obtiene todas las asignaciones de un trámite específico"""
        try:
            return Asignacion.query.filter_by(id_tramite=tramite_id).order_by(Asignacion.id_asignacion).all()
        except SQLAlchemyError as e:
            print(f"Error al obtener asignaciones del trámite {tramite_id}: {e}")
            return []
    
    @staticmethod
    def get_asignacion_by_id(asignacion_id: int) -> Optional[Asignacion]:
        """Obtiene una asignación por su ID"""
        try:
            return Asignacion.query.get(asignacion_id)
        except SQLAlchemyError as e:
            print(f"Error al obtener asignación {asignacion_id}: {e}")
            return None
        
    @staticmethod
    def get_asignaciones_by_usuario(usuario_id: int) -> List[Asignacion]:
        """Obtiene todas las asignaciones de un usuario específico"""
        try:
            return Asignacion.query.filter_by(id_usuario=usuario_id).order_by(Asignacion.id_asignacion).all()
        except SQLAlchemyError as e:
            print(f"Error al obtener asignaciones del usuario {usuario_id}: {e}")
            return []
        
    @staticmethod
    def get_usuarios_by_tramite(tramite_id: int) -> List[int]:
        """Obtiene los IDs de los usuarios asignados a un trámite específico"""
        try:
            asignaciones = Asignacion.query.filter_by(id_tramite=tramite_id).all()
            return [asignacion.id_usuario for asignacion in asignaciones]
        except SQLAlchemyError as e:
            print(f"Error al obtener usuarios del trámite {tramite_id}: {e}")
            return []
    
    @staticmethod
    def create_asignacion(id_tramite: int, id_usuario: int) -> Tuple[Optional[Asignacion], Optional[str]]:
        """Crea una nueva asignación"""
        try:
            nueva_asignacion = Asignacion(
                id_tramite=id_tramite,
                id_usuario=id_usuario
            )
            db.session.add(nueva_asignacion)
            db.session.commit()
            return nueva_asignacion, None
        except SQLAlchemyError as e:
            db.session.rollback()
            error_msg = f"Error al crear asignación: {e}"
            print(error_msg)
            return None, error_msg
        
    @staticmethod
    def delete_asignacion(asignacion_id: int) -> Optional[str]:
        """Elimina una asignación por su ID"""
        try:
            asignacion = Asignacion.query.get(asignacion_id)
            if not asignacion:
                return "Asignación no encontrada."
            
            db.session.delete(asignacion)
            db.session.commit()
            return None
        except SQLAlchemyError as e:
            db.session.rollback()
            error_msg = f"Error al eliminar asignación: {e}"
            print(error_msg)
            return error_msg