"""
Attack model for storing and analyzing attack data
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
import uuid
from typing import List, Optional, Dict, Any

from ..core.database import Base

class Attack(Base):
    """Attack model for storing honeypot attack data"""
    
    __tablename__ = "attacks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_ip = Column(INET, nullable=False, index=True)
    target_port = Column(Integer, nullable=False, index=True)
    attack_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), nullable=False, index=True)
    confidence_score = Column(Float, default=0.0)
    blocked = Column(Boolean, default=False, index=True)
    
    # Location data
    country = Column(String(100), index=True)
    country_code = Column(String(2))
    city = Column(String(100))
    latitude = Column(Float)
    longitude = Column(Float)
    
    # Attack details
    payload_size = Column(Integer)
    session_duration = Column(Integer)  # in seconds
    user_agent = Column(Text)
    request_headers = Column(JSON)
    response_code = Column(Integer)
    raw_payload = Column(Text)
    details = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @classmethod
    async def create(cls, db: AsyncSession, attack_data: Dict[str, Any]) -> "Attack":
        """Create new attack record"""
        attack = cls(**attack_data)
        db.add(attack)
        await db.commit()
        await db.refresh(attack)
        return attack
    
    @classmethod
    async def get_by_id(cls, db: AsyncSession, attack_id: str) -> Optional["Attack"]:
        """Get attack by ID"""
        result = await db.execute(select(cls).where(cls.id == attack_id))
        return result.scalar_one_or_none()
    
    @classmethod
    async def get_recent_by_ip(cls, db: AsyncSession, source_ip: str, limit: int = 10) -> List["Attack"]:
        """Get recent attacks from specific IP"""
        result = await db.execute(
            select(cls)
            .where(cls.source_ip == source_ip)
            .order_by(cls.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
    
    async def block(self, db: AsyncSession):
        """Mark attack as blocked"""
        self.blocked = True
        self.updated_at = datetime.utcnow()
        await db.commit()
    
    async def unblock(self, db: AsyncSession):
        """Mark attack as unblocked"""
        self.blocked = False
        self.updated_at = datetime.utcnow()
        await db.commit()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert attack to dictionary"""
        return {
            "id": str(self.id),
            "source_ip": str(self.source_ip),
            "target_port": self.target_port,
            "attack_type": self.attack_type,
            "severity": self.severity,
            "confidence_score": float(self.confidence_score) if self.confidence_score else 0.0,
            "blocked": self.blocked,
            "location": {
                "country": self.country,
                "country_code": self.country_code,
                "city": self.city,
                "coordinates": {
                    "latitude": float(self.latitude) if self.latitude else None,
                    "longitude": float(self.longitude) if self.longitude else None
                }
            },
            "payload_size": self.payload_size,
            "session_duration": self.session_duration,
            "user_agent": self.user_agent,
            "request_headers": self.request_headers or {},
            "response_code": self.response_code,
            "details": self.details or {},
            "timestamp": self.created_at.isoformat()
        }
