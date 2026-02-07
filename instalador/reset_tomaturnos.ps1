# =========================================
#  RESET / LIMPIEZA TOMATURNOS (ROBUSTO)
# =========================================

$ErrorActionPreference = "Continue"

$BASE_DIR  = "C:\apps\tomaturnos"
$NGINX_DIR = "C:\nginx"

Write-Host ""
Write-Host "======================================="
Write-Host "  RESET SISTEMA TOMATURNOS"
Write-Host "  LIMPIEZA COMPLETA"
Write-Host "======================================="
Write-Host ""

# ==========================
# DETENER PROCESOS
# ==========================

Write-Host "Deteniendo procesos Flask / Python..."

Get-Process python -ErrorAction SilentlyContinue |
    Where-Object { $_.Path -like "*tomaturnos*" } |
    Stop-Process -Force -ErrorAction SilentlyContinue

Write-Host "Deteniendo procesos Nginx (forzado)..."

taskkill /F /IM nginx.exe /T 2>$null | Out-Null

Start-Sleep -Seconds 2

# ==========================
# ELIMINAR FIREWALL
# ==========================

Write-Host "Eliminando regla de firewall..."

netsh advfirewall firewall delete rule name="Tomaturnos HTTP" | Out-Null

# ==========================
# TOMAR CONTROL DE CARPETAS
# ==========================

function Take-Ownership($path) {
    if (Test-Path $path) {
        Write-Host "Tomando control de $path..."
        takeown /F $path /R /D Y | Out-Null
        icacls $path /grant Administrators:F /T | Out-Null
    }
}

Take-Ownership $BASE_DIR
Take-Ownership $NGINX_DIR

# ==========================
# ELIMINAR DIRECTORIOS (SEGURO)
# ==========================

function Remove-DirSafe($path) {
    if (-not (Test-Path $path)) { return }

    for ($i = 1; $i -le 5; $i++) {
        try {
            Remove-Item $path -Recurse -Force -ErrorAction Stop
            Write-Host "Eliminado $path"
            return
        }
        catch {
            Write-Host "Intento $i fallido eliminando $path, reintentando..."
            Start-Sleep -Seconds 2
        }
    }

    Write-Warning "No se pudo eliminar $path."
    Write-Warning "Reinicia Windows y vuelve a ejecutar este script."
}

Write-Host "Eliminando archivos del sistema..."

Remove-DirSafe $BASE_DIR
Remove-DirSafe $NGINX_DIR

# ==========================
# BORRAR BASE DE DATOS (OPCIONAL)
# ==========================

Write-Host ""
$confirmDB = Read-Host "¿Eliminar base de datos 'turnos'? (s/n)"

if ($confirmDB -eq "s") {

    $DB_USER = Read-Host "Usuario BD"
    $DB_PASSWORD = Read-Host "Password BD"
    $DB_HOST = Read-Host "Host BD (default localhost)"
    if ([string]::IsNullOrWhiteSpace($DB_HOST)) { $DB_HOST = "localhost" }

    $DB_PORT = Read-Host "Puerto BD (default 3306)"
    if ([string]::IsNullOrWhiteSpace($DB_PORT)) { $DB_PORT = "3306" }

    Write-Host "Eliminando base de datos..."

    & mysql -u $DB_USER -p$DB_PASSWORD -h $DB_HOST -P $DB_PORT `
        -e "DROP DATABASE IF EXISTS turnos;" 2>$null

    if ($LASTEXITCODE -eq 0) {
        Write-Host "Base de datos eliminada correctamente"
    }
    else {
        Write-Warning "No se pudo eliminar la base de datos"
    }
}

# ==========================
# LIMPIEZA FINAL
# ==========================

Write-Host ""
Write-Host "======================================="
Write-Host "  RESET COMPLETADO"
Write-Host "  Sistema listo para reinstalar"
Write-Host "======================================="
Write-Host ""
