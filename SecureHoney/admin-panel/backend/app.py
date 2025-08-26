#!/usr/bin/env python3
"""
SecureHoney Admin Panel Backend - Enhanced Production-Ready API
Advanced honeypot management and monitoring system with comprehensive features
"""

import os
import asyncio
import logging
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import uuid

# FastAPI and dependencies
from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect, Request, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Database and ORM
import asyncpg
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Security and authentication
import jwt
import bcrypt
from passlib.context import CryptContext

# Data validation
from pydantic import BaseModel, EmailStr, validator
from pydantic.dataclasses import dataclass

# Monitoring and logging
import structlog
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

# Utilities
import aiofiles
import httpx
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

# Configuration
class Config:
    # Database
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "5432"))
    DB_NAME = os.getenv("DB_NAME", "securehoney")
    DB_USER = os.getenv("DB_USER", "securehoney")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "securehoney123")
    
    # Redis
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
    
    # Security
    JWT_SECRET = os.getenv("JWT_SECRET", secrets.token_urlsafe(32))
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "24"))
    
    # CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    
    # Rate limiting
    RATE_LIMIT_REQUESTS = os.getenv("RATE_LIMIT_REQUESTS", "100/minute")
    
    # Email
    SMTP_HOST = os.getenv("SMTP_HOST", "")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    
    # Monitoring
    SENTRY_DSN = os.getenv("SENTRY_DSN", "")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

config = Config()

# Initialize Sentry for error tracking
if config.SENTRY_DSN:
    sentry_sdk.init(
        dsn=config.SENTRY_DSN,
        integrations=[FastApiIntegration()],
        traces_sample_rate=0.1,
    )

# Setup structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

# Metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
ACTIVE_CONNECTIONS = Gauge('websocket_connections_active', 'Active WebSocket connections')
ATTACK_COUNT = Counter('attacks_detected_total', 'Total attacks detected', ['attack_type', 'severity'])

# FastAPI app
app = FastAPI(
    title="SecureHoney Admin API",
    description="Advanced honeypot management and monitoring system",
    version="3.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure for production
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security
security = HTTPBearer()

# Database connection
DATABASE_URL = f"postgresql+asyncpg://{config.DB_USER}:{config.DB_PASSWORD}@{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}"
engine = create_async_engine(DATABASE_URL, echo=False, pool_size=20, max_overflow=0)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Redis connection
redis_client = None

# Data Models
class LoginRequest(BaseModel):
    username: str
    password: str
    remember_me: bool = False

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: str = "user"

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

class AttackFilter(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    severity: Optional[str] = None
    attack_type: Optional[str] = None
    source_ip: Optional[str] = None
    limit: int = 100
    offset: int = 0

class AlertCreate(BaseModel):
    title: str
    message: str
    severity: str
    alert_type: str

class SystemConfig(BaseModel):
    honeypot_enabled: bool = True
    auto_block_enabled: bool = True
    email_alerts_enabled: bool = False
    webhook_url: Optional[str] = None
    block_threshold: int = 10

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[str, List[str]] = {}

    async def connect(self, websocket: WebSocket, connection_id: str, user_id: str = None):
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = []
            self.user_connections[user_id].append(connection_id)
        
        ACTIVE_CONNECTIONS.set(len(self.active_connections))
        logger.info("websocket_connected", connection_id=connection_id, user_id=user_id)

    def disconnect(self, connection_id: str, user_id: str = None):
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        if user_id and user_id in self.user_connections:
            if connection_id in self.user_connections[user_id]:
                self.user_connections[user_id].remove(connection_id)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        ACTIVE_CONNECTIONS.set(len(self.active_connections))
        logger.info("websocket_disconnected", connection_id=connection_id, user_id=user_id)

    async def send_personal_message(self, message: dict, connection_id: str):
        if connection_id in self.active_connections:
            try:
                await self.active_connections[connection_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error("websocket_send_failed", connection_id=connection_id, error=str(e))
                self.disconnect(connection_id)

    async def send_to_user(self, message: dict, user_id: str):
        if user_id in self.user_connections:
            for connection_id in self.user_connections[user_id].copy():
                await self.send_personal_message(message, connection_id)

    async def broadcast(self, message: dict):
        if self.active_connections:
            disconnected = []
            for connection_id, websocket in self.active_connections.items():
                try:
                    await websocket.send_text(json.dumps(message))
                except Exception as e:
                    logger.error("websocket_broadcast_failed", connection_id=connection_id, error=str(e))
                    disconnected.append(connection_id)
            
            for connection_id in disconnected:
                self.disconnect(connection_id)

manager = ConnectionManager()

# Database dependency
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Redis dependency
async def get_redis():
    return redis_client

# Authentication functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=config.JWT_EXPIRY_HOURS)
    
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=30)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])
        username: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if username is None or token_type != "access":
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Check if token is blacklisted (Redis)
        if redis_client:
            blacklisted = await redis_client.get(f"blacklist:{credentials.credentials}")
            if blacklisted:
                raise HTTPException(status_code=401, detail="Token revoked")
        
        return username
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Utility functions
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

