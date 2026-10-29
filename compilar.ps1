[CmdletBinding()]
param(
    # Sin parametro = compilacion/copia completa.
    # Se puede indicar una o varias categorias: -Only Servicios,Licencias,Auth
    [ValidateSet("Inicializacion", "Servicios", "Licencias", "Rutas", "Auth", "Comandos",
                 "Modelos", "Sockets", "Estaticos", "Plantillas")]
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
$ModelsDir    = Join-Path $AppDir "models"
$SocketsDir   = Join-Path $AppDir "sockets"
$StaticDir    = Join-Path $AppDir "static"
$TemplatesDir = Join-Path $AppDir "templates"
$BootstrapFile = Join-Path $AppDir "bootstrap.py"   # contenido real, se compila
$OutputDir    = Join-Path $PSScriptRoot "build"

$AllCategories = @("Inicializacion", "Servicios", "Licencias", "Rutas", "Auth", "Comandos",
                   "Modelos", "Sockets", "Estaticos", "Plantillas")

# Sin parametro -> todas las categorias.
if (-not $Only -or $Only.Count -eq 0) {
    $Only = $AllCategories
}

# Trabajos de compilacion con Nuitka: archivo a compilar + carpeta de salida.
$Jobs = @()

# Trabajos de copia (archivos que NO se compilan).
#   Type = "File": copia un archivo a la carpeta Dest.
#   Type = "Dir" : copia el contenido completo de Source a Dest (sin __pycache__).
$CopyJobs = @()

function Add-CopyFile {
    param([string]$Category, [string]$Source, [string]$Dest)
    if (-not (Test-Path $Source -PathType Leaf)) {
        throw "No se encontró el archivo a copiar: $Source"
    }
    $script:CopyJobs += [pscustomobject]@{
        Category = $Category; Type = "File"; Source = $Source; Dest = $Dest
    }
}

function Add-CopyDir {
    param([string]$Category, [string]$Source, [string]$Dest)
    if (-not (Test-Path $Source -PathType Container)) {
        throw "No existe el directorio a copiar: $Source"
    }
    $script:CopyJobs += [pscustomobject]@{
        Category = $Category; Type = "Dir"; Source = $Source; Dest = $Dest
    }
}

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
    # Archivos que se copian tal cual a build/ (bootstrap.py NO, ese se compila).
    foreach ($FileName in @("__init__.py", "config.py", "extensions.py")) {
        Add-CopyFile "Inicializacion" (Join-Path $AppDir $FileName) $OutputDir
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
    # audio_service.py no se compila, se copia.
    Add-CopyFile "Servicios" (Join-Path $ServicesDir "audio_service.py") (Join-Path $OutputDir "services")
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
    Add-CopyFile "Licencias" (Join-Path $LicensingDir "__init__.py") (Join-Path $OutputDir "licensing")
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
    Add-CopyFile "Rutas" (Join-Path $RoutesDir "__init__.py") (Join-Path $OutputDir "routes")
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
    Add-CopyFile "Comandos" (Join-Path $CommandsDir "__init__.py") (Join-Path $OutputDir "commands")
}

# --- Categorias que solo copian (sin compilar) ---

if ($Only -contains "Modelos") {
    Add-CopyDir "Modelos" $ModelsDir (Join-Path $OutputDir "models")
}

if ($Only -contains "Sockets") {
    Add-CopyDir "Sockets" $SocketsDir (Join-Path $OutputDir "sockets")
}

if ($Only -contains "Estaticos") {
    foreach ($Sub in @("css", "icons", "img", "js", "sounds")) {
        Add-CopyDir "Estaticos" (Join-Path $StaticDir $Sub) (Join-Path $OutputDir "static\$Sub")
    }
}

if ($Only -contains "Plantillas") {
    Add-CopyDir "Plantillas" $TemplatesDir (Join-Path $OutputDir "templates")
}

if ($Jobs.Count -eq 0 -and $CopyJobs.Count -eq 0) {
    throw "No se encontraron módulos para compilar ni archivos para copiar."
}

if ($Jobs.Count -gt 0 -and -not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "No se encontró Python en PATH."
}

# Crear carpetas de salida necesarias.
$Jobs | ForEach-Object { $_.OutDir } | Sort-Object -Unique | ForEach-Object {
    New-Item -ItemType Directory -Path $_ -Force | Out-Null
}

Write-Host "Categorias: $($Only -join ', ')" -ForegroundColor Cyan
Write-Host "Modulos a compilar: $($Jobs.Count)" -ForegroundColor Cyan
Write-Host "Elementos a copiar: $($CopyJobs.Count)" -ForegroundColor Cyan

$Failed = @()

# ---------------- Compilacion ----------------
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

# ---------------- Copia ----------------
foreach ($Copy in $CopyJobs) {
    try {
        if ($Copy.Type -eq "File") {
            New-Item -ItemType Directory -Path $Copy.Dest -Force | Out-Null
            Copy-Item -LiteralPath $Copy.Source -Destination $Copy.Dest -Force
            Write-Host "`n[$($Copy.Category)] Copiado: $($Copy.Source) -> $($Copy.Dest)" -ForegroundColor Green
        }
        else {
            $Root = (Get-Item -LiteralPath $Copy.Source).FullName.TrimEnd('\', '/')
            New-Item -ItemType Directory -Path $Copy.Dest -Force | Out-Null

            # Todo el contenido, excepto cualquier cosa dentro de __pycache__.
            $Files = Get-ChildItem -LiteralPath $Root -Recurse -File -Force |
                Where-Object { $_.FullName -notmatch '[\\/]__pycache__[\\/]' }

            $Count = 0
            foreach ($F in $Files) {
                $Relative = $F.FullName.Substring($Root.Length).TrimStart('\', '/')
                $Target   = Join-Path $Copy.Dest $Relative
                New-Item -ItemType Directory -Path (Split-Path $Target -Parent) -Force | Out-Null
                Copy-Item -LiteralPath $F.FullName -Destination $Target -Force
                $Count++
            }
            Write-Host "`n[$($Copy.Category)] Copiados $Count archivo(s): $($Copy.Source) -> $($Copy.Dest)" -ForegroundColor Green
        }
    }
    catch {
        $Failed += $Copy.Source
        Write-Host "FALLO al copiar: $($Copy.Source) ($($_.Exception.Message))" -ForegroundColor Red
    }
}

Write-Host "`nProceso finalizado." -ForegroundColor Cyan
Write-Host "Salida: $OutputDir"

if ($Failed.Count -gt 0) {
    Write-Host "`nElementos que fallaron:" -ForegroundColor Red
    $Failed | ForEach-Object { Write-Host " - $_" -ForegroundColor Red }
    exit 1
}

Write-Host "Todo se compiló y copió correctamente." -ForegroundColor Green