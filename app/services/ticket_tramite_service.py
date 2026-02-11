from sqlalchemy import select
from app.models import (TicketTramite, Tramite, Ticket, Asignacion, Suplente)
from app.extensions import db
from typing import List, Optional, Tuple
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime


class TicketTramiteService:

    @staticmethod
    def get_by_id(ticket_tramite_id: int) -> Optional[TicketTramite]:
        """Obtiene un ticket_tramite por ID"""
        try:
            return TicketTramite.query.get(ticket_tramite_id)
        except SQLAlchemyError as e:
            print(f"Error al obtener TicketTramite {ticket_tramite_id}: {e}")
            return None

    @staticmethod
    def get_by_id_or_404(ticket_tramite_id: int) -> TicketTramite:
        """Obtiene un ticket_tramite o retorna 404"""
        return TicketTramite.query.get_or_404(ticket_tramite_id)

    @staticmethod
    def create(
        id_ticket: int,
        id_tramite: int,
        prioridad: Optional[int] = None
    ) -> Tuple[Optional[TicketTramite], Optional[str]]:

        try:
            if prioridad is None:
                ultimo = (
                    TicketTramite.query
                    .filter(
                        TicketTramite.id_ticket == id_ticket,
                        TicketTramite.estado.in_(["espera", "pendiente"])
                    )
                    .order_by(TicketTramite.prioridad.asc())
                    .first()
                )
                prioridad = ultimo.prioridad - 1 if ultimo else 1

            tt = TicketTramite(
                id_ticket=id_ticket,
                id_tramite=id_tramite,
                prioridad=prioridad,
                estado="pendiente",
                fecha_creacion=datetime.now()
            )

            db.session.add(tt)
            db.session.flush()

            return tt, None

        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def create_multiple(
        id_ticket: int,
        tramites: List[int]
    ) -> Tuple[List[TicketTramite], Optional[str]]:
        """Crea múltiples trámites para un mismo ticket"""
        try:
            registros = []

            prioridad_base = len(tramites)

            for index, id_tramite in enumerate(tramites):
                tt = TicketTramite(
                    id_ticket=id_ticket,
                    id_tramite=id_tramite,
                    prioridad=prioridad_base - index,
                    estado="espera" if index == 0 else "pendiente",
                    fecha_creacion=datetime.now()
                )

                db.session.add(tt)
                registros.append(tt)

            db.session.commit()
            return registros, None

        except SQLAlchemyError as e:
            db.session.rollback()
            return [], str(e)

    @staticmethod
    def get_cola_para_usuario(usuario_id: int) -> List[TicketTramite]:
        """
        Devuelve la cola de trámites pendientes que el usuario puede atender
        """
        try:
            usuarios_ids = (
                select(Suplente.id_usuario)
                .where(Suplente.id_suplente_usuario == usuario_id)
            )

            tramites_subquery = (
                select(Asignacion.id_tramite)
                .where(
                    db.or_(
                        Asignacion.id_usuario == usuario_id,
                        Asignacion.id_usuario.in_(usuarios_ids)
                    )
                )
            )

            return (
                TicketTramite.query
                .join(Ticket)
                .filter(
                    TicketTramite.estado.in_(["pendiente", "espera"]),
                    TicketTramite.id_tramite.in_(tramites_subquery),
                    Ticket.estado == "activo"
                )
                .order_by(
                    TicketTramite.prioridad.desc(),
                    TicketTramite.fecha_creacion.asc(),
                    TicketTramite.id_ticket_tramite.asc()
                )
                .all()
            )

        except SQLAlchemyError as e:
            print(f"Error al obtener cola del usuario {usuario_id}: {e}")
            return []

    @staticmethod
    def get_siguiente_para_usuario(usuario_id: int) -> Optional[TicketTramite]:
        """
        Obtiene el siguiente TicketTramite que puede atender el usuario
        """
        cola = TicketTramiteService.get_cola_para_usuario(usuario_id)
        cola = [tt for tt in cola if tt.estado == "espera"]
        return cola[0] if cola else None
    
    @staticmethod
    def get_siguiente_espera(ticket_tramite: TicketTramite)-> Tuple[Optional[TicketTramite], Optional[str]]:
        try:
            if siguiente := (
                TicketTramite.query
                .filter(
                    TicketTramite.id_ticket == ticket_tramite.id_ticket,
                    TicketTramite.estado == "pendiente"
                )
                .order_by(
                    TicketTramite.prioridad.desc(),
                    TicketTramite.fecha_creacion.asc(),
                    TicketTramite.id_ticket_tramite.asc()
                )
                .first()
            ):
                siguiente.estado = "espera"
            else:
                ticket_tramite.ticket.estado = "finalizado"

            db.session.commit()
            return siguiente, None

        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Error al obtener siguiente trámite del ticket: {e}")
            return None, str(e)
        
    @staticmethod
    def usuario_puede_atender(ticket_tramite: TicketTramite, usuario_id: int) -> bool:
        """
        Indica si el usuario puede atender un TicketTramite específico
        """
        try:
            usuarios_ids = (
                select(Suplente.id_usuario)
                .where(Suplente.id_suplente_usuario == usuario_id)
            )

            tramites_subquery = (
                select(Asignacion.id_tramite)
                .where(
                    db.or_(
                        Asignacion.id_usuario == usuario_id,
                        Asignacion.id_usuario.in_(usuarios_ids)
                    )
                )
            )

            return (
                db.session.query(TicketTramite.id_ticket_tramite)
                .filter(
                    TicketTramite.id_ticket_tramite == ticket_tramite.id_ticket_tramite,
                    TicketTramite.estado.in_(["pendiente", "espera"]),
                    TicketTramite.id_tramite.in_(tramites_subquery)
                )
                .first()
                is not None
            )

        except SQLAlchemyError as e:
            print(
                f"Error validando si usuario {usuario_id} "
                f"puede atender ticket_tramite {ticket_tramite.id_ticket_tramite}: {e}"
            )
            return False

    @staticmethod
    def marcar_atendiendo(ticket_tramite_id: int) -> Tuple[bool, Optional[str]]:
        try:
            tt = TicketTramite.query.get(ticket_tramite_id)
            if not tt:
                return False, "TicketTramite no encontrado"

            tt.estado = "atendiendo"
            db.session.commit()
            return True, None
        except SQLAlchemyError as e:
            db.session.rollback()
            return False, str(e)

    @staticmethod
    def finalizar(ticket_tramite_id: int) -> Tuple[bool, Optional[str]]:
        try:
            tt = TicketTramite.query.get(ticket_tramite_id)
            if not tt:
                return False, "TicketTramite no encontrado"

            tt.estado = "finalizado"
            db.session.commit()
            return True, None
        except SQLAlchemyError as e:
            db.session.rollback()
            return False, str(e)
        
    @staticmethod
    def cancelar_ticket_tramite(ticket_tramite_id: int) -> Tuple[bool, Optional[str]]:
        try:
            tt = TicketTramite.query.get(ticket_tramite_id)
            if not tt:
                return False, "TicketTramite no encontrado"

            estado_anterior = tt.estado

            tt.estado = "cancelado"

            if estado_anterior == "espera":
                siguiente = TicketTramiteService.get_siguiente_espera(tt)

            db.session.commit()
            return True, None

        except SQLAlchemyError as e:
            db.session.rollback()
            return False, str(e)

    @staticmethod
    def reasignar(ticket_tramite_id: int, nuevo_tramite_id: int, prioridad_extra: int = 10) -> Tuple[bool, Optional[str]]:
        """
        Regresa el trámite a la cola con más prioridad
        """
        try:
            tt = TicketTramite.query.get(ticket_tramite_id)
            if not tt:
                return False, "TicketTramite no encontrado"

            tt.estado = "espera"
            tt.id_tramite = nuevo_tramite_id
            tt.prioridad += prioridad_extra
            db.session.commit()
            return True, None
        except SQLAlchemyError as e:
            db.session.rollback()
            return False, str(e)
            
    @staticmethod
    def insertar_tramite_prioritario(
        ticket_tramite_id: int,
        nuevo_id_tramite: int,
        prioridad_extra: int = 50
    ) -> Tuple[Optional[TicketTramite], Optional[str]]:
        try:
            tt_actual = TicketTramite.query.get(ticket_tramite_id)
            if not tt_actual:
                return None, "TicketTramite original no encontrado"

            tt_actual.estado = "pendiente"

            nuevo_tt = TicketTramite(
                id_ticket=tt_actual.id_ticket,
                id_tramite=nuevo_id_tramite,
                estado="espera",
                prioridad=tt_actual.prioridad + prioridad_extra,
                fecha_creacion=datetime.now()
            )

            db.session.add(nuevo_tt)
            db.session.commit()
            return nuevo_tt, None

        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)
        
    @staticmethod
    def insertar_tramite_en_ticket(
        ticket_id: int,
        id_tramite: int,
        posicion_tipo: str,
        referencia_id: Optional[int] = None
    ) -> Tuple[bool, Optional[str]]:

        try:
            ticket = Ticket.query.get(ticket_id)
            if not ticket:
                return False, "Ticket no encontrado"

            cola = (
                TicketTramite.query
                .filter(
                    TicketTramite.id_ticket == ticket_id,
                    TicketTramite.estado.in_(["espera", "pendiente"])
                )
                .order_by(
                    TicketTramite.prioridad.desc(),
                    TicketTramite.id_ticket_tramite.asc()
                )
                .all()
            )

            if not cola:
                nuevo_tt, error = TicketTramiteService.create(
                    id_ticket=ticket_id,
                    id_tramite=id_tramite,
                    prioridad=1
                )
                if error:
                    return False, error

                nuevo_tt.estado = "espera"
                db.session.commit()
                return True, None

            if posicion_tipo == "inicio":
                index = 0

            elif posicion_tipo == "final":
                index = len(cola)

            elif posicion_tipo in ("antes", "despues"):
                referencia = next(
                    (x for x in cola if x.id_ticket_tramite == int(referencia_id)),
                    None
                )
                if not referencia:
                    return False, "Referencia no válida"

                ref_index = cola.index(referencia)
                index = ref_index if posicion_tipo == "antes" else ref_index + 1

            else:
                return False, "Posición inválida"

            nuevo_tt, error = TicketTramiteService.create(
                id_ticket=ticket_id,
                id_tramite=id_tramite
            )
            if error:
                return False, error

            cola.insert(index, nuevo_tt)

            prioridad_base = len(cola)
            for tt in cola:
                tt.prioridad = prioridad_base
                prioridad_base -= 1

            actual_espera = next((x for x in cola if x.estado == "espera"), None)

            if actual_espera:
                idx_espera = cola.index(actual_espera)
                if index <= idx_espera:
                    actual_espera.estado = "pendiente"
                    nuevo_tt.estado = "espera"
                else:
                    nuevo_tt.estado = "pendiente"
            else:
                cola[0].estado = "espera"

            db.session.commit()
            return True, None

        except SQLAlchemyError as e:
            db.session.rollback()
            return False, str(e)
        
    @staticmethod
    def _reordenar_prioridades(ticket_id: int):

        cola = (
            TicketTramite.query
            .filter(
                TicketTramite.id_ticket == ticket_id,
                TicketTramite.estado.in_(["espera", "pendiente"])
            )
            .order_by(
                TicketTramite.prioridad.desc(),
                TicketTramite.id_ticket_tramite.asc()
            )
            .all()
        )

        prioridad_base = len(cola)

        for tt in cola:
            tt.prioridad = prioridad_base
            prioridad_base -= 1

    @staticmethod
    def get_tramites_by_ticket(ticket_id: int) -> List[Tramite]:
        try:
            return (
                db.session.query(Tramite)
                .join(TicketTramite)
                .filter(TicketTramite.id_ticket == ticket_id)
                .order_by(TicketTramite.id_ticket_tramite)
                .all()
            )
        except SQLAlchemyError as e:
            print(f"Error al obtener trámites del ticket {ticket_id}: {e}")
            return []
        
    @staticmethod    
    def get_tickets_en_espera_por_tramite(id_tramite: int) -> List[TicketTramite]:
        return db.session.query(TicketTramite).filter(
            TicketTramite.id_tramite == id_tramite,
            TicketTramite.estado == 'espera'
        ).order_by(TicketTramite.fecha_creacion.asc()).all()
        
    @staticmethod
    def get_tickets_by_estados(estado_list: List[str]) -> List[TicketTramite]:
        try:
            return (
                TicketTramite.query
                .filter(TicketTramite.estado.in_(estado_list))
                .order_by(TicketTramite.id_ticket_tramite)
                .all()
            )
        except SQLAlchemyError as e:
            print(f"Error al obtener TicketTramites por estados {estado_list}: {e}")
            return []
        
    @staticmethod
    def get_tickets_by_estados_and_area(estados: List[str], id_area: int) -> List[TicketTramite]:
        try:
            return (
                db.session.query(TicketTramite)
                .join(Tramite, TicketTramite.id_tramite == Tramite.id_tramite)
                .filter(
                    TicketTramite.estado.in_(estados),
                    Tramite.id_area == id_area
                )
                .order_by(TicketTramite.id_ticket_tramite)
                .all()
            )
        except SQLAlchemyError as e:
            print(f"Error al obtener TicketTramites por estados {estados} y área {id_area}: {e}")
            return []
        
    @staticmethod
    def get_ticket_tramites_by_ticket(ticket_id: int) -> List[TicketTramite]:
        try:
            return (
                TicketTramite.query
                .filter(TicketTramite.id_ticket == ticket_id)
                .order_by(TicketTramite.id_ticket_tramite)
                .all()
            )
        except SQLAlchemyError as e:
            print(f"Error al obtener TicketTramites por ticket_id {ticket_id}: {e}")
            return []