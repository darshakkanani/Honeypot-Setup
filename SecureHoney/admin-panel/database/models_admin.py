#!/usr/bin/env python3
"""
SecureHoney Admin Panel Database Models
SQLAlchemy models specifically for the admin panel functionality
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent / 'shared-utils'))

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Text, Boolean, ForeignKey, JSON, DECIMAL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import INET, ARRAY, JSONB
from datetime import datetime, timedelta
import hashlib
import secrets
from typing import Dict, Any, List, Optional
import bcrypt

# Import shared models
from database.models import Base, Attack, AttackerProfile, AttackSession
from database.config import get_connection_string, get_sqlalchemy_config

class AdminUser(Base):
    """Administrative users for the honeypot system"""
    __tablename__ = 'admin_users'
    __table_args__ = {'schema': 'securehoney'}
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    salt = Column(String(32), nullable=False)
    role = Column(String(20), default='analyst')  # admin, analyst, viewer
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    failed_login_attempts = Column(Integer, default=0)
    account_locked_until = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sessions = relationship("AdminSession", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AdminAuditLog", back_populates="user")
    
    def set_password(self, password: str):
        """Set password with secure hashing"""
        self.salt = secrets.token_hex(16)
        self.password_hash = bcrypt.hashpw(
            password.encode('utf-8'), 
            bcrypt.gensalt()
        ).decode('utf-8')
    
    def check_password(self, password: str) -> bool:
        """Verify password"""
        return bcrypt.checkpw(
            password.encode('utf-8'),
            self.password_hash.encode('utf-8')
        )
    
    def is_locked(self) -> bool:
        """Check if account is locked"""
        if self.account_locked_until:
            return datetime.utcnow() < self.account_locked_until
        return False
    
    def lock_account(self, duration_minutes: int = 30):
        """Lock account for specified duration"""
        self.account_locked_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
        self.failed_login_attempts = 0
    
    def unlock_account(self):
        """Unlock account"""
        self.account_locked_until = None
        self.failed_login_attempts = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'is_active': self.is_active,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat(),
            'is_locked': self.is_locked()
        }

class AdminSession(Base):
    """Admin user sessions for authentication"""
    __tablename__ = 'admin_sessions'
    __table_args__ = {'schema': 'securehoney'}
    
    id = Column(Integer, primary_key=True)
    session_token = Column(String(128), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('securehoney.admin_users.id'), nullable=False)
    ip_address = Column(INET, nullable=False)
    user_agent = Column(Text)
    expires_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("AdminUser", back_populates="sessions")
    
    @classmethod
    def generate_token(cls) -> str:
        """Generate secure session token"""
        return secrets.token_urlsafe(96)
    
    def is_expired(self) -> bool:
        """Check if session is expired"""
        return datetime.utcnow() > self.expires_at
    
    def extend_session(self, hours: int = 24):
        """Extend session expiration"""
        self.expires_at = datetime.utcnow() + timedelta(hours=hours)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'ip_address': str(self.ip_address),
            'expires_at': self.expires_at.isoformat(),
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat()
        }

class AdminAuditLog(Base):
    """Audit log for admin actions"""
    __tablename__ = 'admin_audit_log'
    __table_args__ = {'schema': 'securehoney'}
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('securehoney.admin_users.id'))
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50))
    resource_id = Column(String(64))
    details = Column(JSONB)
    ip_address = Column(INET)
    user_agent = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("AdminUser", back_populates="audit_logs")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'details': self.details,
            'ip_address': str(self.ip_address) if self.ip_address else None,
            'timestamp': self.timestamp.isoformat()
        }

class SystemConfig(Base):
    """System configuration settings"""
    __tablename__ = 'system_config'
    __table_args__ = {'schema': 'securehoney'}
    
    id = Column(Integer, primary_key=True)
    config_key = Column(String(100), unique=True, nullable=False, index=True)
    config_value = Column(JSONB, nullable=False)
    config_type = Column(String(20), default='string')  # string, integer, boolean, array, object
    description = Column(Text)
    is_sensitive = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_value(self):
        """Get typed configuration value"""
        if self.config_type == 'boolean':
            return bool(self.config_value)
        elif self.config_type == 'integer':
            return int(self.config_value)
        elif self.config_type == 'array':
            return list(self.config_value)
        elif self.config_type == 'object':
            return dict(self.config_value)
        else:
            return str(self.config_value).strip('"')
    
    def set_value(self, value):
        """Set configuration value with proper typing"""
        if self.config_type == 'boolean':
            self.config_value = bool(value)
        elif self.config_type == 'integer':
            self.config_value = int(value)
        elif self.config_type == 'array':
            self.config_value = list(value)
        elif self.config_type == 'object':
            self.config_value = dict(value)
        else:
            self.config_value = str(value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'config_key': self.config_key,
            'config_value': self.config_value if not self.is_sensitive else '***REDACTED***',
            'config_type': self.config_type,
            'description': self.description,
            'is_sensitive': self.is_sensitive,
            'updated_at': self.updated_at.isoformat()
        }

class Alert(Base):
    """System alerts and notifications"""
    __tablename__ = 'alerts'
    __table_args__ = {'schema': 'securehoney'}
    
    id = Column(Integer, primary_key=True)
    alert_id = Column(String(64), unique=True, nullable=False, index=True)
    alert_type = Column(String(50), nullable=False)  # ATTACK_CAMPAIGN, HIGH_THREAT, SYSTEM_ERROR
    severity = Column(String(20), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    title = Column(String(200), nullable=False)
    description = Column(Text)
    source_ip = Column(INET)
    attack_id = Column(String(64), ForeignKey('securehoney.attacks.attack_id'))
    campaign_id = Column(String(64))
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(Integer, ForeignKey('securehoney.admin_users.id'))
    acknowledged_at = Column(DateTime)
    is_resolved = Column(Boolean, default=False)
    resolved_by = Column(Integer, ForeignKey('securehoney.admin_users.id'))
    resolved_at = Column(DateTime)
    metadata = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    acknowledger = relationship("AdminUser", foreign_keys=[acknowledged_by])
    resolver = relationship("AdminUser", foreign_keys=[resolved_by])
    
    @classmethod
    def generate_alert_id(cls) -> str:
        """Generate unique alert ID"""
        return f"ALERT_{secrets.token_hex(8).upper()}"
    
    def acknowledge(self, user_id: int):
        """Acknowledge alert"""
        self.is_acknowledged = True
        self.acknowledged_by = user_id
        self.acknowledged_at = datetime.utcnow()
    
    def resolve(self, user_id: int):
        """Resolve alert"""
        self.is_resolved = True
        self.resolved_by = user_id
        self.resolved_at = datetime.utcnow()
        if not self.is_acknowledged:
            self.acknowledge(user_id)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'alert_id': self.alert_id,
            'alert_type': self.alert_type,
            'severity': self.severity,
            'title': self.title,
            'description': self.description,
            'source_ip': str(self.source_ip) if self.source_ip else None,
            'attack_id': self.attack_id,
            'campaign_id': self.campaign_id,
            'is_acknowledged': self.is_acknowledged,
            'acknowledged_by': self.acknowledged_by,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'is_resolved': self.is_resolved,
            'resolved_by': self.resolved_by,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat()
        }

class AdminDatabaseManager:
    """Database manager specifically for admin panel operations"""
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or get_connection_string()
        self.engine = create_engine(self.database_url, **get_sqlalchemy_config())
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()
    
    def close_session(self, session):
        """Close database session"""
        session.close()
    
    # User Management
    def create_user(self, username: str, email: str, password: str, role: str = 'analyst') -> AdminUser:
        """Create new admin user"""
        session = self.get_session()
        try:
            user = AdminUser(
                username=username,
                email=email,
                role=role
            )
            user.set_password(password)
            
            session.add(user)
            session.commit()
            session.refresh(user)
            
            # Log user creation
            self.log_admin_action(
                session, None, 'USER_CREATED', 'admin_user', str(user.id),
                {'username': username, 'email': email, 'role': role}
            )
            
            return user
            
        finally:
            self.close_session(session)
    
    def authenticate_user(self, username: str, password: str, ip_address: str, user_agent: str = None) -> Optional[AdminSession]:
        """Authenticate user and create session"""
        session = self.get_session()
        try:
            user = session.query(AdminUser).filter(
                AdminUser.username == username,
                AdminUser.is_active == True
            ).first()
            
            if not user:
                return None
            
            # Check if account is locked
            if user.is_locked():
                return None
            
            # Verify password
            if not user.check_password(password):
                user.failed_login_attempts += 1
                if user.failed_login_attempts >= 5:
                    user.lock_account()
                session.commit()
                return None
            
            # Reset failed attempts on successful login
            user.failed_login_attempts = 0
            user.last_login = datetime.utcnow()
            
            # Create session
            admin_session = AdminSession(
                session_token=AdminSession.generate_token(),
                user_id=user.id,
                ip_address=ip_address,
                user_agent=user_agent,
                expires_at=datetime.utcnow() + timedelta(hours=24)
            )
            
            session.add(admin_session)
            session.commit()
            session.refresh(admin_session)
            
            # Log successful login
            self.log_admin_action(
                session, user.id, 'LOGIN_SUCCESS', 'admin_session', admin_session.session_token,
                {'ip_address': ip_address}, ip_address, user_agent
            )
            
            return admin_session
            
        finally:
            self.close_session(session)
    
    def validate_session(self, session_token: str) -> Optional[AdminUser]:
        """Validate session token and return user"""
        session = self.get_session()
        try:
            admin_session = session.query(AdminSession).filter(
                AdminSession.session_token == session_token,
                AdminSession.is_active == True
            ).first()
            
            if not admin_session or admin_session.is_expired():
                return None
            
            return admin_session.user
            
        finally:
            self.close_session(session)
    
    def logout_user(self, session_token: str):
        """Logout user by deactivating session"""
        session = self.get_session()
        try:
            admin_session = session.query(AdminSession).filter(
                AdminSession.session_token == session_token
            ).first()
            
            if admin_session:
                admin_session.is_active = False
                session.commit()
                
                # Log logout
                self.log_admin_action(
                    session, admin_session.user_id, 'LOGOUT', 'admin_session', session_token
                )
            
        finally:
            self.close_session(session)
    
    # Configuration Management
    def get_config(self, key: str) -> Any:
        """Get configuration value"""
        session = self.get_session()
        try:
            config = session.query(SystemConfig).filter(
                SystemConfig.config_key == key
            ).first()
            
            return config.get_value() if config else None
            
        finally:
            self.close_session(session)
    
    def set_config(self, key: str, value: Any, user_id: int = None, config_type: str = 'string', description: str = None):
        """Set configuration value"""
        session = self.get_session()
        try:
            config = session.query(SystemConfig).filter(
                SystemConfig.config_key == key
            ).first()
            
            if config:
                old_value = config.config_value
                config.set_value(value)
                config.updated_at = datetime.utcnow()
            else:
                config = SystemConfig(
                    config_key=key,
                    config_type=config_type,
                    description=description
                )
                config.set_value(value)
                session.add(config)
                old_value = None
            
            session.commit()
            
            # Log configuration change
            self.log_admin_action(
                session, user_id, 'CONFIG_UPDATED', 'system_config', key,
                {'old_value': old_value, 'new_value': value}
            )
            
        finally:
            self.close_session(session)
    
    # Alert Management
    def create_alert(self, alert_type: str, severity: str, title: str, description: str = None, **kwargs) -> Alert:
        """Create system alert"""
        session = self.get_session()
        try:
            alert = Alert(
                alert_id=Alert.generate_alert_id(),
                alert_type=alert_type,
                severity=severity,
                title=title,
                description=description,
                source_ip=kwargs.get('source_ip'),
                attack_id=kwargs.get('attack_id'),
                campaign_id=kwargs.get('campaign_id'),
                metadata=kwargs.get('metadata', {})
            )
            
            session.add(alert)
            session.commit()
            session.refresh(alert)
            
            return alert
            
        finally:
            self.close_session(session)
    
    def get_unresolved_alerts(self, limit: int = 100) -> List[Alert]:
        """Get unresolved alerts"""
        session = self.get_session()
        try:
            return session.query(Alert).filter(
                Alert.is_resolved == False
            ).order_by(Alert.created_at.desc()).limit(limit).all()
            
        finally:
            self.close_session(session)
    
    # Audit Logging
    def log_admin_action(self, db_session, user_id: int, action: str, resource_type: str = None, 
                        resource_id: str = None, details: Dict[str, Any] = None, 
                        ip_address: str = None, user_agent: str = None):
        """Log admin action for audit trail"""
        audit_log = AdminAuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        db_session.add(audit_log)
        db_session.commit()
    
    # Dashboard Data
    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get dashboard summary data"""
        session = self.get_session()
        try:
            from sqlalchemy import func, text
            from datetime import date, timedelta
            
            # Basic attack statistics
            total_attacks = session.query(Attack).count()
            attacks_today = session.query(Attack).filter(
                func.date(Attack.timestamp) == date.today()
            ).count()
            unique_attackers = session.query(AttackerProfile).count()
            
            # Recent high-threat attackers
            high_threat_attackers = session.query(AttackerProfile).filter(
                AttackerProfile.threat_level.in_(['HIGH', 'CRITICAL'])
            ).count()
            
            # Unresolved alerts
            unresolved_alerts = session.query(Alert).filter(
                Alert.is_resolved == False
            ).count()
            
            # System uptime (placeholder - would need actual system metrics)
            uptime = "99.9%"
            
            return {
                'total_attacks': total_attacks,
                'attacks_today': attacks_today,
                'unique_attackers': unique_attackers,
                'high_threat_attackers': high_threat_attackers,
                'unresolved_alerts': unresolved_alerts,
                'system_uptime': uptime,
                'threat_level': self._calculate_current_threat_level(session)
            }
            
        finally:
            self.close_session(session)
    
    def _calculate_current_threat_level(self, session) -> str:
        """Calculate current system threat level"""
        from sqlalchemy import func
        from datetime import datetime, timedelta
        
        # Attacks in last hour
        recent_attacks = session.query(Attack).filter(
            Attack.timestamp >= datetime.utcnow() - timedelta(hours=1)
        ).count()
        
        if recent_attacks >= 50:
            return 'CRITICAL'
        elif recent_attacks >= 20:
            return 'HIGH'
        elif recent_attacks >= 10:
            return 'MEDIUM'
        else:
            return 'LOW'

# Global admin database manager
admin_db = AdminDatabaseManager()
