@echo off
chcp 65001 >nul
cd /d "%~dp0"
rem Serveur de l'interface en mode production (waitress), sans ouvrir le
rem navigateur. Lance generalement de maniere CACHEE par le demarrage
rem automatique (cf. installer-poste-eglise.bat). Pour un lancement visible
rem avec navigateur, utiliser plutot "Preparer un culte.bat".
set WOTK_PROD=1
uv run python webapp/app.py
