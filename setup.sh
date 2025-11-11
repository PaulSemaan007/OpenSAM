#!/bin/bash
# OpenSAM Setup Script for Mac/Linux
# Powered by AppForge Labs

echo ""
echo "================================"
echo "OpenSAM Setup (Mac/Linux)"
echo "Powered by AppForge Labs"
echo "================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null
then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.12+ from https://www.python.org/downloads/"
    echo "Or use your package manager (brew, apt, yum, etc.)"
    exit 1
fi

echo "[1/4] Python detected"
python3 --version

echo ""
echo "[2/4] Creating virtual environment..."
python3 -m venv .venv
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to create virtual environment"
    exit 1
fi

echo ""
echo "[3/4] Activating virtual environment..."
source .venv/bin/activate

echo ""
echo "[4/4] Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi

echo ""
echo "================================"
echo "Setup Complete!"
echo "================================"
echo ""
echo "To run OpenSAM:"
echo "  1. source .venv/bin/activate"
echo "  2. streamlit run app.py"
echo ""
echo "Need help? Email: paulsemaan007@gmail.com"
echo ""
