from app.models import Ticket
from app.extensions import db
from typing import List, Optional, Tuple
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime


class TicketService:

    @staticmethod
    def get_all_tickets() -> List[Ticket]:
        """Obtiene todos los tickets"""
        try:
            return Ticket.query.order_by(Ticket.id_ticket).all()
        except SQLAlchemyError as e:
            print(f"Error al obtener tickets: {e}")
            return []

    @staticmethod
    def get_ticket_by_id(ticket_id: int) -> Optional[Ticket]:
        """Obtiene un ticket por su ID"""
        try:
            return Ticket.query.get(ticket_id)
        except SQLAlchemyError as e:
            print(f"Error al obtener ticket {ticket_id}: {e}")
            return None

    @staticmethod
    def get_ticket_by_id_or_404(ticket_id: int) -> Ticket:
        """Obtiene un ticket por su ID o retorna 404"""
        return Ticket.query.get_or_404(ticket_id)
    
    @staticmethod
    def get_tickets_by_estado(estado: str) -> List[Ticket]:
        """Obtiene tickets por su estado"""
        try:
            return Ticket.query.filter_by(estado=estado).order_by(Ticket.id_ticket).all()
        except SQLAlchemyError as e:
            print(f"Error al obtener tickets con estado {estado}: {e}")
            return []
        
    @staticmethod
    def get_tickets_atendidos_hoy() -> List[Ticket]:
        """Obtiene tickets atendidos hoy"""
        try:
            today = datetime.now().date()
            return Ticket.query.filter(
                Ticket.estado == "finalizado",
                db.func.date(Ticket.fecha_hora) == today
            ).order_by(Ticket.id_ticket).all()
        except SQLAlchemyError as e:
            print(f"Error al obtener tickets atendidos hoy: {e}")
            return []

    @staticmethod
    def create_ticket(
        turno: int,
        estado: str = "activo",
        fecha_hora: Optional[datetime] = None
    ) -> Tuple[Optional[Ticket], Optional[str]]:
        """Crea un nuevo ticket"""
        try:
            new_ticket = Ticket(
                turno=turno,
                estado=estado,
                fecha_hora=fecha_hora or datetime.now()
            )
            db.session.add(new_ticket)
            db.session.commit()
            return new_ticket, None
        except SQLAlchemyError as e:
            db.session.rollback()
            error_msg = f"Error al crear ticket: {e}"
            print(error_msg)
            return None, error_msg

    @staticmethod
    def update_estado(
        ticket_id: int,
        nuevo_estado: str
    ) -> Tuple[bool, Optional[str]]:
        """Actualiza el estado de un ticket"""
        try:
            ticket = Ticket.query.get(ticket_id)
            if not ticket:
                return False, "Ticket no encontrado"

            ticket.estado = nuevo_estado
            db.session.commit()
            return True, None
        except SQLAlchemyError as e:
            db.session.rollback()
            error_msg = f"Error al actualizar estado del ticket {ticket_id}: {e}"
            print(error_msg)
            return False, error_msg

    @staticmethod
    def delete_ticket(ticket_id: int) -> Tuple[bool, Optional[str]]:
        """Elimina un ticket por su ID"""
        try:
            ticket = Ticket.query.get(ticket_id)
            if not ticket:
                return False, "Ticket no encontrado"

            db.session.delete(ticket)
            db.session.commit()
            return True, None
        except SQLAlchemyError as e:
            db.session.rollback()
            error_msg = f"Error al eliminar ticket {ticket_id}: {e}"
            print(error_msg)
            return False, error_msg
