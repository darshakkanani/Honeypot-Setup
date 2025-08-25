# SecureHoney - Advanced Honeypot System

A completely separated, production-ready honeypot system with independent admin panel and honeypot components.

## 🏗️ Clean Architecture

```
SecureHoney/
├── admin-panel/           # Complete admin management system
│   ├── backend/          # FastAPI backend
│   ├── frontend/         # React TypeScript frontend  
│   ├── database/         # Data storage
│   └── config/           # Admin configuration
│
├── honeypot-system/      # Core honeypot detection
│   ├── engine/           # Attack detection engine
│   ├── decoy-site/       # Attractive target website
│   ├── ai-analyzer/      # AI threat analysis
│   └── blockchain/       # Immutable logging
│
├── shared-utils/         # Common utilities
│   ├── logging/          # Centralized logging
│   ├── security/         # Security utilities
│   └── monitoring/       # System monitoring
│
└── deployment/           # Deployment configs
    ├── docker/           # Container setup
    ├── kubernetes/       # K8s manifests
    └── scripts/          # Deployment scripts
```

## 🚀 Quick Start

### Complete System
```bash
cd SecureHoney
./deploy.sh
```

### Individual Components
```bash
# Admin Panel Only
cd admin-panel && ./start.sh

# Honeypot System Only  
cd honeypot-system && ./start.sh
```

## 🔗 Access Points

- **Admin Panel**: http://localhost:5000
- **Honeypot Website**: http://localhost:8080
- **API Documentation**: http://localhost:5000/docs

## 🛡️ Features

- **Total Separation**: Independent systems with clean interfaces
- **Modern UI**: Professional React admin dashboard
- **AI Analysis**: Advanced threat detection and classification
- **Blockchain Logging**: Immutable attack records
- **Real-time Monitoring**: Live attack feeds and alerts
- **Production Ready**: Docker, Kubernetes, and monitoring
