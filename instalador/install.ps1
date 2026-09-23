# =========================================
#  INSTALADOR / ACTUALIZADOR SISTEMA TOMATURNOS
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
$FIREWALL_RULE_NAME = "Tomaturnos HTTP"

$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$PROJECT_SRC = Join-Path $SCRIPT_DIR "proyecto"
$NGINX_SRC = Join-Path $SCRIPT_DIR "nginx-1.28.2"
$NSSM_SRC = Join-Path $SCRIPT_DIR "nssm\nssm.exe"

$LOG_DIR = "$BASE_DIR\logs"

$PROJECT_REQUIREMENTS = Join-Path $PROJECT_SRC "requirements.txt"
$PROJECT_AUDIO_CLIENT = Join-Path $PROJECT_SRC "audio_client"
$PROJECT_KIOSCO_SCRIPT = Join-Path $PROJECT_SRC "LANZAR_KIOSCO.PS1"

$OLD_VENV = Join-Path $BASE_DIR "venv"
$VENV = Join-Path $BASE_DIR "venv\Scripts\python.exe"

$AUDIO_CLIENT_DIR = Join-Path $BASE_DIR "audio_client"
$AUDIO_CLIENT_VENV = Join-Path $AUDIO_CLIENT_DIR "venv"
$AUDIO_CLIENT_PYTHON = Join-Path $AUDIO_CLIENT_VENV "Scripts\python.exe"

$KIOSCO_SCRIPT = Join-Path $BASE_DIR "LANZAR_KIOSCO.PS1"

# ==========================
# DETECTAR INSTALACION
# ==========================

$IS_UPDATE = Test-Path $BASE_DIR

if ($IS_UPDATE) {
    Write-Host ""
    Write-Host "=====================================" -ForegroundColor Yellow
    Write-Host " INSTALACION EXISTENTE DETECTADA" -ForegroundColor Yellow
    Write-Host " MODO ACTUALIZACION" -ForegroundColor Yellow
    Write-Host "=====================================" -ForegroundColor Yellow
    Write-Host ""
}
else {
    Write-Host ""
    Write-Host "=====================================" -ForegroundColor Green
    Write-Host " INSTALACION NUEVA" -ForegroundColor Green
    Write-Host "=====================================" -ForegroundColor Green
    Write-Host ""
}

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

$PYTHON_VERSION = python --version
Write-Host "Python detectado: $PYTHON_VERSION"

# ==========================
# VALIDAR PROYECTO
# ==========================

Write-Host "== Verificando archivos del instalador =="

if (!(Test-Path $PROJECT_SRC)) {
    Write-Error "No se encontro la carpeta proyecto: $PROJECT_SRC"
    exit 1
}

if (!(Test-Path $PROJECT_REQUIREMENTS)) {
    Write-Error "No se encontro requirements.txt en el proyecto"
    exit 1
}

if (!(Test-Path $PROJECT_AUDIO_CLIENT)) {
    Write-Error "No se encontro la carpeta audio_client en el proyecto"
    exit 1
}

if (!(Test-Path $PROJECT_KIOSCO_SCRIPT)) {
    Write-Error "No se encontro LANZAR_KIOSCO.PS1 en el proyecto"
    exit 1
}

# ==========================
# DETENER SERVICIOS
# ==========================

if ($IS_UPDATE) {

    Write-Host ""
    Write-Host "== Deteniendo servicios para actualizar =="

    $serviceAppExists = Get-Service $SERVICE_APP -ErrorAction SilentlyContinue
    $serviceNginxExists = Get-Service $SERVICE_NGINX -ErrorAction SilentlyContinue

    if ($serviceAppExists) {
        Write-Host "Deteniendo $SERVICE_APP..."

        if ($serviceAppExists.Status -ne "Stopped") {
            Stop-Service $SERVICE_APP -Force
        }

        $serviceAppExists.WaitForStatus(
            [System.ServiceProcess.ServiceControllerStatus]::Stopped,
            [TimeSpan]::FromSeconds(30)
        )
    }

    if ($serviceNginxExists) {
        Write-Host "Deteniendo $SERVICE_NGINX..."

        if ($serviceNginxExists.Status -ne "Stopped") {
            Stop-Service $SERVICE_NGINX -Force
        }

        $serviceNginxExists.WaitForStatus(
            [System.ServiceProcess.ServiceControllerStatus]::Stopped,
            [TimeSpan]::FromSeconds(30)
        )
    }

    Start-Sleep -Seconds 2
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

# ==========================
# ROOT
# ==========================

Write-Host ""
Write-Host "== Credenciales ROOT =="

$ROOT_USER = Read-Host "Usuario root (default root)"
if (!$ROOT_USER) { $ROOT_USER = "root" }

$ROOT_PASS_SEC = Read-Host "Password root" -AsSecureString
$ROOT_PASS = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($ROOT_PASS_SEC)
)

