@echo off
chcp 65001 >nul
del "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\worship-obs-serveur.vbs" 2>nul
del "%USERPROFILE%\Desktop\Preparer un culte.url" 2>nul
echo Demarrage automatique et raccourci Bureau supprimes.
echo (Le serveur en cours continue jusqu'a la fermeture de session ;
echo  pour l'arreter tout de suite, lancez "arreter-serveur.bat".)
echo.
pause
