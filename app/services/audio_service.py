import threading
import time
from contextlib import suppress
from app.extensions import socketio, db


class AudioService:
    _thread = None
    _running = False
    _app = None

    _anuncios_cache = []
    _dirty = True
    _lock = threading.Lock()

    @classmethod
    def start(cls, app):
        if cls._running:
            return

        cls._app = app
        cls._running = True

        cls._thread = threading.Thread(target=cls._loop, daemon=True)
        cls._thread.start()

    @classmethod
    def stop(cls):
        cls._running = False

    @classmethod
    def anunciar_turno(cls, turno, ventanilla):
        texto = f"Turno {turno}, pase a {ventanilla}"

        cls._emit_to_clients("tts", {
            "texto": texto
        })

    @classmethod
    def _loop(cls):
        try:
            cls._initialize()

            current_index = 0
            with cls._app.app_context():
                while cls._running:
                    current_index = cls._process_next_anuncio(current_index)

        except Exception as e:
            print(f"Error crítico en AudioService: {e}")

    @classmethod
    def _initialize(cls):
        with cls._app.app_context():
            cls._reload_anuncios()
            cls._dirty = False

        cls._wait_for_socketio_server()

    @classmethod
    def _wait_for_socketio_server(cls):
        print("Esperando SocketIO...")
        while not hasattr(socketio, 'server') or socketio.server is None:
            time.sleep(1)
        print("SocketIO listo")

    @classmethod
    def _process_next_anuncio(cls, current_index: int) -> int:
        if cls._dirty:
            cls._reload_anuncios()
            cls._dirty = False
            current_index = 0

        if not cls._anuncios_cache:
            time.sleep(2)
            return current_index

        # Verificar clientes conectados
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
            "audio": anuncio.audio
        }

        cls._emit_to_clients("anuncio_play", data)

        time.sleep(anuncio.duracion)

        return current_index + 1

    @classmethod
    def _reload_anuncios(cls):
        from app.models.anuncio import Anuncio

        with cls._lock:
            try:
                db.session.rollback()
                cls._anuncios_cache = list(
                    Anuncio.query.filter_by(activo=True)
                    .order_by(Anuncio.id_anuncio.desc())
                    .all()
                )
            except Exception:
                cls._anuncios_cache = []

    @classmethod
    def mark_anuncios_dirty(cls):
        with cls._lock:
            cls._dirty = True

    @classmethod
    def _emit_to_clients(cls, event_name, data):
        try:
            if hasattr(socketio, 'server') and socketio.server:
                socketio.server.emit(event_name, data, namespace='/')
                return True
        except Exception as e:
            print(f"Error socket ({event_name}): {e}")
        return False