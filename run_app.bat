@echo off
echo ========================================================
echo AI Ultimate Diagram Master - UI Launcher
echo ========================================================

REM Ensure we are running from the script's directory
cd /d "%~dp0"

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH.
    echo Please install Python 3.11+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check if venv exists, create if not
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate venv
call venv\Scripts\activate

REM Install dependencies if needed
REM We check for streamlit and dotenv to see if we need to install
python -c "import streamlit; import dotenv" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing dependencies...
    pip install -r requirements.txt
)

REM Run the Streamlit App
echo.
echo Starting AI Diagram Master UI...
echo The application will open in your default browser.
echo Press Ctrl+C to stop the server.
echo.
streamlit run app.py

pause
