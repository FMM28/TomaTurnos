@echo off
echo =========================================
echo  Instalador Sistema Tomaturnos
echo =========================================
echo.

net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Ejecuta este archivo como ADMINISTRADOR
    pause
    exit /b
)

powershell -ExecutionPolicy Bypass -File "%~dp0install.ps1"

echo.
echo Instalacion finalizada.
pause
