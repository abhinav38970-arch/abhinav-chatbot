#!/bin/bash
# Dual startup script for Husky AI
# Launches both FastAPI backend and Streamlit frontend

echo "🚀 Starting Husky AI - Dual Service Launch"
echo "========================================"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3.12+"
    exit 1
fi

# Check if required packages are installed
check_package() {
    python3 -c "import $1" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "⚠️  Package $1 not found. Installing..."
        pip install $1
    fi
}

echo "🔍 Checking dependencies..."
check_package "uvicorn"
check_package "streamlit"
check_package "requests"

# Start FastAPI backend in background
echo "🐍 Starting FastAPI backend on port 8000..."
python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --workers 4 &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Check if backend started successfully
if ! curl -s http://localhost:8000/ &> /dev/null; then
    echo "❌ Backend failed to start. Check for errors."
    kill $BACKEND_PID
    exit 1
fi

echo "✅ Backend started successfully!"

# Start Streamlit frontend
echo "🎨 Starting Streamlit frontend..."
python3 -m streamlit run app.py --server.port 8501 --server.address 0.0.0.0

# Cleanup (this will run when Streamlit exits)
echo "🧹 Cleaning up..."
kill $BACKEND_PID

echo "👋 Husky AI shutdown complete!"
