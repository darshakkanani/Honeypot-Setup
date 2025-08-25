#!/bin/bash
"""
SecureHoney Admin Panel Startup Script
Starts both backend API and frontend React app
"""

echo "🛡️ Starting SecureHoney Admin Panel"
echo "=================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is required but not installed"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed"
    exit 1
fi

# Install backend dependencies
echo "📦 Installing backend dependencies..."
cd backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt

# Start backend in background
echo "🚀 Starting backend API server..."
python main.py &
BACKEND_PID=$!
cd ..

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd frontend
if [ ! -d "node_modules" ]; then
    npm install
fi

# Start frontend
echo "🌐 Starting frontend development server..."
npm start &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ SecureHoney Admin Panel started successfully!"
echo "🔗 Frontend: http://localhost:3000"
echo "🔗 Backend API: http://localhost:5001"
echo "📚 API Docs: http://localhost:5001/docs"
echo ""
echo "🔐 Default login: admin / securehoney2024"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
trap 'echo "🛑 Stopping services..."; kill $BACKEND_PID $FRONTEND_PID; exit' INT
wait
