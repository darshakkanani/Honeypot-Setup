#!/bin/bash
# SecureHoney - Start All Services Script

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

echo -e "${BLUE}🚀 Starting SecureHoney Honeypot System${NC}"
echo "Project root: $PROJECT_ROOT"

# Function to check if port is available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${RED}❌ Port $port is already in use${NC}"
        return 1
    fi
    return 0
}

# Function to wait for service to start
wait_for_service() {
    local port=$1
    local service_name=$2
    local max_attempts=30
    local attempt=0
    
    echo -n "Waiting for $service_name to start on port $port..."
    while [ $attempt -lt $max_attempts ]; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            echo -e " ${GREEN}✅ Started${NC}"
            return 0
        fi
        sleep 1
        echo -n "."
        ((attempt++))
    done
    echo -e " ${RED}❌ Failed to start${NC}"
    return 1
}

# Check prerequisites
echo -e "${YELLOW}📋 Checking prerequisites...${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js is not installed${NC}"
    exit 1
fi

# Check PostgreSQL
if ! command -v psql &> /dev/null; then
    echo -e "${RED}❌ PostgreSQL client is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites check passed${NC}"

# Check required ports
echo -e "${YELLOW}🔍 Checking ports...${NC}"
REQUIRED_PORTS=(5432 5001 3000 2222 8080 2121)
for port in "${REQUIRED_PORTS[@]}"; do
    if [ "$port" != "5432" ]; then  # Skip PostgreSQL port check
        if ! check_port $port; then
            echo -e "${RED}Please stop the service using port $port and try again${NC}"
            exit 1
        fi
    fi
done
echo -e "${GREEN}✅ Ports are available${NC}"

# Create log directories
echo -e "${YELLOW}📁 Creating log directories...${NC}"
mkdir -p "$PROJECT_ROOT/logs"
mkdir -p "$PROJECT_ROOT/honeypot-system/logs"
mkdir -p "$PROJECT_ROOT/admin-panel/logs"

# Start PostgreSQL if not running
echo -e "${YELLOW}🗄️  Checking PostgreSQL...${NC}"
if ! pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
    echo "Starting PostgreSQL..."
    if command -v brew &> /dev/null; then
        # macOS with Homebrew
        brew services start postgresql
    elif command -v systemctl &> /dev/null; then
        # Linux with systemd
        sudo systemctl start postgresql
    else
        echo -e "${RED}❌ Cannot start PostgreSQL automatically. Please start it manually.${NC}"
        exit 1
    fi
    sleep 3
fi

# Test database connection
echo -e "${YELLOW}🔗 Testing database connection...${NC}"
cd "$PROJECT_ROOT/admin-panel/database"
if python3 -c "from config import test_connection; exit(0 if test_connection() else 1)" 2>/dev/null; then
    echo -e "${GREEN}✅ Database connection successful${NC}"
else
    echo -e "${RED}❌ Database connection failed. Please check your database configuration.${NC}"
    echo "Run: cd $PROJECT_ROOT/admin-panel/database && python3 init_db.py"
    exit 1
fi

# Start services in background
echo -e "${YELLOW}🚀 Starting services...${NC}"

# 1. Start Honeypot Engine
echo "Starting Honeypot Engine..."
cd "$PROJECT_ROOT/honeypot-system"
nohup python3 main.py > "$PROJECT_ROOT/logs/honeypot.log" 2>&1 &
HONEYPOT_PID=$!
echo $HONEYPOT_PID > "$PROJECT_ROOT/logs/honeypot.pid"

# 2. Start Admin Panel Backend
echo "Starting Admin Panel Backend..."
cd "$PROJECT_ROOT/admin-panel/backend"
nohup python3 app.py > "$PROJECT_ROOT/logs/admin_backend.log" 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > "$PROJECT_ROOT/logs/admin_backend.pid"

# 3. Start Admin Panel Frontend (production build)
echo "Starting Admin Panel Frontend..."
cd "$PROJECT_ROOT/admin-panel/frontend"
if [ ! -d "build" ]; then
    echo "Building frontend..."
    npm run build
fi
nohup npx serve -s build -l 3000 > "$PROJECT_ROOT/logs/admin_frontend.log" 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > "$PROJECT_ROOT/logs/admin_frontend.pid"

# Wait for services to start
echo -e "${YELLOW}⏳ Waiting for services to start...${NC}"
sleep 5

# Check if services started successfully
SERVICES_OK=true

if ! wait_for_service 2222 "SSH Honeypot"; then
    SERVICES_OK=false
fi

if ! wait_for_service 8080 "HTTP Honeypot"; then
    SERVICES_OK=false
fi

if ! wait_for_service 5001 "Admin Backend"; then
    SERVICES_OK=false
fi

if ! wait_for_service 3000 "Admin Frontend"; then
    SERVICES_OK=false
fi

if [ "$SERVICES_OK" = true ]; then
    echo -e "${GREEN}🎉 All services started successfully!${NC}"
    echo
    echo -e "${BLUE}📊 Access Points:${NC}"
    echo "  Admin Panel:     http://localhost:3000"
    echo "  API Backend:     http://localhost:5001"
    echo "  SSH Honeypot:    localhost:2222"
    echo "  HTTP Honeypot:   http://localhost:8080"
    echo "  FTP Honeypot:    localhost:2121"
    echo
    echo -e "${BLUE}📋 Default Login:${NC}"
    echo "  Username: admin"
    echo "  Password: admin123"
    echo "  ⚠️  Change password immediately!"
    echo
    echo -e "${BLUE}📝 Logs:${NC}"
    echo "  Honeypot:        tail -f $PROJECT_ROOT/logs/honeypot.log"
    echo "  Admin Backend:   tail -f $PROJECT_ROOT/logs/admin_backend.log"
    echo "  Admin Frontend:  tail -f $PROJECT_ROOT/logs/admin_frontend.log"
    echo
    echo -e "${BLUE}🛑 To stop all services:${NC}"
    echo "  $SCRIPT_DIR/stop_all.sh"
else
    echo -e "${RED}❌ Some services failed to start. Check logs for details.${NC}"
    echo "Stopping started services..."
    "$SCRIPT_DIR/stop_all.sh"
    exit 1
fi
