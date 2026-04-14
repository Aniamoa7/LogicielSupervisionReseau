@echo off
cd /d "%~dp0"
python -m pip show flask >nul 2>&1
if errorlevel 1 (
  echo Flask n'est pas installe.
  echo Executer : python -m pip install flask
  pause
  exit /b 1
)
echo Demarrage de l'interface web de supervision...
python appli.py
pause
