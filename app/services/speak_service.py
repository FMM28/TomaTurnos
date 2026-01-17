import threading
from queue import Queue
import pythoncom
import win32com.client
import time


class AudioService:
    _queue = Queue()
    _thread = None
    _running = False
    
    VOICE_INDEX = 0
    RATE = 1
    VOLUME = 100

    @classmethod
    def start(cls):
        """Inicia el hilo de audio"""
        if cls._running:
            return

        cls._running = True
        cls._thread = threading.Thread(
            target=cls._audio_worker,
            daemon=True
        )
        cls._thread.start()

    @classmethod
    def stop(cls):
        cls._running = False
        cls._queue.put(None)

    @classmethod
    def enqueue(cls, texto: str):
        """Agrega un anuncio a la cola"""
        if not texto:
            return
        cls._queue.put(texto)

    @classmethod
    def anunciar_turno(cls, turno, ventanilla):
        texto = f"Turno {turno}, pase a {ventanilla}"
        cls.enqueue(texto)

    @classmethod
    def _audio_worker(cls):
        """Hilo dedicado a reproducir audio"""
        pythoncom.CoInitialize()

        try:
            speaker = win32com.client.Dispatch("SAPI.SpVoice")
            
            speaker.Voice = speaker.GetVoices().Item(cls.VOICE_INDEX)
            speaker.Rate = cls.RATE
            speaker.Volume = cls.VOLUME

            while cls._running:
                texto = cls._queue.get()

                if texto is None:
                    break

                try:
                    speaker.Speak(texto)
                except Exception as e:
                    print("Error en audio:", e)

                cls._queue.task_done()
                time.sleep(0.1)

        finally:
            pythoncom.CoUninitialize()
