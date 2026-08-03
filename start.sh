#!/bin/bash
# Startup script for standalone Streamlit app
# runs entirely locally without any backend server

echo "🚀 Starting Husky AI - Standalone Streamlit App"
echo "=============================================="

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
check_package "streamlit"
check_package "requests"

# Start Streamlit frontend
echo "🎨 Starting Streamlit frontend..."
echo "   Mode: Standalone (local execution only)"
echo "   Port: 8501"
echo "   URL: http://localhost:8501"

python3 -m streamlit run app.py --server.port 8501 --server.address 0.0.0.0

echo "👋 Husky AI shutdown complete!"
