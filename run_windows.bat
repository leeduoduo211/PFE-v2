@echo off
REM ===================================================================
REM PFE-v2 Windows launcher
REM Creates venv on first run, installs deps, then starts Streamlit UI.
REM ===================================================================

setlocal

REM Move into the directory where this .bat lives (project root)
cd /d "%~dp0"

REM ---- 1. Check Python ----------------------------------------------
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    echo and make sure "Add Python to PATH" is checked during install.
    pause
    exit /b 1
)

REM ---- 2. Create venv if missing ------------------------------------
if not exist ".venv\Scripts\python.exe" (
    echo [SETUP] Creating virtual environment in .venv ...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

REM ---- 3. Activate venv ---------------------------------------------
call ".venv\Scripts\activate.bat"

REM ---- 4. Install dependencies on first run -------------------------
if not exist ".venv\.pfe_installed" (
    echo [SETUP] Installing dependencies (this may take a few minutes) ...
    python -m pip install --upgrade pip
    pip install -e ".[dev,ui,plot]"
    if errorlevel 1 (
        echo [ERROR] Dependency installation failed.
        pause
        exit /b 1
    )
    echo. > ".venv\.pfe_installed"
    echo [SETUP] Installation complete.
)

REM ---- 5. Launch Streamlit ------------------------------------------
echo [RUN] Starting PFE-v2 UI ...
echo The app will open in your browser at http://localhost:8501
echo Press Ctrl+C in this window to stop the server.
echo.
python -m streamlit run ui\app.py

pause
endlocal
