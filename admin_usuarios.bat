@echo off
echo ========================================
echo     EZPOCKET-AI - Admin de Usuarios
echo ========================================
echo.

cd /d "%~dp0"

if exist "ezinho_assistente\Scripts\python.exe" (
    echo Usando Python do ambiente virtual...
    ezinho_assistente\Scripts\python.exe backend\admin.py
) else (
    echo Usando Python do sistema...
    python backend\admin.py
)

echo.
pause
