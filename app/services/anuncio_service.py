from contextlib import suppress
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models.anuncio import Anuncio
from app.services.audio_service import AudioService
import os
import uuid
import subprocess
import shutil
from concurrent.futures import ThreadPoolExecutor
import json


class AnuncioService:

    UPLOAD_FOLDER = os.path.join("app", "static", "uploads", "anuncios")
    AUDIO_FOLDER = os.path.join("app", "static", "uploads", "audio")

    VIDEO_EXT = {"mp4", "webm", "ogg", "mov", "mkv"}
    IMAGE_EXT = {"jpg", "jpeg", "png", "webp"}
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB

    BASE_DIR = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..")
    )

    FFMPEG_PATH = os.path.join(
        BASE_DIR,
        "ffmpeg",
        "bin",
        "ffmpeg.exe"
    )

    FFPROBE_PATH = os.path.join(
        BASE_DIR,
        "ffmpeg",
        "bin",
        "ffprobe.exe"
    )

    if not os.path.exists(FFMPEG_PATH):
        raise FileNotFoundError(f"FFmpeg no encontrado en: {FFMPEG_PATH}")

    _executor = ThreadPoolExecutor(max_workers=2)

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
            ext in AnuncioService.VIDEO_EXT
            if tipo == "video"
            else ext in AnuncioService.IMAGE_EXT
        )

    @staticmethod
    def _check_video_codec(video_path: str) -> dict:
        """Verifica si el video ya está en formato óptimo"""
        if not os.path.exists(AnuncioService.FFPROBE_PATH):
            return {"needs_optimization": True}
        
        cmd = [
            AnuncioService.FFPROBE_PATH,
            "-v", "quiet",
            "-print_format", "json",
            "-show_streams",
            "-show_format",
            video_path
        ]
        
        with suppress(Exception):
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            data = json.loads(result.stdout)
            
            if video_stream := next(
                (s for s in data.get("streams", []) if s.get("codec_type") == "video"),
                None
            ):
                codec = video_stream.get("codec_name", "")
                profile = video_stream.get("profile", "")
                pix_fmt = video_stream.get("pix_fmt", "")
                
                is_optimized = (
                    codec == "h264" and
                    profile in ["Main", "High"] and
                    pix_fmt == "yuv420p"
                )
                
                return {
                    "needs_optimization": not is_optimized,
                    "codec": codec,
                    "profile": profile
                }
        
        return {"needs_optimization": True}

    @staticmethod
    def _optimize_video(input_path: str, output_path: str):
        """Optimiza video con configuración de alta velocidad"""
        # Verificar si necesita optimización
        video_info = AnuncioService._check_video_codec(input_path)
        
        if not video_info.get("needs_optimization"):
            # Solo copiar si ya está optimizado
            shutil.copy2(input_path, output_path)
            return
        
        cmd = [
            AnuncioService.FFMPEG_PATH,
            "-y",
            "-i", input_path,
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "23",
            "-profile:v", "main",
            "-level", "4.0",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            "-c:a", "aac",
            "-b:a", "128k",
            "-threads", "0",
            output_path
        ]

        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=120
        )

    @staticmethod
    def _extract_audio_from_video(video_path: str, audio_output_path: str):
        """Extrae audio desde un archivo de video (optimizado)"""
        cmd = [
            AnuncioService.FFMPEG_PATH,
            "-y",
            "-i", video_path,
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "44100",
            "-ac", "2",
            "-threads", "0",
            audio_output_path
        ]

        try:
            subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=60
            )
            return os.path.exists(audio_output_path) and os.path.getsize(audio_output_path) > 0
        except subprocess.CalledProcessError:
            return False

    @staticmethod
    def _process_video_parallel(temp_path: str, final_path: str, audio_path: str):
        """
        Procesa video y audio en paralelo usando FFmpeg con múltiples salidas.
        Esto es MÁS RÁPIDO que dos comandos separados.
        """
        cmd = [
            AnuncioService.FFMPEG_PATH,
            "-y",
            "-i", temp_path,
            "-map", "0:v:0",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "23",
            "-profile:v", "main",
            "-level", "4.0",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            "-map", "0:a:0?",
            "-c:a", "aac",
            "-b:a", "128k",
            "-threads", "0",
            final_path,
            "-map", "0:a:0?",
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "44100",
            "-ac", "2",
            audio_path
        ]

        try:
            subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=120
            )
            
            video_ok = os.path.exists(final_path) and os.path.getsize(final_path) > 0
            audio_ok = os.path.exists(audio_path) and os.path.getsize(audio_path) > 0
            
            return video_ok, audio_ok
        except subprocess.CalledProcessError as e:
            return False, False

    @staticmethod
    def _save_file(file: FileStorage, tipo: str):
        AnuncioService._init_folders()

        if not file or not file.filename:
            return None, None, "Archivo inválido"

        if not AnuncioService._allowed_file(file.filename, tipo):
            return None, None, "Formato no permitido"

        original_name = secure_filename(file.filename)
        uid = uuid.uuid4().hex

        temp_path = os.path.join(
            AnuncioService.UPLOAD_FOLDER,
            f"tmp_{uid}_{original_name}"
        )

        final_name = f"{uid}.mp4" if tipo == "video" else f"{uid}_{original_name}"
        final_path = os.path.join(AnuncioService.UPLOAD_FOLDER, final_name)

        file.save(temp_path)

        if os.path.getsize(temp_path) > AnuncioService.MAX_FILE_SIZE:
            os.remove(temp_path)
            return None, None, "Archivo demasiado grande"

        audio_rel_path = None

        try:
            if tipo == "video":
                audio_filename = f"{uid}.wav"
                audio_full_path = os.path.join(AnuncioService.AUDIO_FOLDER, audio_filename)
                
                video_ok, audio_ok = AnuncioService._process_video_parallel(
                    temp_path, final_path, audio_full_path
                )
                
                if not video_ok:
                    return None, None, "Error al procesar video"
                
                if audio_ok:
                    audio_rel_path = os.path.join("uploads", "audio", audio_filename)
                else:
                    print("⚠️ No se pudo extraer audio del video")
            else:
                shutil.move(temp_path, final_path)
        finally:
            with suppress(Exception):
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        if not os.path.exists(final_path):
            return None, None, "Error al generar archivo final"

        video_rel_path = os.path.join("uploads", "anuncios", final_name)
        return video_rel_path, audio_rel_path, None

    @staticmethod
    def create(archivo, titulo, tipo, duracion):
        ruta, audio, error = AnuncioService._save_file(archivo, tipo)
        if error:
            return None, error

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

            ruta, audio, error = AnuncioService._save_file(archivo, anuncio.tipo)
            if error:
                return None, error

            anuncio.enlace = ruta
            if anuncio.tipo == "video":
                anuncio.audio = audio

        if duracion is not None:
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
            path = os.path.join("app", "static", anuncio.enlace)
            with suppress(Exception):
                if os.path.exists(path):
                    os.remove(path)

        if anuncio.audio:
            path = os.path.join("app", "static", anuncio.audio)
            with suppress(Exception):
                if os.path.exists(path):
                    os.remove(path)

        db.session.delete(anuncio)
        db.session.commit()

        AudioService.mark_anuncios_dirty()
        return True