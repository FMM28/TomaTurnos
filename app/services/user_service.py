from app.models import Usuario
from app.extensions import db
from datetime import timezone
from typing import List, Optional, Tuple
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

class UserService:

    @staticmethod
    def get_all_users(include_deleted: bool = False) -> List[Usuario]:
        """Obtiene todos los usuarios activos"""
        try:
            query = Usuario.query

            if not include_deleted:
                query = query.filter(Usuario.deleted_at.is_(None))

            return query.order_by(Usuario.id_usuario).all()
        except SQLAlchemyError as e:
            print(f"Error al obtener usuarios: {e}")
            return []

    @staticmethod
    def get_user_by_id(user_id: int, include_deleted: bool = False) -> Optional[Usuario]:
        """Obtiene un usuario por ID"""
        try:
            query = Usuario.query.filter_by(id_usuario=user_id)

            if not include_deleted:
                query = query.filter(Usuario.deleted_at.is_(None))

            return query.first()
        except SQLAlchemyError as e:
            print(f"Error al obtener usuario {user_id}: {e}")
            return None

    @staticmethod
    def get_usuarios_by_role(role: str) -> List[Usuario]:
        """Obtiene usuarios activos por rol"""
        try:
            return (
                Usuario.query
                .filter_by(role=role)
                .filter(Usuario.deleted_at.is_(None))
                .order_by(Usuario.username)
                .all()
            )
        except SQLAlchemyError as e:
            print(f"Error al obtener usuarios con rol {role}: {e}")
            return []
        
    @staticmethod
    def get_usuarios_by_area(area_id: int) -> List[Usuario]:
        """Obtiene usuarios activos por area"""
        try:
            return (
                Usuario.query
                .filter_by(area_id=area_id)
                .filter_by(role='ventanilla')
                .filter(Usuario.deleted_at.is_(None))
                .order_by(Usuario.username)
                .all()
            )
        except SQLAlchemyError as e:
            print(f"Error al obtener usuarios en el area {area_id}: {e}")
            return []

    @staticmethod
    def username_exists(username: str, exclude_user_id: Optional[int] = None) -> bool:
        """
        Verifica si ya existe un usuario con el username dado.
        """
        query = Usuario.query.filter(
            Usuario.username == username
        )

        if exclude_user_id:
            query = query.filter(Usuario.id_usuario != exclude_user_id)

        return db.session.query(query.exists()).scalar()

    @staticmethod
    def create_user(
        username: str,
        nombre: str,
        ap_paterno: str,
        role: str,
        area_id: Optional[int],
        password: str,
        ap_materno: Optional[str] = None
    ) -> Tuple[Optional[Usuario], Optional[str]]:

        try:
            username = username.strip()
            nombre = nombre.strip()
            ap_paterno = ap_paterno.strip()
            ap_materno = ap_materno.strip() if ap_materno else None

            if not username:
                return None, "El nombre de usuario es requerido"
            if not nombre:
                return None, "El nombre es requerido"
            if not ap_paterno:
                return None, "El apellido paterno es requerido"
            if not password:
                return None, "La contraseña es requerida"
            if not role:
                return None, "El rol es requerido"

            if UserService.username_exists(username):
                return None, f"Ya existe un usuario con el nombre de usuario '{username}'"

            user = Usuario(
                username=username,
                nombre=nombre,
                ap_paterno=ap_paterno,
                ap_materno=ap_materno,
                role=role,
                area_id=area_id or None
            )
            user.set_password(password)

            db.session.add(user)
            db.session.commit()

            return user, None

        except SQLAlchemyError as e:
            db.session.rollback()
            return None, f"Error al crear el usuario: {e}"

    @staticmethod
    def update_user(
        user_id: int,
        username: str,
        nombre: str,
        ap_paterno: str,
        role: str,
        area_id: Optional[int],
        password: Optional[str] = None,
        ap_materno: Optional[str] = None
    ) -> Tuple[Optional[Usuario], Optional[str]]:

        try:
            user = Usuario.query.filter(
                Usuario.id_usuario == user_id,
                Usuario.deleted_at.is_(None)
            ).first()

            if not user:
                return None, "Usuario no encontrado"

            username = username.strip()

            if UserService.username_exists(username, exclude_user_id=user_id):
                return None, f"Ya existe otro usuario con el nombre de usuario '{username}'"

            user.username = username
            user.nombre = nombre.strip()
            user.ap_paterno = ap_paterno.strip()
            user.ap_materno = ap_materno.strip() if ap_materno else None
            user.role = role
            user.area_id = area_id or None

            if password:
                user.set_password(password)

            db.session.commit()
            return user, None

        except SQLAlchemyError as e:
            db.session.rollback()
            return None, f"Error al actualizar el usuario: {e}"

    @staticmethod
    def delete_user(user_id: int) -> Tuple[bool, Optional[str]]:
        """
        Marca el usuario como eliminado sin borrar registros relacionados
        """
        try:
            user = Usuario.query.filter(
                Usuario.id_usuario == user_id,
                Usuario.deleted_at.is_(None)
            ).first()

            if not user:
                return False, "Usuario no encontrado o ya eliminado"

            user.deleted_at = datetime.now()

            db.session.commit()
            return True, None

        except SQLAlchemyError as e:
            db.session.rollback()
            return False, f"Error al eliminar el usuario: {e}"
