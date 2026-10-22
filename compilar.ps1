$ErrorActionPreference = "Stop"

# Ejecutar desde la raíz del proyecto.
$ServicesDir = Join-Path $PSScriptRoot "app/services"
$LicensingDir = Join-Path $PSScriptRoot "app/licensing"
$OutputDir = Join-Path $PSScriptRoot "build"

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "No se encontró Python en PATH."
}

if (-not (Test-Path $ServicesDir -PathType Container)) {
    throw "No existe el directorio: $ServicesDir"
}

if (-not (Test-Path $LicensingDir -PathType Container)) {
    throw "No existe el directorio: $LicensingDir"
}

New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null

$Modules = @()

# Todos los servicios de primer nivel, excepto audio_service.py.
$Modules += Get-ChildItem -Path $ServicesDir -Filter "*.py" -File |
    Where-Object { $_.BaseName -ne "audio_service" }

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
    $Modules += Get-Item $FilePath
}

if ($Modules.Count -eq 0) {
    throw "No se encontraron módulos para compilar."
}

$Failed = @()

foreach ($Module in $Modules) {
    Write-Host "`nCompilando: $($Module.FullName)" -ForegroundColor Cyan

    & python -m nuitka --module --no-pyi-file $Module.FullName "--output-dir=$OutputDir"

    if ($LASTEXITCODE -ne 0) {
        $Failed += $Module.FullName
        Write-Host "FALLO: $($Module.Name)" -ForegroundColor Red
    } else {
        Write-Host "Correcto: $($Module.Name)" -ForegroundColor Green
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
