# HoneyPort Security Guide

Comprehensive security guide for deploying and operating HoneyPort safely and securely.

## Security Architecture

### Defense in Depth

HoneyPort implements multiple security layers:

1. **Perimeter Security**: Firewall, DDoS protection, rate limiting
2. **Network Security**: Segmentation, VPN access, SSL/TLS
3. **Application Security**: Authentication, authorization, input validation
4. **Data Security**: Encryption at rest/transit, backup, anonymization

### Security Principles

- **Principle of Least Privilege**: Minimal required permissions
- **Zero Trust**: Verify everything, trust nothing
- **Defense in Depth**: Multiple security layers
- **Fail Secure**: Secure defaults and failure modes
- **Security by Design**: Built-in security from the start

## Deployment Security

### Server Hardening

```bash
#!/bin/bash
# server_hardening.sh

# Update system
apt update && apt upgrade -y

# Disable root login
sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config

# Configure SSH security
cat >> /etc/ssh/sshd_config << EOF
Protocol 2
PasswordAuthentication no
PubkeyAuthentication yes
PermitEmptyPasswords no
MaxAuthTries 3
ClientAliveInterval 300
ClientAliveCountMax 2
AllowUsers honeyport-admin
EOF

# Restart SSH
systemctl restart ssh

# Install fail2ban
apt install -y fail2ban
systemctl enable fail2ban

# Configure firewall
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

echo "Server hardening completed"
```

### Container Security

```dockerfile
# Secure Dockerfile
FROM python:3.11-slim

# Security updates
RUN apt-get update && apt-get upgrade -y && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r -g 1000 honeyport && \
    useradd -r -u 1000 -g honeyport -m honeyport

# Set secure permissions
COPY --chown=honeyport:honeyport . /app
WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Switch to non-root user
USER honeyport

# Security labels
LABEL security.scan="enabled"

EXPOSE 5000
CMD ["python", "run.py"]
```

## Network Security

### Firewall Rules

```bash
# iptables configuration
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# Allow loopback
iptables -A INPUT -i lo -j ACCEPT

# Allow established connections
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# SSH (rate limited)
iptables -A INPUT -p tcp --dport 22 -m limit --limit 3/min -j ACCEPT

# HTTP/HTTPS honeypot
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Admin access (restricted)
iptables -A INPUT -p tcp --dport 5000 -s 10.0.0.0/8 -j ACCEPT

# DDoS protection
iptables -A INPUT -p tcp --dport 80 -m limit --limit 25/min -j ACCEPT
```

### SSL/TLS Configuration

```nginx
# nginx-ssl.conf
server {
    listen 443 ssl http2;
    
    # Modern SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
}
```

## Application Security

### Authentication

```python
# auth_security.py
import bcrypt
import jwt
from datetime import datetime, timedelta

class SecurityManager:
    def hash_password(self, password):
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode('utf-8'), salt)
    
    def verify_password(self, password, hashed):
        return bcrypt.checkpw(password.encode('utf-8'), hashed)
    
    def generate_token(self, user_id, expires_hours=1):
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(hours=expires_hours),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, app.config['JWT_SECRET'], algorithm='HS256')
```

### Input Validation

```python
# input_validation.py
import re
import html
from marshmallow import Schema, fields, validate

class AttackDataSchema(Schema):
    source_ip = fields.IP(required=True)
    source_port = fields.Integer(validate=validate.Range(min=1, max=65535))
    attack_type = fields.String(validate=validate.OneOf([
        'sql_injection', 'xss', 'brute_force', 'directory_traversal'
    ]))
    payload = fields.String(validate=validate.Length(max=10000))

class InputValidator:
    def sanitize_payload(self, payload):
        return html.escape(payload)
    
    def detect_sql_injection(self, payload):
        patterns = [
            r"(\b(union|select|insert|update|delete)\b)",
            r"(\b(or|and)\s+\d+\s*=\s*\d+)",
            r"('|\"|;|--)"
        ]
        return any(re.search(p, payload, re.IGNORECASE) for p in patterns)
```

## Data Protection

### Encryption

```python
# encryption.py
from cryptography.fernet import Fernet
import base64

class EncryptionManager:
    def __init__(self, key):
        self.fernet = Fernet(key)
    
    def encrypt_data(self, data):
        if isinstance(data, str):
            data = data.encode()
        return self.fernet.encrypt(data)
    
    def decrypt_data(self, encrypted_data):
        decrypted = self.fernet.decrypt(encrypted_data)
        return decrypted.decode()
    
    def encrypt_database_field(self, value):
        if value is None:
            return None
        encrypted = self.encrypt_data(str(value))
        return base64.b64encode(encrypted).decode()
```

