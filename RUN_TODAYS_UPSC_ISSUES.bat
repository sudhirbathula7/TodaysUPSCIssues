@echo off
setlocal

cd /d "%~dp0"

echo ============================================================
echo TODAY'S UPSC ISSUES
echo VERSION 3.1 - ONE-CLICK DAILY PRODUCTION
echo ============================================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo ERROR: Python virtual environment was not found.
    echo Expected:
    echo %CD%\.venv\Scripts\python.exe
    echo.
    pause
    exit /b 1
)

if not exist "run_daily.py" (
    echo ERROR: run_daily.py was not found.
    echo Expected:
    echo %CD%\run_daily.py
    echo.
    pause
    exit /b 1
)

if not exist "input\DAILY_INPUT.json" (
    echo ERROR: Daily input file was not found.
    echo.
    echo Copy today's final ChatGPT JSON into:
    echo %CD%\input\DAILY_INPUT.json
    echo.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" "run_daily.py"

set "EXIT_CODE=%ERRORLEVEL%"

echo.
echo ============================================================

if "%EXIT_CODE%"=="0" (
    echo DAILY PRODUCTION COMPLETED SUCCESSFULLY
) else (
    echo DAILY PRODUCTION FAILED
    echo Exit code: %EXIT_CODE%
)

echo ============================================================
echo.
pause

exit /b %EXIT_CODE%
