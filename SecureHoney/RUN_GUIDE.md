# SecureHoney Honeypot System - Setup & Run Guide

Complete guide to set up and run the SecureHoney honeypot system.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- Node.js 16+
- Git

### 1. Database Setup (Required First)

```bash
# Navigate to database directory
cd SecureHoney/admin-panel/database

# Install Python dependencies
pip install -r requirements.txt

# Set database environment variables
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=securehoney
export DB_USER=securehoney
export DB_PASSWORD=your_secure_password
export DB_SCHEMA=securehoney

# Initialize database
python init_db.py

# Verify installation
python init_db.py --verify-only
```

### 2. Admin Panel Setup

```bash
# Navigate to admin panel
cd SecureHoney/admin-panel

# Install backend dependencies
cd backend
pip install -r requirements.txt

# Install frontend dependencies
cd ../frontend
npm install

# Build frontend
npm run build
```

### 3. Honeypot Engine Setup

```bash
# Navigate to honeypot system
cd SecureHoney/honeypot-system

# Install dependencies
pip install -r requirements.txt

# Configure honeypot settings
cp config/honeypot_config.example.json config/honeypot_config.json
# Edit config/honeypot_config.json with your settings
```

## 🔧 Configuration

### Database Configuration
Create `.env` file in `SecureHoney/admin-panel/database/`:
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=securehoney
DB_USER=securehoney
DB_PASSWORD=your_secure_password
DB_SCHEMA=securehoney
DB_POOL_SIZE=10
DB_SSL_MODE=prefer
```

### Honeypot Configuration
Edit `SecureHoney/honeypot-system/config/honeypot_config.json`:
```json
{
  "honeypot": {
    "enabled_services": ["ssh", "http", "ftp"],
    "ssh_port": 2222,
    "http_port": 8080,
    "ftp_port": 2121,
    "bind_address": "0.0.0.0"
  },
  "database": {
    "enabled": true,
    "connection_string": "postgresql://securehoney:password@localhost:5432/securehoney"
  },
  "logging": {
    "level": "INFO",
    "file": "logs/honeypot.log"
  }
}
```

### Admin Panel Configuration
Edit `SecureHoney/admin-panel/backend/config.py`:
```python
DATABASE_URL = "postgresql://securehoney:password@localhost:5432/securehoney"
SECRET_KEY = "your-secret-key-here"
JWT_SECRET_KEY = "your-jwt-secret-here"
CORS_ORIGINS = ["http://localhost:3000"]
```

## 🏃‍♂️ Running the System

### Option 1: Manual Startup (Development)

**Terminal 1 - Database (if not running as service):**
```bash
# Start PostgreSQL (varies by system)
# macOS with Homebrew:
brew services start postgresql

# Ubuntu/Debian:
sudo systemctl start postgresql

# Or run manually:
postgres -D /usr/local/var/postgres
```

**Terminal 2 - Honeypot Engine:**
```bash
cd SecureHoney/honeypot-system
python main.py
```

**Terminal 3 - Admin Panel Backend:**
```bash
cd SecureHoney/admin-panel/backend
python app.py
```

**Terminal 4 - Admin Panel Frontend (Development):**
```bash
cd SecureHoney/admin-panel/frontend
npm start
```

### Option 2: Production Startup Scripts

**Start All Services:**
```bash
cd SecureHoney
./scripts/start_all.sh
```

**Stop All Services:**
```bash
cd SecureHoney
./scripts/stop_all.sh
```

**Check Status:**
```bash
cd SecureHoney
./scripts/status.sh
```

## 📊 Accessing the System

### Admin Panel
- **URL**: http://localhost:3000
- **Default Login**: 
  - Username: `admin`
  - Password: `admin123` (⚠️ Change immediately!)

### API Endpoints
- **Backend API**: http://localhost:5001
- **Health Check**: http://localhost:5001/api/health
- **API Documentation**: http://localhost:5001/docs

### Honeypot Services
- **SSH Honeypot**: Port 2222
- **HTTP Honeypot**: Port 8080
- **FTP Honeypot**: Port 2121

## 🔍 Monitoring & Logs

### Log Locations
```bash
# Honeypot logs
tail -f SecureHoney/honeypot-system/logs/honeypot.log

# Admin panel logs
tail -f SecureHoney/admin-panel/logs/admin.log

# Database logs (PostgreSQL default location)
tail -f /usr/local/var/log/postgres.log
```

### System Status
```bash
# Check all services
cd SecureHoney
python scripts/health_check.py

