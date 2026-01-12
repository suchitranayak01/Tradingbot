#!/bin/bash

# Algo Trading Bot Launcher
# This script starts the web dashboard

echo "🚀 Starting Algo Trading Bot Dashboard..."
echo ""

cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Please run:"
    echo "   python3 -m venv .venv"
    echo "   source .venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment and start Streamlit
source .venv/bin/activate

# Install dependencies if needed
echo "📦 Checking dependencies..."
pip install -q -r requirements.txt

echo ""
echo "✅ Starting web dashboard..."
echo "🌐 Dashboard will open in your browser at: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the dashboard"
echo ""

python3 -m streamlit run dashboard.py
