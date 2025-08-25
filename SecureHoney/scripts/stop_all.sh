#!/bin/bash
# SecureHoney - Stop All Services Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}🛑 Stopping SecureHoney Honeypot System${NC}"

# Function to stop service by PID file
stop_service() {
    local service_name=$1
    local pid_file=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            echo "Stopping $service_name (PID: $pid)..."
            kill $pid
            sleep 2
            if ps -p $pid > /dev/null 2>&1; then
                echo "Force killing $service_name..."
                kill -9 $pid
            fi
            echo -e "${GREEN}✅ $service_name stopped${NC}"
        else
            echo -e "${YELLOW}⚠️  $service_name was not running${NC}"
        fi
        rm -f "$pid_file"
    else
        echo -e "${YELLOW}⚠️  No PID file found for $service_name${NC}"
    fi
}

# Function to stop service by port
stop_service_by_port() {
    local service_name=$1
    local port=$2
    
    local pid=$(lsof -ti:$port 2>/dev/null || true)
    if [ -n "$pid" ]; then
        echo "Stopping $service_name on port $port (PID: $pid)..."
        kill $pid 2>/dev/null || true
        sleep 1
        # Force kill if still running
        local still_running=$(lsof -ti:$port 2>/dev/null || true)
        if [ -n "$still_running" ]; then
            kill -9 $still_running 2>/dev/null || true
        fi
        echo -e "${GREEN}✅ $service_name stopped${NC}"
    else
        echo -e "${YELLOW}⚠️  $service_name was not running on port $port${NC}"
    fi
}

# Stop services using PID files
echo -e "${YELLOW}🔍 Stopping services using PID files...${NC}"

stop_service "Honeypot Engine" "$PROJECT_ROOT/logs/honeypot.pid"
stop_service "Admin Backend" "$PROJECT_ROOT/logs/admin_backend.pid"
stop_service "Admin Frontend" "$PROJECT_ROOT/logs/admin_frontend.pid"

# Stop any remaining services by port (fallback)
echo -e "${YELLOW}🔍 Checking for remaining services on ports...${NC}"

stop_service_by_port "SSH Honeypot" 2222
stop_service_by_port "HTTP Honeypot" 8080
stop_service_by_port "FTP Honeypot" 2121
stop_service_by_port "Admin Backend" 5001
stop_service_by_port "Admin Frontend" 3000

# Clean up any Python processes that might be hanging
echo -e "${YELLOW}🧹 Cleaning up Python processes...${NC}"
pkill -f "honeypot" 2>/dev/null || true
pkill -f "admin-panel" 2>/dev/null || true

# Clean up Node.js processes
echo -e "${YELLOW}🧹 Cleaning up Node.js processes...${NC}"
pkill -f "serve.*build" 2>/dev/null || true

echo -e "${GREEN}✅ All SecureHoney services stopped${NC}"

# Show final status
echo -e "${BLUE}📊 Final port status:${NC}"
for port in 2222 8080 2121 5001 3000; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "  Port $port: ${RED}Still in use${NC}"
    else
        echo -e "  Port $port: ${GREEN}Available${NC}"
    fi
done
