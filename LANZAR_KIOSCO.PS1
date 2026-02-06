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

# Kiosco (pantalla touch)
Start-Process $CHROME `
    ($COMMON_FLAGS + @(
        "--app=$URL_KIOSCO"
        "--user-data-dir=$PROFILE_KIOSCO"
        "--window-position=$($kiosco.Bounds.X),$($kiosco.Bounds.Y)"
        "--window-size=$($kiosco.Bounds.Width),$($kiosco.Bounds.Height)"
    ))

# Anuncios (pantalla TV)
Start-Process $CHROME `
    ($COMMON_FLAGS + @(
        "--app=$URL_ANUNCIOS"
        "--user-data-dir=$PROFILE_ANUNCIOS"
        "--window-position=$($anuncios.Bounds.X),$($anuncios.Bounds.Y)"
        "--window-size=$($anuncios.Bounds.Width),$($anuncios.Bounds.Height)"
    ))
