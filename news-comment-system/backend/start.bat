@echo off
setlocal

REM 切到脚本所在目录
cd /d "%~dp0"

echo [Backend] Preparing Python virtual environment...

IF NOT EXIST "venv\Scripts\python.exe" (
    echo [Backend] Creating venv...
    python -m venv venv
    IF ERRORLEVEL 1 (
        echo [Backend] Failed to create venv. Please ensure Python is installed and in PATH.
        pause
        exit /b 1
    )
)

echo [Backend] Activating venv...
call "venv\Scripts\activate.bat"

echo [Backend] Installing/Checking dependencies...
python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt

echo [Backend] Starting Uvicorn on http://localhost:8000 ...
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

endlocal
