"""
FastAPI backend for HoneyPort dashboard
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional
import redis.asyncio as redis
import json

from .models import EventResponse, StatsResponse, AlertResponse
from .routes.events import router as events_router
from .routes.agents import router as agents_router  
from .routes.alerts import router as alerts_router
from .db import Database

logger = logging.getLogger(__name__)

# Global variables
redis_client = None
database = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global redis_client, database
    
    # Startup
    logger.info("🚀 Starting HoneyPort Dashboard API...")
    
    # Initialize Redis
    redis_client = redis.Redis(host='localhost', port=6379, db=0)
    
    # Initialize Database
    database = Database('sqlite:///dashboard.db')
    await database.initialize()
    
    logger.info("✅ Dashboard API started successfully")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Dashboard API...")
    if redis_client:
        await redis_client.close()
    if database:
        await database.cleanup()

# Create FastAPI app
app = FastAPI(
    title="HoneyPort Dashboard API",
    description="REST API for HoneyPort honeypot dashboard",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Simple authentication - in production use proper JWT validation"""
    # For demo purposes, accept any token
    return {"username": "admin"}

# Include routers
app.include_router(events_router, prefix="/api/v1/events", tags=["events"])
app.include_router(agents_router, prefix="/api/v1/agents", tags=["agents"])
app.include_router(alerts_router, prefix="/api/v1/alerts", tags=["alerts"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "HoneyPort Dashboard API", "version": "1.0.0"}

@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check Redis connection
        await redis_client.ping()
        redis_status = "healthy"
    except Exception:
        redis_status = "unhealthy"
    
    return {
        "status": "healthy",
        "services": {
            "redis": redis_status,
            "database": "healthy"
        }
    }

@app.get("/api/v1/stats", response_model=StatsResponse)
async def get_dashboard_stats(user: dict = Depends(get_current_user)):
    """Get dashboard statistics"""
    try:
        # Get stats from database
        stats = await database.get_stats()
        
        # Get real-time stats from Redis
        try:
            active_events = await redis_client.llen('processed_events')
            stats['active_events'] = active_events
        except Exception:
            stats['active_events'] = 0
        
        return StatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")

@app.get("/api/v1/live-events")
async def get_live_events(limit: int = 50, user: dict = Depends(get_current_user)):
    """Get live events from Redis"""
    try:
        # Get recent events from Redis
        events_data = await redis_client.lrange('processed_events', 0, limit - 1)
        
        events = []
        for event_json in events_data:
            try:
                event = json.loads(event_json)
                events.append(event)
            except json.JSONDecodeError:
                continue
        
        return {"events": events, "count": len(events)}
        
    except Exception as e:
        logger.error(f"Error getting live events: {e}")
        raise HTTPException(status_code=500, detail="Failed to get live events")

@app.get("/api/v1/threat-map")
async def get_threat_map(user: dict = Depends(get_current_user)):
    """Get threat map data for visualization"""
    try:
        # Get geographic distribution of threats
        geo_stats = await database.get_geographic_stats()
        
        return {"threat_map": geo_stats}
        
    except Exception as e:
        logger.error(f"Error getting threat map: {e}")
        raise HTTPException(status_code=500, detail="Failed to get threat map data")

@app.post("/api/v1/block-ip")
async def block_ip(ip_data: dict, user: dict = Depends(get_current_user)):
    """Block an IP address"""
    try:
        ip_address = ip_data.get('ip')
        reason = ip_data.get('reason', 'Manual block')
        
        if not ip_address:
            raise HTTPException(status_code=400, detail="IP address required")
        
        # Add to blocked IPs (this would integrate with firewall/iptables)
        await database.add_blocked_ip(ip_address, reason)
        
        return {"message": f"IP {ip_address} blocked successfully"}
        
    except Exception as e:
        logger.error(f"Error blocking IP: {e}")
        raise HTTPException(status_code=500, detail="Failed to block IP")

@app.get("/api/v1/blocked-ips")
async def get_blocked_ips(user: dict = Depends(get_current_user)):
    """Get list of blocked IP addresses"""
    try:
        blocked_ips = await database.get_blocked_ips()
        return {"blocked_ips": blocked_ips}
        
    except Exception as e:
        logger.error(f"Error getting blocked IPs: {e}")
        raise HTTPException(status_code=500, detail="Failed to get blocked IPs")

@app.delete("/api/v1/blocked-ips/{ip}")
async def unblock_ip(ip: str, user: dict = Depends(get_current_user)):
    """Unblock an IP address"""
    try:
        await database.remove_blocked_ip(ip)
        return {"message": f"IP {ip} unblocked successfully"}
        
    except Exception as e:
        logger.error(f"Error unblocking IP: {e}")
        raise HTTPException(status_code=500, detail="Failed to unblock IP")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
