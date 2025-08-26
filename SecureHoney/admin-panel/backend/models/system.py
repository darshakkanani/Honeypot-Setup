"""
System metrics and monitoring models
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
import uuid
from typing import List, Optional, Dict, Any

from ..core.database import Base

class SystemMetrics(Base):
    """System metrics model for monitoring system health"""
    
    __tablename__ = "system_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cpu_usage = Column(Float, nullable=False)
    memory_usage = Column(Float, nullable=False)
    disk_usage = Column(Float, nullable=False)
    network_in = Column(Integer, default=0)
    network_out = Column(Integer, default=0)
    active_connections = Column(Integer, default=0)
    uptime_seconds = Column(Integer, default=0)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    @classmethod
    async def create(cls, db: AsyncSession, metrics_data: Dict[str, Any]) -> "SystemMetrics":
        """Create new system metrics record"""
        metrics = cls(**metrics_data)
        db.add(metrics)
        await db.commit()
        await db.refresh(metrics)
        return metrics
    
    @classmethod
    async def get_latest(cls, db: AsyncSession) -> Optional["SystemMetrics"]:
        """Get latest system metrics"""
        result = await db.execute(
            select(cls).order_by(cls.timestamp.desc()).limit(1)
        )
        return result.scalar_one_or_none()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary"""
        return {
            "id": str(self.id),
            "cpu_usage": float(self.cpu_usage),
            "memory_usage": float(self.memory_usage),
            "disk_usage": float(self.disk_usage),
            "network": {
                "bytes_in": self.network_in,
                "bytes_out": self.network_out
            },
            "active_connections": self.active_connections,
            "uptime_seconds": self.uptime_seconds,
            "timestamp": self.timestamp.isoformat()
        }

class ServiceStatus(Base):
    """Service status model for tracking honeypot services"""
    
    __tablename__ = "service_status"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_name = Column(String(50), nullable=False, index=True)
    status = Column(String(20), nullable=False)  # running, stopped, error
    port = Column(Integer)
    last_check = Column(DateTime, default=datetime.utcnow)
    error_message = Column(Text)
    metadata = Column(JSON)
    
    @classmethod
    async def update_status(cls, db: AsyncSession, service_name: str, status: str, 
                           port: int = None, error_message: str = None, metadata: Dict = None):
        """Update service status"""
        from sqlalchemy import text
        
        await db.execute(text("""
            INSERT INTO service_status (service_name, status, port, last_check, error_message, metadata)
            VALUES (:service_name, :status, :port, NOW(), :error_message, :metadata)
            ON CONFLICT (service_name) DO UPDATE SET
                status = :status,
                port = :port,
                last_check = NOW(),
                error_message = :error_message,
                metadata = :metadata
        """), {
            "service_name": service_name,
            "status": status,
            "port": port,
            "error_message": error_message,
            "metadata": metadata
        })
        await db.commit()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert service status to dictionary"""
        return {
            "id": str(self.id),
            "service_name": self.service_name,
            "status": self.status,
            "port": self.port,
            "last_check": self.last_check.isoformat(),
            "error_message": self.error_message,
            "metadata": self.metadata or {}
        }
