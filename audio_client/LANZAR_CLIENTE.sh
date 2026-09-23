#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

CONFIG_FILE="$SCRIPT_DIR/config.ini"
VENV_DIR="$SCRIPT_DIR/venv"
AUDIO_CLIENT="$SCRIPT_DIR/audio_client.py"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "ERROR: No se encontró config.ini"
    exit 1
fi

if [ ! -f "$AUDIO_CLIENT" ]; then
    echo "ERROR: No se encontró audio_client.py"
    exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "ERROR: No se encontró el entorno virtual: $VENV_DIR"
    exit 1
fi

HOST=$(awk -F '=' '/^\[SERVER\]/{server=1; next} /^\[/{server=0} server && /^[[:space:]]*HOST[[:space:]]*=/{gsub(/[[:space:]]/, "", $2); print $2}' "$CONFIG_FILE")
PORT=$(awk -F '=' '/^\[SERVER\]/{server=1; next} /^\[/{server=0} server && /^[[:space:]]*PORT[[:space:]]*=/{gsub(/[[:space:]]/, "", $2); print $2}' "$CONFIG_FILE")

if [ -z "$HOST" ]; then
    echo "ERROR: No se encontró SERVER.HOST en config.ini"
    exit 1
fi

if [ -z "$PORT" ]; then
    echo "ERROR: No se encontró SERVER.PORT en config.ini"
    exit 1
fi

ANNOUNCEMENTS_URL="http://${HOST}:${PORT}/anuncios"

echo "Servidor: $HOST:$PORT"
echo "Vista de anuncios: $ANNOUNCEMENTS_URL"

# Esperar a que exista conexión de red
echo "Esperando conexión de red..."

until ping -c 1 -W 1 "$HOST" >/dev/null 2>&1; do
    sleep 2
done

echo "Servidor disponible."

# Cerrar posibles instancias anteriores de Chromium
pkill -f "chromium.*${ANNOUNCEMENTS_URL}" 2>/dev/null || true

# Lanzar vista de anuncios
chromium \
    --kiosk \
    --noerrdialogs \
    --disable-infobars \
    --disable-session-crashed-bubble \
    --disable-features=Translate \
    --autoplay-policy=no-user-gesture-required \
    "$ANNOUNCEMENTS_URL" &

CHROMIUM_PID=$!

echo "Chromium iniciado (PID: $CHROMIUM_PID)"

# Activar entorno virtual
source "$VENV_DIR/bin/activate"

echo "Iniciando cliente de audio..."

python "$AUDIO_CLIENT" &
AUDIO_PID=$!

echo "Audio client iniciado (PID: $AUDIO_PID)"

# Esperar ambos procesos
wait "$CHROMIUM_PID" "$AUDIO_PID"