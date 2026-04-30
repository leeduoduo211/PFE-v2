@echo off
REM ===================================================================
REM PFE-v2 Windows launcher
REM Creates venv on first run, installs deps, then starts Streamlit UI.
REM ===================================================================

setlocal

REM Move into the directory where this .bat lives (project root)
cd /d "%~dp0"

REM ---- 1. Resolve Python --------------------------------------------
REM Prefer explicit overrides. Fall back to an existing .venv, then PATH python3.
set "PYTHONUTF8=1"
set "USE_EXISTING_ENV=0"
if not defined PFE_STREAMLIT_PORT set "PFE_STREAMLIT_PORT=8504"

if defined PFE_PYTHON (
    set "PY_EXE=%PFE_PYTHON%"
    set "USE_EXISTING_ENV=1"
) else if exist ".venv\Scripts\python.exe" (
    set "PY_EXE=.venv\Scripts\python.exe"
) else (
    set "PY_EXE=python3"
)

"%PY_EXE%" -X utf8 --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not available.
    echo Set PFE_PYTHON to a Python 3.9+ executable, or install Python and add it to PATH.
    pause
    exit /b 1
)

REM ---- 2. Create venv if needed -------------------------------------
if "%USE_EXISTING_ENV%"=="0" if not defined PFE_PYTHON if not exist ".venv\Scripts\python.exe" (
    echo [SETUP] Creating virtual environment in .venv ...
    "%PY_EXE%" -X utf8 -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

if "%USE_EXISTING_ENV%"=="0" if not defined PFE_PYTHON (
    REM ---- 3. Activate venv -----------------------------------------
    call ".venv\Scripts\activate.bat"
    set "PY_EXE=.venv\Scripts\python.exe"
)

REM ---- 4. Install dependencies on first run -------------------------
if "%USE_EXISTING_ENV%"=="0" if not exist ".venv\.pfe_installed" (
    echo [SETUP] Installing dependencies (this may take a few minutes) ...
    "%PY_EXE%" -X utf8 -m pip install --upgrade pip
    "%PY_EXE%" -X utf8 -m pip install -e ".[dev,ui,plot]"
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
echo The app will open in your browser at http://localhost:%PFE_STREAMLIT_PORT%
echo Press Ctrl+C in this window to stop the server.
echo.
"%PY_EXE%" -X utf8 -m streamlit run ui\app.py --server.port %PFE_STREAMLIT_PORT%

pause
endlocal
