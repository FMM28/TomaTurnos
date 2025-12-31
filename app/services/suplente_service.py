from app.models import Suplente
from app.extensions import db
from typing import List, Optional, Tuple
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload

class SuplenteService:
    
    @staticmethod
    def get_suplentes_by_usuario(usuario_id: int) -> List[Suplente]:
        try:
            return (
                Suplente.query
                .options(joinedload(Suplente.suplente_usuario))
                .filter(Suplente.id_usuario == usuario_id)
                .order_by(Suplente.id_suplente)
                .all()
            )
        except SQLAlchemyError as e:
            print(f"Error al obtener suplentes del usuario {usuario_id}: {e}")
            return []
    
    @staticmethod
    def get_suplente_by_id(suplente_id: int) -> Optional[Suplente]:
        """Obtiene un suplente por su ID"""
        try:
            return Suplente.query.get(suplente_id)
        except SQLAlchemyError as e:
            print(f"Error al obtener suplente {suplente_id}: {e}")
            return None
        
    @staticmethod
    def create_suplente(id_usuario: int, id_suplente_usuario: int, activo: bool = False) -> Tuple[Optional[Suplente], Optional[str]]:
        """Crea un nuevo suplente"""
        try:
            nuevo_suplente = Suplente(
                id_usuario=id_usuario,
                id_suplente_usuario=id_suplente_usuario,
                activo=activo
            )
            db.session.add(nuevo_suplente)
            db.session.commit()
            return nuevo_suplente, None
        except SQLAlchemyError as e:
            db.session.rollback()
            error_msg = f"Error al crear suplente: {e}"
            print(error_msg)
            return None, error_msg
        
    @staticmethod
    def deactivate_suplente(suplente_id: int) -> Tuple[bool, Optional[str]]:
        """Desactiva un suplente por su ID"""
        try:
            suplente = Suplente.query.get(suplente_id)
            if not suplente:
                return False, "Suplente no encontrado"
            suplente.activo = False
            db.session.commit()
            return True, None
        except SQLAlchemyError as e:
            db.session.rollback()
            error_msg = f"Error al desactivar suplente {suplente_id}: {e}"
            print(error_msg)
            return False, error_msg
        
    @staticmethod
    def activate_suplente(suplente_id: int) -> Tuple[bool, Optional[str]]:
        """Activa un suplente por su ID"""
        try:
            suplente = Suplente.query.get(suplente_id)
            if not suplente:
                return False, "Suplente no encontrado"
            suplente.activo = True
            db.session.commit()
            return True, None
        except SQLAlchemyError as e:
            db.session.rollback()
            error_msg = f"Error al activar suplente {suplente_id}: {e}"
            print(error_msg)
            return False, error_msg
        
    @staticmethod
    def delete_suplente(suplente_id: int) -> Optional[str]:
        """Elimina un suplente por su ID"""
        try:
            suplente = Suplente.query.get(suplente_id)
            if not suplente:
                return "Suplente no encontrado"
            db.session.delete(suplente)
            db.session.commit()
            return None
        except SQLAlchemyError as e:
            db.session.rollback()
            error_msg = f"Error al eliminar suplente {suplente_id}: {e}"
            print(error_msg)
            return error_msg