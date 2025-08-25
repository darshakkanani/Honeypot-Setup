# HoneyPort - AI-Powered Honeypot with Blockchain Logging

An advanced, enterprise-grade honeypot system featuring AI-powered dynamic behavior adaptation and blockchain-secured immutable logging for enhanced security research and threat detection.

## 🚀 Features

### Core AI & Blockchain Capabilities
- **AI-Powered Dynamic Behavior**: Machine learning-driven adaptive responses based on attacker patterns
- **Blockchain Secure Logging**: Immutable, tamper-proof attack logs with cryptographic verification
- **Real-time Anomaly Detection**: AI-based detection of sophisticated and unusual attack patterns
- **Adaptive Response Engine**: Dynamic honeypot behavior modification to maximize attacker engagement
- **Intelligent Attack Classification**: ML-powered categorization and severity assessment

### Advanced Security Features
- **Multi-Protocol Listeners**: HTTP, SSH, TCP with intelligent attack detection
- **Behavioral Analytics**: Pattern recognition for brute force, reconnaissance, and advanced attacks
- **Real-time Dashboard**: Modern web interface with blockchain verification and AI insights
- **Decoy Operations**: Realistic fake services (WordPress, phpMyAdmin, cPanel) with AI-driven responses
- **Secure Alert System**: Multi-channel alerting with rate limiting and severity-based filtering

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   HoneyPort     │    │   AI Behavior   │    │    Dashboard    │
│    Engine       │───▶│    Engine       │───▶│   (FastAPI)     │
│                 │    │                 │    │                 │
│ • HTTP Listener │    │ • ML Models     │    │ • Real-time UI  │
│ • Attack Parser │    │ • Anomaly Det.  │    │ • AI Insights   │
│ • Session Mgr   │    │ • Adaptation    │    │ • Blockchain    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 ▼
                    ┌─────────────────────────┐
                    │   Blockchain Logger     │
                    │                         │
                    │ • Immutable Logs        │
                    │ • Cryptographic Proof   │
                    │ • Chain Verification    │
                    └─────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+ with pip
- 4GB+ RAM recommended
- Network access for AI model downloads (optional)

### Installation

1. **Clone and Setup**
```bash
git clone <repository-url>
cd honeyport-project
```

2. **Install Dependencies**
```bash
# Install Python dependencies
pip install -r requirements.txt

# Create AI models directory
mkdir -p ai_models
```

3. **Configure Settings**
Edit `config.yaml` for your environment:
```yaml
network:
  honeypot_port: 8888
  bind_address: "0.0.0.0"

ai:
  enabled: true
  models_path: "ai_models/"

blockchain:
  enabled: true
  difficulty: 4

dashboard:
  host: "127.0.0.1"
  port: 8080
  admin_username: "admin"
  admin_password: "honeyport2024"
```

4. **Start Services**
```bash
# Start main honeypot engine
python main.py

# In another terminal, start dashboard
python run_dashboard.py
```

5. **Access Dashboard**
- **Dashboard**: http://localhost:8080 (admin/honeyport2024)
- **Honeypot**: http://localhost:8888 (for attackers)

## 📋 Configuration

### Main Configuration (`config.yaml`)
```yaml
network:
  honeypot_port: 8888
  bind_address: "0.0.0.0"

ai:
  enabled: true
  models_path: "ai_models/"
  behavior_model:
    adaptation_threshold: 0.7
  anomaly_detection:
    sensitivity: 0.8

blockchain:
  enabled: true
  difficulty: 4
  mining_reward: 1.0
  encryption:
    enabled: true
    algorithm: "AES-256-GCM"

dashboard:
  host: "127.0.0.1"
  port: 8080
  admin_username: "admin"
  admin_password: "honeyport2024"

alerts:
  enabled: true
  severity_threshold: "medium"
  rate_limit: 10
  email:
    enabled: false
    smtp_server: "smtp.gmail.com"
    smtp_port: 587
  webhook:
    enabled: false
    url: "https://hooks.slack.com/your-webhook"
```

