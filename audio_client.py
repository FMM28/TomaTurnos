import socketio
import pygame
import threading
import time
import os
import pythoncom
import win32com.client

sio = socketio.Client()

pygame.mixer.init()

BASE_VOLUME = 0.7
DUCK_VOLUME = 0.1

current_sound = None
sound_lock = threading.Lock()

def speak(texto):
    pythoncom.CoInitialize()
    try:
        speaker = win32com.client.Dispatch("SAPI.SpVoice")

        with sound_lock:
            if current_sound:
                current_sound.set_volume(DUCK_VOLUME)

        speaker.Speak(texto)

    finally:
        with sound_lock:
            if current_sound:
                current_sound.set_volume(BASE_VOLUME)

        pythoncom.CoUninitialize()

def play_audio(path, duracion):
    global current_sound

    try:
        if not os.path.exists(path):
            print("No existe:", path)
            return

        sound = pygame.mixer.Sound(path)

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
    print("Conectado al servidor")


@sio.on("tts")
def on_tts(data):
    texto = data.get("texto")

    threading.Thread(target=speak, args=(texto,), daemon=True).start()

@sio.on("anuncio_play")
def on_anuncio(data):
    audio = data.get("audio")
    duracion = data.get("duracion", 5)

    path = os.path.join("app", "static", audio)

    threading.Thread(
        target=play_audio,
        args=(path, duracion),
        daemon=True
    ).start()

def connect_loop():
    while True:
        try:
            sio.connect("http://localhost:5000", transports=["websocket"])
            break
        except Exception as e:
            print("Reintentando conexión...", e)
            time.sleep(2)


if __name__ == "__main__":
    connect_loop()
    sio.wait()