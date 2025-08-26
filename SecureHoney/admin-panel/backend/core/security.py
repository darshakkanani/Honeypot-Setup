"""
Security utilities for authentication and authorization
"""

import jwt
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
import structlog

from .config import config

logger = structlog.get_logger()
security = HTTPBearer()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=config.JWT_EXPIRY_HOURS)
    
    to_encode.update({
        "exp": expire,
        "type": "access",
        "iat": datetime.utcnow(),
        "jti": secrets.token_urlsafe(16)  # JWT ID for tracking
    })
    
    return jwt.encode(to_encode, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)

def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create a JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=30)
    
    to_encode.update({
        "exp": expire,
        "type": "refresh",
        "iat": datetime.utcnow(),
        "jti": secrets.token_urlsafe(16)
    })
    
    return jwt.encode(to_encode, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Verify JWT token and return username"""
    try:
        payload = jwt.decode(
            credentials.credentials, 
            config.JWT_SECRET, 
            algorithms=[config.JWT_ALGORITHM]
        )
        
        username: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if username is None or token_type != "access":
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # TODO: Check if token is blacklisted in Redis
        # This would require Redis dependency injection
        
        return username
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def validate_password(password: str) -> bool:
    """Validate password against security policy"""
    if len(password) < config.MIN_PASSWORD_LENGTH:
        return False
    
    if config.REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
        return False
    
    if config.REQUIRE_LOWERCASE and not any(c.islower() for c in password):
        return False
    
    if config.REQUIRE_NUMBERS and not any(c.isdigit() for c in password):
        return False
    
    if config.REQUIRE_SPECIAL_CHARS and not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        return False
    
    return True

def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token"""
    return secrets.token_urlsafe(length)

def check_permissions(required_permissions: list, user_permissions: list) -> bool:
    """Check if user has required permissions"""
    return all(perm in user_permissions for perm in required_permissions)

class PermissionChecker:
    """Permission checker dependency"""
    
    def __init__(self, required_permissions: list):
        self.required_permissions = required_permissions
    
    def __call__(self, username: str = Depends(verify_token)) -> str:
        # TODO: Get user permissions from database
        # For now, assume admin users have all permissions
        return username

# Common permission checkers
require_admin = PermissionChecker(["admin"])
require_read = PermissionChecker(["read"])
require_write = PermissionChecker(["write"])
require_delete = PermissionChecker(["delete"])