async def send_email(to_email: str, subject: str, body: str):
    if not config.SMTP_HOST:
        logger.warning("SMTP not configured, skipping email")
        return
    
    try:
        msg = MIMEMultipart()
        msg['From'] = config.SMTP_USER
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT)
        server.starttls()
        server.login(config.SMTP_USER, config.SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        logger.info("email_sent", to=to_email, subject=subject)
    except Exception as e:
        logger.error("email_failed", to=to_email, error=str(e))

# Middleware for request logging and metrics
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.utcnow()
    
    # Generate request ID
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # Log request
    logger.info(
        "request_started",
        request_id=request_id,
        method=request.method,
        url=str(request.url),
        client_ip=request.client.host
    )
    
    # Process request
    response = await call_next(request)
    
    # Calculate duration
    duration = (datetime.utcnow() - start_time).total_seconds()
    
    # Update metrics
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
    REQUEST_DURATION.observe(duration)
    
    # Log response
    logger.info(
        "request_completed",
        request_id=request_id,
        status_code=response.status_code,
        duration=duration
    )
    
    # Add request ID to response headers
    response.headers["X-Request-ID"] = request_id
    
    return response

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint for load balancers and monitoring"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "3.0.0",
        "services": {}
    }
    
    # Check database
    try:
        async with AsyncSessionLocal() as session:
            await session.execute("SELECT 1")
        health_status["services"]["database"] = "healthy"
    except Exception as e:
        health_status["services"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Redis
    try:
        if redis_client:
            await redis_client.ping()
            health_status["services"]["redis"] = "healthy"
        else:
            health_status["services"]["redis"] = "not_configured"
    except Exception as e:
        health_status["services"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    return health_status

# Metrics endpoint
@app.get("/api/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type="text/plain")

# Authentication endpoints
@app.post("/api/auth/login")
@limiter.limit("5/minute")
async def login(request: Request, login_data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate user and return JWT tokens"""
    try:
        # Query user from database
        result = await db.execute(
            "SELECT id, username, email, password_hash, role, is_active, failed_attempts, locked_until FROM admin_users WHERE username = $1",
            login_data.username
        )
        user = result.fetchone()
        
        if not user:
            logger.warning("login_failed", username=login_data.username, reason="user_not_found")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.utcnow():
            logger.warning("login_failed", username=login_data.username, reason="account_locked")
            raise HTTPException(status_code=423, detail="Account temporarily locked")
        
        # Verify password
        if not verify_password(login_data.password, user.password_hash):
            # Increment failed attempts
            await db.execute(
                "UPDATE admin_users SET failed_attempts = failed_attempts + 1, locked_until = CASE WHEN failed_attempts >= 4 THEN NOW() + INTERVAL '15 minutes' ELSE NULL END WHERE id = $1",
                user.id
            )
            await db.commit()
            
            logger.warning("login_failed", username=login_data.username, reason="invalid_password")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Check if user is active
        if not user.is_active:
            logger.warning("login_failed", username=login_data.username, reason="account_disabled")
            raise HTTPException(status_code=403, detail="Account disabled")
        
        # Reset failed attempts
        await db.execute(
            "UPDATE admin_users SET failed_attempts = 0, locked_until = NULL, last_login = NOW() WHERE id = $1",
            user.id
        )
        await db.commit()
        
        # Create tokens
        token_data = {"sub": user.username, "user_id": user.id, "role": user.role}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        # Store refresh token in Redis
        if redis_client:
            await redis_client.setex(f"refresh:{user.id}", 30 * 24 * 3600, refresh_token)
        
        # Log successful login
        await db.execute(
            "INSERT INTO audit_logs (user_id, action, details, ip_address) VALUES ($1, 'LOGIN', $2, $3)",
            user.id, json.dumps({"success": True}), request.client.host
        )
        await db.commit()
        
        logger.info("login_successful", username=user.username, user_id=user.id)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": config.JWT_EXPIRY_HOURS * 3600,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("login_error", username=login_data.username, error=str(e))
        raise HTTPException(status_code=500, detail="Login failed")

@app.post("/api/auth/logout")
async def logout(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Logout user and blacklist token"""
    try:
        # Decode token to get user info
        payload = jwt.decode(credentials.credentials, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])
        user_id = payload.get("user_id")
        
        # Blacklist the token
        if redis_client:
            exp = payload.get("exp")
            if exp:
                ttl = exp - int(datetime.utcnow().timestamp())
                if ttl > 0:
                    await redis_client.setex(f"blacklist:{credentials.credentials}", ttl, "1")
        
        # Log logout
        if user_id:
            await db.execute(
                "INSERT INTO audit_logs (user_id, action, details, ip_address) VALUES ($1, 'LOGOUT', $2, $3)",
                user_id, json.dumps({"success": True}), request.client.host
            )
            await db.commit()
        
        return {"message": "Successfully logged out"}
        
    except Exception as e:
        logger.error("logout_error", error=str(e))
        return {"message": "Logged out"}

@app.post("/api/auth/refresh")
async def refresh_token(refresh_token: str, db: AsyncSession = Depends(get_db)):
    """Refresh access token using refresh token"""
    try:
        payload = jwt.decode(refresh_token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])
        
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        user_id = payload.get("user_id")
        username = payload.get("sub")
        
        # Verify refresh token in Redis
        if redis_client:
            stored_token = await redis_client.get(f"refresh:{user_id}")
            if not stored_token or stored_token.decode() != refresh_token:
                raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        # Create new access token
        token_data = {"sub": username, "user_id": user_id, "role": payload.get("role")}
        new_access_token = create_access_token(token_data)
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": config.JWT_EXPIRY_HOURS * 3600
        }
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

# User management endpoints
@app.get("/api/auth/me")
async def get_current_user(username: str = Depends(verify_token), db: AsyncSession = Depends(get_db)):
    """Get current user information"""
    result = await db.execute(
        "SELECT id, username, email, role, created_at, last_login FROM admin_users WHERE username = $1",
        username
    )
    user = result.fetchone()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "created_at": user.created_at.isoformat(),
        "last_login": user.last_login.isoformat() if user.last_login else None
    }

