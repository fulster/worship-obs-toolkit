@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Preparation des cultes - serveur (laisser ouvert)
echo.
echo   Demarrage de l'interface de preparation des cultes...
echo   Le navigateur va s'ouvrir automatiquement dans quelques secondes.
echo   Laissez cette fenetre ouverte pendant l'utilisation ;
echo   fermez-la pour arreter le serveur.
echo.
rem  Ouvre le navigateur apres un court delai, en arriere-plan,
rem  pendant que le serveur demarre dans cette fenetre.
start "" /b cmd /c "timeout /t 4 /nobreak >nul & start http://127.0.0.1:5000"
uv run python webapp/app.py
echo.
echo   Serveur arrete. Vous pouvez fermer cette fenetre.
pause >nul
