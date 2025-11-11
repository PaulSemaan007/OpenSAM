@echo off
REM OpenSAM Setup Script for Windows
REM Powered by AppForge Labs

echo.
echo ================================
echo OpenSAM Setup (Windows)
echo Powered by AppForge Labs
echo ================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.12+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo [1/4] Python detected
python --version

echo.
echo [2/4] Creating virtual environment...
python -m venv .venv
if %errorlevel% neq 0 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

echo.
echo [3/4] Activating virtual environment...
call .venv\Scripts\activate.bat

echo.
echo [4/4] Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo ================================
echo Setup Complete!
echo ================================
echo.
echo To run OpenSAM:
echo   1. run.bat
echo.
echo Or manually:
echo   1. .venv\Scripts\activate
echo   2. streamlit run app.py
echo.
echo Need help? Email: paulsemaan007@gmail.com
echo.
pause
