import configparser
import io
import os
import socketio
import pygame
import threading
import time
import requests
import subprocess
import tempfile

config = configparser.ConfigParser()
if not config.read("config.ini"):
    raise FileNotFoundError(
        "No se encontró el archivo config.ini"
    )

HOST = config.get("SERVER", "HOST")
PORT = config.getint("SERVER", "PORT")
SERVER_URL = f"http://{HOST}:{PORT}"

sio = socketio.Client()

pygame.mixer.init()

# Canales independientes
AUDIO_CHANNEL = pygame.mixer.Channel(0)
TTS_CHANNEL = pygame.mixer.Channel(1)

BASE_VOLUME = 0.7
DUCK_VOLUME = 0.1

PIPER_MODEL = "voices/es_MX-claude-high.onnx"

sound_lock = threading.Lock()
tts_lock = threading.Lock()


def speak(texto):
    with tts_lock:
        temp_path = None

        try:
            # Reducir el volumen del audio que esté reproduciéndose
            with sound_lock:
                if AUDIO_CHANNEL.get_busy():
                    AUDIO_CHANNEL.set_volume(DUCK_VOLUME)

            # Crear archivo temporal para Piper
            with tempfile.NamedTemporaryFile(
                suffix=".wav",
                delete=False
            ) as temp_file:
                temp_path = temp_file.name

            # Generar voz con Piper
            subprocess.run(
                [
                    "piper",
                    "--model",
                    PIPER_MODEL,
                    "--output_file",
                    temp_path
                ],
                input=texto,
                text=True,
                check=True
            )

            # Cargar audio generado
            sound = pygame.mixer.Sound(temp_path)
            sound.set_volume(BASE_VOLUME)

            # Reproducir TTS en su propio canal
            TTS_CHANNEL.play(sound)

            # Esperar únicamente a que termine el TTS
            while TTS_CHANNEL.get_busy():
                time.sleep(0.05)

        except Exception as e:
            print(f"Error en TTS: {e}")

        finally:
            # Restaurar volumen del anuncio
            with sound_lock:
                AUDIO_CHANNEL.set_volume(BASE_VOLUME)

            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass


def play_audio(audio_bytes, duracion):
    try:
        sound = pygame.mixer.Sound(
            io.BytesIO(audio_bytes)
        )

        with sound_lock:
            # Detener el anuncio anterior
            if AUDIO_CHANNEL.get_busy():
                AUDIO_CHANNEL.stop()

            AUDIO_CHANNEL.set_volume(BASE_VOLUME)

            # Reproducir en el canal dedicado
            AUDIO_CHANNEL.play(sound)

        start = time.time()

        while (
            time.time() - start < duracion
            and AUDIO_CHANNEL.get_busy()
        ):
            time.sleep(0.05)

    except Exception as e:
        print(f"Error reproduciendo audio: {e}")


@sio.event
def connect():
    print(f"Conectado al servidor {SERVER_URL}")


@sio.event
def disconnect():
    print("Desconectado del servidor")


@sio.on("tts")
def on_tts(data):
    texto = data.get("texto")

    if not texto:
        return

    threading.Thread(
        target=speak,
        args=(texto,),
        daemon=True
    ).start()


@sio.on("anuncio_play")
def on_anuncio(data):
    audio = data.get("audio")
    duracion = data.get("duracion", 5)
    play_at = data.get("play_at")

    if not audio:
        return

    audio_url = f"{SERVER_URL}{audio}"

    try:
        response = requests.get(
            audio_url,
            timeout=10
        )

        response.raise_for_status()

        audio_bytes = response.content

        if play_at:
            delay = play_at - time.time()

            if delay > 0:
                time.sleep(delay)

        threading.Thread(
            target=play_audio,
            args=(audio_bytes, duracion),
            daemon=True
        ).start()

    except Exception as e:
        print(f"Error descargando audio: {e}")


def connect_loop():
    while True:
        try:
            print(f"Conectando a {SERVER_URL}...")

            sio.connect(
                SERVER_URL,
                transports=["websocket"]
            )

            break

        except Exception as e:
            print("Reintentando conexión...", e)
            time.sleep(2)


if __name__ == "__main__":
    connect_loop()
    sio.wait()