$env:MYSQL_PWD = $ROOT_PASS

& mysql -u $ROOT_USER -h $DB_HOST -P $DB_PORT -e "SELECT 1;" 2>$null

if ($LASTEXITCODE -ne 0) {
    Remove-Item Env:\MYSQL_PWD -ErrorAction SilentlyContinue
    Write-Error "No se pudo conectar a MariaDB"
    exit 1
}

# ==========================
# USUARIO APP
# ==========================

Write-Host ""
Write-Host "== Usuario Base de Datos APP =="

if ($IS_UPDATE -and (Test-Path "$BASE_DIR\.env")) {

    Write-Host "Instalacion existente detectada."

    $existingEnv = Get-Content "$BASE_DIR\.env" -ErrorAction SilentlyContinue

    $existingDBUser = ($existingEnv |
        Where-Object { $_ -match "^DB_USER=" } |
        Select-Object -First 1) -replace "^DB_USER=", ""

    $existingDBHost = ($existingEnv |
        Where-Object { $_ -match "^DB_HOST=" } |
        Select-Object -First 1) -replace "^DB_HOST=", ""

    $existingDBPort = ($existingEnv |
        Where-Object { $_ -match "^DB_PORT=" } |
        Select-Object -First 1) -replace "^DB_PORT=", ""

    if ($existingDBUser) {
        $APP_DB_USER = $existingDBUser
        Write-Host "Usuario APP conservado: $APP_DB_USER"
    }
    else {
        $APP_DB_USER = Read-Host "Usuario (default tomaturnos)"
        if (!$APP_DB_USER) { $APP_DB_USER = "tomaturnos" }
    }

    if ($existingDBHost) {
        $DB_HOST = $existingDBHost
    }

    if ($existingDBPort) {
        $DB_PORT = $existingDBPort
    }

    Write-Host ""
    Write-Host "Por seguridad, se solicita nuevamente el password de la BD."

    $APP_DB_PASS_SEC = Read-Host "Password app" -AsSecureString
    $APP_DB_PASS = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [Runtime.InteropServices.Marshal]::SecureStringToBSTR($APP_DB_PASS_SEC)
    )
}
else {

    $APP_DB_USER = Read-Host "Usuario (default tomaturnos)"
    if (!$APP_DB_USER) { $APP_DB_USER = "tomaturnos" }

    $APP_DB_PASS_SEC = Read-Host "Password app" -AsSecureString
    $APP_DB_PASS = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [Runtime.InteropServices.Marshal]::SecureStringToBSTR($APP_DB_PASS_SEC)
    )
}

$sql = @"
CREATE DATABASE IF NOT EXISTS turnos
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS '$APP_DB_USER'@'localhost'
IDENTIFIED BY '$APP_DB_PASS';

ALTER USER '$APP_DB_USER'@'localhost'
IDENTIFIED BY '$APP_DB_PASS';

GRANT ALL PRIVILEGES ON turnos.* TO '$APP_DB_USER'@'localhost';

FLUSH PRIVILEGES;
"@

$sql | & mysql -u $ROOT_USER -h $DB_HOST -P $DB_PORT

if ($LASTEXITCODE -ne 0) {
    Remove-Item Env:\MYSQL_PWD -ErrorAction SilentlyContinue
    Write-Error "No se pudo crear/actualizar el usuario o la base de datos"
    exit 1
}

Remove-Item Env:\MYSQL_PWD -ErrorAction SilentlyContinue

# ==========================
# COPIAR / ACTUALIZAR PROYECTO
# ==========================

Write-Host ""
Write-Host "== Instalando archivos del proyecto =="

