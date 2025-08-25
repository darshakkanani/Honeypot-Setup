# HoneyPort - Separated Architecture

## New Directory Structure

```
HoneyPort-System/
├── honeypot-engine/           # Core honeypot system
│   ├── src/
│   │   ├── core/             # Honeypot engine
│   │   ├── ai/               # AI detection & behavior
│   │   ├── logging/          # Attack logging system
│   │   └── blockchain/       # Blockchain integration
│   ├── config/
│   ├── logs/
│   ├── data/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── run_honeypot.py
│
├── honeypot-website/          # Attractive decoy website
│   ├── public/               # Static website files
│   ├── templates/            # Dynamic page templates
│   ├── assets/               # Images, CSS, JS
│   ├── server.py             # Website server
│   ├── config.json
│   └── README.md
│
├── admin-dashboard/           # Management interface
│   ├── backend/              # FastAPI backend
│   │   ├── api/
│   │   ├── auth/
│   │   ├── database/
│   │   └── main.py
│   ├── frontend/             # React/Static frontend
│   │   ├── src/
│   │   ├── public/
│   │   └── package.json
│   ├── config/
│   └── run_dashboard.py
│
├── shared-services/           # Common utilities
│   ├── database/             # Shared database models
│   ├── messaging/            # Inter-service communication
│   ├── monitoring/           # System monitoring
│   └── utils/                # Common utilities
│
├── deployment/                # Deployment configs
│   ├── docker/
│   ├── kubernetes/
│   ├── nginx/
│   └── scripts/
│
└── docs/                     # Documentation
    ├── api/
    ├── deployment/
    └── architecture/
```

## Service Communication

- **Honeypot Engine**: Port 8080 (decoy services)
- **Honeypot Website**: Port 3000 (attractive website)
- **Admin Dashboard**: Port 5000 (management interface)
- **API Gateway**: Port 9000 (service coordination)
- **Database**: PostgreSQL on 5432
- **Message Queue**: Redis on 6379

## Independent Operation

Each component can run independently:
1. Honeypot engine captures attacks
2. Website serves as attractive target
3. Admin dashboard manages everything
4. Services communicate via APIs/messaging
