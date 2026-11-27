@echo off
cd /d "%~dp0"
where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    py -3 -m pip install -r requirements.txt || goto :error
    py -3 main.py
) else (
    python -m pip install -r requirements.txt || goto :error
    python main.py
)
pause
exit /b 0
:error
echo Failed to install dependencies. Install Python 3.10+ and check your internet connection.
pause
exit /b 1