### Data Anonymization

```python
# anonymization.py
import hashlib
import ipaddress

class DataAnonymizer:
    def anonymize_ip(self, ip_address, preserve_subnet=True):
        if preserve_subnet:
            network = ipaddress.IPv4Network(f"{ip_address}/24", strict=False)
            hash_value = int(hashlib.md5(ip_address.encode()).hexdigest()[:8], 16)
            host_part = hash_value % 254 + 1
            return str(network.network_address + host_part)
        else:
            return hashlib.sha256(ip_address.encode()).hexdigest()[:15]
    
    def anonymize_payload(self, payload):
        return hashlib.sha256(payload.encode()).hexdigest()[:32]
```

## Security Monitoring

### Threat Detection

```python
# security_monitoring.py
from collections import defaultdict
from datetime import datetime, timedelta

class SecurityMonitor:
    def __init__(self):
        self.attack_patterns = defaultdict(list)
        self.alert_thresholds = {
            'high_frequency_attacks': 50,
            'distributed_attack': 10,
            'privilege_escalation': 1
        }
    
    def record_attack(self, attack_data):
        source_ip = attack_data.get('source_ip')
        self.attack_patterns[source_ip].append({
            'timestamp': datetime.now(),
            'attack_type': attack_data.get('attack_type'),
            'threat_level': attack_data.get('threat_level', 0.5)
        })
        
        self.check_threats()
    
    def check_threats(self):
        # Check for high-frequency attacks
        recent_attacks = sum(
            len([a for a in attacks if a['timestamp'] > datetime.now() - timedelta(minutes=1)])
            for attacks in self.attack_patterns.values()
        )
        
        if recent_attacks > self.alert_thresholds['high_frequency_attacks']:
            self.send_alert('High frequency attack detected')
```

## Incident Response

### Response Procedures

1. **Detection**: Automated monitoring alerts
2. **Analysis**: Threat assessment and classification
3. **Containment**: Isolate affected systems
4. **Eradication**: Remove threats and vulnerabilities
5. **Recovery**: Restore normal operations
6. **Lessons Learned**: Document and improve

### Automated Response

```python
# incident_response.py
class IncidentResponse:
    def handle_high_threat(self, attack_data):
        # Block IP address
        self.block_ip(attack_data['source_ip'])
        
        # Send immediate alert
        self.send_critical_alert(attack_data)
        
        # Increase monitoring
        self.escalate_monitoring()
    
    def block_ip(self, ip_address):
        # Add to firewall block list
        os.system(f"iptables -A INPUT -s {ip_address} -j DROP")
        
        # Log the action
        self.log_action(f"Blocked IP: {ip_address}")
```

## Compliance

### GDPR Compliance

- **Data Minimization**: Collect only necessary data
- **Purpose Limitation**: Use data only for stated purposes
- **Storage Limitation**: Retain data only as long as needed
- **Data Subject Rights**: Provide access, rectification, erasure
- **Privacy by Design**: Build privacy into system design

### SOC 2 Controls

- **Security**: Protect against unauthorized access
- **Availability**: System available for operation
- **Processing Integrity**: System processing is complete and accurate
- **Confidentiality**: Information designated as confidential is protected
- **Privacy**: Personal information is collected, used, retained, disclosed

## Security Checklist

### Pre-Deployment

- [ ] Server hardening completed
- [ ] Firewall rules configured
- [ ] SSL/TLS certificates installed
- [ ] Secrets management implemented
- [ ] Input validation enabled
- [ ] Encryption configured
- [ ] Monitoring setup
- [ ] Backup procedures tested

### Post-Deployment

- [ ] Security monitoring active
- [ ] Log analysis configured
- [ ] Incident response procedures documented
- [ ] Regular security updates scheduled
- [ ] Penetration testing planned
- [ ] Compliance audit scheduled

### Ongoing Maintenance

- [ ] Regular security updates
- [ ] Log review and analysis
- [ ] Threat intelligence updates
- [ ] Security awareness training
- [ ] Incident response drills
- [ ] Vulnerability assessments

---

This security guide provides comprehensive protection for HoneyPort deployments. Regular review and updates are essential to maintain security posture.
