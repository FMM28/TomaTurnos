from app.models import Usuario
from app.extensions import db
from typing import List, Optional, Tuple
from sqlalchemy.exc import SQLAlchemyError


class UserService:
    
    @staticmethod
    def get_all_users() -> List[Usuario]:
        """Obtiene todos los usuarios"""
        try:
            return Usuario.query.order_by(Usuario.id_usuario).all()
        except SQLAlchemyError as e:
            print(f"Error al obtener usuarios: {e}")
            return []
    
    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[Usuario]:
        """Obtiene un usuario por su ID"""
        try:
            return Usuario.query.get(user_id)
        except SQLAlchemyError as e:
            print(f"Error al obtener usuario {user_id}: {e}")
            return None
    
    @staticmethod
    def get_user_by_id_or_404(user_id: int) -> Usuario:
        """Obtiene un usuario por su ID o retorna 404"""
        return Usuario.query.get_or_404(user_id)
    
    @staticmethod
    def get_usuarios_by_role(role: str) -> List[Usuario]:
        """Obtiene todos los usuarios con un rol específico"""
        try:
            return Usuario.query.filter_by(role=role).order_by(Usuario.username).all()
        except SQLAlchemyError as e:
            print(f"Error al obtener usuarios con rol {role}: {e}")
            return []
    
    @staticmethod
    def create_user(username: str, nombre: str, ap_paterno: str, role: str, password: str, ap_materno: Optional[str] = None) -> Tuple[Optional[Usuario], Optional[str]]:
        """Crea un nuevo usuario"""
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
            
            user = Usuario(
                username=username,
                nombre=nombre,
                ap_paterno=ap_paterno,
                ap_materno=ap_materno,
                role=role
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            return user, None
        except SQLAlchemyError as e:
            db.session.rollback()
            error_msg = f"Error al crear el usuario: {str(e)}"
            print(error_msg)
            return None, error_msg

    @staticmethod
    def update_user(user_id: int, username: str, nombre: str, ap_paterno: str, role: str, password: Optional[str] = None, ap_materno: Optional[str] = None) -> Tuple[Optional[Usuario], Optional[str]]:
        """Actualiza un usuario existente"""
        try:
            user = Usuario.query.get(user_id)
            if not user:
                return None, "Usuario no encontrado"
            
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
            
            if not role:
                return None, "El rol es requerido"
            
            user.username = username
            user.nombre = nombre
            user.ap_paterno = ap_paterno
            user.ap_materno = ap_materno
            user.role = role
            
            if password:
                user.set_password(password)
            
            db.session.commit()
            return user, None
        except SQLAlchemyError as e:
            db.session.rollback()
            error_msg = f"Error al actualizar el usuario: {str(e)}"
            print(error_msg)
            return None, error_msg
    
    @staticmethod
    def delete_user(user_id: int) -> Tuple[bool, Optional[str]]:
        """Elimina un usuario"""
        try:
            user = Usuario.query.get(user_id)
            if not user:
                return False, "Usuario no encontrado"
            
            db.session.delete(user)
            db.session.commit()
            return True, None
        except SQLAlchemyError as e:
            db.session.rollback()
            error_msg = f"Error al eliminar el usuario: {str(e)}"
            print(error_msg)
            return False, error_msg