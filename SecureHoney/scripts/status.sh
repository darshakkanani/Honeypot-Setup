#!/bin/bash
# SecureHoney - System Status Check Script

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

echo -e "${BLUE}📊 SecureHoney System Status${NC}"
echo "Timestamp: $(date)"
echo

# Function to check service status
check_service_status() {
    local service_name=$1
    local port=$2
    local expected_process=$3
    
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        local pid=$(lsof -ti:$port)
        local process_info=$(ps -p $pid -o comm= 2>/dev/null || echo "unknown")
        echo -e "  $service_name: ${GREEN}✅ Running${NC} (PID: $pid, Port: $port)"
        return 0
    else
        echo -e "  $service_name: ${RED}❌ Not Running${NC} (Port: $port)"
        return 1
    fi
}

# Check database connection
echo -e "${YELLOW}🗄️  Database Status:${NC}"
if pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
    echo -e "  PostgreSQL: ${GREEN}✅ Running${NC}"
    
    # Test application database connection
    cd "$PROJECT_ROOT/admin-panel/database"
    if python3 -c "from config import test_connection; exit(0 if test_connection() else 1)" 2>/dev/null; then
        echo -e "  SecureHoney DB: ${GREEN}✅ Connected${NC}"
        
        # Get database stats
        db_stats=$(python3 -c "
from config import get_health_status
import json
health = get_health_status()
print(f\"Size: {health.get('performance_metrics', {}).get('database_size', 'Unknown')}\")
print(f\"Connections: {health.get('performance_metrics', {}).get('active_connections', 'Unknown')}\")
" 2>/dev/null || echo "Stats unavailable")
        echo "    $db_stats"
    else
        echo -e "  SecureHoney DB: ${RED}❌ Connection Failed${NC}"
    fi
else
    echo -e "  PostgreSQL: ${RED}❌ Not Running${NC}"
fi

echo

# Check honeypot services
echo -e "${YELLOW}🍯 Honeypot Services:${NC}"
services_running=0
total_services=0

if check_service_status "SSH Honeypot" 2222 "python"; then
    ((services_running++))
fi
((total_services++))

if check_service_status "HTTP Honeypot" 8080 "python"; then
    ((services_running++))
fi
((total_services++))

if check_service_status "FTP Honeypot" 2121 "python"; then
    ((services_running++))
fi
((total_services++))

echo

# Check admin panel services
echo -e "${YELLOW}🎛️  Admin Panel Services:${NC}"
admin_services_running=0
total_admin_services=0

if check_service_status "Backend API" 5001 "python"; then
    ((admin_services_running++))
fi
((total_admin_services++))

if check_service_status "Frontend Web" 3000 "node"; then
    ((admin_services_running++))
fi
((total_admin_services++))

echo

# System resources
echo -e "${YELLOW}💻 System Resources:${NC}"
echo "  CPU Usage: $(top -l 1 | grep "CPU usage" | awk '{print $3}' | sed 's/%//' 2>/dev/null || echo "N/A")"
echo "  Memory: $(free -h 2>/dev/null | grep Mem | awk '{print $3"/"$2}' || echo "$(vm_stat | grep 'Pages active' | awk '{print $3}' | sed 's/\.//' 2>/dev/null || echo 'N/A')")"
echo "  Disk: $(df -h . | tail -1 | awk '{print $5" used of "$2}')"

echo

# Log file sizes
echo -e "${YELLOW}📝 Log Files:${NC}"
if [ -d "$PROJECT_ROOT/logs" ]; then
    for log_file in "$PROJECT_ROOT/logs"/*.log; do
        if [ -f "$log_file" ]; then
            size=$(du -h "$log_file" | cut -f1)
            name=$(basename "$log_file")
            echo "  $name: $size"
        fi
    done
else
    echo "  No log directory found"
fi

echo

# Recent activity (if database is available)
echo -e "${YELLOW}📈 Recent Activity (Last 24h):${NC}"
cd "$PROJECT_ROOT/admin-panel/database" 2>/dev/null || true
if python3 -c "from config import test_connection; exit(0 if test_connection() else 1)" 2>/dev/null; then
    activity_stats=$(python3 -c "
try:
    from models_admin import admin_db
    stats = admin_db.get_dashboard_summary()
    print(f\"Total Attacks: {stats.get('total_attacks', 0)}\")
    print(f\"Attacks Today: {stats.get('attacks_today', 0)}\")
    print(f\"Unique Attackers: {stats.get('unique_attackers', 0)}\")
    print(f\"Threat Level: {stats.get('threat_level', 'UNKNOWN')}\")
except Exception as e:
    print(f\"Error: {e}\")
" 2>/dev/null || echo "  Database query failed")
    echo "  $activity_stats"
else
    echo "  Database not available"
fi

echo

# Overall status summary
echo -e "${YELLOW}📋 Overall Status:${NC}"
if [ $services_running -eq $total_services ] && [ $admin_services_running -eq $total_admin_services ]; then
    echo -e "  System Status: ${GREEN}✅ All Services Running${NC}"
    echo -e "  Honeypot Services: ${GREEN}$services_running/$total_services Running${NC}"
    echo -e "  Admin Services: ${GREEN}$admin_services_running/$total_admin_services Running${NC}"
elif [ $services_running -gt 0 ] || [ $admin_services_running -gt 0 ]; then
    echo -e "  System Status: ${YELLOW}⚠️  Partially Running${NC}"
    echo -e "  Honeypot Services: ${YELLOW}$services_running/$total_services Running${NC}"
    echo -e "  Admin Services: ${YELLOW}$admin_services_running/$total_admin_services Running${NC}"
else
    echo -e "  System Status: ${RED}❌ Not Running${NC}"
    echo -e "  Honeypot Services: ${RED}$services_running/$total_services Running${NC}"
    echo -e "  Admin Services: ${RED}$admin_services_running/$total_admin_services Running${NC}"
fi

echo

# Quick access information
if [ $admin_services_running -gt 0 ]; then
    echo -e "${BLUE}🔗 Quick Access:${NC}"
    echo "  Admin Panel: http://localhost:3000"
    echo "  API Docs: http://localhost:5001/docs"
    echo "  Health Check: http://localhost:5001/api/health"
fi