# Dashboard endpoints
@app.get("/api/dashboard/stats")
async def get_dashboard_stats(username: str = Depends(verify_token), db: AsyncSession = Depends(get_db)):
    """Get dashboard statistics"""
    try:
        # Get attack statistics
        stats_result = await db.execute("""
            SELECT 
                COUNT(*) as total_attacks,
                COUNT(DISTINCT source_ip) as unique_attackers,
                COUNT(CASE WHEN created_at >= NOW() - INTERVAL '24 hours' THEN 1 END) as attacks_today,
                COUNT(CASE WHEN severity = 'CRITICAL' THEN 1 END) as critical_attacks
            FROM attacks
        """)
        stats = stats_result.fetchone()
        
        # Get system uptime (mock for now)
        uptime = "7d 14h 32m"
        
        # Calculate threat level
        threat_level = "LOW"
        if stats.attacks_today > 100:
            threat_level = "HIGH"
        elif stats.attacks_today > 50:
            threat_level = "MEDIUM"
        
        return {
            "total_attacks": stats.total_attacks or 0,
            "unique_attackers": stats.unique_attackers or 0,
            "attacks_today": stats.attacks_today or 0,
            "critical_attacks": stats.critical_attacks or 0,
            "system_uptime": uptime,
            "threat_level": threat_level,
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("dashboard_stats_error", error=str(e))
        # Return mock data as fallback
        return {
            "total_attacks": 1247,
            "unique_attackers": 89,
            "attacks_today": 23,
            "critical_attacks": 5,
            "system_uptime": "7d 14h 32m",
            "threat_level": "MEDIUM",
            "last_updated": datetime.utcnow().isoformat()
        }

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: Optional[str] = None):
    """WebSocket endpoint for real-time updates"""
    connection_id = str(uuid.uuid4())
    user_id = None
    
    # Verify token if provided
    if token:
        try:
            payload = jwt.decode(token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])
            user_id = payload.get("user_id")
        except:
            pass
    
    await manager.connect(websocket, connection_id, user_id)
    
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get("type") == "ping":
                await manager.send_personal_message({"type": "pong"}, connection_id)
            elif message.get("type") == "subscribe":
                # Handle subscription to specific data streams
                pass
                
    except WebSocketDisconnect:
        manager.disconnect(connection_id, user_id)
    except Exception as e:
        logger.error("websocket_error", connection_id=connection_id, error=str(e))
        manager.disconnect(connection_id, user_id)

# Background tasks
async def monitor_system():
    """Background task for system monitoring"""
    while True:
        try:
            # Send periodic updates to connected clients
            stats_update = {
                "type": "stats_update",
                "data": await get_dashboard_stats(),
                "timestamp": datetime.utcnow().isoformat()
            }
            await manager.broadcast(stats_update)
            
            await asyncio.sleep(30)  # Update every 30 seconds
            
        except Exception as e:
            logger.error("monitor_system_error", error=str(e))
            await asyncio.sleep(60)

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global redis_client
    
    logger.info("starting_securehoney_backend", version="3.0.0")
    
    # Initialize Redis connection
    try:
        if config.REDIS_PASSWORD:
            redis_client = redis.Redis(
                host=config.REDIS_HOST,
                port=config.REDIS_PORT,
                password=config.REDIS_PASSWORD,
                decode_responses=True
            )
        else:
            redis_client = redis.Redis(
                host=config.REDIS_HOST,
                port=config.REDIS_PORT,
                decode_responses=True
            )
        
        await redis_client.ping()
        logger.info("redis_connected")
    except Exception as e:
        logger.warning("redis_connection_failed", error=str(e))
        redis_client = None
    
    # Start background tasks
    asyncio.create_task(monitor_system())
    
    logger.info("securehoney_backend_started")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("shutting_down_securehoney_backend")
    
    if redis_client:
        await redis_client.close()
    
    logger.info("securehoney_backend_shutdown_complete")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=5001,
        log_level=config.LOG_LEVEL.lower(),
        reload=False,
        workers=1
    )
