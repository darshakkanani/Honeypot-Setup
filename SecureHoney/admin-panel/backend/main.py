#!/usr/bin/env python3
"""
SecureHoney Admin Panel Backend
FastAPI backend for honeypot management and monitoring
"""

from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import jwt
import bcrypt
import json
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
import os
from database_api import router as database_router

# Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "securehoney-admin-secret-key-2024")
JWT_ALGORITHM = "HS256"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = bcrypt.hashpw("securehoney2024".encode(), bcrypt.gensalt())

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="SecureHoney Admin API",
    description="Advanced honeypot management and monitoring system",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include database API routes
app.include_router(database_router)

# Security
security = HTTPBearer()

# Data models
class LoginRequest(BaseModel):
    username: str
    password: str

class User(BaseModel):
    username: str
    role: str
    permissions: List[str]

class AttackEvent(BaseModel):
    id: str
    timestamp: str
    source_ip: str
    target_port: int
    attack_type: str
    severity: str
    confidence: float
    location: Dict[str, Any]
    details: Dict[str, Any]

class SystemStats(BaseModel):
    total_attacks: int
    attacks_today: int
    unique_attackers: int
    blocked_ips: int
    system_uptime: str
    threat_level: str

# WebSocket manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        if self.active_connections:
            disconnected = []
            for connection in self.active_connections:
                try:
                    await connection.send_text(json.dumps(message))
                except:
                    disconnected.append(connection)
            
            # Remove disconnected connections
            for conn in disconnected:
                self.disconnect(conn)

manager = ConnectionManager()

# Authentication functions
def create_jwt_token(username: str) -> str:
    payload = {
        "username": username,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username = payload.get("username")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Mock data generators
def get_mock_stats() -> SystemStats:
    return SystemStats(
        total_attacks=1247,
        attacks_today=89,
        unique_attackers=156,
        blocked_ips=45,
        system_uptime="7d 14h 32m",
        threat_level="MEDIUM"
    )

def get_mock_attacks() -> List[AttackEvent]:
    import random
    attacks = []
    attack_types = ["SSH_BRUTE_FORCE", "HTTP_INJECTION", "PORT_SCAN", "MALWARE_UPLOAD", "DDoS"]
    severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    
    for i in range(20):
        attacks.append(AttackEvent(
            id=f"attack_{i+1}",
            timestamp=datetime.now().isoformat(),
            source_ip=f"192.168.{random.randint(1,255)}.{random.randint(1,255)}",
            target_port=random.choice([22, 80, 443, 8080, 3389]),
            attack_type=random.choice(attack_types),
            severity=random.choice(severities),
            confidence=round(random.uniform(0.6, 0.99), 2),
            location={"country": "Unknown", "city": "Unknown"},
            details={"payload_size": random.randint(100, 5000)}
        ))
    return attacks

# API Routes
@app.post("/api/auth/login")
async def login(request: LoginRequest):
    if request.username == ADMIN_USERNAME:
        if bcrypt.checkpw(request.password.encode(), ADMIN_PASSWORD_HASH):
            token = create_jwt_token(request.username)
            return {
                "access_token": token,
                "token_type": "bearer",
                "user": {
                    "username": request.username,
                    "role": "admin",
                    "permissions": ["read", "write", "admin"]
                }
            }
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/api/auth/me")
async def get_current_user(username: str = Depends(verify_token)):
    return User(
        username=username,
        role="admin",
        permissions=["read", "write", "admin"]
    )

@app.get("/api/dashboard/stats")
async def get_dashboard_stats(username: str = Depends(verify_token)):
    return get_mock_stats()

@app.get("/api/attacks")
async def get_attacks(
    limit: int = 50,
    severity: Optional[str] = None,
    username: str = Depends(verify_token)
):
    attacks = get_mock_attacks()
    if severity:
        attacks = [a for a in attacks if a.severity == severity]
    return {"attacks": attacks[:limit], "total": len(attacks)}

@app.get("/api/alerts")
async def get_alerts(username: str = Depends(verify_token)):
    return {
        "alerts": [
            {
                "id": "alert_1",
                "type": "HIGH_ATTACK_VOLUME",
                "severity": "HIGH",
                "message": "Unusual attack volume detected from 192.168.1.100",
                "timestamp": datetime.now().isoformat(),
                "status": "active"
            }
        ]
    }

@app.get("/api/system/health")
async def get_system_health(username: str = Depends(verify_token)):
    return {
        "status": "healthy",
        "services": {
            "honeypot_engine": "running",
            "ai_analyzer": "running",
            "blockchain": "synced",
            "database": "connected"
        },
        "resources": {
            "cpu_usage": 45.2,
            "memory_usage": 62.1,
            "disk_usage": 23.8
        }
    }

@app.get("/api/blockchain/status")
async def get_blockchain_status(username: str = Depends(verify_token)):
    return {
        "total_blocks": 1247,
        "chain_valid": True,
        "pending_transactions": 3,
        "chain_size_mb": 15.7,
        "recent_blocks": [
            {
                "index": 1247,
                "hash": "0x7d865e959b2466918c9863afca942d0fb89d7c9ac0c99bafc3749504ded97730",
                "timestamp": datetime.now().isoformat(),
                "transactions": 5,
                "miner": "SecureHoney"
            }
        ]
    }

@app.get("/api/analytics/trends")
async def get_analytics_trends(
    period: str = "24h",
    username: str = Depends(verify_token)
):
    return {
        "period": period,
        "attack_trends": [
            {"hour": i, "attacks": __import__("random").randint(5, 25)} 
            for i in range(24)
        ],
        "attack_types": {
            "SSH_BRUTE_FORCE": 45,
            "HTTP_INJECTION": 32,
            "PORT_SCAN": 28,
            "MALWARE_UPLOAD": 15,
            "DDoS": 8
        },
        "top_countries": [
            {"country": "Russia", "attacks": 89},
            {"country": "China", "attacks": 67},
            {"country": "USA", "attacks": 45}
        ]
    }

@app.post("/api/export/attacks")
async def export_attacks(
    format: str = "json",
    username: str = Depends(verify_token)
):
    attacks = get_mock_attacks()
    if format == "csv":
        # Return CSV format
        return {"message": "CSV export ready", "download_url": "/downloads/attacks.csv"}
    return {"attacks": attacks}

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Send periodic updates
            await asyncio.sleep(5)
            update = {
                "type": "stats_update",
                "data": get_mock_stats().dict(),
                "timestamp": datetime.now().isoformat()
            }
            await manager.broadcast(update)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Background task for monitoring
@app.on_event("startup")
async def startup_event():
    logger.info("SecureHoney Admin Panel Backend started")
    
    # Start background monitoring
    asyncio.create_task(monitor_attacks())

async def monitor_attacks():
    """Background task to monitor for new attacks"""
    while True:
        await asyncio.sleep(10)
        
        # Simulate new attack detection
        if __import__("random").random() < 0.3:  # 30% chance
            new_attack = {
                "type": "new_attack",
                "data": {
                    "id": f"attack_{datetime.now().timestamp()}",
                    "source_ip": f"192.168.{__import__('random').randint(1,255)}.{__import__('random').randint(1,255)}",
                    "attack_type": __import__("random").choice(["SSH_BRUTE_FORCE", "HTTP_INJECTION", "PORT_SCAN"]),
                    "severity": __import__("random").choice(["LOW", "MEDIUM", "HIGH"]),
                    "timestamp": datetime.now().isoformat()
                }
            }
            await manager.broadcast(new_attack)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001, log_level="info")
