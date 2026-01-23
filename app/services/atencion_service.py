import threading
from typing import Optional, List, Tuple
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from flask import current_app
from app.extensions import db, socketio
from app.models import Atencion, TicketTramite
from app.services.ventanilla_service import VentanillaService
from app.services.turno_service import TurnoService


TIEMPO_LLAMADO = 10

_llamado_timers: dict[int, threading.Timer] = {}


class AtencionService:
    """
    Servicio responsable del ciclo de vida de una atención
    """

    @staticmethod
    def iniciar_atencion(ticket_tramite: TicketTramite, id_usuario: int) -> Tuple[Optional[Atencion], Optional[str]]:

        try:
            ventanilla = VentanillaService.get_ventanilla_by_tramite(ticket_tramite.id_tramite)

            if not ventanilla:
                return None, "El trámite no tiene ventanilla asignada"

            atencion = Atencion(
                id_ticket_tramite=ticket_tramite.id_ticket_tramite,
                id_ventanilla=ventanilla.id_ventanilla,
                id_usuario=id_usuario,
                estado="llamado",
                hora_inicio=datetime.now()
            )

            ticket_tramite.estado = "llamado"

            db.session.add(atencion)
            db.session.commit()
            
            app = current_app._get_current_object()

            timer = threading.Timer(
                TIEMPO_LLAMADO,
                AtencionService.set_atendiendo,
                args=(app,atencion.id_atencion,)
            )

            _llamado_timers[atencion.id_atencion] = timer
            timer.start()

            return atencion, None

        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def set_atendiendo(app, id_atencion: int) -> None:
        with app.app_context():
            try:
                atencion = Atencion.query.get(id_atencion)

                if not atencion:
                    return

                if atencion.estado != "llamado":
                    return

                atencion.estado = "atendiendo"
                atencion.ticket_tramite.estado = "atendiendo"

                db.session.commit()

                _llamado_timers.pop(id_atencion, None)

                socketio.emit("turnos_en_llamado", TurnoService.get_turnos_en_llamado())

            except SQLAlchemyError:
                db.session.rollback()

    @staticmethod
    def rellamar(atencion: Atencion) -> None:
        app = current_app._get_current_object()
        
        timer = _llamado_timers.pop(atencion.id_atencion, None)
        if timer:
            timer.cancel()

        atencion.estado = "llamado"
        atencion.hora_inicio = datetime.now()
        atencion.ticket_tramite.estado = "llamado"

        db.session.commit()

        socketio.emit("turnos_en_llamado", TurnoService.get_turnos_en_llamado())

        nuevo_timer = threading.Timer(
            TIEMPO_LLAMADO,
            AtencionService.set_atendiendo,
            args=(app,atencion.id_atencion,)
        )

        _llamado_timers[atencion.id_atencion] = nuevo_timer
        nuevo_timer.start()

    @staticmethod
    def finalizar_atencion(
        atencion: Atencion,
        descripcion: Optional[str] = None
    ) -> None:

        timer = _llamado_timers.pop(atencion.id_atencion, None)
        if timer:
            timer.cancel()

        atencion.estado = "finalizado"
        atencion.hora_fin = datetime.now()
        atencion.descripcion_estado = descripcion

        atencion.ticket_tramite.estado = "atendido"

        db.session.commit()

        socketio.emit(
            "turnos_en_llamado",
            TurnoService.get_turnos_en_llamado()
        )
        
    @staticmethod
    def cancelar_atencion(
        atencion: Atencion,
        descripcion: Optional[str] = None
    ) -> None:

        timer = _llamado_timers.pop(atencion.id_atencion, None)
        if timer:
            timer.cancel()

        atencion.estado = "cancelado"
        atencion.hora_fin = datetime.now()
        atencion.descripcion_estado = descripcion

        atencion.ticket_tramite.estado = "cancelado"

        db.session.commit()

        socketio.emit(
            "turnos_en_llamado",
            TurnoService.get_turnos_en_llamado()
        )

    @staticmethod
    def volver_a_espera(
        atencion: Atencion,
        descripcion: Optional[str] = None
    ) -> None:
        """
        Regresa el trámite a la cola
        """

        atencion.estado = "cancelado"
        atencion.hora_fin = datetime.now()
        atencion.descripcion_estado = descripcion

        atencion.ticket_tramite.estado = "espera"

        db.session.commit()

    @staticmethod
    def get_atencion_activa_por_usuario(
        id_usuario: int
    ) -> Optional[Atencion]:

        return (
            Atencion.query
            .filter(
                Atencion.id_usuario == id_usuario,
                Atencion.estado.in_(["llamado", "atendiendo"])
            )
            .order_by(Atencion.hora_inicio.desc())
            .first()
        )

    @staticmethod
    def get_atencion_by_id(id_atencion: int) -> Optional[Atencion]:
        return Atencion.query.get(id_atencion)

    @staticmethod
    def get_turnos_en_llamado(limit: int = 14) -> List[Atencion]:
        return (
            Atencion.query
            .filter(Atencion.estado == "llamado")
            .order_by(Atencion.hora_inicio.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def tiempo_desde_ultimo_llamado(atencion:Atencion) -> int:
        """
        Calcula el tiempo transcurrido desde el último llamado
        """

        ahora = datetime.now()
        tiempo_transcurrido = (ahora - atencion.hora_inicio).total_seconds()
        
        return tiempo_transcurrido
