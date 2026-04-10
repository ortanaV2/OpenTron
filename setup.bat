@echo off
title OPENTRON – Setup
color 0F
chcp 65001 > nul

echo.
echo  ══════════════════════════════════════
echo   OPENTRON – Setup ^& Start
echo  ══════════════════════════════════════
echo.

:: ── Check Python ──────────────────────────────────────────
python --version > nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found!
    echo.
    echo  Please install Python:
    echo  https://www.python.org/downloads/
    echo.
    echo  Important: Check "Add Python to PATH" during installation!
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('python --version 2^>^&1') do set PY_VER=%%v
echo  [OK] %PY_VER% found
echo.

:: ── Check pip ─────────────────────────────────────────────
pip --version > nul 2>&1
if errorlevel 1 (
    echo  [ERROR] pip not found.
    echo  Please reinstall Python.
    pause
    exit /b 1
)

:: ── Install websockets ────────────────────────────────────
echo  Installing dependencies...
pip install websockets --quiet --disable-pip-version-check
if errorlevel 1 (
    echo.
    echo  [ERROR] Installation failed.
    echo  Try manually: pip install websockets
    pause
    exit /b 1
)
echo  [OK] websockets installed
echo.

:: ── Check files ───────────────────────────────────────────
if not exist "server.py" (
    echo  [ERROR] server.py not found!
    echo  Please place all files in the same folder:
    echo    server.py, game.py, http_server.py, index.html, game.js
    echo.
    pause
    exit /b 1
)
if not exist "game.py" (
    echo  [ERROR] game.py not found!
    pause
    exit /b 1
)
if not exist "http_server.py" (
    echo  [ERROR] http_server.py not found!
    pause
    exit /b 1
)
if not exist "index.html" (
    echo  [ERROR] index.html not found!
    pause
    exit /b 1
)
if not exist "game.js" (
    echo  [ERROR] game.js not found!
    pause
    exit /b 1
)

echo  [OK] All files found
echo.

:: ── Firewall rule (one-time, requires admin) ──────────────
netsh advfirewall firewall show rule name="OpenTron" > nul 2>&1
if errorlevel 1 (
    echo  Adding firewall rule ^(one-time^)...
    netsh advfirewall firewall add rule name="OpenTron" dir=in action=allow protocol=TCP localport=8080,8765 > nul 2>&1
    if errorlevel 1 (
        echo  [NOTICE] Firewall rule could not be set.
        echo  Please open ports 8080 and 8765 manually,
        echo  or run this script as Administrator.
        echo.
    ) else (
        echo  [OK] Firewall rule added
        echo.
    )
)

:: ── Start server ──────────────────────────────────────────
color 0A
echo  ══════════════════════════════════════
echo   Server starting...
echo   Keep this window open!
echo   To stop: Ctrl+C or close window
echo  ══════════════════════════════════════
echo.
python server.py

:: If server.py crashes
echo.
color 0C
echo  [!] Server stopped.
pause