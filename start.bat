@echo off
cd /d "%~dp0"
python -m pip show flask >nul 2>&1
if errorlevel 1 (
  echo Flask n'est pas installe.
  echo Executer : python -m pip install flask
  pause
  exit /b 1
)
echo Demarrage du serveur de supervision...
start "Superviseur" python superviseur.py
echo Demarrage de l'interface web...
start "Serveur Flask" python appli.py
timeout /t 3 /nobreak >nul
start "" http://127.0.0.1:5000
exit /b 0
