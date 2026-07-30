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

if not exist "src\distribution\distribution_runner.py" (
    echo ERROR: Distribution runner was not found.
    echo Expected:
    echo %CD%\src\distribution\distribution_runner.py
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

echo ============================================================
echo STAGE 1 - DAILY PDF PRODUCTION
echo ============================================================
echo.

".venv\Scripts\python.exe" "run_daily.py"

set "DAILY_EXIT_CODE=%ERRORLEVEL%"

if not "%DAILY_EXIT_CODE%"=="0" (
    echo.
    echo ============================================================
    echo DAILY PDF PRODUCTION FAILED
    echo Exit code: %DAILY_EXIT_CODE%
    echo Distribution was not started.
    echo ============================================================
    echo.
    pause
    exit /b %DAILY_EXIT_CODE%
)

echo.
echo ============================================================
echo STAGE 2 - DISTRIBUTION OUTPUT GENERATION
echo ============================================================
echo.

".venv\Scripts\python.exe" "src\distribution\distribution_runner.py"

set "DISTRIBUTION_EXIT_CODE=%ERRORLEVEL%"

if not "%DISTRIBUTION_EXIT_CODE%"=="0" (
    echo.
    echo ============================================================
    echo DISTRIBUTION GENERATION FAILED
    echo Exit code: %DISTRIBUTION_EXIT_CODE%
    echo ============================================================
    echo.
    pause
    exit /b %DISTRIBUTION_EXIT_CODE%
)

echo.
echo ============================================================
echo COMPLETE DAILY PRODUCTION SUCCESSFUL
echo ============================================================
echo.
echo Generated successfully:
echo - Daily PDF
echo - Repository outputs
echo - Intelligence outputs
echo - Telegram distribution outputs
echo - YouTube distribution outputs
echo - Website distribution outputs
echo.
pause

exit /b 0