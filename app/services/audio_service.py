import threading
import time
import os
from queue import Queue
from contextlib import suppress
import pythoncom
import win32com.client
import pygame
from app.extensions import socketio, db


class AudioService:
    _thread = None
    _running = False
    _app = None

    _priority_queue = Queue()

    _anuncios_cache = []
    _dirty = True
    _lock = threading.Lock()

    _pending_delete = set()

    BASE_VOLUME = 0.9
    DUCK_VOLUME = 0.1
    
    VOICE_INDEX = 0
    RATE = 0
    TTS_VOLUME = 100

    _emit_callback = None

    _current_sound = None
    _sound_lock = threading.Lock()
    _tts_active = False

    @classmethod
    def start(cls, app):
        if cls._running:
            return

        cls._app = app
        cls._running = True

        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

        cls._thread = threading.Thread(target=cls._loop, daemon=True)
        cls._thread.start()

    @classmethod
    def stop(cls):
        cls._running = False
        cls._priority_queue.put(None)
        with cls._sound_lock:
            if cls._current_sound:
                cls._current_sound.stop()
        pygame.mixer.quit()

    @classmethod
    def anunciar_turno(cls, turno, ventanilla):
        texto = f"Turno {turno}, pase a {ventanilla}"
        
        # Lanzar TTS en hilo separado → no bloquea ni interrumpe anuncios
        threading.Thread(target=cls._speak_tts, args=(texto,), daemon=True).start()
        
    @classmethod
    def _speak_tts(cls, texto):
        pythoncom.CoInitialize()
        try:
            speaker = win32com.client.Dispatch("SAPI.SpVoice")

            voices = speaker.GetVoices()
            if cls.VOICE_INDEX < voices.Count:
                speaker.Voice = voices.Item(cls.VOICE_INDEX)

            speaker.Rate = cls.RATE
            speaker.Volume = cls.TTS_VOLUME

            with cls._sound_lock:
                if cls._current_sound:
                    cls._current_sound.set_volume(cls.DUCK_VOLUME)

            speaker.Speak(texto)

        except Exception as e:
            print(f"Error en TTS: {e}")

        finally:
            with cls._sound_lock:
                if cls._current_sound:
                    cls._current_sound.set_volume(cls.BASE_VOLUME)
                    
            pythoncom.CoUninitialize()

    @classmethod
    def mark_anuncios_dirty(cls):
        with cls._lock:
            cls._dirty = True

    @classmethod
    def mark_audio_for_delete(cls, audio_rel_path: str):
        if audio_rel_path:
            cls._pending_delete.add(audio_rel_path)

    @classmethod
    def _emit_to_clients(cls, event_name, data):
        try:
            if hasattr(socketio, 'server') and socketio.server:
                socketio.server.emit(event_name, data, namespace='/')
                return True
            else:
                print("SocketIO server no disponible. No se emitió evento.")
                return False
        except Exception as e:
            print(f"Error al emitir evento {event_name}: {e}")
            return False

    @classmethod
    def _loop(cls):
        pythoncom.CoInitialize()
        try:
            cls._initialize_audio_loop()

            current_index = 0
            with cls._app.app_context():
                while cls._running:
                    current_index = cls._process_next_anuncio(current_index)
                    cls._cleanup_audio_files()

        except Exception as e:
            print(f"Error crítico en el bucle de AudioService: {e}")
            with cls._sound_lock:
                if cls._current_sound:
                    cls._current_sound.stop()
                    cls._current_sound = None
            pygame.mixer.quit()
            pythoncom.CoUninitialize()

    @classmethod
    def _initialize_audio_loop(cls):
        speaker = win32com.client.Dispatch("SAPI.SpVoice")
        speaker.Volume = 100

        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

        with cls._app.app_context():
            cls._reload_anuncios()
            cls._dirty = False

        cls._wait_for_socketio_server()

    @classmethod
    def _wait_for_socketio_server(cls):
        print("Esperando servidor SocketIO...")
        while not hasattr(socketio, 'server') or socketio.server is None:
            time.sleep(1)
        print("Servidor SocketIO disponible")

    @classmethod
    def _process_next_anuncio(cls, current_index: int) -> int:
        if cls._dirty:
            cls._reload_anuncios()
            cls._dirty = False
            current_index = 0

        if not cls._anuncios_cache:
            time.sleep(2)
            return current_index

        num_clients = 0
        with suppress(Exception):
            rooms = socketio.server.manager.rooms.get('/', {})
            num_clients = len(rooms.keys())
        if num_clients == 0:
            time.sleep(2)
            return current_index

        if current_index >= len(cls._anuncios_cache):
            current_index = 0

        anuncio = cls._anuncios_cache[current_index]

        enlace = "/static/" + anuncio.enlace.replace("\\", "/")
        data = {
            "id": anuncio.id_anuncio,
            "tipo": anuncio.tipo,
            "enlace": enlace,
            "duracion": anuncio.duracion,
        }

        interrupted = False
        audio_path = None
        sound = None

        if anuncio.audio:
            audio_path = os.path.join("app", "static", anuncio.audio)
            if os.path.exists(audio_path):
                try:
                    sound = pygame.mixer.Sound(audio_path)
                except Exception as e:
                    print(f"Error cargando audio: {e}")
                    sound = None

        cls._emit_to_clients("anuncio_play", data)

        if sound:
            interrupted = cls._play_sound_preloaded(sound, anuncio.duracion)
        elif anuncio.audio:
            interrupted = cls._play_sound(anuncio.audio, anuncio.duracion)
        else:
            interrupted = cls._interruptible_sleep(anuncio.duracion)

        if interrupted:
            print(f"Anuncio [{current_index}] interrumpido. Se reintentará.")
        elif cls._dirty:
            print("Anuncios marcados como dirty durante reproducción. Reiniciando índice.")
        else:
            current_index += 1

        return current_index

    @classmethod
    def _play_sound_preloaded(cls, sound, duracion):
        """Reproduce un sonido ya cargado en memoria"""
        try:
            with cls._sound_lock:
                if cls._current_sound:
                    cls._current_sound.stop()
                cls._current_sound = sound
                sound.set_volume(cls.BASE_VOLUME)

            sound.play(loops=0)
            start = time.time()
            while time.time() - start < duracion:
                if not pygame.mixer.get_busy():
                    time.sleep(duracion - (time.time() - start))
                    break
                time.sleep(0.05)
            return False
        except Exception:
            time.sleep(duracion)
            return False
        finally:
            with cls._sound_lock:
                if cls._current_sound is sound:
                    cls._current_sound = None


    @classmethod
    def _interruptible_sleep(cls, seconds):
        time.sleep(seconds)
        return False

    @classmethod
    def _reload_anuncios(cls):
        from app.models.anuncio import Anuncio
        with cls._lock:
            try:
                db.session.rollback()
                all_anuncios = Anuncio.query.filter_by(activo=True).order_by(Anuncio.id_anuncio.desc()).all()
                cls._anuncios_cache = list(all_anuncios)
                ids = [a.id_anuncio for a in cls._anuncios_cache]
            except Exception as e:
                cls._anuncios_cache = []

    @classmethod
    def _cleanup_audio_files(cls):
        if not cls._pending_delete:
            return
        for audio in list(cls._pending_delete):
            path = os.path.join("app", "static", audio)
            try:
                if os.path.exists(path):
                    os.remove(path)
                cls._pending_delete.discard(audio)
            except Exception as e:
                print(f"No se pudo eliminar {path}: {e}")