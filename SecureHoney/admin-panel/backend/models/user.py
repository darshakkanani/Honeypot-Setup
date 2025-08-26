"""
User model for authentication and authorization
"""

from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timedelta
import uuid
from typing import List, Optional, Dict, Any

from ..core.database import Base

class User(Base):
    """User model for admin panel authentication"""
    
    __tablename__ = "admin_users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    salt = Column(String(255), nullable=True)
    role = Column(String(20), nullable=False, default="user")
    is_active = Column(Boolean, default=True)
    failed_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    preferences = Column(JSON, default=dict)
    
    def get_permissions(self) -> List[str]:
        """Get user permissions based on role"""
        role_permissions = {
            "admin": ["read", "write", "delete", "admin", "manage_users", "system_config"],
            "moderator": ["read", "write", "manage_attacks", "view_reports"],
            "analyst": ["read", "write", "analyze_attacks", "view_reports"],
            "user": ["read", "view_dashboard"]
        }
        return role_permissions.get(self.role, ["read"])
    
    @classmethod
    async def get_by_username(cls, db: AsyncSession, username: str) -> Optional["User"]:
        """Get user by username"""
        result = await db.execute(select(cls).where(cls.username == username))
        return result.scalar_one_or_none()
    
    @classmethod
    async def get_by_email(cls, db: AsyncSession, email: str) -> Optional["User"]:
        """Get user by email"""
        result = await db.execute(select(cls).where(cls.email == email))
        return result.scalar_one_or_none()
    
    @classmethod
    async def get_by_id(cls, db: AsyncSession, user_id: str) -> Optional["User"]:
        """Get user by ID"""
        result = await db.execute(select(cls).where(cls.id == user_id))
        return result.scalar_one_or_none()
    
    @classmethod
    async def create(cls, db: AsyncSession, user_data: Dict[str, Any]) -> "User":
        """Create new user"""
        user = cls(**user_data)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    
    async def increment_failed_attempts(self, db: AsyncSession):
        """Increment failed login attempts and lock if necessary"""
        self.failed_attempts += 1
        
        # Lock account after 5 failed attempts for 15 minutes
        if self.failed_attempts >= 5:
            self.locked_until = datetime.utcnow() + timedelta(minutes=15)
        
        await db.commit()
    
    async def reset_failed_attempts(self, db: AsyncSession):
        """Reset failed login attempts"""
        self.failed_attempts = 0
        self.locked_until = None
        await db.commit()
    
    async def update_last_login(self, db: AsyncSession):
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()
        await db.commit()
    
    async def update_password(self, db: AsyncSession, password_hash: str):
        """Update user password"""
        self.password_hash = password_hash
        self.updated_at = datetime.utcnow()
        await db.commit()
    
    async def log_action(self, db: AsyncSession, action: str, details: Dict[str, Any], ip_address: str = None):
        """Log user action to audit log"""
        from sqlalchemy import text
        
        await db.execute(text("""
            INSERT INTO audit_logs (user_id, action, details, ip_address, created_at)
            VALUES (:user_id, :action, :details, :ip_address, NOW())
        """), {
            "user_id": self.id,
            "action": action,
            "details": details,
            "ip_address": ip_address
        })
        await db.commit()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary"""
        return {
            "id": str(self.id),
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "is_active": self.is_active,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "created_at": self.created_at.isoformat(),
            "permissions": self.get_permissions(),
            "preferences": self.preferences or {}
        }
