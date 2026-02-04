from contextlib import suppress
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models.anuncio import Anuncio
from app.services.audio_service import AudioService
import os
import uuid
import subprocess


class AnuncioService:

    UPLOAD_FOLDER = os.path.join("app", "static", "uploads", "anuncios")
    AUDIO_FOLDER = os.path.join("app", "static", "uploads", "audio")

    VIDEO_EXT = {"mp4", "webm", "ogg", "mov", "mkv"}
    IMAGE_EXT = {"jpg", "jpeg", "png", "webp"}
    MAX_FILE_SIZE = 100 * 1024 * 1024
    
    BASE_DIR = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..")
    )

    FFMPEG_PATH = os.path.join(
        BASE_DIR,
        "ffmpeg",
        "bin",
        "ffmpeg.exe"
    )

    if not os.path.exists(FFMPEG_PATH):
        raise FileNotFoundError(f"FFmpeg no encontrado en: {FFMPEG_PATH}")

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
    def _save_file(file: FileStorage, tipo: str):
        AnuncioService._init_folders()

        if not file or not file.filename:
            return None, "Archivo inválido"

        if not AnuncioService._allowed_file(file.filename, tipo):
            return None, "Formato no permitido"

        filename = secure_filename(file.filename)
        unique_name = f"{uuid.uuid4()}_{filename}"
        full_path = os.path.join(AnuncioService.UPLOAD_FOLDER, unique_name)

        file.save(full_path)

        if os.path.getsize(full_path) > AnuncioService.MAX_FILE_SIZE:
            os.remove(full_path)
            return None, "Archivo demasiado grande"

        return os.path.join("uploads", "anuncios", unique_name), None

    @staticmethod
    def _extract_audio_from_video(video_rel_path):
        video_path = os.path.join("app", "static", video_rel_path)
        
        video_path = os.path.abspath(video_path)
        allowed_dir = os.path.abspath(os.path.join("app", "static", "uploads", "anuncios"))
        if not video_path.startswith(allowed_dir) or not os.path.exists(video_path):
            return None, "Invalid video path"

        audio_filename = f"{uuid.uuid4()}.wav"
        audio_full_path = os.path.join(
            AnuncioService.AUDIO_FOLDER,
            audio_filename
        )

        cmd = [
            AnuncioService.FFMPEG_PATH,
            "-y",
            "-i", video_path,
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "44100",
            "-ac", "2",
            audio_full_path
        ]

        try:
            subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                shell=False
            )
            return os.path.join("uploads", "audio", audio_filename), None
        except subprocess.CalledProcessError as e:
            return None, f"Error extrayendo audio: {e}"

    @staticmethod
    def create(archivo, titulo, tipo, duracion):

        ruta, error = AnuncioService._save_file(archivo, tipo)
        if error:
            return None, error

        audio = None
        if tipo == "video":
            audio, error = AnuncioService._extract_audio_from_video(ruta)
            if error:
                audio = None

        anuncio = Anuncio(
            enlace=ruta,
            titulo=titulo.strip(),
            audio=audio,
            duracion=duracion,
            tipo=tipo,
            activo=True
        )

        db.session.add(anuncio)
        db.session.commit()

        AudioService.mark_anuncios_dirty()

        return anuncio, None

    @staticmethod
    def update(id_anuncio, archivo=None, duracion=None, activo=None):
        anuncio = Anuncio.query.get(id_anuncio)
        if not anuncio:
            return None, "No encontrado"

        if archivo:
            AudioService.mark_audio_for_delete(anuncio.audio)

            ruta, error = AnuncioService._save_file(archivo, anuncio.tipo)
            if error:
                return None, error

            anuncio.enlace = ruta
            if anuncio.tipo == "video":
                anuncio.audio, _ = AnuncioService._extract_audio_from_video(ruta)

        if duracion:
            anuncio.duracion = duracion

        if activo is not None:
            anuncio.activo = activo

        db.session.commit()
        AudioService.mark_anuncios_dirty()
        return anuncio, None

    @staticmethod
    def get_all():
        return Anuncio.query.order_by(Anuncio.id_anuncio.desc()).all()
    
    @staticmethod
    def get_by_id(id_anuncio):
        return Anuncio.query.get(id_anuncio)
    
    @staticmethod
    def toggle_active(id_anuncio):
        anuncio = Anuncio.query.get(id_anuncio)
        if not anuncio:
            return None, "No encontrado"

        anuncio.activo = not anuncio.activo
        db.session.commit()

        AudioService.mark_anuncios_dirty()
        return anuncio, None

    @staticmethod
    def delete(id_anuncio):
        anuncio = Anuncio.query.get(id_anuncio)
        if not anuncio:
            return False

        if anuncio.enlace:
            file_path = os.path.join("app", "static", anuncio.enlace)
            with suppress(Exception):
                if os.path.exists(file_path):
                    os.remove(file_path)

        if anuncio.audio:
            audio_path = os.path.join("app", "static", anuncio.audio)
            with suppress(Exception):
                if os.path.exists(audio_path):
                    os.remove(audio_path)

        db.session.delete(anuncio)
        db.session.commit()

        AudioService.mark_anuncios_dirty()
        return True