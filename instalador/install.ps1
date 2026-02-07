# =========================================
#  INSTALADOR SISTEMA TOMATURNOS (PROD)
# =========================================

$ErrorActionPreference = "Stop"

# ==========================
# CONFIGURACION GENERAL
# ==========================
$BASE_DIR = "C:\apps\tomaturnos"
$NGINX_DIR = "C:\nginx"
$SERVICE_APP = "tomaturnos-app"
$SERVICE_NGINX = "tomaturnos-nginx"

$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$PROJECT_SRC = Join-Path $SCRIPT_DIR "proyecto"
$NGINX_SRC = Join-Path $SCRIPT_DIR "nginx-1.28.2"
$NSSM = Join-Path $SCRIPT_DIR "nssm\nssm.exe"

# ==========================
# VALIDACIONES
# ==========================
Write-Host "== Verificando Python =="
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python no esta instalado"
    exit 1
}

Write-Host "== Verificando NSSM =="
if (!(Test-Path $NSSM)) {
    Write-Error "nssm.exe no encontrado"
    exit 1
}

New-Item -ItemType Directory -Force -Path $BASE_DIR | Out-Null

# ==========================
# MARIADB / MYSQL
# ==========================
$mysqlPath = $null
$possiblePaths = @(
    "C:\Program Files\MariaDB *\bin",
    "C:\Program Files\MySQL\MySQL Server *\bin"
)

foreach ($p in $possiblePaths) {
    Get-ChildItem $p -Directory -ErrorAction SilentlyContinue | ForEach-Object {
        if (Test-Path (Join-Path $_.FullName "mysql.exe")) {
            $mysqlPath = $_.FullName
        }
    }
}

if (-not $mysqlPath) {
    Write-Error "MariaDB/MySQL no encontrado"
    exit 1
}

$machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
if ($machinePath -notlike "*$mysqlPath*") {
    [Environment]::SetEnvironmentVariable("Path", "$machinePath;$mysqlPath", "Machine")
    Write-Host "MariaDB agregado al PATH. Reabre PowerShell y ejecuta de nuevo."
    exit 0
}

# ==========================
# DATOS BD
# ==========================
$DB_HOST = Read-Host "Host BD (default localhost)"
if ([string]::IsNullOrWhiteSpace($DB_HOST)) { $DB_HOST = "localhost" }

$DB_PORT = Read-Host "Puerto BD (default 3306)"
if ([string]::IsNullOrWhiteSpace($DB_PORT)) { $DB_PORT = "3306" }

# ==========================
# ROOT BD
# ==========================
Write-Host ""
Write-Host "== Credenciales ROOT MariaDB =="

$ROOT_USER = Read-Host "Usuario root (default root)"
if ([string]::IsNullOrWhiteSpace($ROOT_USER)) { $ROOT_USER = "root" }

$ROOT_PASS_SEC = Read-Host "Password root" -AsSecureString
$ROOT_PASS = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($ROOT_PASS_SEC)
)

Write-Host "Probando conexion root..."
& mysql -u $ROOT_USER -p$ROOT_PASS -h $DB_HOST -P $DB_PORT -e "SELECT 1;" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Error "No se pudo conectar como root"
    exit 1
}

# ==========================
# USUARIO APP
# ==========================
Write-Host ""
Write-Host "== Usuario BD aplicacion =="

$APP_DB_USER = Read-Host "Usuario BD (default tomaturnos)"
if ([string]::IsNullOrWhiteSpace($APP_DB_USER)) { $APP_DB_USER = "tomaturnos" }

$APP_DB_PASS_SEC = Read-Host "Password BD app" -AsSecureString
$APP_DB_PASS = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($APP_DB_PASS_SEC)
)

$sql = @"
CREATE DATABASE IF NOT EXISTS turnos
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS '$APP_DB_USER'@'localhost'
IDENTIFIED BY '$APP_DB_PASS';

GRANT ALL PRIVILEGES ON turnos.* TO '$APP_DB_USER'@'localhost';

FLUSH PRIVILEGES;
"@


$tmp = New-TemporaryFile
$sql | Set-Content $tmp -Encoding UTF8

Get-Content $tmp | & mysql -u $ROOT_USER -p$ROOT_PASS -h $DB_HOST -P $DB_PORT

Remove-Item $tmp -Force


if ($LASTEXITCODE -ne 0) {
    Write-Error "Error creando usuario o base de datos"
    exit 1
}

