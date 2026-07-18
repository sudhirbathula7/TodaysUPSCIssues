@echo off
cd /d "%~dp0"

call .venv\Scripts\activate.bat

python system\main.py

echo.
echo ============================================================
echo Production process finished.
echo ============================================================
pause