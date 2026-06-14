@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo   Installation de l'interface de preparation des cultes sur ce poste
echo   ------------------------------------------------------------------
echo.

rem 1) Raccourci sur le Bureau qui ouvre l'interface dans le navigateur.
set "URL=%USERPROFILE%\Desktop\Preparer un culte.url"
> "%URL%" echo [InternetShortcut]
>> "%URL%" echo URL=http://127.0.0.1:5000
echo   [ok] Raccourci Bureau cree : "Preparer un culte"

rem 2) Demarrage automatique du serveur (cache) a chaque ouverture de session.
set "STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "VBS=%STARTUP%\worship-obs-serveur.vbs"
> "%VBS%" echo CreateObject("WScript.Shell").Run "cmd /c ""%CD%\serveur.bat""", 0, False
echo   [ok] Demarrage automatique du serveur active (fenetre cachee)

rem 3) S'assurer que les dependances sont installees, puis demarrer maintenant.
echo   ... preparation de l'environnement (uv sync)
call uv sync >nul 2>&1
wscript "%VBS%"
echo   [ok] Serveur demarre

echo.
echo   Termine.
echo   - Double-cliquez "Preparer un culte" sur le Bureau pour ouvrir l'interface.
echo   - Le serveur redemarrera tout seul a chaque ouverture de session.
echo.
pause
