#!/usr/bin/env python3
"""
SecureHoney Database Analytics
Advanced analytics and pattern detection for hacker behavior
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy import func, and_, or_
from models import (
    DatabaseManager, Attack, AttackerProfile, AttackSession, 
    AttackPattern, HoneypotInteraction, GeolocationData
)
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HackerPatternAnalyzer:
    """Advanced hacker pattern analysis and behavioral profiling"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def analyze_attack_patterns(self, ip_address: str = None, days: int = 30) -> Dict[str, Any]:
        """Comprehensive attack pattern analysis"""
        session = self.db.get_session()
        try:
            # Base query
            query = session.query(Attack)
            
            # Filter by IP if specified
            if ip_address:
                query = query.filter(Attack.source_ip == ip_address)
            
            # Filter by time range
            since_date = datetime.utcnow() - timedelta(days=days)
            query = query.filter(Attack.timestamp >= since_date)
            
            attacks = query.all()
            
            if not attacks:
                return {'message': 'No attacks found for analysis'}
            
            # Convert to DataFrame for analysis
            attack_data = []
            for attack in attacks:
                attack_data.append({
                    'timestamp': attack.timestamp,
                    'source_ip': attack.source_ip,
                    'target_port': attack.target_port,
                    'attack_type': attack.attack_type,
                    'severity': attack.severity,
                    'payload_size': attack.payload_size or 0,
                    'hour': attack.timestamp.hour,
                    'day_of_week': attack.timestamp.weekday(),
                    'confidence': attack.confidence or 0.5
                })
            
            df = pd.DataFrame(attack_data)
            
            # Perform pattern analysis
            patterns = {
                'temporal_patterns': self._analyze_temporal_patterns(df),
                'port_targeting_patterns': self._analyze_port_patterns(df),
                'attack_type_patterns': self._analyze_attack_type_patterns(df),
                'intensity_patterns': self._analyze_intensity_patterns(df),
                'behavioral_signatures': self._detect_behavioral_signatures(df),
                'anomaly_detection': self._detect_anomalies(df)
            }
            
            return patterns
            
        finally:
            self.db.close_session(session)
    
    def _analyze_temporal_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze temporal attack patterns"""
        patterns = {}
        
        # Hourly distribution
        hourly_dist = df.groupby('hour').size().to_dict()
        patterns['hourly_distribution'] = hourly_dist
        patterns['peak_hours'] = sorted(hourly_dist.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # Daily distribution
        daily_dist = df.groupby('day_of_week').size().to_dict()
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        patterns['daily_distribution'] = {day_names[k]: v for k, v in daily_dist.items()}
        
        # Attack frequency analysis
        df['date'] = df['timestamp'].dt.date
        daily_counts = df.groupby('date').size()
        patterns['average_daily_attacks'] = daily_counts.mean()
        patterns['max_daily_attacks'] = daily_counts.max()
        patterns['attack_frequency_trend'] = self._calculate_trend(daily_counts.values)
        
        return patterns
    
    def _analyze_port_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze port targeting patterns"""
        port_stats = df.groupby('target_port').agg({
            'source_ip': 'nunique',
            'attack_type': lambda x: x.mode().iloc[0] if not x.empty else 'Unknown',
            'severity': lambda x: x.mode().iloc[0] if not x.empty else 'Unknown'
        }).to_dict('index')
        
        # Port preference analysis
        port_counts = df['target_port'].value_counts().to_dict()
        
        return {
            'port_statistics': port_stats,
            'most_targeted_ports': dict(list(port_counts.items())[:10]),
            'port_diversity': len(port_counts),
            'port_concentration': self._calculate_concentration_index(list(port_counts.values()))
        }
    
    def _analyze_attack_type_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze attack type patterns and evolution"""
        type_counts = df['attack_type'].value_counts().to_dict()
        
        # Attack type evolution over time
        df['week'] = df['timestamp'].dt.isocalendar().week
        type_evolution = df.groupby(['week', 'attack_type']).size().unstack(fill_value=0)
        
        return {
            'attack_type_distribution': type_counts,
            'primary_attack_types': dict(list(type_counts.items())[:5]),
            'attack_type_diversity': len(type_counts),
            'type_switching_behavior': self._analyze_type_switching(df)
        }
    
    def _analyze_intensity_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze attack intensity and escalation patterns"""
        # Group attacks by hour to analyze intensity
        df['hour_bucket'] = df['timestamp'].dt.floor('H')
        intensity_data = df.groupby('hour_bucket').agg({
            'source_ip': 'count',
            'payload_size': 'mean',
            'severity': lambda x: (x == 'HIGH').sum() + (x == 'CRITICAL').sum() * 2
        })
        
        return {
            'average_attacks_per_hour': intensity_data['source_ip'].mean(),
            'max_attacks_per_hour': intensity_data['source_ip'].max(),
            'intensity_variance': intensity_data['source_ip'].var(),
            'escalation_patterns': self._detect_escalation_patterns(df)
        }
    
    def _detect_behavioral_signatures(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect unique behavioral signatures"""
        signatures = {}
        
        # Rapid-fire attacks (many attacks in short time)
        df_sorted = df.sort_values('timestamp')
        time_diffs = df_sorted['timestamp'].diff().dt.total_seconds()
        rapid_fire_threshold = 5  # seconds
        rapid_fire_count = (time_diffs < rapid_fire_threshold).sum()
        signatures['rapid_fire_attacks'] = rapid_fire_count
        
        # Port scanning behavior
        unique_ports_per_ip = df.groupby('source_ip')['target_port'].nunique()
        port_scanners = (unique_ports_per_ip > 5).sum()
        signatures['port_scanning_behavior'] = port_scanners
        
        # Persistence patterns
        attack_spans = df.groupby('source_ip')['timestamp'].agg(['min', 'max'])
        attack_spans['duration'] = (attack_spans['max'] - attack_spans['min']).dt.total_seconds()
        persistent_attackers = (attack_spans['duration'] > 3600).sum()  # > 1 hour
        signatures['persistent_attackers'] = persistent_attackers
        
        return signatures
    
    def _detect_anomalies(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect anomalous attack patterns"""
        anomalies = {}
        
        # Unusual payload sizes
        if 'payload_size' in df.columns and df['payload_size'].sum() > 0:
            payload_mean = df['payload_size'].mean()
            payload_std = df['payload_size'].std()
            unusual_payloads = df[df['payload_size'] > payload_mean + 3 * payload_std]
            anomalies['unusual_payload_sizes'] = len(unusual_payloads)
        
        # Unusual time patterns (attacks at very unusual hours)
        night_attacks = df[df['hour'].isin([2, 3, 4, 5])]  # 2-5 AM
        anomalies['night_time_attacks'] = len(night_attacks)
        
        # Geographic anomalies would require geolocation data
        
        return anomalies
    
    def _calculate_trend(self, values: np.ndarray) -> str:
        """Calculate trend direction"""
        if len(values) < 2:
            return 'insufficient_data'
        
        # Simple linear regression slope
        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]
        
        if slope > 0.1:
            return 'increasing'
        elif slope < -0.1:
            return 'decreasing'
        else:
            return 'stable'
    
    def _calculate_concentration_index(self, values: List[int]) -> float:
        """Calculate Herfindahl concentration index"""
        if not values:
            return 0.0
        
        total = sum(values)
        if total == 0:
            return 0.0
        
        return sum((v / total) ** 2 for v in values)
    
    def _analyze_type_switching(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze attack type switching behavior"""
        switching_data = {}
        
        for ip in df['source_ip'].unique():
            ip_attacks = df[df['source_ip'] == ip].sort_values('timestamp')
            if len(ip_attacks) > 1:
                attack_types = ip_attacks['attack_type'].tolist()
                switches = sum(1 for i in range(1, len(attack_types)) 
                             if attack_types[i] != attack_types[i-1])
                switching_data[ip] = {
                    'total_attacks': len(attack_types),
                    'type_switches': switches,
                    'switch_rate': switches / len(attack_types) if len(attack_types) > 0 else 0
                }
        
        return switching_data
    
    def _detect_escalation_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect attack escalation patterns"""
        severity_order = {'LOW': 1, 'MEDIUM': 2, 'HIGH': 3, 'CRITICAL': 4}
        escalations = {}
        
        for ip in df['source_ip'].unique():
            ip_attacks = df[df['source_ip'] == ip].sort_values('timestamp')
            if len(ip_attacks) > 1:
                severities = [severity_order.get(s, 0) for s in ip_attacks['severity']]
                escalation_count = sum(1 for i in range(1, len(severities)) 
                                     if severities[i] > severities[i-1])
                escalations[ip] = escalation_count
        
        return escalations
    
    def generate_threat_profile(self, ip_address: str) -> Dict[str, Any]:
        """Generate comprehensive threat profile for specific IP"""
        session = self.db.get_session()
        try:
            # Get attacker profile
            profile = session.query(AttackerProfile).filter(
                AttackerProfile.source_ip == ip_address
            ).first()
            
            if not profile:
                return {'error': 'IP address not found in database'}
            
            # Get attack patterns for this IP
            patterns = self.analyze_attack_patterns(ip_address=ip_address)
            
            # Get recent attacks
            recent_attacks = session.query(Attack).filter(
                Attack.source_ip == ip_address
            ).order_by(Attack.timestamp.desc()).limit(50).all()
            
            # Calculate threat metrics
            threat_metrics = self._calculate_threat_metrics(profile, recent_attacks)
            
            return {
                'ip_address': ip_address,
                'profile': {
                    'first_seen': profile.first_seen.isoformat(),
                    'last_seen': profile.last_seen.isoformat(),
                    'total_attacks': profile.total_attacks,
                    'skill_level': profile.skill_level,
                    'threat_level': profile.threat_level,
                    'reputation_score': profile.reputation_score
                },
                'attack_patterns': patterns,
                'threat_metrics': threat_metrics,
                'recent_activity': [
                    {
                        'timestamp': attack.timestamp.isoformat(),
                        'target_port': attack.target_port,
                        'attack_type': attack.attack_type,
                        'severity': attack.severity
                    } for attack in recent_attacks[:10]
                ]
            }
            
        finally:
            self.db.close_session(session)
    
    def _calculate_threat_metrics(self, profile: AttackerProfile, attacks: List[Attack]) -> Dict[str, Any]:
        """Calculate advanced threat metrics"""
        if not attacks:
            return {}
        
        # Attack frequency
        time_span = (attacks[0].timestamp - attacks[-1].timestamp).total_seconds()
        attack_frequency = len(attacks) / (time_span / 3600) if time_span > 0 else 0
        
        # Severity distribution
        severity_counts = {}
        for attack in attacks:
            severity_counts[attack.severity] = severity_counts.get(attack.severity, 0) + 1
        
        # Port diversity
        unique_ports = len(set(attack.target_port for attack in attacks if attack.target_port))
        
        return {
            'attack_frequency_per_hour': round(attack_frequency, 2),
            'port_diversity': unique_ports,
            'severity_distribution': severity_counts,
            'persistence_score': min(time_span / 86400, 10),  # days, capped at 10
            'threat_score': self._calculate_composite_threat_score(profile, attacks)
        }
    
    def _calculate_composite_threat_score(self, profile: AttackerProfile, attacks: List[Attack]) -> float:
        """Calculate composite threat score (0-100)"""
        score = 0
        
        # Base score from attack count
        score += min(len(attacks) * 2, 30)
        
        # Severity bonus
        for attack in attacks:
            if attack.severity == 'CRITICAL':
                score += 5
            elif attack.severity == 'HIGH':
                score += 3
            elif attack.severity == 'MEDIUM':
                score += 1
        
        # Port diversity bonus
        unique_ports = len(set(attack.target_port for attack in attacks if attack.target_port))
        score += min(unique_ports * 2, 20)
        
        # Persistence bonus
        if profile.total_attacks > 50:
            score += 15
        elif profile.total_attacks > 20:
            score += 10
        elif profile.total_attacks > 10:
            score += 5
        
        return min(score, 100)

class DatabaseReporter:
    """Generate comprehensive reports from database"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.analyzer = HackerPatternAnalyzer(db_manager)
    
    def generate_daily_report(self, date: datetime = None) -> Dict[str, Any]:
        """Generate daily security report"""
        if date is None:
            date = datetime.utcnow().date()
        
        session = self.db.get_session()
        try:
            # Get attacks for the day
            start_time = datetime.combine(date, datetime.min.time())
            end_time = datetime.combine(date, datetime.max.time())
            
            daily_attacks = session.query(Attack).filter(
                and_(Attack.timestamp >= start_time, Attack.timestamp <= end_time)
            ).all()
            
            # Statistics
            total_attacks = len(daily_attacks)
            unique_attackers = len(set(attack.source_ip for attack in daily_attacks))
            
            # Top attackers
            attacker_counts = {}
            for attack in daily_attacks:
                attacker_counts[attack.source_ip] = attacker_counts.get(attack.source_ip, 0) + 1
            
            top_attackers = sorted(attacker_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # Attack types
            type_counts = {}
            for attack in daily_attacks:
                type_counts[attack.attack_type] = type_counts.get(attack.attack_type, 0) + 1
            
            return {
                'date': date.isoformat(),
                'summary': {
                    'total_attacks': total_attacks,
                    'unique_attackers': unique_attackers,
                    'attack_types': len(type_counts)
                },
                'top_attackers': [{'ip': ip, 'attacks': count} for ip, count in top_attackers],
                'attack_type_distribution': type_counts,
                'hourly_distribution': self._get_hourly_distribution(daily_attacks)
            }
            
        finally:
            self.db.close_session(session)
    
    def _get_hourly_distribution(self, attacks: List[Attack]) -> Dict[int, int]:
        """Get hourly attack distribution"""
        hourly = {}
        for attack in attacks:
            hour = attack.timestamp.hour
            hourly[hour] = hourly.get(hour, 0) + 1
        return hourly
    
    def export_threat_intelligence(self, format: str = 'json') -> str:
        """Export threat intelligence data"""
        session = self.db.get_session()
        try:
            # Get top threat IPs
            threat_ips = session.query(AttackerProfile).filter(
                AttackerProfile.threat_level.in_(['HIGH', 'CRITICAL'])
            ).all()
            
            intelligence_data = {
                'export_timestamp': datetime.utcnow().isoformat(),
                'threat_ips': [],
                'attack_signatures': [],
                'iocs': []  # Indicators of Compromise
            }
            
            for profile in threat_ips:
                intelligence_data['threat_ips'].append({
                    'ip': profile.source_ip,
                    'threat_level': profile.threat_level,
                    'first_seen': profile.first_seen.isoformat(),
                    'last_seen': profile.last_seen.isoformat(),
                    'total_attacks': profile.total_attacks,
                    'attack_types': profile.attack_patterns.get('types', []) if profile.attack_patterns else []
                })
            
            if format == 'json':
                return json.dumps(intelligence_data, indent=2)
            else:
                return "Unsupported format"
                
        finally:
            self.db.close_session(session)
