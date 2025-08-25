#!/usr/bin/env python3
"""
SecureHoney Database Models
Comprehensive database schema for storing hacker patterns and attack data
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Text, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import json
from typing import Dict, Any, List, Optional

Base = declarative_base()

class AttackSession(Base):
    """Main attack session - groups related attacks from same source"""
    __tablename__ = 'attack_sessions'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(64), unique=True, index=True)
    source_ip = Column(String(45), index=True)  # IPv4/IPv6
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    duration_seconds = Column(Integer)
    total_attacks = Column(Integer, default=0)
    unique_ports = Column(Integer, default=0)
    attack_intensity = Column(String(20))  # LOW, MEDIUM, HIGH, CRITICAL
    session_type = Column(String(50))  # RECONNAISSANCE, BRUTE_FORCE, EXPLOITATION, etc.
    geolocation = Column(JSON)
    user_agent = Column(Text)
    is_active = Column(Boolean, default=True)
    threat_score = Column(Float, default=0.0)
    
    # Relationships
    attacks = relationship("Attack", back_populates="session")
    attacker_profile = relationship("AttackerProfile", back_populates="sessions")

class Attack(Base):
    """Individual attack events"""
    __tablename__ = 'attacks'
    
    id = Column(Integer, primary_key=True)
    attack_id = Column(String(64), unique=True, index=True)
    session_id = Column(String(64), ForeignKey('attack_sessions.session_id'))
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    source_ip = Column(String(45), index=True)
    source_port = Column(Integer)
    target_port = Column(Integer, index=True)
    protocol = Column(String(10))  # TCP, UDP, HTTP, etc.
    attack_type = Column(String(50), index=True)
    attack_vector = Column(String(50))
    severity = Column(String(20), index=True)
    confidence = Column(Float)
    payload = Column(Text)
    payload_size = Column(Integer)
    payload_hash = Column(String(64))
    response_sent = Column(Text)
    connection_duration = Column(Float)
    bytes_received = Column(Integer)
    bytes_sent = Column(Integer)
    honeypot_response = Column(String(50))  # ENGAGED, BLOCKED, REDIRECTED
    
    # Relationships
    session = relationship("AttackSession", back_populates="attacks")
    patterns = relationship("AttackPattern", back_populates="attack")

class AttackerProfile(Base):
    """Comprehensive attacker profiling"""
    __tablename__ = 'attacker_profiles'
    
    id = Column(Integer, primary_key=True)
    source_ip = Column(String(45), unique=True, index=True)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    total_attacks = Column(Integer, default=0)
    total_sessions = Column(Integer, default=0)
    attack_frequency = Column(Float)  # attacks per hour
    primary_attack_type = Column(String(50))
    skill_level = Column(String(20))  # SCRIPT_KIDDIE, INTERMEDIATE, ADVANCED, EXPERT
    persistence_score = Column(Float)  # how persistent they are
    stealth_score = Column(Float)  # how stealthy their attacks are
    success_rate = Column(Float)  # percentage of successful attacks
    preferred_ports = Column(JSON)  # list of most targeted ports
    attack_patterns = Column(JSON)  # behavioral patterns
    tools_used = Column(JSON)  # detected tools and frameworks
    geolocation_history = Column(JSON)  # location changes over time
    user_agents = Column(JSON)  # all user agents used
    is_bot = Column(Boolean, default=False)
    is_tor = Column(Boolean, default=False)
    is_vpn = Column(Boolean, default=False)
    threat_level = Column(String(20))
    reputation_score = Column(Float, default=0.5)
    
    # Relationships
    sessions = relationship("AttackSession", back_populates="attacker_profile")

class AttackPattern(Base):
    """Detected attack patterns and signatures"""
    __tablename__ = 'attack_patterns'
    
    id = Column(Integer, primary_key=True)
    attack_id = Column(String(64), ForeignKey('attacks.attack_id'))
    pattern_type = Column(String(50))  # SIGNATURE, BEHAVIORAL, TEMPORAL
    pattern_name = Column(String(100))
    pattern_description = Column(Text)
    confidence = Column(Float)
    severity = Column(String(20))
    indicators = Column(JSON)  # specific indicators that matched
    mitre_technique = Column(String(20))  # MITRE ATT&CK technique ID
    
    # Relationships
    attack = relationship("Attack", back_populates="patterns")

class HoneypotInteraction(Base):
    """Detailed honeypot service interactions"""
    __tablename__ = 'honeypot_interactions'
    
    id = Column(Integer, primary_key=True)
    attack_id = Column(String(64), ForeignKey('attacks.attack_id'))
    service_type = Column(String(50))  # SSH, HTTP, FTP, etc.
    interaction_type = Column(String(50))  # LOGIN_ATTEMPT, FILE_UPLOAD, COMMAND_EXECUTION
    timestamp = Column(DateTime, default=datetime.utcnow)
    username_attempted = Column(String(255))
    password_attempted = Column(String(255))
    command_executed = Column(Text)
    file_uploaded = Column(String(500))
    file_hash = Column(String(64))
    http_method = Column(String(10))
    http_path = Column(String(500))
    http_headers = Column(JSON)
    response_code = Column(Integer)
    interaction_success = Column(Boolean)
    data_extracted = Column(JSON)

class ThreatIntelligence(Base):
    """Threat intelligence data"""
    __tablename__ = 'threat_intelligence'
    
    id = Column(Integer, primary_key=True)
    ip_address = Column(String(45), index=True)
    domain = Column(String(255))
    hash_value = Column(String(64))
    threat_type = Column(String(50))  # MALWARE, BOTNET, TOR_EXIT, etc.
    threat_source = Column(String(100))  # source of intelligence
    confidence = Column(Float)
    first_reported = Column(DateTime)
    last_updated = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    additional_info = Column(JSON)

class AttackCampaign(Base):
    """Coordinated attack campaigns"""
    __tablename__ = 'attack_campaigns'
    
    id = Column(Integer, primary_key=True)
    campaign_id = Column(String(64), unique=True)
    campaign_name = Column(String(200))
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    total_attackers = Column(Integer)
    total_attacks = Column(Integer)
    primary_targets = Column(JSON)  # ports, services targeted
    attack_methods = Column(JSON)
    geographic_distribution = Column(JSON)
    campaign_type = Column(String(50))  # BOTNET, COORDINATED, DISTRIBUTED
    threat_actor = Column(String(200))
    is_active = Column(Boolean, default=True)

class SystemMetrics(Base):
    """System performance and honeypot metrics"""
    __tablename__ = 'system_metrics'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    metric_type = Column(String(50))  # ATTACK_RATE, RESPONSE_TIME, etc.
    metric_value = Column(Float)
    metric_unit = Column(String(20))
    component = Column(String(50))  # ENGINE, WEB_SERVER, AI_ANALYZER
    additional_data = Column(JSON)

class MalwareAnalysis(Base):
    """Analysis of malware samples collected"""
    __tablename__ = 'malware_analysis'
    
    id = Column(Integer, primary_key=True)
    file_hash = Column(String(64), unique=True, index=True)
    file_name = Column(String(500))
    file_size = Column(Integer)
    file_type = Column(String(50))
    upload_timestamp = Column(DateTime, default=datetime.utcnow)
    source_ip = Column(String(45))
    attack_id = Column(String(64), ForeignKey('attacks.attack_id'))
    malware_family = Column(String(100))
    threat_level = Column(String(20))
    analysis_status = Column(String(20))  # PENDING, ANALYZING, COMPLETE
    static_analysis = Column(JSON)
    dynamic_analysis = Column(JSON)
    iocs = Column(JSON)  # Indicators of Compromise
    yara_matches = Column(JSON)

class GeolocationData(Base):
    """IP geolocation tracking"""
    __tablename__ = 'geolocation_data'
    
    id = Column(Integer, primary_key=True)
    ip_address = Column(String(45), unique=True, index=True)
    country = Column(String(100))
    country_code = Column(String(2))
    region = Column(String(100))
    city = Column(String(100))
    latitude = Column(Float)
    longitude = Column(Float)
    timezone = Column(String(50))
    isp = Column(String(200))
    organization = Column(String(200))
    asn = Column(String(20))
    is_proxy = Column(Boolean, default=False)
    is_tor = Column(Boolean, default=False)
    is_vpn = Column(Boolean, default=False)
    last_updated = Column(DateTime, default=datetime.utcnow)

class DatabaseManager:
    """Database management class"""
    
    def __init__(self, database_url: str = "sqlite:///securehoney.db"):
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.create_tables()
    
    def create_tables(self):
        """Create all database tables"""
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()
    
    def close_session(self, session):
        """Close database session"""
        session.close()
    
    def insert_attack(self, attack_data: Dict[str, Any]) -> str:
        """Insert attack data into database"""
        session = self.get_session()
        try:
            # Create or get attack session
            session_obj = self.get_or_create_session(session, attack_data)
            
            # Create attack record
            attack = Attack(
                attack_id=attack_data.get('id'),
                session_id=session_obj.session_id,
                timestamp=datetime.fromisoformat(attack_data.get('timestamp', datetime.utcnow().isoformat())),
                source_ip=attack_data.get('source_ip'),
                source_port=attack_data.get('source_port'),
                target_port=attack_data.get('target_port'),
                protocol=attack_data.get('protocol', 'TCP'),
                attack_type=attack_data.get('attack_type'),
                attack_vector=attack_data.get('attack_vector', 'NETWORK'),
                severity=attack_data.get('severity'),
                confidence=attack_data.get('confidence', 0.5),
                payload=attack_data.get('payload'),
                payload_size=len(attack_data.get('payload', '')),
                response_sent=attack_data.get('response_sent'),
                honeypot_response=attack_data.get('honeypot_response', 'ENGAGED')
            )
            
            session.add(attack)
            session.commit()
            
            # Update attacker profile
            self.update_attacker_profile(session, attack_data)
            
            return attack.attack_id
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            self.close_session(session)
    
    def get_or_create_session(self, db_session, attack_data: Dict[str, Any]) -> AttackSession:
        """Get existing or create new attack session"""
        source_ip = attack_data.get('source_ip')
        
        # Look for active session from same IP within last hour
        existing_session = db_session.query(AttackSession).filter(
            AttackSession.source_ip == source_ip,
            AttackSession.is_active == True
        ).first()
        
        if existing_session:
            # Update existing session
            existing_session.total_attacks += 1
            existing_session.end_time = datetime.utcnow()
            return existing_session
        else:
            # Create new session
            import hashlib
            session_id = hashlib.md5(f"{source_ip}_{datetime.utcnow().timestamp()}".encode()).hexdigest()
            
            new_session = AttackSession(
                session_id=session_id,
                source_ip=source_ip,
                total_attacks=1,
                geolocation=attack_data.get('location', {}),
                user_agent=attack_data.get('user_agent')
            )
            
            db_session.add(new_session)
            return new_session
    
    def update_attacker_profile(self, db_session, attack_data: Dict[str, Any]):
        """Update or create attacker profile"""
        source_ip = attack_data.get('source_ip')
        
        profile = db_session.query(AttackerProfile).filter(
            AttackerProfile.source_ip == source_ip
        ).first()
        
        if profile:
            # Update existing profile
            profile.total_attacks += 1
            profile.last_seen = datetime.utcnow()
            
            # Update preferred ports
            target_port = attack_data.get('target_port')
            if target_port:
                preferred_ports = profile.preferred_ports or []
                if target_port not in preferred_ports:
                    preferred_ports.append(target_port)
                profile.preferred_ports = preferred_ports
        else:
            # Create new profile
            profile = AttackerProfile(
                source_ip=source_ip,
                total_attacks=1,
                total_sessions=1,
                preferred_ports=[attack_data.get('target_port')] if attack_data.get('target_port') else [],
                attack_patterns={},
                tools_used=[],
                user_agents=[attack_data.get('user_agent')] if attack_data.get('user_agent') else []
            )
            db_session.add(profile)
    
    def get_attack_statistics(self) -> Dict[str, Any]:
        """Get comprehensive attack statistics"""
        session = self.get_session()
        try:
            total_attacks = session.query(Attack).count()
            unique_attackers = session.query(AttackerProfile).count()
            active_sessions = session.query(AttackSession).filter(AttackSession.is_active == True).count()
            
            # Top attack types
            from sqlalchemy import func
            top_attack_types = session.query(
                Attack.attack_type,
                func.count(Attack.id).label('count')
            ).group_by(Attack.attack_type).order_by(func.count(Attack.id).desc()).limit(10).all()
            
            # Top targeted ports
            top_ports = session.query(
                Attack.target_port,
                func.count(Attack.id).label('count')
            ).group_by(Attack.target_port).order_by(func.count(Attack.id).desc()).limit(10).all()
            
            return {
                'total_attacks': total_attacks,
                'unique_attackers': unique_attackers,
                'active_sessions': active_sessions,
                'top_attack_types': [{'type': t[0], 'count': t[1]} for t in top_attack_types],
                'top_targeted_ports': [{'port': p[0], 'count': p[1]} for p in top_ports]
            }
            
        finally:
            self.close_session(session)
    
    def get_attacker_profile(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """Get detailed attacker profile"""
        session = self.get_session()
        try:
            profile = session.query(AttackerProfile).filter(
                AttackerProfile.source_ip == ip_address
            ).first()
            
            if profile:
                return {
                    'ip_address': profile.source_ip,
                    'first_seen': profile.first_seen.isoformat(),
                    'last_seen': profile.last_seen.isoformat(),
                    'total_attacks': profile.total_attacks,
                    'skill_level': profile.skill_level,
                    'threat_level': profile.threat_level,
                    'preferred_ports': profile.preferred_ports,
                    'attack_patterns': profile.attack_patterns,
                    'reputation_score': profile.reputation_score
                }
            return None
            
        finally:
            self.close_session(session)

# Initialize database manager
db_manager = DatabaseManager()
