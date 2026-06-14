@echo off
chcp 65001 >nul
rem Arrete le serveur de l'interface (utile avant une mise a jour : ensuite
rem relancer "serveur.bat" ou rouvrir une session).
for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":5000 " ^| findstr LISTENING') do taskkill /PID %%P /F >nul 2>&1
echo Serveur arrete (s'il etait en cours).
timeout /t 2 /nobreak >nul
