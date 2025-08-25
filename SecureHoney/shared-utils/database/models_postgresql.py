#!/usr/bin/env python3
"""
SecureHoney PostgreSQL Models with Custom Types
Enhanced SQLAlchemy models using PostgreSQL custom data types
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, DECIMAL, ARRAY, JSON
from sqlalchemy.dialects.postgresql import INET, ENUM, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from sqlalchemy.types import TypeDecorator, VARCHAR
from datetime import datetime
from typing import Optional, Dict, Any, List
import json

Base = declarative_base()

# Custom PostgreSQL Enum Types
attack_severity_enum = ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='attack_severity', schema='securehoney')
threat_level_enum = ENUM('UNKNOWN', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='threat_level', schema='securehoney')
attack_type_enum = ENUM(
    'PORT_SCAN', 'BRUTE_FORCE', 'SQL_INJECTION', 'XSS', 'MALWARE_UPLOAD',
    'CREDENTIAL_THEFT', 'COMMAND_INJECTION', 'DIRECTORY_TRAVERSAL', 'DDOS',
    'RECONNAISSANCE', 'EXPLOITATION', 'PERSISTENCE', 'PRIVILEGE_ESCALATION',
    'LATERAL_MOVEMENT', 'EXFILTRATION', 'UNKNOWN',
    name='attack_type', schema='securehoney'
)
service_type_enum = ENUM(
    'SSH', 'HTTP', 'HTTPS', 'FTP', 'TELNET', 'SMTP', 'POP3', 'IMAP',
    'DNS', 'MYSQL', 'POSTGRESQL', 'REDIS', 'MONGODB', 'ELASTICSEARCH', 'CUSTOM',
    name='service_type', schema='securehoney'
)
interaction_type_enum = ENUM(
    'CONNECTION', 'LOGIN_ATTEMPT', 'COMMAND_EXECUTION', 'FILE_UPLOAD',
    'FILE_DOWNLOAD', 'DATA_EXTRACTION', 'MALWARE_DEPLOYMENT',
    'CONFIGURATION_CHANGE', 'PRIVILEGE_ESCALATION', 'LATERAL_MOVEMENT',
    name='interaction_type', schema='securehoney'
)
skill_level_enum = ENUM(
    'SCRIPT_KIDDIE', 'INTERMEDIATE', 'ADVANCED', 'EXPERT', 'NATION_STATE',
    name='skill_level', schema='securehoney'
)
analysis_status_enum = ENUM(
    'PENDING', 'IN_PROGRESS', 'COMPLETED', 'FAILED', 'QUARANTINED',
    name='analysis_status', schema='securehoney'
)
metric_type_enum = ENUM(
    'ATTACK_RATE', 'CPU_USAGE', 'MEMORY_USAGE', 'DISK_USAGE',
    'NETWORK_TRAFFIC', 'CONNECTION_COUNT', 'RESPONSE_TIME',
    'ERROR_RATE', 'THREAT_SCORE',
    name='metric_type', schema='securehoney'
)

# Custom Type for Hash Values
class HashType(TypeDecorator):
    """Custom type for hash values with validation"""
    impl = VARCHAR
    
    def __init__(self, hash_type='sha256'):
        self.hash_type = hash_type
        if hash_type == 'sha256':
            super().__init__(64)
        elif hash_type == 'md5':
            super().__init__(32)
        else:
            super().__init__(64)

class AttackSession(Base):
    """Attack session model with PostgreSQL custom types"""
    __tablename__ = 'attack_sessions'
    
    session_id = Column(String(64), primary_key=True)
    source_ip = Column(INET, nullable=False, index=True)
    start_time = Column(DateTime, default=func.now())
    end_time = Column(DateTime)
    duration_seconds = Column(Integer)
    total_attacks = Column(Integer, default=0)
    session_fingerprint = Column(String(64))
    threat_score = Column(Integer, default=0)
    session_metadata = Column(JSON)
    
    # Relationships
    attacks = relationship("Attack", back_populates="session")

class Attack(Base):
    """Enhanced attack model with PostgreSQL custom types"""
    __tablename__ = 'attacks'
    
    id = Column(Integer, primary_key=True)
    attack_id = Column(String(64), unique=True, nullable=False)
    session_id = Column(String(64), nullable=True, index=True)
    timestamp = Column(DateTime, default=func.now(), index=True)
    source_ip = Column(INET, nullable=False, index=True)
    target_port = Column(Integer, nullable=False)
    attack_type = Column(attack_type_enum, nullable=False)
    severity = Column(attack_severity_enum, nullable=False)
    confidence = Column(DECIMAL(3, 2), default=0.5)
    payload = Column(Text)
    payload_size = Column(Integer)
    payload_hash = Column(HashType('sha256'))
    attack_signatures = Column(ARRAY(String))
    blocked = Column(Boolean, default=False)
    honeypot_response = Column(Text)
    
    # Relationships
    session = relationship("AttackSession", back_populates="attacks")
    interactions = relationship("HoneypotInteraction", back_populates="attack")

class AttackerProfile(Base):
    """Enhanced attacker profile with PostgreSQL custom types"""
    __tablename__ = 'attacker_profiles'
    
    id = Column(Integer, primary_key=True)
    source_ip = Column(INET, unique=True, nullable=False, index=True)
    first_seen = Column(DateTime, default=func.now())
    last_seen = Column(DateTime, default=func.now())
    total_attacks = Column(Integer, default=0)
    unique_sessions = Column(Integer, default=0)
    threat_level = Column(threat_level_enum, default='UNKNOWN')
    skill_level = Column(skill_level_enum, default='SCRIPT_KIDDIE')
    reputation_score = Column(Integer, default=0)
    preferred_ports = Column(ARRAY(Integer))
    attack_patterns = Column(JSON)
    behavioral_patterns = Column(JSON)
    threat_intelligence = Column(JSON)
    notes = Column(Text)

class HoneypotInteraction(Base):
    """Honeypot interaction model with service types"""
    __tablename__ = 'honeypot_interactions'
    
    id = Column(Integer, primary_key=True)
    attack_id = Column(String(64), nullable=True, index=True)
    timestamp = Column(DateTime, default=func.now())
    service_type = Column(service_type_enum, nullable=False)
    interaction_type = Column(interaction_type_enum, nullable=False)
    username_attempted = Column(String(255))
    password_attempted = Column(String(255))
    command_executed = Column(Text)
    file_uploaded = Column(Text)
    file_hash = Column(HashType('sha256'))
    http_method = Column(String(10))
    http_path = Column(Text)
    http_headers = Column(JSON)
    response_code = Column(Integer)
    interaction_success = Column(Boolean, default=False)
    data_extracted = Column(JSON)
    
    # Relationships
    attack = relationship("Attack", back_populates="interactions")

class MalwareAnalysis(Base):
    """Malware analysis model with enhanced tracking"""
    __tablename__ = 'malware_analysis'
    
    id = Column(Integer, primary_key=True)
    file_hash = Column(HashType('sha256'), unique=True, nullable=False)
    file_name = Column(String(255))
    file_size = Column(Integer)
    file_type = Column(String(100))
    upload_timestamp = Column(DateTime, default=func.now())
    source_ip = Column(INET)
    attack_id = Column(String(64))
    malware_family = Column(String(100))
    threat_level = Column(threat_level_enum, default='UNKNOWN')
    analysis_status = Column(analysis_status_enum, default='PENDING')
    analysis_results = Column(JSON)
    sandbox_report = Column(JSON)
    yara_matches = Column(ARRAY(String))
    behavioral_indicators = Column(JSON)

class SystemMetrics(Base):
    """System metrics with typed metrics"""
    __tablename__ = 'system_metrics'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=func.now())
    metric_type = Column(metric_type_enum, nullable=False)
    metric_value = Column(DECIMAL(10, 4), nullable=False)
    metric_unit = Column(String(50))
    component = Column(String(100))
    additional_data = Column(JSON)

class GeolocationData(Base):
    """Geolocation data model"""
    __tablename__ = 'geolocation_data'
    
    id = Column(Integer, primary_key=True)
    ip_address = Column(INET, unique=True, nullable=False, index=True)
    country = Column(String(100))
    country_code = Column(String(2), index=True)
    region = Column(String(100))
    city = Column(String(100))
    latitude = Column(DECIMAL(10, 8))
    longitude = Column(DECIMAL(11, 8))
    timezone = Column(String(50))
    isp = Column(String(200))
    organization = Column(String(200))
    asn = Column(String(50))
    is_proxy = Column(Boolean, default=False)
    is_tor = Column(Boolean, default=False)
    is_vpn = Column(Boolean, default=False)
    last_updated = Column(DateTime, default=func.now())

class AttackCampaign(Base):
    """Attack campaign tracking"""
    __tablename__ = 'attack_campaigns'
    
    id = Column(Integer, primary_key=True)
    campaign_id = Column(String(64), unique=True, nullable=False)
    name = Column(String(200))
    description = Column(Text)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    attack_type = Column(attack_type_enum)
    target_ports = Column(ARRAY(Integer))
    source_ips = Column(ARRAY(INET))
    campaign_fingerprint = Column(String(64))
    threat_level = Column(threat_level_enum, default='MEDIUM')
    attribution = Column(String(200))
    indicators_of_compromise = Column(JSON)
    mitigation_recommendations = Column(ARRAY(String))

class ThreatIntelligence(Base):
    """Threat intelligence data"""
    __tablename__ = 'threat_intelligence'
    
    id = Column(Integer, primary_key=True)
    indicator = Column(String(255), unique=True, nullable=False, index=True)
    indicator_type = Column(String(50))  # IP, DOMAIN, HASH, URL
    threat_type = Column(String(100))
    malware_family = Column(String(100))
    campaign_name = Column(String(200))
    attribution = Column(String(200))
    confidence_score = Column(DECIMAL(3, 2))
    first_seen = Column(DateTime)
    last_seen = Column(DateTime)
    tags = Column(ARRAY(String))
    description = Column(Text)
    source = Column(String(100))
    created_at = Column(DateTime, default=func.now())

class PostgreSQLDatabaseManager:
    """Enhanced database manager for PostgreSQL with custom types"""
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or "postgresql://postgres:securehoney@localhost:5432/securehoney"
        self.engine = create_engine(self.database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def create_tables(self):
        """Create all tables"""
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()
    
    def close_session(self, session):
        """Close database session"""
        session.close()
    
    def insert_attack_with_types(self, attack_data: Dict[str, Any]) -> str:
        """Insert attack using PostgreSQL custom types"""
        session = self.get_session()
        try:
            attack = Attack(
                attack_id=attack_data['attack_id'],
                session_id=attack_data.get('session_id'),
                source_ip=attack_data['source_ip'],
                target_port=attack_data['target_port'],
                attack_type=attack_data['attack_type'],
                severity=attack_data['severity'],
                confidence=attack_data.get('confidence', 0.5),
                payload=attack_data.get('payload'),
                payload_size=len(attack_data.get('payload', '')),
                payload_hash=attack_data.get('payload_hash'),
                attack_signatures=attack_data.get('signatures', []),
                blocked=attack_data.get('blocked', False),
                honeypot_response=attack_data.get('response')
            )
            
            session.add(attack)
            session.commit()
            return attack.attack_id
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            self.close_session(session)
    
    def get_attacks_by_severity(self, severity: str) -> List[Dict[str, Any]]:
        """Get attacks filtered by severity using enum"""
        session = self.get_session()
        try:
            attacks = session.query(Attack).filter(
                Attack.severity == severity
            ).order_by(Attack.timestamp.desc()).all()
            
            return [
                {
                    'attack_id': attack.attack_id,
                    'timestamp': attack.timestamp.isoformat(),
                    'source_ip': str(attack.source_ip),
                    'target_port': attack.target_port,
                    'attack_type': attack.attack_type,
                    'severity': attack.severity,
                    'confidence': float(attack.confidence) if attack.confidence else 0.0
                }
                for attack in attacks
            ]
            
        finally:
            self.close_session(session)
    
    def get_threat_actors_by_level(self, threat_level: str) -> List[Dict[str, Any]]:
        """Get threat actors by threat level"""
        session = self.get_session()
        try:
            profiles = session.query(AttackerProfile).filter(
                AttackerProfile.threat_level == threat_level
            ).order_by(AttackerProfile.reputation_score.desc()).all()
            
            return [
                {
                    'source_ip': str(profile.source_ip),
                    'threat_level': profile.threat_level,
                    'skill_level': profile.skill_level,
                    'reputation_score': profile.reputation_score,
                    'total_attacks': profile.total_attacks,
                    'first_seen': profile.first_seen.isoformat(),
                    'last_seen': profile.last_seen.isoformat()
                }
                for profile in profiles
            ]
            
        finally:
            self.close_session(session)
    
    def execute_custom_function(self, function_name: str, *args):
        """Execute custom PostgreSQL function"""
        session = self.get_session()
        try:
            result = session.execute(f"SELECT securehoney.{function_name}({','.join(['%s'] * len(args))})", args)
            return result.fetchone()[0] if result.rowcount > 0 else None
        finally:
            self.close_session(session)
    
    def get_attack_analytics_view(self) -> List[Dict[str, Any]]:
        """Get data from attack analytics view"""
        session = self.get_session()
        try:
            result = session.execute("SELECT * FROM securehoney.attack_analytics ORDER BY reputation_score DESC LIMIT 100")
            columns = result.keys()
            
            return [
                dict(zip(columns, row))
                for row in result.fetchall()
            ]
            
        finally:
            self.close_session(session)
    
    def refresh_materialized_views(self):
        """Refresh materialized views for performance"""
        session = self.get_session()
        try:
            session.execute("SELECT securehoney.refresh_daily_stats()")
            session.commit()
        finally:
            self.close_session(session)

# Global database manager instance
postgresql_db = PostgreSQLDatabaseManager()

# Convenience functions for PostgreSQL operations
def insert_attack_postgresql(attack_data: Dict[str, Any]) -> str:
    """Insert attack using PostgreSQL custom types"""
    return postgresql_db.insert_attack_with_types(attack_data)

def get_high_severity_attacks() -> List[Dict[str, Any]]:
    """Get high severity attacks"""
    return postgresql_db.get_attacks_by_severity('HIGH')

def get_critical_threat_actors() -> List[Dict[str, Any]]:
    """Get critical threat actors"""
    return postgresql_db.get_threat_actors_by_level('CRITICAL')

def calculate_threat_score_postgresql(attack_count: int, severity_avg: float, 
                                    unique_techniques: int, time_span_hours: int) -> int:
    """Calculate threat score using PostgreSQL function"""
    return postgresql_db.execute_custom_function(
        'calculate_threat_score', 
        attack_count, severity_avg, unique_techniques, time_span_hours
    )

def extract_attack_signatures_postgresql(payload: str) -> List[str]:
    """Extract attack signatures using PostgreSQL function"""
    result = postgresql_db.execute_custom_function('extract_attack_signatures', payload)
    return result if result else []
