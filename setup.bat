@echo off
title OPENTRON – Setup
color 0F
chcp 65001 > nul

echo.
echo  ══════════════════════════════════════
echo   OPENTRON – Setup ^& Start
echo  ══════════════════════════════════════
echo.

:: ── Python prüfen ─────────────────────────────────────────
python --version > nul 2>&1
if errorlevel 1 (
    echo  [FEHLER] Python nicht gefunden!
    echo.
    echo  Bitte Python installieren:
    echo  https://www.python.org/downloads/
    echo.
    echo  Wichtig: Haken bei "Add Python to PATH" setzen!
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('python --version 2^>^&1') do set PY_VER=%%v
echo  [OK] %PY_VER% gefunden
echo.

:: ── pip prüfen ────────────────────────────────────────────
pip --version > nul 2>&1
if errorlevel 1 (
    echo  [FEHLER] pip nicht gefunden.
    echo  Bitte Python neu installieren.
    pause
    exit /b 1
)

:: ── websockets installieren ───────────────────────────────
echo  Installiere Abhaengigkeiten...
pip install websockets --quiet --disable-pip-version-check
if errorlevel 1 (
    echo.
    echo  [FEHLER] Installation fehlgeschlagen.
    echo  Versuche manuell: pip install websockets
    pause
    exit /b 1
)
echo  [OK] websockets installiert
echo.

:: ── Dateien prüfen ────────────────────────────────────────
if not exist "server.py" (
    echo  [FEHLER] server.py nicht gefunden!
    echo  Bitte alle Dateien in denselben Ordner legen:
    echo    server.py, game.py, http_server.py, index.html, game.js
    echo.
    pause
    exit /b 1
)
if not exist "game.py" (
    echo  [FEHLER] game.py nicht gefunden!
    pause
    exit /b 1
)
if not exist "http_server.py" (
    echo  [FEHLER] http_server.py nicht gefunden!
    pause
    exit /b 1
)
if not exist "index.html" (
    echo  [FEHLER] index.html nicht gefunden!
    pause
    exit /b 1
)
if not exist "game.js" (
    echo  [FEHLER] game.js nicht gefunden!
    pause
    exit /b 1
)

echo  [OK] Alle Dateien gefunden
echo.

:: ── Firewall-Regel (einmalig, braucht Admin) ──────────────
netsh advfirewall firewall show rule name="OpenTron" > nul 2>&1
if errorlevel 1 (
    echo  Firewall-Regel wird hinzugefuegt ^(einmalig^)...
    netsh advfirewall firewall add rule name="OpenTron" dir=in action=allow protocol=TCP localport=8080,8765 > nul 2>&1
    if errorlevel 1 (
        echo  [HINWEIS] Firewall-Regel konnte nicht gesetzt werden.
        echo  Bitte Port 8080 und 8765 manuell freigeben,
        echo  oder dieses Skript als Administrator starten.
        echo.
    ) else (
        echo  [OK] Firewall-Regel gesetzt
        echo.
    )
)

:: ── Server starten ────────────────────────────────────────
color 0A
echo  ══════════════════════════════════════
echo   Server startet...
echo   Dieses Fenster offen lassen!
echo   Beenden: Strg+C oder Fenster schliessen
echo  ══════════════════════════════════════
echo.
python server.py

:: Falls server.py abstuerzt
echo.
color 0C
echo  [!] Server wurde beendet.
pause