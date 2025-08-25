#!/usr/bin/env python3
"""
HoneyPort Setup Script
Automated setup and initialization for HoneyPort honeypot system
"""

import os
import sys
import subprocess
import shutil
import yaml
import secrets
import argparse
from pathlib import Path
from typing import Dict, Any

def generate_secret_key(length: int = 32) -> str:
    """Generate a secure random secret key"""
    return secrets.token_urlsafe(length)

def create_directories():
    """Create necessary directories"""
    directories = [
        'logs/raw_logs',
        'logs/processed',
        'logs/alerts',
        'models',
        'data',
        'blockchain/contracts/build',
        'monitoring/prometheus',
        'monitoring/grafana/dashboards',
        'monitoring/grafana/datasources',
        'nginx/ssl',
        'scripts/migrations',
        'tests/fixtures',
        'utils/templates'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created directory: {directory}")

def create_config_file():
    """Create default configuration file"""
    config = {
        'honeypot': {
            'host': '0.0.0.0',
            'ports': [22, 80, 443, 21, 23, 25, 53, 110, 143, 993, 995],
            'ssh_port': 2222,
            'http_port': 8080,
            'https_port': 8443,
            'enable_ssl': True,
            'ssl_cert_path': './nginx/ssl/cert.pem',
            'ssl_key_path': './nginx/ssl/key.pem'
        },
        'database': {
            'url': 'sqlite:///honeyport.db',
            'pool_size': 10,
            'max_overflow': 20,
            'echo': False
        },
        'redis': {
            'host': 'localhost',
            'port': 6379,
            'db': 0,
            'password': None
        },
        'blockchain': {
            'enabled': True,
            'provider_url': 'http://localhost:8545',
            'network_id': 1337,
            'gas_limit': 6721975,
            'gas_price': 20000000000
        },
        'ai': {
            'enabled': True,
            'models_path': './models',
            'continuous_learning': True,
            'feature_extraction': {
                'temporal_windows': [60, 300, 900, 3600, 86400],
                'max_payload_length': 10000,
                'geoip_database': './data/GeoLite2-City.mmdb'
            },
            'neural_networks': {
                'device': 'auto',
                'batch_size': 32,
                'learning_rate': 0.001,
                'epochs': 100,
                'early_stopping_patience': 10
            },
            'ensemble': {
                'n_estimators': 200,
                'max_depth': 15,
                'contamination': 0.1
            },
            'behavior_model': {
                'adaptation_threshold': 0.7,
                'retrain_threshold': 0.1,
                'min_samples_retrain': 100
            }
        },
        'dashboard': {
            'host': '127.0.0.1',
            'port': 5000,
            'debug': False,
            'secret_key': generate_secret_key(),
            'session_timeout': 3600,
            'max_content_length': 16777216
        },
        'attacker_site': {
            'host': '0.0.0.0',
            'port': 3000,
            'templates_path': './attacker_site/templates',
            'static_path': './attacker_site/static'
        },
        'alerts': {
            'enabled': True,
            'email': {
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'username': '',
                'password': '',
                'recipients': []
            },
            'slack': {
                'webhook_url': '',
                'channel': '#security-alerts'
            },
            'thresholds': {
                'high_threat': 0.8,
                'suspicious_activity': 0.6,
                'mass_scanning': 10,
                'brute_force': 5
            }
        },
        'logging': {
            'level': 'INFO',
            'format': 'json',
            'file_path': './logs/honeyport.log',
            'rotation_size': '100MB',
            'retention_days': 30,
            'backup_count': 10
        },
        'monitoring': {
            'prometheus': {
                'enabled': True,
                'port': 9090,
                'metrics_path': '/metrics'
            },
            'grafana': {
                'enabled': True,
                'port': 3001,
                'admin_password': generate_secret_key(16)
            }
        },
        'security': {
            'encryption_key': generate_secret_key(32),
            'jwt_secret': generate_secret_key(32),
            'rate_limiting': {
                'enabled': True,
                'requests_per_minute': 60,
                'burst_size': 100
            },
            'ip_whitelist': ['127.0.0.1', '::1'],
            'geo_blocking': {
                'enabled': False,
                'blocked_countries': []
            }
        }
    }
    
    with open('config.yaml', 'w') as f:
        yaml.dump(config, f, default_flow_style=False, indent=2)
    
    print("✓ Created config.yaml")

def create_env_file():
    """Create .env file from template"""
    if not os.path.exists('.env') and os.path.exists('.env.example'):
        shutil.copy('.env.example', '.env')
        print("✓ Created .env file from template")
        print("⚠️  Please edit .env file with your actual configuration values")

def install_dependencies():
    """Install Python dependencies"""
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✓ Installed Python dependencies")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False
    return True

def generate_ssl_certificates():
    """Generate self-signed SSL certificates for development"""
    ssl_dir = Path('nginx/ssl')
    cert_file = ssl_dir / 'cert.pem'
    key_file = ssl_dir / 'key.pem'
    
    if not cert_file.exists() or not key_file.exists():
        try:
            subprocess.check_call([
                'openssl', 'req', '-x509', '-newkey', 'rsa:4096',
                '-keyout', str(key_file), '-out', str(cert_file),
                '-days', '365', '-nodes', '-subj',
                '/C=US/ST=State/L=City/O=HoneyPort/CN=localhost'
            ])
            print("✓ Generated SSL certificates")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠️  OpenSSL not found. SSL certificates not generated.")
            print("   You can generate them manually or disable SSL in config.")

def create_monitoring_configs():
    """Create monitoring configuration files"""
    
    # Prometheus configuration
    prometheus_config = {
        'global': {
            'scrape_interval': '15s',
            'evaluation_interval': '15s'
        },
        'scrape_configs': [
            {
                'job_name': 'honeyport',
                'static_configs': [
                    {'targets': ['honeyport:5000']}
                ],
                'metrics_path': '/metrics',
                'scrape_interval': '30s'
            }
        ]
    }
    
    with open('monitoring/prometheus/prometheus.yml', 'w') as f:
        yaml.dump(prometheus_config, f, default_flow_style=False)
    
    # Grafana datasource
    grafana_datasource = {
        'apiVersion': 1,
        'datasources': [
            {
                'name': 'Prometheus',
                'type': 'prometheus',
                'access': 'proxy',
                'url': 'http://prometheus:9090',
                'isDefault': True
            }
        ]
    }
    
    with open('monitoring/grafana/datasources/prometheus.yml', 'w') as f:
        yaml.dump(grafana_datasource, f, default_flow_style=False)
    
    print("✓ Created monitoring configurations")

def create_nginx_config():
    """Create Nginx configuration"""
    nginx_config = """
events {
    worker_connections 1024;
}

http {
    upstream honeyport_backend {
        server honeyport:5000;
    }
    
    upstream attacker_site {
        server honeyport:3000;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;

    server {
        listen 80;
        server_name _;
        
        # Redirect HTTP to HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name _;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
        ssl_prefer_server_ciphers off;

        # Dashboard
        location / {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://honeyport_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Attacker site
        location /login {
            limit_req zone=login burst=5 nodelay;
            proxy_pass http://attacker_site;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }
    }
}
"""
    
    with open('nginx/nginx.conf', 'w') as f:
        f.write(nginx_config)
    
    print("✓ Created Nginx configuration")

def create_systemd_service():
    """Create systemd service file"""
    service_content = f"""[Unit]
Description=HoneyPort Honeypot System
After=network.target
Wants=network.target

[Service]
Type=simple
User=honeyport
Group=honeyport
WorkingDirectory={os.getcwd()}
Environment=PATH={os.getcwd()}/venv/bin
ExecStart={sys.executable} run.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""
    
    with open('scripts/honeyport.service', 'w') as f:
        f.write(service_content)
    
    print("✓ Created systemd service file")
    print("   To install: sudo cp scripts/honeyport.service /etc/systemd/system/")
    print("   Then: sudo systemctl enable honeyport && sudo systemctl start honeyport")

def main():
    parser = argparse.ArgumentParser(description='HoneyPort Setup Script')
    parser.add_argument('--skip-deps', action='store_true', help='Skip dependency installation')
    parser.add_argument('--skip-ssl', action='store_true', help='Skip SSL certificate generation')
    parser.add_argument('--development', action='store_true', help='Setup for development environment')
    
    args = parser.parse_args()
    
    print("🍯 Setting up HoneyPort Honeypot System...")
    print("=" * 50)
    
    # Create directories
    create_directories()
    
    # Create configuration files
    create_config_file()
    create_env_file()
    
    # Install dependencies
    if not args.skip_deps:
        if not install_dependencies():
            print("❌ Setup failed due to dependency installation error")
            return 1
    
    # Generate SSL certificates
    if not args.skip_ssl:
        generate_ssl_certificates()
    
    # Create monitoring configs
    create_monitoring_configs()
    
    # Create Nginx config
    create_nginx_config()
    
    # Create systemd service
    if not args.development:
        create_systemd_service()
    
    print("\n" + "=" * 50)
    print("✅ HoneyPort setup completed successfully!")
    print("\nNext steps:")
    print("1. Edit .env file with your configuration")
    print("2. Edit config.yaml if needed")
    print("3. Run: python run.py (or use Docker)")
    print("4. Access dashboard at: https://localhost:5000")
    print("\nFor production deployment:")
    print("1. Use docker-compose up -d")
    print("2. Configure firewall rules")
    print("3. Set up log rotation")
    print("4. Configure monitoring alerts")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