if ($IS_UPDATE) {

    Write-Host "Actualizando proyecto..."

    $APP_SRC = Join-Path $PROJECT_SRC "app"
    $APP_DST = Join-Path $BASE_DIR "app"

    if (Test-Path $APP_SRC) {

        New-Item -ItemType Directory -Force -Path $APP_DST | Out-Null

        Write-Host "Actualizando app..."

        Get-ChildItem $APP_SRC -File -Force | ForEach-Object {
            Copy-Item $_.FullName $APP_DST -Force
        }

        # services
        $SRC = Join-Path $APP_SRC "services"
        $DST = Join-Path $APP_DST "services"

        if (Test-Path $SRC) {
            Write-Host "Actualizando app\services..."

            if (Test-Path $DST) {
                Remove-Item $DST -Recurse -Force
            }

            Copy-Item $SRC $DST -Recurse -Force
        }

        # templates
        $SRC = Join-Path $APP_SRC "templates"
        $DST = Join-Path $APP_DST "templates"

        if (Test-Path $SRC) {
            Write-Host "Actualizando app\templates..."

            if (Test-Path $DST) {
                Remove-Item $DST -Recurse -Force
            }

            Copy-Item $SRC $DST -Recurse -Force
        }

        $SRC = Join-Path $APP_SRC "static"
        $DST = Join-Path $APP_DST "static"

        if (Test-Path $SRC) {

            Write-Host "Actualizando app\static..."

            New-Item -ItemType Directory -Force -Path $DST | Out-Null

            # Actualizar static excepto uploads
            Get-ChildItem $SRC -Force |
                Where-Object { $_.Name -ne "uploads" } |
                ForEach-Object {

                    $destination = Join-Path $DST $_.Name

                    if ($_.PSIsContainer -and (Test-Path $destination)) {
                        Remove-Item $destination -Recurse -Force
                    }

                    Copy-Item $_.FullName $DST -Recurse -Force
                }

            # Asegurar uploads
            $UPLOADS = Join-Path $DST "uploads"

            if (!(Test-Path $UPLOADS)) {
                New-Item -ItemType Directory -Force -Path $UPLOADS | Out-Null
            }
        }

        # Otros directorios de app
        Get-ChildItem $APP_SRC -Directory -Force |
            Where-Object {
                $_.Name -ne "backups" -and
                $_.Name -ne "static" -and
                $_.Name -ne "services" -and
                $_.Name -ne "templates"
            } |
            ForEach-Object {

                $destination = Join-Path $APP_DST $_.Name

                Write-Host "Actualizando app\$($_.Name)..."

                if (Test-Path $destination) {
                    Remove-Item $destination -Recurse -Force
                }

                Copy-Item $_.FullName $APP_DST -Recurse -Force
            }

        # Asegurar backups
        $BACKUPS = Join-Path $APP_DST "backups"

        if (!(Test-Path $BACKUPS)) {
            New-Item -ItemType Directory -Force -Path $BACKUPS | Out-Null
        }

        # Asegurar uploads
        $UPLOADS = Join-Path $APP_DST "static\uploads"

        if (!(Test-Path $UPLOADS)) {
            New-Item -ItemType Directory -Force -Path $UPLOADS | Out-Null
        }
    }

    Get-ChildItem $PROJECT_SRC -File -Force |
        Where-Object {
            $_.Name -ne ".env" -and
            $_.Name -ne "requirements.txt"
        } |
        ForEach-Object {
            Copy-Item $_.FullName $BASE_DIR -Force
        }

}
else {

    Write-Host "Copiando proyecto completo..."

    Copy-Item "$PROJECT_SRC\*" $BASE_DIR -Recurse -Force
}

# ==========================
# .ENV
# ==========================

Write-Host ""
Write-Host "== Configurando .env =="

$ENV_FILE = "$BASE_DIR\.env"

