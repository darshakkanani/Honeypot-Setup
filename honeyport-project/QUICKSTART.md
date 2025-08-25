# 🚀 HoneyPort Quick Start Guide

Get your HoneyPort AI honeypot system running in minutes!

## Prerequisites

- **Python 3.11+** installed
- **Docker & Docker Compose** (recommended)
- **4GB+ RAM** available
- **Network ports** 80, 443, 5000, 8080 available

## Option 1: Docker Quick Start (Recommended)

### 1. Clone and Navigate
```bash
cd /Users/hunter/Desktop/Honeypot-Setup/honeyport-project
```

### 2. Start with Docker Compose
```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f honeyport
```

### 3. Access Your System
- **Dashboard**: http://localhost:5000 (admin/honeyport2024)
- **Honeypot**: http://localhost:8080 (for attackers)
- **Monitoring**: http://localhost:3000 (Grafana)

## Option 2: Manual Setup

### 1. Install Dependencies
```bash
# Install Python dependencies
pip3 install -r requirements.txt
pip3 install -r requirements-dev.txt

# Install system dependencies (Ubuntu/Debian)
sudo apt update
sudo apt install -y postgresql redis-server nginx
```

### 2. Setup Environment
```bash
# Copy environment template
cp .env.example .env

# Edit configuration (use your preferred editor)
nano .env
```

### 3. Initialize Database
```bash
# Start PostgreSQL
sudo systemctl start postgresql

# Create database and user
sudo -u postgres psql -f scripts/init_db.sql

# Run database initialization
python3 scripts/setup.py
```

### 4. Start Services
```bash
# Start Redis
sudo systemctl start redis

# Start HoneyPort (in separate terminals)
python3 run.py                    # Main honeypot
python3 dashboard/app.py          # Dashboard
```

## Option 3: Development Mode

### 1. Quick Development Setup
```bash
# Use the Makefile for easy setup
make install    # Install all dependencies
make setup      # Run initial setup
make dev        # Start development server
```

### 2. Run Tests
```bash
make test       # Run test suite
make lint       # Check code quality
```

## Testing Your Honeypot

### 1. Test Basic Functionality
```bash
# Test honeypot is responding
curl http://localhost:8080

# Test dashboard API
curl -u admin:honeyport2024 http://localhost:5000/api/honeypot/status
```

### 2. Simulate Attacks
```bash
# SQL Injection test
curl "http://localhost:8080/login?id=1' OR 1=1--"

# XSS test
curl "http://localhost:8080/search?q=<script>alert('xss')</script>"

# Brute force test
for i in {1..5}; do
  curl -X POST "http://localhost:8080/admin" \
    -d "username=admin&password=pass$i"
done
```

### 3. Check Results
- View attacks in dashboard: http://localhost:5000
- Check logs: `tail -f logs/honeyport.log`
- Monitor AI analysis: Check dashboard "AI Insights" section

## Configuration

### Basic Configuration (`config.yaml`)
```yaml
honeypot:
  host: "0.0.0.0"
  ports: [80, 443, 8080, 2222]
  
ai:
  enabled: true
  continuous_learning: true
  
blockchain:
  enabled: true
  
dashboard:
  host: "127.0.0.1"
  port: 5000
  admin_username: "admin"
  admin_password: "honeyport2024"
```

### Environment Variables (`.env`)
```bash
# Database
DATABASE_URL=postgresql://honeyport_user:password@localhost/honeyport

# Security
SECRET_KEY=your-secret-key-here
ENCRYPTION_KEY=your-encryption-key-here

# Optional: AI Features
OPENAI_API_KEY=your-openai-key  # For enhanced AI features
```

## Common Issues & Solutions

### Port Already in Use
```bash
# Find what's using port 80
sudo lsof -i :80

# Kill the process or change HoneyPort port in config.yaml
```

### Database Connection Error
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Restart if needed
sudo systemctl restart postgresql

# Test connection
psql -h localhost -U honeyport_user -d honeyport
```

### Docker Issues
```bash
# Reset Docker environment
docker-compose down -v
docker-compose up -d

# Check Docker logs
docker-compose logs honeyport
```

### Permission Errors
```bash
# Fix file permissions
sudo chown -R $USER:$USER /Users/hunter/Desktop/Honeypot-Setup/honeyport-project
chmod +x scripts/*.py
```

## Production Deployment

### 1. Security Hardening
```bash
# Run security setup
sudo python3 scripts/setup.py --production

# Configure firewall
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 2. SSL/TLS Setup
```bash
# Generate SSL certificates
make ssl

# Or use Let's Encrypt
sudo certbot --nginx -d yourdomain.com
```

### 3. System Service
```bash
# Install as system service
sudo cp scripts/honeyport.service /etc/systemd/system/
sudo systemctl enable honeyport
sudo systemctl start honeyport
```

## Monitoring & Maintenance

### Health Checks
```bash
# Check system health
curl http://localhost:5000/health

# Monitor with make commands
make logs      # View logs
make health    # Check health status
```

### Backup
```bash
# Backup data
make backup

# Manual backup
python3 scripts/backup.py
```

### Updates
```bash
# Update system
git pull origin main
make install
docker-compose up -d --build
```

## Next Steps

1. **Customize Configuration**: Edit `config.yaml` for your environment
2. **Set Up Monitoring**: Configure Grafana dashboards
3. **Enable Alerts**: Set up email/Slack notifications
4. **Review Security**: Follow `docs/SECURITY.md` guidelines
5. **Scale Up**: Use `docs/DEPLOYMENT.md` for production setup

## Getting Help

- **Documentation**: Check `docs/` directory
- **API Reference**: `docs/API.md`
- **Architecture**: `docs/ARCHITECTURE.md`
- **Security**: `docs/SECURITY.md`
- **Logs**: Check `logs/honeyport.log` for issues

## Quick Commands Reference

```bash
# Docker
docker-compose up -d              # Start all services
docker-compose down               # Stop all services
docker-compose logs -f honeyport  # View logs

# Make commands
make install                      # Install dependencies
make setup                        # Initial setup
make dev                          # Development mode
make test                         # Run tests
make clean                        # Clean temporary files

# Manual
python3 run.py                    # Start honeypot
python3 dashboard/app.py          # Start dashboard
python3 scripts/setup.py          # Run setup
```

Your HoneyPort system is now ready to detect and analyze cyber attacks! 🛡️
