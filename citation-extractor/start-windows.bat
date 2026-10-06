@echo off
REM One-step launcher for Windows. Double-click this file.
cd /d "%~dp0"
where py >nul 2>nul || (echo Python isn't installed. Get it from https://www.python.org/downloads/ and try again. & pause & exit /b 1)
if not exist .venv\Scripts\python.exe (
  echo First run: setting things up ^(this takes a minute^)...
  py -m venv .venv || (pause & exit /b 1)
)
.venv\Scripts\python -m pip install -q --disable-pip-version-check -r requirements.txt || (pause & exit /b 1)
.venv\Scripts\python -m pip install -q --disable-pip-version-check --no-deps eyecite==2.6.11 || (pause & exit /b 1)
.venv\Scripts\python app.py
pause
