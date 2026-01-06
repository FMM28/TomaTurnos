from app.models import TicketTramite, Tramite
from app.extensions import db
from typing import List, Optional, Tuple
from sqlalchemy.exc import SQLAlchemyError


class TicketTramiteService:

    @staticmethod
    def get_all() -> List[TicketTramite]:
        """Obtiene todos los ticket_tramite"""
        try:
            return TicketTramite.query.order_by(
                TicketTramite.id_ticket_tramite
            ).all()
        except SQLAlchemyError as e:
            print(f"Error al obtener ticket_tramite: {e}")
            return []

    @staticmethod
    def get_by_id(ticket_tramite_id: int) -> Optional[TicketTramite]:
        """Obtiene un ticket_tramite por ID"""
        try:
            return TicketTramite.query.get(ticket_tramite_id)
        except SQLAlchemyError as e:
            print(f"Error al obtener ticket_tramite {ticket_tramite_id}: {e}")
            return None

    @staticmethod
    def get_by_id_or_404(ticket_tramite_id: int) -> TicketTramite:
        """Obtiene un ticket_tramite o retorna 404"""
        return TicketTramite.query.get_or_404(ticket_tramite_id)

    @staticmethod
    def create(
        id_ticket: int,
        id_tramite: int,
        prioridad: Optional[int] = None,
        estado: str = "espera"
    ) -> Tuple[Optional[TicketTramite], Optional[str]]:
        """Crea la relación Ticket–Trámite"""
        try:
            new_tt = TicketTramite(
                id_ticket=id_ticket,
                id_tramite=id_tramite,
                prioridad=prioridad,
                estado=estado
            )
            db.session.add(new_tt)
            db.session.commit()
            return new_tt, None
        except SQLAlchemyError as e:
            db.session.rollback()
            error_msg = f"Error al crear TicketTramite: {e}"
            print(error_msg)
            return None, error_msg

    @staticmethod
    def create_multiple(
        id_ticket: int,
        tramites: List[int],
        prioridad: Optional[int] = None
    ) -> Tuple[List[TicketTramite], Optional[str]]:
        """Crea múltiples trámites para un mismo ticket"""
        try:
            registros = []
            for id_tramite in tramites:
                tt = TicketTramite(
                    id_ticket=id_ticket,
                    id_tramite=id_tramite,
                    prioridad=prioridad,
                    estado="espera"
                )
                db.session.add(tt)
                registros.append(tt)

            db.session.commit()
            return registros, None
        except SQLAlchemyError as e:
            db.session.rollback()
            error_msg = f"Error al crear múltiples TicketTramite: {e}"
            print(error_msg)
            return [], error_msg

    @staticmethod
    def update_estado(
        ticket_tramite_id: int,
        nuevo_estado: str
    ) -> Tuple[bool, Optional[str]]:
        """Actualiza el estado del ticket_tramite"""
        try:
            tt = TicketTramite.query.get(ticket_tramite_id)
            if not tt:
                return False, "TicketTramite no encontrado"

            tt.estado = nuevo_estado
            db.session.commit()
            return True, None
        except SQLAlchemyError as e:
            db.session.rollback()
            error_msg = f"Error al actualizar estado {ticket_tramite_id}: {e}"
            print(error_msg)
            return False, error_msg

    @staticmethod
    def delete(ticket_tramite_id: int) -> Tuple[bool, Optional[str]]:
        """Elimina un ticket_tramite"""
        try:
            tt = TicketTramite.query.get(ticket_tramite_id)
            if not tt:
                return False, "TicketTramite no encontrado"

            db.session.delete(tt)
            db.session.commit()
            return True, None
        except SQLAlchemyError as e:
            db.session.rollback()
            error_msg = f"Error al eliminar TicketTramite {ticket_tramite_id}: {e}"
            print(error_msg)
            return False, error_msg

    @staticmethod
    def get_tramites_by_ticket(ticket_id: int) -> List[Tramite]:
        """Obtiene los trámites asociados a un ticket usando JOIN"""
        try:
            return (
                db.session.query(Tramite)
                .join(TicketTramite, TicketTramite.id_tramite == Tramite.id_tramite)
                .filter(TicketTramite.id_ticket == ticket_id)
                .order_by(TicketTramite.id_ticket_tramite)
                .all()
            )
        except SQLAlchemyError as e:
            print(f"Error al obtener trámites del ticket {ticket_id}: {e}")
            return []