if ($IS_UPDATE -and (Test-Path $ENV_FILE)) {

    Write-Host ".env existente conservado."

    $envContent = Get-Content $ENV_FILE

    $newEnvContent = @()

    $foundDBUser = $false
    $foundDBPassword = $false
    $foundDBHost = $false
    $foundDBPort = $false
    $foundDBName = $false

    foreach ($line in $envContent) {

        if ($line -match "^DB_USER=") {
            $newEnvContent += "DB_USER=$APP_DB_USER"
            $foundDBUser = $true
        }
        elseif ($line -match "^DB_PASSWORD=") {
            $newEnvContent += "DB_PASSWORD=$APP_DB_PASS"
            $foundDBPassword = $true
        }
        elseif ($line -match "^DB_HOST=") {
            $newEnvContent += "DB_HOST=$DB_HOST"
            $foundDBHost = $true
        }
        elseif ($line -match "^DB_PORT=") {
            $newEnvContent += "DB_PORT=$DB_PORT"
            $foundDBPort = $true
        }
        elseif ($line -match "^DB_NAME=") {
            $newEnvContent += "DB_NAME=turnos"
            $foundDBName = $true
        }
        else {
            $newEnvContent += $line
        }
    }

    if (!$foundDBUser) {
        $newEnvContent += "DB_USER=$APP_DB_USER"
    }

    if (!$foundDBPassword) {
        $newEnvContent += "DB_PASSWORD=$APP_DB_PASS"
    }

    if (!$foundDBHost) {
        $newEnvContent += "DB_HOST=$DB_HOST"
    }

    if (!$foundDBPort) {
        $newEnvContent += "DB_PORT=$DB_PORT"
    }

    if (!$foundDBName) {
        $newEnvContent += "DB_NAME=turnos"
    }

    $newEnvContent | Set-Content $ENV_FILE
}
else {

    Write-Host "Creando .env..."

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
"@ | Set-Content $ENV_FILE
}

# ==========================
# REQUIREMENTS
# ==========================

Write-Host ""
Write-Host "== Actualizando requirements.txt =="

$OLD_REQUIREMENTS = Join-Path $BASE_DIR "requirements.txt"

if (Test-Path $OLD_REQUIREMENTS) {
    Remove-Item $OLD_REQUIREMENTS -Force
}

Copy-Item $PROJECT_REQUIREMENTS $OLD_REQUIREMENTS -Force

# ==========================
# VENV PRINCIPAL
# ==========================

Write-Host ""
Write-Host "== Actualizando entorno virtual principal =="

if (Test-Path $OLD_VENV) {
    Write-Host "Eliminando venv anterior..."
    Remove-Item $OLD_VENV -Recurse -Force
}

Write-Host "Creando nuevo entorno virtual..."

python -m venv $OLD_VENV

if (!(Test-Path $VENV)) {
    Write-Error "No se pudo crear el entorno virtual principal"
    exit 1
}

Write-Host "Actualizando pip, wheel y setuptools..."

& $VENV -m pip install --upgrade pip wheel setuptools

if ($LASTEXITCODE -ne 0) {
    Write-Error "No se pudieron actualizar las herramientas del entorno virtual"
    exit 1
}

Write-Host "Instalando dependencias..."

& $VENV -m pip install -r $OLD_REQUIREMENTS

if ($LASTEXITCODE -ne 0) {
    Write-Error "No se pudieron instalar las dependencias de Tomaturnos"
    exit 1
}

# ==========================
# AUDIO CLIENT
# ==========================

Write-Host ""
Write-Host "== Instalando audio_client =="

if (Test-Path $AUDIO_CLIENT_DIR) {
    Write-Host "Eliminando audio_client anterior..."
    Remove-Item $AUDIO_CLIENT_DIR -Recurse -Force
}

# Eliminar antiguo archivo audio_client si existiera
$OLD_AUDIO_FILE = Join-Path $BASE_DIR "audio_client.py"

if (Test-Path $OLD_AUDIO_FILE -PathType Leaf) {
    Write-Host "Eliminando antiguo archivo audio_client.py..."
    Remove-Item $OLD_AUDIO_FILE -Force
}

Copy-Item $PROJECT_AUDIO_CLIENT $BASE_DIR -Recurse -Force

if (!(Test-Path $AUDIO_CLIENT_DIR)) {
    Write-Error "No se pudo instalar la carpeta audio_client"
    exit 1
}

# requirements del cliente
$AUDIO_REQUIREMENTS = Join-Path $AUDIO_CLIENT_DIR "requirements.txt"

