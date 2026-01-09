from flask_socketio import emit, join_room
from flask_login import current_user
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

@socketio.on("user_connect")
def on_user_connect():
    if not current_user.is_authenticated:
        return False

    join_room(f"usuario_{current_user.id_usuario}")
    emit("connected", {"ok": True})