# ==========================
# COPIAR ARCHIVOS
# ==========================
Copy-Item "$PROJECT_SRC\*" $BASE_DIR -Recurse -Force
New-Item -ItemType Directory -Force -Path $NGINX_DIR | Out-Null
Copy-Item "$NGINX_SRC\*" $NGINX_DIR -Recurse -Force

# ==========================
# .ENV
# ==========================
$SECRET = [guid]::NewGuid().ToString("N")
@"
FLASK_ENV=production
FLASK_DEBUG=0

DB_USER=$APP_DB_USER
DB_PASSWORD=$APP_DB_PASS
DB_HOST=$DB_HOST
DB_PORT=$DB_PORT
DB_NAME=turnos

DB_POOL_SIZE=5
DB_MAX_OVERFLOW=5
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=1800

SECRET_KEY=$SECRET
MAX_TURNO=999
PRINT_MODE=usb
"@ | Set-Content "$BASE_DIR\.env" -Encoding UTF8

# ==========================
# VENV
# ==========================
python -m venv "$BASE_DIR\venv"
$VENV = "$BASE_DIR\venv\Scripts\python.exe"
& $VENV -m pip install --upgrade pip setuptools wheel
& $VENV -m pip install -r "$BASE_DIR\requirements.txt"

# ==========================
# MIGRACIONES
# ==========================
Push-Location $BASE_DIR
$env:FLASK_APP = "main.py"
& $VENV -m flask db upgrade
Pop-Location

# ==========================
# ADMIN
# ==========================
Write-Host ""
Write-Host "== Usuario administrador inicial =="

$ADMIN_USER = Read-Host "Username"
$ADMIN_PASS_SEC = Read-Host "Password" -AsSecureString
$ADMIN_PASS = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($ADMIN_PASS_SEC)
)
$ADMIN_NOMBRE = Read-Host "Nombre"
$ADMIN_AP = Read-Host "Apellido paterno"

Push-Location $BASE_DIR
& $VENV create_admin.py $ADMIN_USER $ADMIN_PASS $ADMIN_NOMBRE $ADMIN_AP
Pop-Location

# ==========================
# SERVICIOS
# ==========================
& $NSSM remove $SERVICE_APP confirm 2>$null
& $NSSM remove $SERVICE_NGINX confirm 2>$null

& $NSSM install $SERVICE_APP $VENV "$BASE_DIR\main.py"
& $NSSM set $SERVICE_APP AppDirectory $BASE_DIR
& $NSSM set $SERVICE_APP Start SERVICE_AUTO_START

& $NSSM install $SERVICE_NGINX "$NGINX_DIR\nginx.exe"
& $NSSM set $SERVICE_NGINX AppDirectory $NGINX_DIR
& $NSSM set $SERVICE_NGINX Start SERVICE_AUTO_START

# ==========================
# FIREWALL
# ==========================
netsh advfirewall firewall add rule name="Tomaturnos HTTP" dir=in action=allow protocol=TCP localport=80 | Out-Null

# ==========================
# ARRANQUE
# ==========================
Start-Service $SERVICE_APP
Start-Service $SERVICE_NGINX

# ==========================
# ACCESO DIRECTO KIOSCO
# ==========================
Write-Host "Creando acceso directo para modo kiosco..."

$KIOSCO_SCRIPT = "$BASE_DIR\LANZAR_KIOSCO.ps1"

if (Test-Path $KIOSCO_SCRIPT) {

    $DesktopPath = [Environment]::GetFolderPath("Desktop")
    $ShortcutPath = Join-Path $DesktopPath "Tomaturnos - Kiosco.lnk"

    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut($ShortcutPath)

    $Shortcut.TargetPath = "powershell.exe"
    $Shortcut.Arguments = "-ExecutionPolicy Bypass -WindowStyle Hidden -File `"$KIOSCO_SCRIPT`""
    $Shortcut.WorkingDirectory = $BASE_DIR
    $Shortcut.IconLocation = "powershell.exe,0"

    $Shortcut.Save()

    Write-Host "Acceso directo creado en el escritorio."
}
else {
    Write-Warning "LANZAR_KIOSCO.ps1 no encontrado en $BASE_DIR"
}

# ==========================
# FIN
# ==========================
$IP = (Get-NetIPAddress -AddressFamily IPv4 |
    Where-Object { $_.InterfaceAlias -notlike "*Loopback*" } |
    Select-Object -First 1).IPAddress

Write-Host ""
Write-Host "=====================================" -ForegroundColor Green
Write-Host " INSTALACION COMPLETA" -ForegroundColor Green
Write-Host " http://$IP" -ForegroundColor Cyan
Write-Host "====================================="
