# =========================================
#  INSTALADOR SISTEMA TOMATURNOS 
# =========================================

$ErrorActionPreference = "Stop"

# ==========================
# VALIDAR ADMIN
# ==========================

$currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($currentUser)

if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "Este instalador debe ejecutarse como Administrador"
    exit 1
}

# ==========================
# CONFIGURACION GENERAL
# ==========================

$BASE_DIR = "C:\apps\tomaturnos"
$NGINX_DIR = "C:\nginx"
$NSSM_DIR = "C:\apps\nssm"

$SERVICE_APP = "tomaturnos-app"
$SERVICE_NGINX = "tomaturnos-nginx"

$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$PROJECT_SRC = Join-Path $SCRIPT_DIR "proyecto"
$NGINX_SRC = Join-Path $SCRIPT_DIR "nginx-1.28.2"
$NSSM_SRC = Join-Path $SCRIPT_DIR "nssm\nssm.exe"

$LOG_DIR = "$BASE_DIR\logs"

# ==========================
# CREAR DIRECTORIOS
# ==========================

Write-Host "== Creando estructura =="

New-Item -ItemType Directory -Force -Path $BASE_DIR | Out-Null
New-Item -ItemType Directory -Force -Path $NGINX_DIR | Out-Null
New-Item -ItemType Directory -Force -Path $NSSM_DIR | Out-Null
New-Item -ItemType Directory -Force -Path $LOG_DIR | Out-Null

# ==========================
# INSTALAR NSSM
# ==========================

Write-Host "== Instalando NSSM =="

if (!(Test-Path $NSSM_SRC)) {
    Write-Error "nssm.exe no encontrado en el instalador"
    exit 1
}

$NSSM = Join-Path $NSSM_DIR "nssm.exe"

Copy-Item $NSSM_SRC $NSSM -Force

# Agregar NSSM al PATH
$machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")

if ($machinePath -notlike "*$NSSM_DIR*") {

    Write-Host "Agregando NSSM al PATH..."

    [Environment]::SetEnvironmentVariable(
        "Path",
        "$machinePath;$NSSM_DIR",
        "Machine"
    )

    $env:Path += ";$NSSM_DIR"
}

Write-Host "NSSM instalado correctamente"

# ==========================
# VALIDAR PYTHON
# ==========================

Write-Host "== Verificando Python =="

if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python no esta instalado"
    exit 1
}

# ==========================
# VALIDAR MYSQL/MARIADB
# ==========================

Write-Host "== Verificando MariaDB/MySQL =="

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

    Write-Host "Agregando MariaDB al PATH..."

    [Environment]::SetEnvironmentVariable(
        "Path",
        "$machinePath;$mysqlPath",
        "Machine"
    )

    $env:Path += ";$mysqlPath"
}

# ==========================
# DATOS BD
# ==========================

Write-Host ""
Write-Host "== Configuracion Base de Datos =="

$DB_HOST = Read-Host "Host (default localhost)"
if (!$DB_HOST) { $DB_HOST = "localhost" }

$DB_PORT = Read-Host "Puerto (default 3306)"
if (!$DB_PORT) { $DB_PORT = "3306" }

# ROOT
Write-Host ""
Write-Host "== Credenciales ROOT =="

$ROOT_USER = Read-Host "Usuario root (default root)"
if (!$ROOT_USER) { $ROOT_USER = "root" }

$ROOT_PASS_SEC = Read-Host "Password root" -AsSecureString
$ROOT_PASS = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($ROOT_PASS_SEC)
)

& mysql -u $ROOT_USER -p$ROOT_PASS -h $DB_HOST -P $DB_PORT -e "SELECT 1;" 2>$null

if ($LASTEXITCODE -ne 0) {
    Write-Error "No se pudo conectar a MariaDB"
    exit 1
}

# ==========================
# USUARIO APP
# ==========================

Write-Host ""
Write-Host "== Usuario Base de Datos APP =="

$APP_DB_USER = Read-Host "Usuario (default tomaturnos)"
if (!$APP_DB_USER) { $APP_DB_USER = "tomaturnos" }

$APP_DB_PASS_SEC = Read-Host "Password app" -AsSecureString
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
$sql | Set-Content $tmp

