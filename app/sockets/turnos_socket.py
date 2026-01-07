from flask_socketio import emit
from app.extensions import socketio
from app.services.turno_service import TurnoService

@socketio.on("connect")
def on_connect():
    print("Pantalla conectada")
    turnos = TurnoService.get_turnos_en_espera()
    emit("turnos_en_espera", turnos)

@socketio.on("disconnect")
def on_disconnect():
    print("Pantalla desconectada")