# Database health
cd SecureHoney/admin-panel/database
python -c "from config import get_health_status; print(get_health_status())"
```

## 🛠 Troubleshooting

### Common Issues

**1. Database Connection Failed**
```bash
# Check PostgreSQL is running
pg_isready -h localhost -p 5432

# Test connection manually
psql -h localhost -p 5432 -U securehoney -d securehoney

# Reset database if needed
cd SecureHoney/admin-panel/database
python init_db.py --reset
python init_db.py
```

**2. Port Already in Use**
```bash
# Check what's using the port
lsof -i :2222  # SSH honeypot
lsof -i :8080  # HTTP honeypot
lsof -i :5001  # Admin backend
lsof -i :3000  # Admin frontend

# Kill process if needed
kill -9 <PID>
```

**3. Permission Denied**
```bash
# Fix file permissions
chmod +x SecureHoney/scripts/*.sh

# Run with sudo if needed for low ports
sudo python SecureHoney/honeypot-system/main.py
```

**4. Frontend Build Issues**
```bash
cd SecureHoney/admin-panel/frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Debug Mode

**Enable Debug Logging:**
```bash
export LOG_LEVEL=DEBUG
export DB_ENABLE_LOGGING=true
```

**Run Components Individually:**
```bash
# Test database connection
cd SecureHoney/admin-panel/database
python -c "from config import test_connection; print('OK' if test_connection() else 'FAILED')"

# Test honeypot engine
cd SecureHoney/honeypot-system
python -c "from main import HoneypotEngine; engine = HoneypotEngine(); print('Engine loaded')"

# Test admin backend
cd SecureHoney/admin-panel/backend
python -c "from app import app; print('Backend loaded')"
```

## 🔒 Security Considerations

### Initial Security Setup
1. **Change Default Passwords**
   ```bash
   # Login to admin panel and change admin password
   # Or use CLI:
   cd SecureHoney/admin-panel/database
   python -c "
   from models_admin import admin_db
   user = admin_db.get_user('admin')
   user.set_password('new_secure_password')
   admin_db.save_user(user)
   "
   ```

2. **Configure Firewall**
   ```bash
   # Allow only necessary ports
   sudo ufw allow 22    # SSH (real)
   sudo ufw allow 80    # HTTP (real)
   sudo ufw allow 443   # HTTPS (real)
   sudo ufw allow 2222  # SSH honeypot
   sudo ufw allow 8080  # HTTP honeypot
   sudo ufw enable
   ```

3. **SSL/TLS Setup**
   - Configure SSL certificates for admin panel
   - Enable database SSL connections
   - Use HTTPS for all web interfaces

### Production Recommendations
- Run honeypots in isolated network segments
- Use dedicated database server
- Implement log rotation
- Set up monitoring and alerting
- Regular security updates
- Backup database regularly

## 📈 Performance Tuning

### Database Optimization
```sql
-- Connect to database and run:
-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM securehoney.attacks WHERE source_ip = '192.168.1.1';

-- Update statistics
ANALYZE;

-- Vacuum if needed
VACUUM ANALYZE;
```

### System Resources
```bash
# Monitor system resources
htop
iotop
nethogs

# Check disk usage
df -h
du -sh SecureHoney/*/logs/
```

## 🔄 Maintenance

### Regular Tasks
```bash
# Weekly database cleanup (keeps 90 days)
cd SecureHoney/admin-panel/database
python -c "
from database_integration import honeypot_db
honeypot_db.cleanup_old_data(days_to_keep=90)
"

# Log rotation
logrotate /etc/logrotate.d/securehoney

# Update threat intelligence
cd SecureHoney/shared-utils
python update_threat_intel.py
```

### Backup & Recovery
```bash
# Database backup
pg_dump -h localhost -U securehoney securehoney > backup_$(date +%Y%m%d).sql

# Configuration backup
tar -czf config_backup_$(date +%Y%m%d).tar.gz SecureHoney/*/config/

# Restore database
psql -h localhost -U securehoney securehoney < backup_20240826.sql
```

## 📞 Support

### Getting Help
1. Check logs for error messages
2. Verify all dependencies are installed
3. Ensure database is properly initialized
4. Test network connectivity
5. Review configuration files

### Useful Commands
```bash
# System overview
cd SecureHoney
./scripts/system_info.sh

# Generate diagnostic report
python scripts/diagnostic.py > diagnostic_report.txt

# Test all components
python scripts/integration_test.py
```

This guide covers the complete setup and operation of the SecureHoney honeypot system. Start with the database setup, then proceed through each component systematically.
