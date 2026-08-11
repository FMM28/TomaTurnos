import configparser
import io
import socketio
import pygame
import threading
import time
import requests
import pyttsx3

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

BASE_VOLUME = 0.7
DUCK_VOLUME = 0.1

current_sound = None
sound_lock = threading.Lock()
tts_lock = threading.Lock()


def speak(texto):

    with tts_lock:
        with sound_lock:
            if current_sound:
                current_sound.set_volume(DUCK_VOLUME)
        try:
            engine = pyttsx3.init()
            engine.say(texto)
            engine.runAndWait()
            engine.stop()
        finally:
            with sound_lock:
                if current_sound:
                    current_sound.set_volume(BASE_VOLUME)


def play_audio(audio_bytes, duracion):
    global current_sound
    sound = None
    try:
        sound = pygame.mixer.Sound(io.BytesIO(audio_bytes))
        with sound_lock:
            if current_sound:
                current_sound.stop()
            current_sound = sound
            sound.set_volume(BASE_VOLUME)
        sound.play()
        start = time.time()
        while time.time() - start < duracion and pygame.mixer.get_busy():
            time.sleep(0.05)
    finally:
        with sound_lock:
            if current_sound is sound:
                current_sound = None


@sio.event
def connect():
    print(f"Conectado al servidor {SERVER_URL}")


@sio.event
def disconnect():
    print("Desconectado del servidor")


@sio.on("tts")
def on_tts(data):
    texto = data.get("texto")
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
        response = requests.get(audio_url, timeout=10)
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