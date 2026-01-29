from typing import Optional, Tuple
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models.anuncio import Anuncio
import os
import uuid


class AnuncioService:

    UPLOAD_FOLDER = os.path.join("app", "static", "uploads", "anuncios")
    AUDIO_FOLDER = os.path.join("app", "static", "uploads", "audio")

    VIDEO_EXT = {"mp4", "webm", "ogg", "mov", "mkv"}
    IMAGE_EXT = {"jpg", "jpeg", "png", "webp"}
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB

    @staticmethod
    def _init_folders():
        os.makedirs(AnuncioService.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(AnuncioService.AUDIO_FOLDER, exist_ok=True)

    @staticmethod
    def _allowed_file(filename: str, tipo: str) -> bool:
        if "." not in filename:
            return False
        ext = filename.rsplit(".", 1)[1].lower()
        return (
            ext in AnuncioService.VIDEO_EXT if tipo == "video"
            else ext in AnuncioService.IMAGE_EXT
        )

    @staticmethod
    def _save_file(file: FileStorage, tipo: str) -> Tuple[Optional[str], Optional[str]]:
        AnuncioService._init_folders()

        if not file or not file.filename:
            return None, "Archivo inválido"

        if not AnuncioService._allowed_file(file.filename, tipo):
            return None, "Formato de archivo no permitido"

        filename = secure_filename(file.filename)
        unique_name = f"{uuid.uuid4()}_{filename}"
        full_path = os.path.join(AnuncioService.UPLOAD_FOLDER, unique_name)

        file.save(full_path)

        if os.path.getsize(full_path) > AnuncioService.MAX_FILE_SIZE:
            os.remove(full_path)
            return None, "El archivo excede 100 MB"

        return os.path.join("uploads", "anuncios", unique_name), None

    # ---------------------------------------------------
    # CREATE
    # ---------------------------------------------------
    @staticmethod
    def create(
        archivo: FileStorage,
        titulo: str,
        tipo: str,
        duracion: Optional[int]
    ) -> Tuple[Optional[Anuncio], Optional[str]]:

        if tipo not in ("video", "imagen"):
            return None, "Tipo inválido"

        if not duracion or duracion <= 0:
            return None, "Duración inválida"

        ruta, error = AnuncioService._save_file(archivo, tipo)
        if error:
            return None, error

        anuncio = Anuncio(
            enlace=ruta,
            titulo=titulo,
            duracion=duracion,
            tipo=tipo,
            activo=True
        )

        db.session.add(anuncio)
        db.session.commit()

        return anuncio, None

    # ---------------------------------------------------
    # UPDATE
    # ---------------------------------------------------
    @staticmethod
    def update(
        id_anuncio: int,
        archivo: Optional[FileStorage] = None,
        duracion: Optional[int] = None,
        activo: Optional[bool] = None
    ) -> Tuple[Optional[Anuncio], Optional[str]]:

        anuncio = Anuncio.query.get(id_anuncio)
        if not anuncio:
            return None, "Anuncio no encontrado"

        # Reemplazar archivo
        if archivo and archivo.filename:
            old_path = os.path.join("app", "static", anuncio.enlace)
            if os.path.exists(old_path):
                os.remove(old_path)

            ruta, error = AnuncioService._save_file(archivo, anuncio.tipo)
            if error:
                return None, error

            anuncio.enlace = ruta

        # Actualizar duración (imagen o video)
        if duracion is not None:
            if duracion <= 0:
                return None, "Duración inválida"
            anuncio.duracion = duracion

        if activo is not None:
            anuncio.activo = activo

        db.session.commit()
        return anuncio, None

    # ---------------------------------------------------
    # OTROS
    # ---------------------------------------------------
    @staticmethod
    def get_all():
        return Anuncio.query.order_by(Anuncio.id_anuncio.desc()).all()

    @staticmethod
    def get_by_id(id_anuncio: int) -> Optional[Anuncio]:
        return Anuncio.query.get(id_anuncio)

    @staticmethod
    def deactivate(id_anuncio: int) -> bool:
        anuncio = Anuncio.query.get(id_anuncio)
        if not anuncio:
            return False
        anuncio.activo = False
        db.session.commit()
        return True

    @staticmethod
    def delete(id_anuncio: int) -> bool:
        anuncio = Anuncio.query.get(id_anuncio)
        if not anuncio:
            return False

        file_path = os.path.join("app", "static", anuncio.enlace)

        db.session.delete(anuncio)
        db.session.commit()

        if os.path.exists(file_path):
            os.remove(file_path)

        return True