if (Test-Path $AUDIO_REQUIREMENTS) {

    Write-Host "Creando entorno virtual de audio_client..."

    python -m venv $AUDIO_CLIENT_VENV

    if (!(Test-Path $AUDIO_CLIENT_PYTHON)) {
        Write-Error "No se pudo crear el entorno virtual de audio_client"
        exit 1
    }

    Write-Host "Actualizando pip del audio_client..."

    & $AUDIO_CLIENT_PYTHON -m pip install --upgrade pip wheel setuptools

    if ($LASTEXITCODE -ne 0) {
        Write-Error "No se pudieron actualizar las herramientas del audio_client"
        exit 1
    }

    Write-Host "Instalando dependencias del audio_client..."

    & $AUDIO_CLIENT_PYTHON -m pip install -r $AUDIO_REQUIREMENTS

    if ($LASTEXITCODE -ne 0) {
        Write-Error "No se pudieron instalar las dependencias del audio_client"
        exit 1
    }
}
else {
    Write-Host "audio_client no contiene requirements.txt."
    Write-Host "No se instalaron dependencias adicionales."
}

# ==========================
# LANZAR KIOSCO
# ==========================

Write-Host ""
Write-Host "== Instalando lanzador del kiosco =="

if (!(Test-Path $KIOSCO_SCRIPT)) {
    Write-Error "No se encontro LANZAR_KIOSCO.PS1 en $BASE_DIR"
    exit 1
}

# ==========================
# CREAR ACCESO DIRECTO
# ==========================

Write-Host "Creando acceso directo..."

$DESKTOP = [Environment]::GetFolderPath("CommonDesktopDirectory")
$SHORTCUT_PATH = Join-Path $DESKTOP "Tomaturnos - Lanzar Kiosco.lnk"

$WScriptShell = New-Object -ComObject WScript.Shell
$Shortcut = $WScriptShell.CreateShortcut($SHORTCUT_PATH)

$Shortcut.TargetPath = "powershell.exe"
$Shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$KIOSCO_SCRIPT`""
$Shortcut.WorkingDirectory = $BASE_DIR
$Shortcut.Description = "Lanzar kiosco Tomaturnos"
$Shortcut.WindowStyle = 1

# Icono de PowerShell
$Shortcut.IconLocation = "powershell.exe,0"

$Shortcut.Save()

[System.Runtime.InteropServices.Marshal]::ReleaseComObject($WScriptShell) | Out-Null

Write-Host "Acceso directo creado:"
Write-Host $SHORTCUT_PATH

# ==========================
# MIGRACIONES
# ==========================

Write-Host ""
Write-Host "== Ejecutando migraciones =="

Push-Location $BASE_DIR

$env:FLASK_APP = "main.py"

& $VENV -m flask db upgrade

if ($LASTEXITCODE -ne 0) {
    Pop-Location
    Write-Error "Las migraciones fallaron"
    exit 1
}

Pop-Location

# ==========================
# ADMIN
# ==========================

Write-Host ""

if ($IS_UPDATE) {

    Write-Host "== Actualizacion: usuario administrador =="
    Write-Host "El usuario administrador existente se conserva."
    Write-Host "No es necesario volver a crearlo."

}
else {

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

    if ($LASTEXITCODE -ne 0) {
        Pop-Location
        Write-Error "No se pudo crear el usuario administrador"
        exit 1
    }

    Pop-Location
}

# ==========================
# SERVICIOS
# ==========================

Write-Host ""
Write-Host "== Configurando servicios =="

# --------------------------------------------------
# TOMATURNOS APP
# --------------------------------------------------

$existingAppService = Get-Service $SERVICE_APP -ErrorAction SilentlyContinue

if ($existingAppService) {

    Write-Host "Actualizando servicio $SERVICE_APP..."

    & $NSSM set $SERVICE_APP Application $VENV
    & $NSSM set $SERVICE_APP AppDirectory $BASE_DIR
    & $NSSM set $SERVICE_APP AppParameters "$BASE_DIR\main.py"

    & $NSSM set $SERVICE_APP Start SERVICE_AUTO_START

    & $NSSM set $SERVICE_APP AppStdout "$LOG_DIR\app.log"
    & $NSSM set $SERVICE_APP AppStderr "$LOG_DIR\app-error.log"

}
else {

    Write-Host "Instalando servicio $SERVICE_APP..."

    & $NSSM install $SERVICE_APP $VENV "$BASE_DIR\main.py"

    & $NSSM set $SERVICE_APP AppDirectory $BASE_DIR
    & $NSSM set $SERVICE_APP Start SERVICE_AUTO_START

    & $NSSM set $SERVICE_APP AppStdout "$LOG_DIR\app.log"
    & $NSSM set $SERVICE_APP AppStderr "$LOG_DIR\app-error.log"
}

# --------------------------------------------------
# NGINX
# --------------------------------------------------

$existingNginxService = Get-Service $SERVICE_NGINX -ErrorAction SilentlyContinue

if ($existingNginxService) {

    Write-Host "Actualizando servicio $SERVICE_NGINX..."

    & $NSSM set $SERVICE_NGINX Application "$NGINX_DIR\nginx.exe"
    & $NSSM set $SERVICE_NGINX AppDirectory $NGINX_DIR
    & $NSSM set $SERVICE_NGINX Start SERVICE_AUTO_START

    & $NSSM set $SERVICE_NGINX AppStdout "$LOG_DIR\nginx.log"
    & $NSSM set $SERVICE_NGINX AppStderr "$LOG_DIR\nginx-error.log"

}
else {

    Write-Host "Instalando servicio $SERVICE_NGINX..."

    & $NSSM install $SERVICE_NGINX "$NGINX_DIR\nginx.exe"

    & $NSSM set $SERVICE_NGINX AppDirectory $NGINX_DIR
    & $NSSM set $SERVICE_NGINX Start SERVICE_AUTO_START

    & $NSSM set $SERVICE_NGINX AppStdout "$LOG_DIR\nginx.log"
    & $NSSM set $SERVICE_NGINX AppStderr "$LOG_DIR\nginx-error.log"
}

# ==========================
# FIREWALL
# ==========================

Write-Host ""
Write-Host "== Configurando firewall =="

$existingFwRule = Get-NetFirewallRule -DisplayName $FIREWALL_RULE_NAME -ErrorAction SilentlyContinue

if (-not $existingFwRule) {

    Write-Host "Creando regla de firewall..."

    netsh advfirewall firewall add rule `
        name="$FIREWALL_RULE_NAME" `
        dir=in `
        action=allow `
        protocol=TCP `
        localport=80 | Out-Null
}
else {
    Write-Host "Regla de firewall ya existe, se omite."
}

