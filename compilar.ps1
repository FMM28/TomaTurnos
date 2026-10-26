[CmdletBinding()]
param(
    # Sin parametro = compilacion completa.
    # Se puede indicar una o varias categorias: -Only Servicios,Licencias,Auth
    [ValidateSet("Inicializacion", "Servicios", "Licencias", "Rutas", "Auth", "Comandos")]
    [string[]]$Only
)

$ErrorActionPreference = "Stop"

# Ejecutar desde la raíz del proyecto.
$AppDir       = Join-Path $PSScriptRoot "app"
$ServicesDir  = Join-Path $AppDir "services"
$LicensingDir = Join-Path $AppDir "licensing"
$RoutesDir    = Join-Path $AppDir "routes"
$AuthDir      = Join-Path $AppDir "auth"
$CommandsDir  = Join-Path $AppDir "commands"
$BootstrapFile = Join-Path $AppDir "bootstrap.py"   # contenido real, se compila
$OutputDir    = Join-Path $PSScriptRoot "build"

# Sin parametro -> todas las categorias.
if (-not $Only -or $Only.Count -eq 0) {
    $Only = @("Inicializacion", "Servicios", "Licencias", "Rutas", "Auth", "Comandos")
}

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "No se encontró Python en PATH."
}

# Cada entrada: archivo a compilar + carpeta de salida.
$Jobs = @()

if ($Only -contains "Inicializacion") {
    foreach ($Required in @($BootstrapFile)) {
        if (-not (Test-Path $Required -PathType Leaf)) {
            throw "No se encontró el módulo requerido: $Required"
        }
    }
    # bootstrap se compila y va directamente en build/.
    $Jobs += [pscustomobject]@{
        Category = "Inicializacion"
        File     = Get-Item $BootstrapFile
        OutDir   = $OutputDir
    }
}

if ($Only -contains "Servicios") {
    if (-not (Test-Path $ServicesDir -PathType Container)) {
        throw "No existe el directorio: $ServicesDir"
    }
    # Todos los servicios de primer nivel, excepto audio_service.py.
    $Services = Get-ChildItem -Path $ServicesDir -Filter "*.py" -File |
        Where-Object { $_.BaseName -ne "audio_service" }

    foreach ($Svc in $Services) {
        $Jobs += [pscustomobject]@{
            Category = "Servicios"
            File     = $Svc
            OutDir   = Join-Path $OutputDir "services"
        }
    }
}

if ($Only -contains "Licencias") {
    if (-not (Test-Path $LicensingDir -PathType Container)) {
        throw "No existe el directorio: $LicensingDir"
    }
    # Módulos de licensing solicitados, excluyendo __init__.py.
    $LicensingFiles = @(
        "decorators.py",
        "licensing_client.py"
    )
    foreach ($FileName in $LicensingFiles) {
        $FilePath = Join-Path $LicensingDir $FileName
        if (-not (Test-Path $FilePath -PathType Leaf)) {
            throw "No se encontró el módulo requerido: $FilePath"
        }
        $Jobs += [pscustomobject]@{
            Category = "Licencias"
            File     = Get-Item $FilePath
            OutDir   = Join-Path $OutputDir "licensing"
        }
    }
}

if ($Only -contains "Rutas") {
    if (-not (Test-Path $RoutesDir -PathType Container)) {
        throw "No existe el directorio: $RoutesDir"
    }
    # Todos los archivos de rutas de primer nivel, excepto __init__.py
    $RouteFiles = Get-ChildItem -Path $RoutesDir -Filter "*.py" -File |
        Where-Object { $_.BaseName -ne "__init__" }

    foreach ($RouteFile in $RouteFiles) {
        $Jobs += [pscustomobject]@{
            Category = "Rutas"
            File     = $RouteFile
            OutDir   = Join-Path $OutputDir "routes"
        }
    }
}

if ($Only -contains "Auth") {
    if (-not (Test-Path $AuthDir -PathType Container)) {
        throw "No existe el directorio: $AuthDir"
    }
    # Módulos de auth solicitados, excluyendo __init__.py.
    $AuthFiles = @(
        "decorators.py",
        "login_manager.py"
    )
    foreach ($FileName in $AuthFiles) {
        $FilePath = Join-Path $AuthDir $FileName
        if (-not (Test-Path $FilePath -PathType Leaf)) {
            throw "No se encontró el módulo requerido: $FilePath"
        }
        $Jobs += [pscustomobject]@{
            Category = "Auth"
            File     = Get-Item $FilePath
            OutDir   = Join-Path $OutputDir "auth"
        }
    }
}

if ($Only -contains "Comandos") {
    if (-not (Test-Path $CommandsDir -PathType Container)) {
        throw "No existe el directorio: $CommandsDir"
    }
    # Módulos de commands solicitados, excluyendo __init__.py.
    $CommandFiles = @(
        "commands.py"
    )
    foreach ($FileName in $CommandFiles) {
        $FilePath = Join-Path $CommandsDir $FileName
        if (-not (Test-Path $FilePath -PathType Leaf)) {
            throw "No se encontró el módulo requerido: $FilePath"
        }
        $Jobs += [pscustomobject]@{
            Category = "Comandos"
            File     = Get-Item $FilePath
            OutDir   = Join-Path $OutputDir "commands"
        }
    }
}

if ($Jobs.Count -eq 0) {
    throw "No se encontraron módulos para compilar."
}

# Crear carpetas de salida necesarias.
$Jobs | ForEach-Object { $_.OutDir } | Sort-Object -Unique | ForEach-Object {
    New-Item -ItemType Directory -Path $_ -Force | Out-Null
}

Write-Host "Categorias: $($Only -join ', ')" -ForegroundColor Cyan
Write-Host "Modulos a compilar: $($Jobs.Count)" -ForegroundColor Cyan

$Failed = @()

foreach ($Job in $Jobs) {
    $Module = $Job.File
    Write-Host "`n[$($Job.Category)] Compilando: $($Module.FullName)" -ForegroundColor Cyan

    & python -m nuitka --module --msvc=latest --no-pyi-file --remove-output $Module.FullName "--output-dir=$($Job.OutDir)"

    if ($LASTEXITCODE -ne 0) {
        $Failed += $Module.FullName
        Write-Host "FALLO: $($Module.Name)" -ForegroundColor Red
    } else {
        Write-Host "Correcto: $($Module.Name) -> $($Job.OutDir)" -ForegroundColor Green
    }
}

Write-Host "`nCompilacion finalizada." -ForegroundColor Cyan
Write-Host "Salida: $OutputDir"

if ($Failed.Count -gt 0) {
    Write-Host "`nModulos que fallaron:" -ForegroundColor Red
    $Failed | ForEach-Object { Write-Host " - $_" -ForegroundColor Red }
    exit 1
}

Write-Host "Todos los modulos se compilaron correctamente." -ForegroundColor Green