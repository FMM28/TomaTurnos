[CmdletBinding()]
param(
    # Sin parametro = compilacion completa.
    # Se puede indicar una o varias categorias: -Only Servicios,Licencias
    [ValidateSet("Inicializacion", "Servicios", "Licencias")]
    [string[]]$Only
)

$ErrorActionPreference = "Stop"

# Ejecutar desde la raíz del proyecto.
$AppDir       = Join-Path $PSScriptRoot "app"
$ServicesDir  = Join-Path $AppDir "services"
$LicensingDir = Join-Path $AppDir "licensing"
$InitFile     = Join-Path $AppDir "__init__.py"
$OutputDir    = Join-Path $PSScriptRoot "build"

# Sin parametro -> las tres categorias.
if (-not $Only -or $Only.Count -eq 0) {
    $Only = @("Inicializacion", "Servicios", "Licencias")
}

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "No se encontró Python en PATH."
}

# Cada entrada: archivo a compilar + carpeta de salida.
$Jobs = @()

if ($Only -contains "Inicializacion") {
    if (-not (Test-Path $InitFile -PathType Leaf)) {
        throw "No se encontró el módulo requerido: $InitFile"
    }
    # __init__ va directamente en build/
    $Jobs += [pscustomobject]@{
        Category = "Inicializacion"
        File     = Get-Item $InitFile
        OutDir   = $OutputDir
        IsInit   = $true
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

    if ($Job.IsInit) {
        # Nuitka no acepta __init__.py suelto: se compila un paquete temporal
        # que contiene solo ese __init__.py, y luego se renombra el resultado.
        $PkgName = Split-Path $AppDir -Leaf
        $TempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("nuitka_init_" + [guid]::NewGuid().ToString("N"))
        $TempPkg = Join-Path $TempRoot $PkgName
        New-Item -ItemType Directory -Path $TempPkg -Force | Out-Null
        Copy-Item $Module.FullName (Join-Path $TempPkg "__init__.py")

        & python -m nuitka --module --msvc=latest --no-pyi-file --remove-output $TempPkg "--output-dir=$($Job.OutDir)"

        Remove-Item $TempRoot -Recurse -Force -ErrorAction SilentlyContinue

        if ($LASTEXITCODE -eq 0) {
            # app.cp311-win_amd64.pyd -> __init__.cp311-win_amd64.pyd
            $Built = Get-ChildItem -Path $Job.OutDir -Filter "$PkgName.*.pyd" -File |
                Sort-Object LastWriteTime -Descending | Select-Object -First 1
            if ($Built) {
                $NewName = "__init__" + $Built.Name.Substring($PkgName.Length)
                Move-Item $Built.FullName (Join-Path $Job.OutDir $NewName) -Force
                Write-Host "Renombrado: $($Built.Name) -> $NewName" -ForegroundColor DarkGray
            } else {
                Write-Host "Aviso: no se encontró el .pyd generado para renombrar." -ForegroundColor Yellow
            }
        }
    } else {
        & python -m nuitka --module --msvc=latest --no-pyi-file --remove-output $Module.FullName "--output-dir=$($Job.OutDir)"
    }

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