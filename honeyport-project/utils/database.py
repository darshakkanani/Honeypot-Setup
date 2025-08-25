#!/usr/bin/env python3
"""
Database utilities and ORM models for HoneyPort
"""

import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Boolean, Text, JSON, DECIMAL, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class AttackLog(Base):
    __tablename__ = 'attack_logs'
    __table_args__ = {'schema': 'honeyport'}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=func.now())
    source_ip = Column(INET, nullable=False)
    source_port = Column(Integer)
    destination_port = Column(Integer, nullable=False)
    protocol = Column(String(10), nullable=False)
    attack_type = Column(String(50))
    payload = Column(Text)
    user_agent = Column(Text)
    http_method = Column(String(10))
    url_path = Column(Text)
    headers = Column(JSONB)
    session_id = Column(String(255))
    geolocation = Column(JSONB)
    threat_level = Column(DECIMAL(3, 2), default=0.5)
    blockchain_hash = Column(String(66))
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

class AttackSession(Base):
    __tablename__ = 'attack_sessions'
    __table_args__ = {'schema': 'honeyport'}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(255), unique=True, nullable=False)
    source_ip = Column(INET, nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False, default=func.now())
    end_time = Column(DateTime(timezone=True))
    duration_seconds = Column(Integer)
    request_count = Column(Integer, default=0)
    unique_urls = Column(Integer, default=0)
    attack_types = Column(ARRAY(Text))
    user_agents = Column(ARRAY(Text))
    geolocation = Column(JSONB)
    sophistication_score = Column(DECIMAL(3, 2), default=0.5)
    automation_level = Column(DECIMAL(3, 2), default=0.5)
    persistence_score = Column(DECIMAL(3, 2), default=0.5)
    status = Column(String(20), default='active')
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

class AIInsight(Base):
    __tablename__ = 'ai_insights'
    __table_args__ = {'schema': 'honeyport'}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    attack_log_id = Column(UUID(as_uuid=True))
    session_id = Column(String(255))
    insight_type = Column(String(50), nullable=False)
    confidence_score = Column(DECIMAL(3, 2))
    prediction = Column(JSONB)
    model_version = Column(String(50))
    processing_time_ms = Column(Integer)
    created_at = Column(DateTime(timezone=True), default=func.now())

class SecurityAlert(Base):
    __tablename__ = 'security_alerts'
    __table_args__ = {'schema': 'honeyport'}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    source_ip = Column(INET)
    attack_log_id = Column(UUID(as_uuid=True))
    session_id = Column(String(255))
    metadata = Column(JSONB)
    acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(String(100))
    acknowledged_at = Column(DateTime(timezone=True))
    resolved = Column(Boolean, default=False)
    resolved_by = Column(String(100))
    resolved_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=func.now())

class DatabaseManager:
    """Database connection and session management"""
    
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def get_session(self) -> Session:
        """Get database session"""
        return self.SessionLocal()
    
    def create_tables(self):
        """Create all tables"""
        Base.metadata.create_all(bind=self.engine)
    
    def close(self):
        """Close database connection"""
        self.engine.dispose()

class AttackLogRepository:
    """Repository for attack log operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def create_attack_log(self, **kwargs) -> AttackLog:
        """Create new attack log entry"""
        with self.db_manager.get_session() as session:
            attack_log = AttackLog(**kwargs)
            session.add(attack_log)
            session.commit()
            session.refresh(attack_log)
            return attack_log
    
    def get_recent_attacks(self, limit: int = 100) -> List[AttackLog]:
        """Get recent attack logs"""
        with self.db_manager.get_session() as session:
            return session.query(AttackLog).order_by(AttackLog.timestamp.desc()).limit(limit).all()
    
    def get_attacks_by_ip(self, source_ip: str) -> List[AttackLog]:
        """Get attacks from specific IP"""
        with self.db_manager.get_session() as session:
            return session.query(AttackLog).filter(AttackLog.source_ip == source_ip).all()
    
    def get_high_threat_attacks(self, threshold: float = 0.7) -> List[AttackLog]:
        """Get high threat level attacks"""
        with self.db_manager.get_session() as session:
            return session.query(AttackLog).filter(AttackLog.threat_level >= threshold).all()

# Global database manager instance
db_manager: Optional[DatabaseManager] = None

def init_database(database_url: str) -> DatabaseManager:
    """Initialize database connection"""
    global db_manager
    db_manager = DatabaseManager(database_url)
    db_manager.create_tables()
    return db_manager

def get_db_manager() -> DatabaseManager:
    """Get global database manager"""
    if db_manager is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return db_manager
