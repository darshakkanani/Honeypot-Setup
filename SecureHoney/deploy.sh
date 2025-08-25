#!/bin/bash
"""
SecureHoney Complete System Deployment Script
Deploys both admin panel and honeypot system
"""

echo "🛡️ SecureHoney - Complete System Deployment"
echo "============================================"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "🔍 Checking prerequisites..."

if ! command_exists python3; then
    echo "❌ Python3 is required but not installed"
    exit 1
fi

if ! command_exists node; then
    echo "❌ Node.js is required but not installed"
    exit 1
fi

if ! command_exists npm; then
    echo "❌ npm is required but not installed"
    exit 1
fi

echo "✅ All prerequisites satisfied"

# Create shared logging directories
echo "📁 Creating shared directories..."
mkdir -p shared-utils/logging/{attacks,web-attacks,analysis,blockchain,system}

# Deploy Admin Panel
echo ""
echo "🎛️ Deploying Admin Panel..."
cd admin-panel

# Backend setup
echo "📦 Setting up backend..."
cd backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt
cd ..

# Frontend setup
echo "📦 Setting up frontend..."
cd frontend
if [ ! -d "node_modules" ]; then
    npm install
fi
cd ..

cd ..

# Deploy Honeypot System
echo ""
echo "🎯 Deploying Honeypot System..."
cd honeypot-system

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install asyncio pathlib numpy

cd ..

# Start services
echo ""
echo "🚀 Starting all services..."

# Start honeypot system
echo "🎯 Starting honeypot system..."
cd honeypot-system
./start.sh &
HONEYPOT_PID=$!
cd ..

# Wait a moment for honeypot to initialize
sleep 3

# Start admin panel
echo "🎛️ Starting admin panel..."
cd admin-panel
./start.sh &
ADMIN_PID=$!
cd ..

echo ""
echo "🎉 SecureHoney deployment complete!"
echo "=================================="
echo ""
echo "📊 Admin Panel:"
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:5001"
echo "   API Docs: http://localhost:5001/docs"
echo ""
echo "🎯 Honeypot System:"
echo "   Decoy Site: http://localhost:8080"
echo "   Engine: Listening on ports 22, 80, 443, 8080, 3389, 21, 23, 25"
echo ""
echo "🔐 Default Admin Login: admin / securehoney2024"
echo ""
echo "📝 Logs are stored in: shared-utils/logging/"
echo "⛓️ Blockchain data: shared-utils/logging/blockchain/"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
trap 'echo ""; echo "🛑 Stopping all SecureHoney services..."; kill $HONEYPOT_PID $ADMIN_PID 2>/dev/null; echo "✅ All services stopped"; exit' INT
wait