Get-Content $tmp | mysql -u $ROOT_USER -p$ROOT_PASS -h $DB_HOST -P $DB_PORT

Remove-Item $tmp

# ==========================
# COPIAR ARCHIVOS
# ==========================

Write-Host "== Copiando archivos =="

Copy-Item "$PROJECT_SRC\*" $BASE_DIR -Recurse -Force
Copy-Item "$NGINX_SRC\*" $NGINX_DIR -Recurse -Force

# ==========================
# .ENV
# ==========================

Write-Host "== Creando .env =="

$SECRET = [guid]::NewGuid().ToString("N")

@"
FLASK_ENV=production
FLASK_DEBUG=0

DB_USER=$APP_DB_USER
DB_PASSWORD=$APP_DB_PASS
DB_HOST=$DB_HOST
DB_PORT=$DB_PORT
DB_NAME=turnos

SECRET_KEY=$SECRET

MAX_TURNOS=999
PRINT_MODE=usb
"@ | Set-Content "$BASE_DIR\.env"

# ==========================
# VENV
# ==========================

Write-Host "== Creando entorno virtual =="

python -m venv "$BASE_DIR\venv"

$VENV = "$BASE_DIR\venv\Scripts\python.exe"

& $VENV -m pip install --upgrade pip wheel setuptools
& $VENV -m pip install -r "$BASE_DIR\requirements.txt"

# ==========================
# MIGRACIONES
# ==========================

Write-Host "== Ejecutando migraciones =="

Push-Location $BASE_DIR

$env:FLASK_APP="main.py"

& $VENV -m flask db upgrade

Pop-Location

# ==========================
# ADMIN
# ==========================

Write-Host ""
Write-Host "== Crear usuario administrador =="

$ADMIN_USER = Read-Host "Username"
$ADMIN_PASS_SEC = Read-Host "Password" -AsSecureString
$ADMIN_PASS = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($ADMIN_PASS_SEC)
)

$ADMIN_NOMBRE = Read-Host "Nombre"
$ADMIN_AP = Read-Host "Apellido"

Push-Location $BASE_DIR

& $VENV create_admin.py $ADMIN_USER $ADMIN_PASS $ADMIN_NOMBRE $ADMIN_AP

Pop-Location

# ==========================
# SERVICIOS
# ==========================

Write-Host "== Instalando servicios =="

# APP
& $NSSM install $SERVICE_APP $VENV "$BASE_DIR\main.py"
& $NSSM set $SERVICE_APP AppDirectory $BASE_DIR
& $NSSM set $SERVICE_APP Start SERVICE_AUTO_START
& $NSSM set $SERVICE_APP AppStdout "$LOG_DIR\app.log"
& $NSSM set $SERVICE_APP AppStderr "$LOG_DIR\app-error.log"

# NGINX
& $NSSM install $SERVICE_NGINX "$NGINX_DIR\nginx.exe"
& $NSSM set $SERVICE_NGINX AppDirectory $NGINX_DIR
& $NSSM set $SERVICE_NGINX Start SERVICE_AUTO_START
& $NSSM set $SERVICE_NGINX AppStdout "$LOG_DIR\nginx.log"
& $NSSM set $SERVICE_NGINX AppStderr "$LOG_DIR\nginx-error.log"

# ==========================
# FIREWALL
# ==========================

Write-Host "== Configurando firewall =="

netsh advfirewall firewall add rule name="Tomaturnos HTTP" dir=in action=allow protocol=TCP localport=80 | Out-Null

# ==========================
# INICIAR SERVICIOS
# ==========================

Write-Host "== Iniciando servicios =="

Start-Service $SERVICE_APP
Start-Service $SERVICE_NGINX

# ==========================
# FINAL
# ==========================

$IP = (Get-NetIPAddress -AddressFamily IPv4 |
Where-Object { $_.InterfaceAlias -notlike "*Loopback*" } |
Select-Object -First 1).IPAddress

Write-Host ""
Write-Host "=====================================" -ForegroundColor Green
Write-Host " INSTALACION COMPLETA" -ForegroundColor Green
Write-Host " http://$IP" -ForegroundColor Cyan
Write-Host "====================================="
