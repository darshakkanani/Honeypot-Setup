#!/bin/bash
"""
SecureHoney Honeypot System Startup Script
Starts all honeypot components
"""

echo "🛡️ Starting SecureHoney Honeypot System"
echo "======================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is required but not installed"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install asyncio pathlib

# Start honeypot engine
echo "🎯 Starting honeypot engine..."
cd engine
python honeypot_core.py &
ENGINE_PID=$!
cd ..

# Start decoy website
echo "🌐 Starting decoy website..."
cd decoy-site
python web_server.py &
WEBSITE_PID=$!
cd ..

# Start AI analyzer
echo "🤖 Starting AI threat analyzer..."
cd ai-analyzer
python threat_analyzer.py &
AI_PID=$!
cd ..

# Start blockchain logger
echo "⛓️ Starting blockchain logger..."
cd blockchain
python chain_logger.py &
BLOCKCHAIN_PID=$!
cd ..

echo ""
echo "✅ SecureHoney Honeypot System started successfully!"
echo "🎯 Honeypot Engine: Listening on multiple ports"
echo "🌐 Decoy Website: http://localhost:8080"
echo "🤖 AI Analyzer: Running threat analysis"
echo "⛓️ Blockchain: Logging attacks immutably"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
trap 'echo "🛑 Stopping honeypot services..."; kill $ENGINE_PID $WEBSITE_PID $AI_PID $BLOCKCHAIN_PID; exit' INT
wait
