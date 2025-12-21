from app.models import Usuario
from app.extensions import db
from typing import List, Optional


class UserService:
    
    @staticmethod
    def get_all_users() -> List[Usuario]:
        return Usuario.query.all()
    
    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[Usuario]:
        return Usuario.query.get(user_id)
    
    @staticmethod
    def get_user_by_id_or_404(user_id: int) -> Usuario:
        return Usuario.query.get_or_404(user_id)
    
    @staticmethod
    def create_user(username: str, role: str, password: str) -> Usuario:

        user = Usuario(username=username, role=role)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        return user
    
    @staticmethod
    def update_user(user_id: int, username: str, role: str, password: Optional[str] = None) -> Usuario:

        user = Usuario.query.get_or_404(user_id)
        
        user.username = username
        user.role = role
        
        if password:
            user.set_password(password)
        
        db.session.commit()
        
        return user
    
    @staticmethod
    def delete_user(user_id: int) -> None:

        user = Usuario.query.get_or_404(user_id)
        
        db.session.delete(user)
        db.session.commit()