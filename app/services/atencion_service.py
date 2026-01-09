from typing import Optional, List, Tuple
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from app.extensions import db
from app.models import Atencion, TicketTramite, Ventanilla


class AtencionService:
    """
    Servicio responsable del ciclo de vida de una atención
    """

    @staticmethod
    def iniciar_atencion(
        ticket_tramite: TicketTramite,
        id_usuario: int
    ) -> Tuple[Optional[Atencion], Optional[str]]:
        """
        Marca un TicketTramite como atendiendo y crea la atención
        """

        try:
            ventanilla = Ventanilla.query.filter_by(
                id_usuario=id_usuario
            ).first()

            if not ventanilla:
                return None, "El usuario no tiene ventanilla asignada"

            # Crear atención
            atencion = Atencion(
                id_ticket_tramite=ticket_tramite.id_ticket_tramite,
                id_ventanilla=ventanilla.id_ventanilla,
                id_usuario=id_usuario,
                estado="llamado",
                hora_inicio=datetime.now()
            )

            ticket_tramite.estado = "atendiendo"

            db.session.add(atencion)
            db.session.commit()

            return atencion, None

        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def get_atencion_activa_por_usuario(
        id_usuario: int
    ) -> Optional[Atencion]:
        """
        Retorna la atención activa del usuario (si existe)
        """

        return (
            Atencion.query
            .filter(
                Atencion.id_usuario == id_usuario,
                Atencion.estado.in_(["llamado", "en_curso"])
            )
            .order_by(Atencion.hora_inicio.desc())
            .first()
        )

    @staticmethod
    def get_atencion_activa_por_ventanilla(
        id_ventanilla: int
    ) -> Optional[Atencion]:
        """
        Retorna la atención activa de una ventanilla
        """

        return (
            Atencion.query
            .filter(
                Atencion.id_ventanilla == id_ventanilla,
                Atencion.estado.in_(["llamado", "en_curso"])
            )
            .order_by(Atencion.hora_inicio.desc())
            .first()
        )

    @staticmethod
    def get_turnos_en_llamado(
        limit: int = 5
    ) -> List[Atencion]:
        """
        Retorna los últimos turnos llamados (para pantalla de anuncios)
        """

        return (
            Atencion.query
            .filter(Atencion.estado == "llamado")
            .order_by(Atencion.hora_inicio.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def rellamar(atencion: Atencion) -> None:
        """
        Solo actualiza timestamp para reflejar nuevo llamado
        """
        atencion.hora_inicio = datetime.now()
        db.session.commit()

    @staticmethod
    def finalizar_atencion(
        atencion: Atencion,
        descripcion: Optional[str] = None
    ) -> None:
        """
        Marca la atención como finalizada
        """

        atencion.estado = "finalizado"
        atencion.hora_fin = datetime.now()
        atencion.descripcion_estado = descripcion

        # Marcar ticket_tramite como atendido
        atencion.ticket_tramite.estado = "atendido"

        db.session.commit()

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
