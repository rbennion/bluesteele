#!/bin/bash

# Blue Steele Fantasy Analysis Launcher
echo "💙 Starting Blue Steele Fantasy Analysis Dashboard..."

# Check if virtual environment exists
if [ ! -d "fantasy_dashboard_env" ]; then
    echo "Creating virtual environment..."
    python3 -m venv fantasy_dashboard_env
    source fantasy_dashboard_env/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
else
    echo "Activating virtual environment..."
    source fantasy_dashboard_env/bin/activate
fi

# Check if database exists
if [ ! -f "fantasy_auction.db" ]; then
    echo "Database not found. Creating database from CSV data..."
    python3 create_fantasy_database.py
fi

# Launch dashboard
echo "🚀 Launching dashboard at http://localhost:8501"
echo "📱 Opening dashboard launcher page..."

# Open the launcher HTML page
if command -v open >/dev/null 2>&1; then
    open dashboard_launcher.html
elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open dashboard_launcher.html
fi

echo "Press Ctrl+C to stop the dashboard"
streamlit run fantasy_dashboard.py
