Add-Type -AssemblyName System.Windows.Forms

$screens = [System.Windows.Forms.Screen]::AllScreens

if ($screens.Count -lt 2) {
    Write-Error "Se requieren al menos 2 pantallas conectadas"
    exit 1
}

# Asignar pantallas
$kiosco = $screens | Where-Object { $_.Primary } | Select-Object -First 1
$anuncios = $screens | Where-Object { -not $_.Primary } | Select-Object -First 1

$URL_KIOSCO   = "http://localhost/kiosco"
$URL_ANUNCIOS = "http://localhost/anuncios"

$CHROME = "C:\Program Files\Google\Chrome\Application\chrome.exe"

# Directorio raíz de TomaTurnos
$BASE_DIR = $PSScriptRoot

# Cliente de audio
$AUDIO_DIR = Join-Path $BASE_DIR "audio_client"
$AUDIO_PYTHON = Join-Path $AUDIO_DIR ".venv\Scripts\python.exe"
$AUDIO_CLIENT = Join-Path $AUDIO_DIR "audio_client.py"

if (-not (Test-Path $AUDIO_PYTHON)) {
    Write-Error "No se encontró el Python del entorno virtual del cliente de audio: $AUDIO_PYTHON"
    exit 1
}

if (-not (Test-Path $AUDIO_CLIENT)) {
    Write-Error "No se encontró el cliente de audio: $AUDIO_CLIENT"
    exit 1
}

# Carpetas de perfil temporal
$BASE_PROFILE = "$env:LOCALAPPDATA\TomaturnosKiosco"
$PROFILE_KIOSCO = "$BASE_PROFILE\kiosco"
$PROFILE_ANUNCIOS = "$BASE_PROFILE\anuncios"

New-Item -ItemType Directory -Force -Path $PROFILE_KIOSCO | Out-Null
New-Item -ItemType Directory -Force -Path $PROFILE_ANUNCIOS | Out-Null

$COMMON_FLAGS = @(
    "--kiosk"
    "--no-first-run"
    "--disable-infobars"
    "--disable-session-crashed-bubble"
    "--disable-pinch"
    "--disable-features=TranslateUI"
    "--autoplay-policy=no-user-gesture-required"
    "--disable-backgrounding-occluded-windows"
    "--disable-renderer-backgrounding"
    "--disable-background-timer-throttling"
    "--disable-gpu"
    "--disable-software-rasterizer"
)

Start-Process $CHROME `
    ($COMMON_FLAGS + @(
        "--app=$URL_KIOSCO"
        "--user-data-dir=$PROFILE_KIOSCO"
        "--window-position=$($kiosco.Bounds.X),$($kiosco.Bounds.Y)"
        "--window-size=$($kiosco.Bounds.Width),$($kiosco.Bounds.Height)"
    ))

Start-Process $CHROME `
    ($COMMON_FLAGS + @(
        "--app=$URL_ANUNCIOS"
        "--user-data-dir=$PROFILE_ANUNCIOS"
        "--window-position=$($anuncios.Bounds.X),$($anuncios.Bounds.Y)"
        "--window-size=$($anuncios.Bounds.Width),$($anuncios.Bounds.Height)"
    ))

# Lanzar cliente de audio usando su entorno virtual
Start-Process `
    -FilePath $AUDIO_PYTHON `
    -ArgumentList "`"$AUDIO_CLIENT`"" `
    -WorkingDirectory $AUDIO_DIR