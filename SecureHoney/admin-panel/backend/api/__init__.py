"""
API module initialization
"""

from fastapi import APIRouter
from . import auth, dashboard, attacks, websocket

# Create main API router
api_router = APIRouter()

# Include all API routers
api_router.include_router(auth.router)
api_router.include_router(dashboard.router)
api_router.include_router(attacks.router)
api_router.include_router(websocket.router)

__all__ = ["api_router"]