### AI Behavior Patterns
```yaml
behavior_templates:
  aggressive:
    delay_range: [0.1, 0.5]
    error_rate: 0.8
    fake_success_rate: 0.1
  
  enticing:
    delay_range: [0.5, 1.5]
    error_rate: 0.3
    fake_success_rate: 0.4
  
  realistic:
    delay_range: [1.0, 3.0]
    error_rate: 0.6
    fake_success_rate: 0.2
```

## 🔧 Development

### Local Development Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Start services individually
python main.py                    # Main honeypot engine
python run_dashboard.py          # Dashboard interface
python perfect_demo.py           # Demo with fake panels
```

### Testing Attack Scenarios
```bash
# Test SQL injection
curl "http://localhost:8888/admin?id=1' OR 1=1--"

# Test XSS
curl "http://localhost:8888/search?q=<script>alert('xss')</script>"

# Test directory traversal
curl "http://localhost:8888/files?path=../../../etc/passwd"

# Test brute force
for i in {1..10}; do
  curl -X POST "http://localhost:8888/wp-admin" \
    -d "username=admin&password=pass$i"
done
```

## 📊 Monitoring & AI Features

### Real-time Dashboard
- **Live Attack Feed**: Real-time display of incoming attacks
- **AI Behavior Tracking**: Current honeypot behavior mode and adaptations
- **Blockchain Verification**: Chain integrity status and verification
- **Attack Statistics**: Comprehensive metrics and visualizations

### AI-Powered Features
- **Dynamic Behavior**: Automatic adaptation based on attacker patterns
- **Anomaly Detection**: ML-based identification of unusual activities
- **Response Optimization**: AI-driven response timing and content
- **Pattern Recognition**: Advanced attack classification and correlation

### Blockchain Security
- **Immutable Logs**: Tamper-proof attack event storage
- **Cryptographic Verification**: Chain integrity validation
- **Secure Export**: Verified log export with proof of authenticity
- **Mining Protection**: Proof-of-work secured log blocks

## 🛡️ Security Considerations

### Deployment Security
- **Network Isolation**: Deploy honeypot in isolated network segments
- **Dashboard Protection**: Secure admin access with strong authentication
- **Blockchain Security**: Encrypted log storage with cryptographic verification
- **AI Model Security**: Protect trained models from tampering

### Operational Security
- **Regular AI Training**: Update models with new attack patterns
- **Blockchain Backup**: Regular export of verified blockchain data
- **Incident Response**: Automated alerting for high-severity events
- **Legal Compliance**: Ensure honeypot deployment follows local regulations

## 📚 API Documentation

### Dashboard API
```bash
# Get honeypot statistics
curl -u admin:honeyport2024 "http://localhost:8080/api/stats"

# Get recent attack events
curl -u admin:honeyport2024 "http://localhost:8080/api/events?limit=50"

# Verify blockchain integrity
curl -u admin:honeyport2024 "http://localhost:8080/api/blockchain/verify"

# Get AI insights
curl -u admin:honeyport2024 "http://localhost:8080/api/ai/insights"

# Retrain AI models
curl -X POST -u admin:honeyport2024 "http://localhost:8080/api/ai/retrain"

# Export logs
curl -u admin:honeyport2024 "http://localhost:8080/api/export/logs?format=json"
```

### AI Behavior API
```python
# Example: Analyze attacker session
from core.ai_behavior import AIBehaviorEngine

ai_engine = AIBehaviorEngine(config)
session_data = {
    'requests': [...],
    'duration': 300,
    'source_ip': '192.168.1.100'
}

analysis = ai_engine.analyze_attacker_behavior(session_data)
print(f"Recommended behavior: {analysis['recommendation']}")
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This system is designed for research, education, and authorized security testing purposes only. Users are responsible for ensuring compliance with all applicable laws and regulations. The authors assume no liability for misuse of this software.

## 🆘 Support

- **Documentation**: See `docs/` directory for detailed guides
- **Issues**: Report bugs and feature requests via GitHub Issues
- **Security**: Report security vulnerabilities privately to security@yourcompany.com

---

**Made with ❤️ for the cybersecurity community**