# ==========================
# INICIAR SERVICIOS
# ==========================

Write-Host ""
Write-Host "== Iniciando servicios =="

Start-Service $SERVICE_APP
Start-Service $SERVICE_NGINX

Start-Sleep -Seconds 2

# ==========================
# VERIFICAR SERVICIOS
# ==========================

Write-Host ""
Write-Host "== Verificando servicios =="

$appStatus = (Get-Service $SERVICE_APP).Status
$nginxStatus = (Get-Service $SERVICE_NGINX).Status

Write-Host "$SERVICE_APP : $appStatus"
Write-Host "$SERVICE_NGINX : $nginxStatus"

# ==========================
# IP
# ==========================

$IP = (
    Get-NetIPAddress -AddressFamily IPv4 |
    Where-Object {
        $_.InterfaceAlias -notlike "*Loopback*" -and
        $_.IPAddress -notlike "169.254.*"
    } |
    Select-Object -First 1
).IPAddress

# ==========================
# FINAL
# ==========================

Write-Host ""

if ($IS_UPDATE) {

    Write-Host "=====================================" -ForegroundColor Green
    Write-Host " ACTUALIZACION COMPLETA" -ForegroundColor Green
    Write-Host "=====================================" -ForegroundColor Green

}
else {

    Write-Host "=====================================" -ForegroundColor Green
    Write-Host " INSTALACION COMPLETA" -ForegroundColor Green
    Write-Host "=====================================" -ForegroundColor Green
}

Write-Host ""
Write-Host " URL: http://$IP" -ForegroundColor Cyan
Write-Host ""
Write-Host "Tomaturnos Python:"
Write-Host " $VENV"
Write-Host ""
Write-Host "Audio Client:"
Write-Host " $AUDIO_CLIENT_DIR"
Write-Host " $AUDIO_CLIENT_PYTHON"
Write-Host ""
Write-Host "Lanzador kiosco:"
Write-Host " $KIOSCO_SCRIPT"
Write-Host ""
Write-Host "Acceso directo:"
Write-Host " $SHORTCUT_PATH"
Write-Host ""
Write-Host "Servicios:"
Write-Host " $SERVICE_APP : $appStatus"
Write-Host " $SERVICE_NGINX : $nginxStatus"
Write-Host ""
Write-Host "====================================="