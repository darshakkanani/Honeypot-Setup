# HoneyPort Deployment Guide

Complete deployment guide for HoneyPort AI-powered honeypot system across different environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start Deployment](#quick-start-deployment)
- [Docker Deployment](#docker-deployment)
- [Production Deployment](#production-deployment)
- [Cloud Deployment](#cloud-deployment)
- [Security Hardening](#security-hardening)
- [Monitoring Setup](#monitoring-setup)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

**Minimum Requirements:**
- CPU: 2 cores, 2.4GHz
- RAM: 4GB
- Storage: 20GB SSD
- Network: 100Mbps
- OS: Ubuntu 20.04+, CentOS 8+, or Docker

**Recommended for Production:**
- CPU: 4+ cores, 3.0GHz+
- RAM: 8GB+
- Storage: 100GB+ SSD
- Network: 1Gbps+
- OS: Ubuntu 22.04 LTS

### Software Dependencies

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3.11 python3-pip postgresql redis-server nginx docker.io docker-compose

# CentOS/RHEL
sudo yum install -y python3.11 python3-pip postgresql redis nginx docker docker-compose
```

### Network Requirements

**Inbound Ports:**
- `22`: SSH (admin access)
- `80/443`: HTTP/HTTPS (honeypot listeners)
- `5000`: Dashboard (internal)
- `8080`: Alternative HTTP
- `2222`: SSH honeypot
- `9090`: Prometheus (monitoring)
- `3000`: Grafana (monitoring)

**Outbound Ports:**
- `443`: HTTPS (AI model downloads, updates)
- `8545`: Ethereum node (blockchain logging)
- `25/587`: SMTP (email alerts)

## Quick Start Deployment

### 1. Automated Setup

```bash
# Clone repository
git clone https://github.com/your-org/honeyport.git
cd honeyport-project

# Run automated setup
sudo python3 scripts/setup.py

# Start services
make docker-run
```

### 2. Manual Setup

```bash
# Install Python dependencies
pip3 install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your configuration

# Initialize database
python3 scripts/init_db.py

# Start HoneyPort
python3 run.py
```

## Docker Deployment

### Development Environment

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f honeyport

# Stop services
docker-compose down
```

### Production Environment

```bash
# Use production configuration
docker-compose -f docker-compose.prod.yml up -d

# Scale honeypot instances
docker-compose -f docker-compose.prod.yml up -d --scale honeyport=3

# Update services
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

### Custom Docker Build

```dockerfile
# Custom Dockerfile for specific requirements
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# Copy application
COPY . /app
WORKDIR /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user
RUN useradd -m -u 1000 honeyport
USER honeyport

# Expose ports
EXPOSE 5000 8080 2222

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5000/health || exit 1

# Start application
CMD ["python", "run.py"]
```

## Production Deployment

### 1. Infrastructure Setup

#### Load Balancer Configuration (Nginx)

```nginx
# /etc/nginx/sites-available/honeyport
upstream honeyport_backend {
    server 127.0.0.1:5000;
    server 127.0.0.1:5001;
    server 127.0.0.1:5002;
}

server {
    listen 80;
    listen 443 ssl http2;
    server_name honeyport.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/ssl/certs/honeyport.crt;
    ssl_certificate_key /etc/ssl/private/honeyport.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;

    # Security Headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";

    # Dashboard (Admin Access Only)
    location /admin {
        allow 10.0.0.0/8;
        allow 192.168.0.0/16;
        deny all;
        
        proxy_pass http://honeyport_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Honeypot Endpoints (Public)
    location / {
        proxy_pass http://honeyport_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Rate limiting
        limit_req zone=honeypot burst=100 nodelay;
    }
}

# Rate limiting configuration
http {
    limit_req_zone $binary_remote_addr zone=honeypot:10m rate=10r/s;
}
```

#### Database Setup (PostgreSQL)

```sql
-- Create dedicated database and user
CREATE DATABASE honeyport;
CREATE USER honeyport_user WITH ENCRYPTED PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE honeyport TO honeyport_user;

-- Performance tuning
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;

-- Restart PostgreSQL
sudo systemctl restart postgresql
```

### 2. Application Deployment

#### Systemd Service Configuration

```ini
# /etc/systemd/system/honeyport.service
[Unit]
Description=HoneyPort AI Honeypot System
After=network.target postgresql.service redis.service
Wants=postgresql.service redis.service

[Service]
Type=forking
User=honeyport
Group=honeyport
WorkingDirectory=/opt/honeyport
Environment=PATH=/opt/honeyport/venv/bin
ExecStart=/opt/honeyport/venv/bin/python run.py --daemon
ExecReload=/bin/kill -s HUP $MAINPID
ExecStop=/bin/kill -s TERM $MAINPID
Restart=always
RestartSec=10

# Security
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=/opt/honeyport/logs /opt/honeyport/data

[Install]
WantedBy=multi-user.target
```

#### Application Configuration

```yaml
# config.prod.yaml
honeypot:
  host: "0.0.0.0"
  ports: [80, 443, 22, 21, 23, 25, 110, 143, 993, 995]
  max_connections: 10000
  
ai:
  enabled: true
  continuous_learning: true
  models_path: "/opt/honeyport/models"
  gpu_enabled: true
  batch_size: 64
  
blockchain:
  enabled: true
  provider_url: "https://mainnet.infura.io/v3/YOUR_PROJECT_ID"
  gas_limit: 100000
  
database:
  url: "postgresql://honeyport_user:secure_password@localhost/honeyport"
  pool_size: 20
  max_overflow: 30
  
redis:
  url: "redis://localhost:6379/0"
  max_connections: 100
  
logging:
  level: "INFO"
  max_file_size: "100MB"
  backup_count: 10
  
alerts:
  enabled: true
  severity_threshold: "medium"
  rate_limit: 100
  channels:
    email:
      enabled: true
      smtp_server: "smtp.yourdomain.com"
      smtp_port: 587
      username: "alerts@yourdomain.com"
      recipients: ["security@yourdomain.com"]
    slack:
      enabled: true
      webhook_url: "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
    webhook:
      enabled: true
      url: "https://your-siem.com/webhook"
      
security:
  encryption_key: "your-32-byte-encryption-key"
  jwt_secret: "your-jwt-secret-key"
  session_timeout: 3600
  max_login_attempts: 5
  ip_whitelist:
    - "10.0.0.0/8"
    - "192.168.0.0/16"
```

### 3. Deployment Script

```bash
#!/bin/bash
# deploy.sh - Production deployment script

set -e

# Configuration
APP_DIR="/opt/honeyport"
BACKUP_DIR="/opt/honeyport-backups"
SERVICE_NAME="honeyport"
NGINX_CONFIG="/etc/nginx/sites-available/honeyport"

# Create backup
echo "Creating backup..."
mkdir -p $BACKUP_DIR
tar -czf "$BACKUP_DIR/honeyport-$(date +%Y%m%d-%H%M%S).tar.gz" -C $APP_DIR .

# Stop services
echo "Stopping services..."
sudo systemctl stop $SERVICE_NAME
sudo systemctl stop nginx

# Update application
echo "Updating application..."
cd $APP_DIR
git pull origin main

# Install dependencies
echo "Installing dependencies..."
source venv/bin/activate
pip install -r requirements.txt

# Run database migrations
echo "Running database migrations..."
python scripts/migrate_db.py

# Update AI models
echo "Updating AI models..."
python scripts/update_models.py

# Restart services
echo "Starting services..."
sudo systemctl start $SERVICE_NAME
sudo systemctl start nginx

# Health check
echo "Performing health check..."
sleep 10
curl -f http://localhost:5000/health || {
    echo "Health check failed! Rolling back..."
    # Rollback logic here
    exit 1
}

echo "Deployment completed successfully!"
```

## Cloud Deployment

### AWS Deployment

#### ECS Fargate

```json
{
  "family": "honeyport-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "honeyport",
      "image": "your-account.dkr.ecr.region.amazonaws.com/honeyport:latest",
      "portMappings": [
        {"containerPort": 5000, "protocol": "tcp"},
        {"containerPort": 8080, "protocol": "tcp"}
      ],
      "environment": [
        {"name": "DATABASE_URL", "value": "postgresql://..."},
        {"name": "REDIS_URL", "value": "redis://..."}
      ],
      "secrets": [
        {
          "name": "SECRET_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:honeyport/secrets"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/honeyport",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:5000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3
      }
    }
  ]
}
```

#### Terraform Configuration

```hcl
# main.tf
provider "aws" {
  region = "us-west-2"
}

# VPC and Networking
resource "aws_vpc" "honeyport_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = {
    Name = "honeyport-vpc"
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "honeyport_cluster" {
  name = "honeyport-cluster"
  
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

# RDS Database
resource "aws_db_instance" "honeyport_db" {
  identifier = "honeyport-db"
  
  engine         = "postgres"
  engine_version = "13.7"
  instance_class = "db.t3.micro"
  
  allocated_storage     = 20
  max_allocated_storage = 100
  storage_type          = "gp2"
  storage_encrypted     = true
  
  db_name  = "honeyport"
  username = "honeyport_user"
  password = var.db_password
  
  vpc_security_group_ids = [aws_security_group.rds_sg.id]
  db_subnet_group_name   = aws_db_subnet_group.honeyport_db_subnet_group.name
  
  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  skip_final_snapshot = false
  final_snapshot_identifier = "honeyport-db-final-snapshot"
  
  tags = {
    Name = "honeyport-database"
  }
}

# Application Load Balancer
resource "aws_lb" "honeyport_alb" {
  name               = "honeyport-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg.id]
  subnets           = aws_subnet.public_subnet[*].id
  
  enable_deletion_protection = true
  
  tags = {
    Name = "honeyport-alb"
  }
}
```

### Azure Deployment

#### Container Instances

```yaml
# azure-deploy.yaml
apiVersion: 2019-12-01
location: eastus
name: honeyport-container-group
properties:
  containers:
  - name: honeyport
    properties:
      image: your-registry.azurecr.io/honeyport:latest
      resources:
        requests:
          cpu: 2
          memoryInGb: 4
      ports:
      - port: 5000
        protocol: TCP
      - port: 8080
        protocol: TCP
      environmentVariables:
      - name: DATABASE_URL
        secureValue: postgresql://...
      - name: REDIS_URL
        value: redis://...
  osType: Linux
  restartPolicy: Always
  ipAddress:
    type: Public
    ports:
    - protocol: tcp
      port: 5000
    - protocol: tcp
      port: 8080
  tags:
    application: honeyport
    environment: production
```

### Google Cloud Platform

#### Cloud Run Deployment

```yaml
# cloudrun.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: honeyport
  annotations:
    run.googleapis.com/ingress: all
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/maxScale: "10"
        run.googleapis.com/cpu-throttling: "false"
    spec:
      containerConcurrency: 100
      containers:
      - image: gcr.io/your-project/honeyport:latest
        ports:
        - containerPort: 5000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: honeyport-secrets
              key: database-url
        resources:
          limits:
            cpu: "2"
            memory: "4Gi"
        livenessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
```

## Security Hardening

### 1. Network Security

```bash
# Firewall configuration (UFW)
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow specific ports
sudo ufw allow 22/tcp    # SSH (admin)
sudo ufw allow 80/tcp    # HTTP honeypot
sudo ufw allow 443/tcp   # HTTPS honeypot
sudo ufw allow 2222/tcp  # SSH honeypot

# Rate limiting
sudo ufw limit 22/tcp
sudo ufw limit 2222/tcp

# Enable firewall
sudo ufw enable
```

### 2. Application Security

```python
# security_config.py
SECURITY_CONFIG = {
    'encryption': {
        'algorithm': 'AES-256-GCM',
        'key_rotation_days': 90,
        'secure_random': True
    },
    'authentication': {
        'password_policy': {
            'min_length': 12,
            'require_uppercase': True,
            'require_lowercase': True,
            'require_numbers': True,
            'require_symbols': True
        },
        'session_security': {
            'secure_cookies': True,
            'httponly_cookies': True,
            'samesite': 'Strict',
            'session_timeout': 3600
        },
        'rate_limiting': {
            'login_attempts': 5,
            'lockout_duration': 900,
            'api_rate_limit': 1000
        }
    },
    'data_protection': {
        'encrypt_at_rest': True,
        'encrypt_in_transit': True,
        'data_retention_days': 365,
        'anonymize_ips': True
    }
}
```

### 3. Container Security

```dockerfile
# Secure Dockerfile
FROM python:3.11-slim

# Security updates
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    gcc postgresql-client && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r honeyport && useradd -r -g honeyport honeyport

# Set secure permissions
COPY --chown=honeyport:honeyport . /app
WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Switch to non-root user
USER honeyport

# Security labels
LABEL security.scan="enabled"
LABEL security.policy="restricted"

# Run with minimal privileges
EXPOSE 5000
CMD ["python", "run.py"]
```

## Monitoring Setup

### 1. Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "honeyport_rules.yml"

scrape_configs:
  - job_name: 'honeyport'
    static_configs:
      - targets: ['localhost:5000']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['localhost:9100']

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

### 2. Grafana Dashboards

```json
{
  "dashboard": {
    "title": "HoneyPort Security Dashboard",
    "panels": [
      {
        "title": "Attack Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(honeyport_attacks_total[5m])",
            "legendFormat": "Attacks/sec"
          }
        ]
      },
      {
        "title": "Threat Level Distribution",
        "type": "piechart",
        "targets": [
          {
            "expr": "honeyport_threat_levels",
            "legendFormat": "{{level}}"
          }
        ]
      }
    ]
  }
}
```

### 3. Alert Rules

```yaml
# honeyport_rules.yml
groups:
- name: honeyport_alerts
  rules:
  - alert: HighAttackRate
    expr: rate(honeyport_attacks_total[5m]) > 10
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "High attack rate detected"
      description: "Attack rate is {{ $value }} attacks/sec"

  - alert: SystemDown
    expr: up{job="honeyport"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "HoneyPort system is down"
      description: "HoneyPort has been down for more than 1 minute"

  - alert: HighThreatLevel
    expr: honeyport_threat_level > 0.8
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "High threat level detected"
      description: "Current threat level is {{ $value }}"
```

## Troubleshooting

### Common Issues

#### 1. Database Connection Issues

```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test connection
psql -h localhost -U honeyport_user -d honeyport -c "SELECT 1;"

# Check logs
sudo tail -f /var/log/postgresql/postgresql-*.log
```

#### 2. AI Model Loading Issues

```bash
# Check model files
ls -la /opt/honeyport/models/

# Test model loading
python3 -c "
from ai_models.neural_networks import ThreatLevelPredictor
model = ThreatLevelPredictor(64, 128)
print('Model loaded successfully')
"

# Check GPU availability
python3 -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

#### 3. Blockchain Connection Issues

```bash
# Test Ethereum connection
python3 -c "
from web3 import Web3
w3 = Web3(Web3.HTTPProvider('http://localhost:8545'))
print(f'Connected: {w3.isConnected()}')
print(f'Block number: {w3.eth.block_number}')
"

# Check Ganache logs
docker logs ganache-cli
```

### Performance Optimization

#### 1. Database Optimization

```sql
-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM attack_logs WHERE timestamp > NOW() - INTERVAL '1 hour';

-- Create indexes for common queries
CREATE INDEX CONCURRENTLY idx_attack_logs_timestamp ON attack_logs(timestamp);
CREATE INDEX CONCURRENTLY idx_attack_logs_source_ip ON attack_logs(source_ip);
CREATE INDEX CONCURRENTLY idx_attack_logs_threat_level ON attack_logs(threat_level);

-- Update statistics
ANALYZE attack_logs;
```

#### 2. Application Optimization

```python
# Performance monitoring
import cProfile
import pstats

def profile_analysis():
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Your analysis code here
    ai_engine.analyze_attack(attack_data)
    
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)

# Memory optimization
import gc
import psutil

def monitor_memory():
    process = psutil.Process()
    memory_info = process.memory_info()
    print(f"RSS: {memory_info.rss / 1024 / 1024:.2f} MB")
    print(f"VMS: {memory_info.vms / 1024 / 1024:.2f} MB")
    
    # Force garbage collection
    gc.collect()
```

### Log Analysis

```bash
# Monitor application logs
tail -f /opt/honeyport/logs/honeyport.log | grep -E "(ERROR|CRITICAL)"

# Analyze attack patterns
grep "sql_injection" /opt/honeyport/logs/attacks.log | \
  awk '{print $1}' | sort | uniq -c | sort -nr

# Monitor system resources
htop
iotop
nethogs
```

---

This deployment guide provides comprehensive instructions for deploying HoneyPort in various environments with proper security, monitoring, and troubleshooting procedures.
