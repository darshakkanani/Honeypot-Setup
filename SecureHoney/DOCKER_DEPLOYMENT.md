# SecureHoney Docker Deployment Guide

This guide provides comprehensive instructions for deploying the SecureHoney honeypot system using Docker containers.

## Overview

The SecureHoney system consists of multiple containerized services:
- **PostgreSQL Database**: Stores attack data, user sessions, and system configuration
- **Redis**: Caching and session storage
- **Honeypot Engine**: Core honeypot services (SSH, HTTP, FTP, Telnet)
- **Admin Backend**: FastAPI-based REST API
- **Admin Frontend**: React-based web interface
- **Nginx**: Reverse proxy and load balancer (production)

## Quick Start

### 1. Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- At least 4GB RAM
- 10GB free disk space

### 2. Clone and Setup

```bash
cd SecureHoney
cp .env.example .env
# Edit .env with your configuration
```

### 3. Development Deployment

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 4. Production Deployment

```bash
# Start production stack
docker-compose -f docker-compose.prod.yml up -d

# View status
docker-compose -f docker-compose.prod.yml ps
```

## Configuration

### Environment Variables

Edit `.env` file with your settings:

```bash
# Database
POSTGRES_DB=securehoney
POSTGRES_USER=securehoney
POSTGRES_PASSWORD=your-secure-password

# Security
JWT_SECRET=your-super-secret-jwt-key

# Honeypot Ports
HONEYPOT_SSH_PORT=2222
HONEYPOT_HTTP_PORT=8080
HONEYPOT_FTP_PORT=2121
HONEYPOT_TELNET_PORT=2323
```

### SSL Configuration (Production)

For HTTPS in production:

1. Place SSL certificates in `docker/nginx/ssl/`
2. Update `docker/nginx/nginx.conf` to enable HTTPS server block
3. Restart nginx container

## Service Access

| Service | Development URL | Production URL |
|---------|----------------|----------------|
| Admin Panel | http://localhost:3000 | http://localhost |
| API | http://localhost:5001/api | http://localhost/api |
| Database | localhost:5432 | Internal only |
| Honeypot SSH | localhost:2222 | localhost:2222 |
| Honeypot HTTP | localhost:8080 | localhost:8080 |

## Default Credentials

- **Username**: admin
- **Password**: admin123

⚠️ **Change default credentials immediately after first login!**

## Management Commands

### Start Services
```bash
# Development
docker-compose up -d

# Production
docker-compose -f docker-compose.prod.yml up -d
```

### Stop Services
```bash
# Development
docker-compose down

# Production
docker-compose -f docker-compose.prod.yml down
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f honeypot
```

### Database Operations
```bash
# Access database
docker-compose exec database psql -U securehoney -d securehoney

# Backup database
docker-compose exec database pg_dump -U securehoney securehoney > backup.sql

# Restore database
docker-compose exec -T database psql -U securehoney -d securehoney < backup.sql
```

### Scale Services
```bash
# Scale honeypot instances
docker-compose up -d --scale honeypot=3
```

## Monitoring

### Health Checks
```bash
# Check service health
docker-compose ps

# Detailed health status
docker inspect securehoney-honeypot | grep -A 10 Health
```

### Resource Usage
```bash
# Container stats
docker stats

# System resource usage
docker system df
```

### Log Management

Logs are stored in `./logs/` directory:
- `honeypot/`: Honeypot engine logs
- `admin/`: Admin panel logs
- `nginx/`: Nginx access and error logs

## Backup and Recovery

### Automated Backups (Production)

Production deployment includes automated daily backups:
- Location: `./backups/`
- Retention: 7 days
- Format: Compressed SQL dumps

### Manual Backup
```bash
# Create backup
docker-compose exec database pg_dump -U securehoney -Fc securehoney > backup_$(date +%Y%m%d).dump

# Restore from backup
docker-compose exec -T database pg_restore -U securehoney -d securehoney -c < backup_20240101.dump
```

## Security Considerations

### Network Security
- Use firewall rules to restrict access
- Change default ports in production
- Enable SSL/TLS for web interfaces

### Container Security
- All containers run as non-root users
- Minimal base images (Alpine Linux)
- Regular security updates

### Data Security
- Encrypt database backups
- Use strong passwords
- Rotate JWT secrets regularly

## Troubleshooting

### Common Issues

**Database Connection Failed**
```bash
# Check database status
docker-compose logs database

# Verify network connectivity
docker-compose exec honeypot nc -zv database 5432
```

**Port Conflicts**
```bash
# Check port usage
netstat -tulpn | grep :2222

# Change ports in .env file
HONEYPOT_SSH_PORT=2223
```

**Memory Issues**
```bash
# Check memory usage
docker stats

# Increase Docker memory limit
# Docker Desktop: Settings > Resources > Memory
```

### Log Analysis
```bash
# Search for errors
docker-compose logs | grep -i error

# Follow specific service logs
docker-compose logs -f --tail=100 honeypot
```

### Performance Tuning

**Database Performance**
- Increase `shared_buffers` in PostgreSQL config
- Add more memory to database container
- Use SSD storage for volumes

**Application Performance**
- Scale backend services horizontally
- Enable Redis caching
- Optimize database queries

## Development

### Building Images
```bash
# Build all images
docker-compose build

# Build specific service
docker-compose build honeypot
```

### Development Mode
```bash
# Mount source code for development
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

### Testing
```bash
# Run tests in containers
docker-compose exec honeypot python -m pytest
docker-compose exec admin-backend python -m pytest
```

## Production Deployment Checklist

- [ ] Change default passwords
- [ ] Configure SSL certificates
- [ ] Set up firewall rules
- [ ] Configure log rotation
- [ ] Set up monitoring alerts
- [ ] Test backup/restore procedures
- [ ] Configure external database (optional)
- [ ] Set up load balancing (if needed)
- [ ] Configure DNS records
- [ ] Test all honeypot services

## Support

For issues and questions:
1. Check logs: `docker-compose logs`
2. Verify configuration: `.env` file
3. Check system resources: `docker stats`
4. Review this documentation
5. Check GitHub issues and documentation

## Architecture Diagram

```
┌─────────────────┐    ┌─────────────────┐
│   Admin Panel   │    │   Honeypot      │
│   (Frontend)    │    │   Engine        │
│   Port: 3000    │    │   Ports: 2222+  │
└─────────────────┘    └─────────────────┘
         │                       │
         └───────────┬───────────┘
                     │
         ┌─────────────────┐
         │     Nginx       │
         │  (Reverse Proxy)│
         │   Port: 80/443  │
         └─────────────────┘
                     │
         ┌─────────────────┐
         │  Admin Backend  │
         │     (API)       │
         │   Port: 5001    │
         └─────────────────┘
                     │
    ┌────────────────┼────────────────┐
    │                │                │
┌─────────┐    ┌─────────┐    ┌─────────┐
│PostgreSQL│    │  Redis  │    │  Logs   │
│Database │    │ Cache   │    │ Volume  │
│Port:5432│    │Port:6379│    │         │
└─────────┘    └─────────┘    └─────────┘
```
