# HoneyPort API Documentation

Comprehensive API reference for the HoneyPort AI-powered honeypot system.

## Table of Contents

- [Authentication](#authentication)
- [Core Honeypot API](#core-honeypot-api)
- [AI & Machine Learning API](#ai--machine-learning-api)
- [Blockchain Logging API](#blockchain-logging-api)
- [Dashboard API](#dashboard-api)
- [Monitoring API](#monitoring-api)
- [Configuration API](#configuration-api)
- [Webhook API](#webhook-api)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)

## Authentication

### Basic Authentication
All API endpoints require HTTP Basic Authentication:

```bash
curl -u admin:password https://localhost:5000/api/endpoint
```

### API Key Authentication
Alternatively, use API key in header:

```bash
curl -H "X-API-Key: your-api-key" https://localhost:5000/api/endpoint
```

### JWT Token Authentication
For programmatic access:

```bash
# Get token
curl -X POST https://localhost:5000/api/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}'

# Use token
curl -H "Authorization: Bearer <token>" https://localhost:5000/api/endpoint
```

## Core Honeypot API

### Get Honeypot Status

**GET** `/api/honeypot/status`

Returns current honeypot operational status.

```bash
curl -u admin:password https://localhost:5000/api/honeypot/status
```

**Response:**
```json
{
  "status": "running",
  "uptime": 3600,
  "listeners": [
    {"port": 80, "protocol": "HTTP", "active": true},
    {"port": 22, "protocol": "SSH", "active": true}
  ],
  "total_connections": 1234,
  "active_sessions": 5
}
```

### Get Attack Statistics

**GET** `/api/honeypot/stats`

Query parameters:
- `period` (optional): `1h`, `24h`, `7d`, `30d` (default: `24h`)
- `attack_type` (optional): Filter by attack type
- `source_ip` (optional): Filter by source IP

```bash
curl -u admin:password "https://localhost:5000/api/honeypot/stats?period=24h"
```

**Response:**
```json
{
  "period": "24h",
  "total_attacks": 456,
  "unique_attackers": 123,
  "attack_types": {
    "sql_injection": 234,
    "xss": 123,
    "brute_force": 99
  },
  "top_countries": [
    {"country": "CN", "count": 145},
    {"country": "RU", "count": 89}
  ],
  "threat_levels": {
    "high": 45,
    "medium": 234,
    "low": 177
  }
}
```

### Get Attack Events

**GET** `/api/honeypot/events`

Query parameters:
- `limit` (optional): Number of events (default: 100, max: 1000)
- `offset` (optional): Pagination offset
- `since` (optional): ISO timestamp
- `threat_level` (optional): `high`, `medium`, `low`
- `attack_type` (optional): Filter by attack type

```bash
curl -u admin:password "https://localhost:5000/api/honeypot/events?limit=50&threat_level=high"
```

**Response:**
```json
{
  "events": [
    {
      "id": "evt_123456",
      "timestamp": "2024-01-15T10:30:00Z",
      "source_ip": "192.168.1.100",
      "source_port": 12345,
      "destination_port": 80,
      "protocol": "HTTP",
      "attack_type": "sql_injection",
      "payload": "' OR 1=1--",
      "threat_level": "high",
      "confidence": 0.95,
      "geolocation": {
        "country": "CN",
        "city": "Beijing",
        "latitude": 39.9042,
        "longitude": 116.4074
      },
      "session_id": "sess_789",
      "blockchain_hash": "0x1234..."
    }
  ],
  "total": 1234,
  "has_more": true
}
```

### Control Honeypot Services

**POST** `/api/honeypot/control`

```bash
curl -X POST -u admin:password \
  -H "Content-Type: application/json" \
  -d '{"action":"restart","service":"http_listener"}' \
  https://localhost:5000/api/honeypot/control
```

**Request Body:**
```json
{
  "action": "start|stop|restart",
  "service": "all|http_listener|ssh_listener|tcp_listener"
}
```

## AI & Machine Learning API

### Get AI Model Status

**GET** `/api/ai/status`

```bash
curl -u admin:password https://localhost:5000/api/ai/status
```

**Response:**
```json
{
  "ai_enabled": true,
  "models": {
    "threat_predictor": {
      "status": "loaded",
      "version": "v1.2.3",
      "accuracy": 0.94,
      "last_trained": "2024-01-10T15:30:00Z"
    },
    "attacker_profiler": {
      "status": "loaded",
      "version": "v1.1.0",
      "accuracy": 0.89,
      "last_trained": "2024-01-08T12:00:00Z"
    }
  },
  "continuous_learning": {
    "enabled": true,
    "last_retrain": "2024-01-12T08:00:00Z",
    "next_retrain": "2024-01-19T08:00:00Z"
  }
}
```

### Analyze Attack with AI

**POST** `/api/ai/analyze`

```bash
curl -X POST -u admin:password \
  -H "Content-Type: application/json" \
  -d '{
    "source_ip": "192.168.1.100",
    "attack_type": "sql_injection",
    "payload": "admin\' OR 1=1--",
    "session_data": {...}
  }' \
  https://localhost:5000/api/ai/analyze
```

**Response:**
```json
{
  "analysis_id": "analysis_123",
  "threat_level": 0.85,
  "confidence": 0.92,
  "attacker_profile": {
    "sophistication": "intermediate",
    "automation_level": "high",
    "persistence": "medium",
    "geographic_risk": "high"
  },
  "recommended_response": {
    "strategy": "cautious",
    "engagement_level": 0.3,
    "delay_response": true,
    "fake_success_rate": 0.1
  },
  "explanation": {
    "key_factors": [
      "High payload complexity",
      "Automated tool signatures",
      "High-risk geographic origin"
    ],
    "reasoning": "Advanced SQL injection attempt with automated tool characteristics..."
  }
}
```

### Get AI Insights

**GET** `/api/ai/insights`

Query parameters:
- `period` (optional): Time period for insights
- `insight_type` (optional): `trends`, `patterns`, `anomalies`

```bash
curl -u admin:password "https://localhost:5000/api/ai/insights?period=7d&insight_type=trends"
```

**Response:**
```json
{
  "insights": [
    {
      "type": "trend",
      "title": "Increasing SQL Injection Attempts",
      "description": "40% increase in SQL injection attacks over the past week",
      "confidence": 0.87,
      "severity": "medium",
      "recommendations": [
        "Increase monitoring for SQL injection patterns",
        "Update response strategies for database-related attacks"
      ]
    }
  ],
  "model_performance": {
    "accuracy": 0.94,
    "precision": 0.91,
    "recall": 0.96,
    "f1_score": 0.93
  }
}
```

### Retrain AI Models

**POST** `/api/ai/retrain`

```bash
curl -X POST -u admin:password \
  -H "Content-Type: application/json" \
  -d '{"models":["threat_predictor"],"force":false}' \
  https://localhost:5000/api/ai/retrain
```

**Request Body:**
```json
{
  "models": ["threat_predictor", "attacker_profiler"],
  "force": false,
  "training_data_days": 30
}
```

### Explain AI Decision

**POST** `/api/ai/explain`

```bash
curl -X POST -u admin:password \
  -H "Content-Type: application/json" \
  -d '{"analysis_id":"analysis_123"}' \
  https://localhost:5000/api/ai/explain
```

**Response:**
```json
{
  "explanation": {
    "prediction": 0.85,
    "confidence": 0.92,
    "method": "SHAP",
    "feature_importance": {
      "payload_complexity": 0.34,
      "request_frequency": 0.28,
      "geographic_risk": 0.21,
      "user_agent_risk": 0.17
    },
    "explanation_text": "The AI assessed this as a HIGH threat (score: 0.850). Key factors: payload complexity increases threat level; request frequency increases threat level; geographic risk increases threat level.",
    "visualization_data": {
      "shap_values": [0.34, 0.28, 0.21, 0.17],
      "feature_names": ["payload_complexity", "request_frequency", "geographic_risk", "user_agent_risk"]
    }
  }
}
```

## Blockchain Logging API

### Get Blockchain Status

**GET** `/api/blockchain/status`

```bash
curl -u admin:password https://localhost:5000/api/blockchain/status
```

**Response:**
```json
{
  "blockchain_enabled": true,
  "chain_length": 1234,
  "last_block_hash": "0x1234567890abcdef...",
  "last_block_time": "2024-01-15T10:30:00Z",
  "integrity_status": "valid",
  "smart_contract": {
    "deployed": true,
    "address": "0xabcdef1234567890...",
    "network": "ethereum",
    "gas_used": 45000
  }
}
```

### Verify Blockchain Integrity

**POST** `/api/blockchain/verify`

```bash
curl -X POST -u admin:password https://localhost:5000/api/blockchain/verify
```

**Response:**
```json
{
  "verification_id": "verify_123",
  "status": "valid",
  "blocks_verified": 1234,
  "verification_time": 2.34,
  "integrity_score": 1.0,
  "issues_found": [],
  "last_verified": "2024-01-15T10:35:00Z"
}
```

### Get Blockchain Logs

**GET** `/api/blockchain/logs`

Query parameters:
- `limit` (optional): Number of logs (default: 100)
- `block_hash` (optional): Specific block hash
- `since_block` (optional): Starting block number

```bash
curl -u admin:password "https://localhost:5000/api/blockchain/logs?limit=50"
```

**Response:**
```json
{
  "logs": [
    {
      "block_hash": "0x1234...",
      "block_number": 1234,
      "transaction_hash": "0x5678...",
      "timestamp": "2024-01-15T10:30:00Z",
      "event_id": "evt_123456",
      "data_hash": "0x9abc...",
      "gas_used": 21000
    }
  ],
  "total_blocks": 1234,
  "chain_integrity": "valid"
}
```

## Dashboard API

### Get Dashboard Data

**GET** `/api/dashboard/data`

```bash
curl -u admin:password https://localhost:5000/api/dashboard/data
```

**Response:**
```json
{
  "summary": {
    "total_attacks_today": 234,
    "unique_attackers_today": 89,
    "threat_level_avg": 0.67,
    "system_health": "healthy"
  },
  "recent_attacks": [...],
  "attack_trends": {
    "hourly": [12, 15, 8, 23, ...],
    "by_type": {...},
    "by_country": {...}
  },
  "ai_insights": [...],
  "blockchain_status": {...}
}
```

### Export Attack Data

**GET** `/api/dashboard/export`

Query parameters:
- `format`: `json`, `csv`, `xml`
- `period`: Time period for export
- `include_blockchain`: Include blockchain verification data

```bash
curl -u admin:password "https://localhost:5000/api/dashboard/export?format=json&period=7d" > attacks.json
```

## Monitoring API

### Get System Health

**GET** `/api/monitoring/health`

```bash
curl https://localhost:5000/api/monitoring/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "uptime": 86400,
  "components": {
    "honeypot_engine": "healthy",
    "ai_engine": "healthy",
    "blockchain": "healthy",
    "database": "healthy",
    "dashboard": "healthy"
  },
  "metrics": {
    "cpu_usage": 45.2,
    "memory_usage": 67.8,
    "disk_usage": 23.1,
    "network_connections": 156
  }
}
```

### Get Metrics

**GET** `/api/monitoring/metrics`

Returns Prometheus-formatted metrics:

```bash
curl https://localhost:5000/api/monitoring/metrics
```

**Response:**
```
# HELP honeyport_attacks_total Total number of attacks detected
# TYPE honeyport_attacks_total counter
honeyport_attacks_total{attack_type="sql_injection"} 234
honeyport_attacks_total{attack_type="xss"} 123

# HELP honeyport_threat_level Current threat level
# TYPE honeyport_threat_level gauge
honeyport_threat_level 0.67
```

## Configuration API

### Get Configuration

**GET** `/api/config`

```bash
curl -u admin:password https://localhost:5000/api/config
```

### Update Configuration

**PUT** `/api/config`

```bash
curl -X PUT -u admin:password \
  -H "Content-Type: application/json" \
  -d '{
    "ai": {
      "enabled": true,
      "continuous_learning": true
    },
    "alerts": {
      "severity_threshold": "high"
    }
  }' \
  https://localhost:5000/api/config
```

## Webhook API

### Register Webhook

**POST** `/api/webhooks`

```bash
curl -X POST -u admin:password \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-server.com/webhook",
    "events": ["high_threat_attack", "system_alert"],
    "secret": "your-webhook-secret"
  }' \
  https://localhost:5000/api/webhooks
```

### Webhook Payload Example

When events occur, HoneyPort sends POST requests to registered webhooks:

```json
{
  "event": "high_threat_attack",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "attack_id": "att_123456",
    "source_ip": "192.168.1.100",
    "threat_level": 0.95,
    "attack_type": "sql_injection",
    "ai_analysis": {...}
  },
  "signature": "sha256=..."
}
```

## Error Handling

All API endpoints return standard HTTP status codes:

- `200 OK` - Success
- `201 Created` - Resource created
- `400 Bad Request` - Invalid request
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

**Error Response Format:**
```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "The request payload is invalid",
    "details": {
      "field": "attack_type",
      "issue": "must be one of: sql_injection, xss, brute_force"
    }
  },
  "request_id": "req_123456",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Rate Limiting

API endpoints are rate limited:

- **General API**: 1000 requests per hour per IP
- **Analysis endpoints**: 100 requests per hour per API key
- **Export endpoints**: 10 requests per hour per user

Rate limit headers are included in responses:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642248000
```

## SDK Examples

### Python SDK

```python
import requests
from datetime import datetime

class HoneyPortAPI:
    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.auth = (username, password)
    
    def get_attack_stats(self, period='24h'):
        response = requests.get(
            f"{self.base_url}/api/honeypot/stats",
            params={'period': period},
            auth=self.auth
        )
        return response.json()
    
    def analyze_attack(self, attack_data):
        response = requests.post(
            f"{self.base_url}/api/ai/analyze",
            json=attack_data,
            auth=self.auth
        )
        return response.json()

# Usage
api = HoneyPortAPI('https://localhost:5000', 'admin', 'password')
stats = api.get_attack_stats('7d')
print(f"Total attacks: {stats['total_attacks']}")
```

### JavaScript SDK

```javascript
class HoneyPortAPI {
    constructor(baseUrl, apiKey) {
        this.baseUrl = baseUrl;
        this.apiKey = apiKey;
    }
    
    async getAttackEvents(limit = 100) {
        const response = await fetch(`${this.baseUrl}/api/honeypot/events?limit=${limit}`, {
            headers: {
                'X-API-Key': this.apiKey
            }
        });
        return response.json();
    }
    
    async getAIInsights(period = '24h') {
        const response = await fetch(`${this.baseUrl}/api/ai/insights?period=${period}`, {
            headers: {
                'X-API-Key': this.apiKey
            }
        });
        return response.json();
    }
}

// Usage
const api = new HoneyPortAPI('https://localhost:5000', 'your-api-key');
api.getAttackEvents(50).then(events => {
    console.log(`Retrieved ${events.events.length} attack events`);
});
```

## WebSocket API

For real-time updates, HoneyPort provides WebSocket endpoints:

### Connect to Real-time Feed

```javascript
const ws = new WebSocket('wss://localhost:5000/ws/realtime?token=your-jwt-token');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    if (data.type === 'new_attack') {
        console.log('New attack detected:', data.attack);
    }
};

// Subscribe to specific events
ws.send(JSON.stringify({
    action: 'subscribe',
    events: ['high_threat_attack', 'ai_insight', 'blockchain_update']
}));
```

### WebSocket Message Types

- `new_attack` - New attack detected
- `threat_level_change` - System threat level changed
- `ai_insight` - New AI insight generated
- `blockchain_update` - Blockchain state updated
- `system_alert` - System health alert

---

**Note**: Replace `localhost:5000` with your actual HoneyPort instance URL. Ensure proper SSL/TLS configuration for production deployments.
