#!/usr/bin/env python3
"""
SecureHoney Database Integration
Integration layer for connecting honeypot components to database
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
import hashlib
from models import DatabaseManager, db_manager
from analytics import HackerPatternAnalyzer, DatabaseReporter
from geolocation import GeolocationService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HoneypotDatabaseIntegrator:
    """Main integration class for honeypot database operations"""
    
    def __init__(self, database_url: str = None):
        self.db = DatabaseManager(database_url) if database_url else db_manager
        self.analyzer = HackerPatternAnalyzer(self.db)
        self.reporter = DatabaseReporter(self.db)
        self.geo_service = GeolocationService(self.db)
        
    def log_attack_event(self, attack_data: Dict[str, Any]) -> str:
        """Log attack event with full analysis and geolocation"""
        try:
            # Enrich attack data with geolocation
            if 'source_ip' in attack_data:
                location_data = self.geo_service.get_ip_location(attack_data['source_ip'])
                attack_data['location'] = location_data
            
            # Generate attack ID if not present
            if 'id' not in attack_data:
                attack_string = f"{attack_data.get('source_ip')}_{attack_data.get('timestamp')}_{attack_data.get('target_port')}"
                attack_data['id'] = hashlib.md5(attack_string.encode()).hexdigest()[:16]
            
            # Insert into database
            attack_id = self.db.insert_attack(attack_data)
            
            # Perform real-time analysis
            self._perform_realtime_analysis(attack_data)
            
            logger.info(f"Attack logged: {attack_id} from {attack_data.get('source_ip')}")
            return attack_id
            
        except Exception as e:
            logger.error(f"Failed to log attack: {e}")
            return None
    
    def log_honeypot_interaction(self, interaction_data: Dict[str, Any]):
        """Log detailed honeypot service interaction"""
        session = self.db.get_session()
        try:
            from models import HoneypotInteraction
            
            interaction = HoneypotInteraction(
                attack_id=interaction_data.get('attack_id'),
                service_type=interaction_data.get('service_type'),
                interaction_type=interaction_data.get('interaction_type'),
                username_attempted=interaction_data.get('username'),
                password_attempted=interaction_data.get('password'),
                command_executed=interaction_data.get('command'),
                file_uploaded=interaction_data.get('file_path'),
                http_method=interaction_data.get('http_method'),
                http_path=interaction_data.get('http_path'),
                http_headers=interaction_data.get('http_headers'),
                response_code=interaction_data.get('response_code'),
                interaction_success=interaction_data.get('success', False),
                data_extracted=interaction_data.get('extracted_data')
            )
            
            session.add(interaction)
            session.commit()
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to log interaction: {e}")
        finally:
            self.db.close_session(session)
    
    def log_malware_sample(self, malware_data: Dict[str, Any]):
        """Log malware sample for analysis"""
        session = self.db.get_session()
        try:
            from models import MalwareAnalysis
            
            # Calculate file hash if not provided
            file_hash = malware_data.get('file_hash')
            if not file_hash and 'file_content' in malware_data:
                file_hash = hashlib.sha256(malware_data['file_content']).hexdigest()
            
            malware = MalwareAnalysis(
                file_hash=file_hash,
                file_name=malware_data.get('file_name'),
                file_size=malware_data.get('file_size'),
                file_type=malware_data.get('file_type'),
                source_ip=malware_data.get('source_ip'),
                attack_id=malware_data.get('attack_id'),
                analysis_status='PENDING'
            )
            
            session.add(malware)
            session.commit()
            
            logger.info(f"Malware sample logged: {file_hash}")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to log malware: {e}")
        finally:
            self.db.close_session(session)
    
    def _perform_realtime_analysis(self, attack_data: Dict[str, Any]):
        """Perform real-time analysis on incoming attack"""
        try:
            source_ip = attack_data.get('source_ip')
            if not source_ip:
                return
            
            # Check if this IP should be blocked
            profile = self.db.get_attacker_profile(source_ip)
            if profile and profile.get('total_attacks', 0) > 10:
                self._trigger_ip_block(source_ip, profile)
            
            # Detect attack campaigns
            self._detect_campaign_activity(attack_data)
            
            # Update system metrics
            self._update_system_metrics(attack_data)
            
        except Exception as e:
            logger.error(f"Real-time analysis failed: {e}")
    
    def _trigger_ip_block(self, ip_address: str, profile: Dict[str, Any]):
        """Trigger IP blocking for high-threat attackers"""
        logger.warning(f"🚫 High-threat IP detected: {ip_address} (attacks: {profile.get('total_attacks')})")
        
        # Here you would integrate with firewall/blocking system
        # For now, we'll just log the recommendation
        block_recommendation = {
            'ip_address': ip_address,
            'reason': 'High attack frequency',
            'threat_score': profile.get('reputation_score', 0),
            'recommended_action': 'BLOCK',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Save blocking recommendation
        self._save_blocking_recommendation(block_recommendation)
    
    def _detect_campaign_activity(self, attack_data: Dict[str, Any]):
        """Detect coordinated attack campaign activity"""
        session = self.db.get_session()
        try:
            from models import Attack, AttackCampaign
            from sqlalchemy import func
            from datetime import timedelta
            
            # Look for similar attacks in last hour
            recent_time = datetime.utcnow() - timedelta(hours=1)
            attack_type = attack_data.get('attack_type')
            target_port = attack_data.get('target_port')
            
            similar_attacks = session.query(Attack).filter(
                Attack.timestamp >= recent_time,
                Attack.attack_type == attack_type,
                Attack.target_port == target_port
            ).count()
            
            # If we see coordinated activity, flag as potential campaign
            if similar_attacks > 20:  # Threshold for campaign detection
                logger.warning(f"🎯 Potential attack campaign detected: {attack_type} on port {target_port}")
                self._create_campaign_alert(attack_type, target_port, similar_attacks)
            
        finally:
            self.db.close_session(session)
    
    def _update_system_metrics(self, attack_data: Dict[str, Any]):
        """Update system performance metrics"""
        session = self.db.get_session()
        try:
            from models import SystemMetrics
            
            # Log attack rate metric
            metric = SystemMetrics(
                metric_type='ATTACK_RATE',
                metric_value=1.0,
                metric_unit='attacks_per_minute',
                component='HONEYPOT_ENGINE',
                additional_data={
                    'attack_type': attack_data.get('attack_type'),
                    'source_ip': attack_data.get('source_ip'),
                    'target_port': attack_data.get('target_port')
                }
            )
            
            session.add(metric)
            session.commit()
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to update metrics: {e}")
        finally:
            self.db.close_session(session)
    
    def _save_blocking_recommendation(self, recommendation: Dict[str, Any]):
        """Save IP blocking recommendation"""
        # Save to a recommendations file for now
        recommendations_file = Path("../logging/blocking_recommendations.json")
        recommendations_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(recommendations_file, 'a') as f:
                f.write(json.dumps(recommendation) + '\n')
        except Exception as e:
            logger.error(f"Failed to save blocking recommendation: {e}")
    
    def _create_campaign_alert(self, attack_type: str, target_port: int, attack_count: int):
        """Create alert for potential attack campaign"""
        alert_data = {
            'alert_type': 'ATTACK_CAMPAIGN',
            'severity': 'HIGH',
            'attack_type': attack_type,
            'target_port': target_port,
            'attack_count': attack_count,
            'timestamp': datetime.utcnow().isoformat(),
            'message': f"Coordinated {attack_type} campaign detected on port {target_port}"
        }
        
        # Save alert
        alerts_file = Path("../logging/campaign_alerts.json")
        alerts_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(alerts_file, 'a') as f:
                f.write(json.dumps(alert_data) + '\n')
        except Exception as e:
            logger.error(f"Failed to save campaign alert: {e}")
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data from database"""
        try:
            # Basic statistics
            stats = self.db.get_attack_statistics()
            
            # Geographic analysis
            geo_patterns = self.geo_service.analyze_geographic_patterns(days=7)
            
            # Recent high-threat attackers
            session = self.db.get_session()
            from models import AttackerProfile
            
            high_threat_attackers = session.query(AttackerProfile).filter(
                AttackerProfile.threat_level.in_(['HIGH', 'CRITICAL'])
            ).order_by(AttackerProfile.last_seen.desc()).limit(10).all()
            
            threat_list = []
            for attacker in high_threat_attackers:
                threat_list.append({
                    'ip': attacker.source_ip,
                    'threat_level': attacker.threat_level,
                    'total_attacks': attacker.total_attacks,
                    'last_seen': attacker.last_seen.isoformat(),
                    'reputation_score': attacker.reputation_score
                })
            
            self.db.close_session(session)
            
            return {
                'statistics': stats,
                'geographic_patterns': geo_patterns,
                'high_threat_attackers': threat_list,
                'heatmap_data': self.geo_service.get_attack_heatmap_data()
            }
            
        except Exception as e:
            logger.error(f"Failed to get dashboard data: {e}")
            return {'error': str(e)}
    
    def search_attacks(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search attacks with advanced criteria"""
        session = self.db.get_session()
        try:
            from models import Attack
            from sqlalchemy import and_, or_
            
            query = session.query(Attack)
            
            # Apply filters
            if 'source_ip' in criteria:
                query = query.filter(Attack.source_ip == criteria['source_ip'])
            
            if 'attack_type' in criteria:
                query = query.filter(Attack.attack_type == criteria['attack_type'])
            
            if 'severity' in criteria:
                query = query.filter(Attack.severity == criteria['severity'])
            
            if 'target_port' in criteria:
                query = query.filter(Attack.target_port == criteria['target_port'])
            
            if 'date_from' in criteria:
                query = query.filter(Attack.timestamp >= criteria['date_from'])
            
            if 'date_to' in criteria:
                query = query.filter(Attack.timestamp <= criteria['date_to'])
            
            # Execute query
            attacks = query.order_by(Attack.timestamp.desc()).limit(1000).all()
            
            # Convert to dict format
            results = []
            for attack in attacks:
                results.append({
                    'id': attack.attack_id,
                    'timestamp': attack.timestamp.isoformat(),
                    'source_ip': attack.source_ip,
                    'target_port': attack.target_port,
                    'attack_type': attack.attack_type,
                    'severity': attack.severity,
                    'confidence': attack.confidence,
                    'payload_size': attack.payload_size
                })
            
            return results
            
        finally:
            self.db.close_session(session)
    
    def export_threat_intelligence(self) -> Dict[str, Any]:
        """Export threat intelligence in standard format"""
        return self.reporter.export_threat_intelligence()
    
    def cleanup_old_data(self, days_to_keep: int = 90):
        """Clean up old attack data to manage database size"""
        session = self.db.get_session()
        try:
            from models import Attack, AttackSession, SystemMetrics
            from datetime import timedelta
            
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            # Delete old attacks
            old_attacks = session.query(Attack).filter(Attack.timestamp < cutoff_date)
            deleted_attacks = old_attacks.count()
            old_attacks.delete()
            
            # Delete old sessions
            old_sessions = session.query(AttackSession).filter(AttackSession.start_time < cutoff_date)
            deleted_sessions = old_sessions.count()
            old_sessions.delete()
            
            # Delete old metrics
            old_metrics = session.query(SystemMetrics).filter(SystemMetrics.timestamp < cutoff_date)
            deleted_metrics = old_metrics.count()
            old_metrics.delete()
            
            session.commit()
            
            logger.info(f"Cleanup completed: {deleted_attacks} attacks, {deleted_sessions} sessions, {deleted_metrics} metrics deleted")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Cleanup failed: {e}")
        finally:
            self.db.close_session(session)

# Global integrator instance
honeypot_db = HoneypotDatabaseIntegrator()

# Convenience functions for easy integration
def log_attack(attack_data: Dict[str, Any]) -> str:
    """Quick function to log attack from any component"""
    return honeypot_db.log_attack_event(attack_data)

def log_interaction(interaction_data: Dict[str, Any]):
    """Quick function to log honeypot interaction"""
    return honeypot_db.log_honeypot_interaction(interaction_data)

def get_attacker_profile(ip_address: str) -> Optional[Dict[str, Any]]:
    """Quick function to get attacker profile"""
    return honeypot_db.db.get_attacker_profile(ip_address)

def search_attacks(**criteria) -> List[Dict[str, Any]]:
    """Quick function to search attacks"""
    return honeypot_db.search_attacks(criteria)

def get_dashboard_stats() -> Dict[str, Any]:
    """Quick function to get dashboard statistics"""
    return honeypot_db.get_dashboard_data()

# Async wrapper for integration with async honeypot components
async def async_log_attack(attack_data: Dict[str, Any]) -> str:
    """Async wrapper for logging attacks"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, log_attack, attack_data)

async def async_log_interaction(interaction_data: Dict[str, Any]):
    """Async wrapper for logging interactions"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, log_interaction, interaction_data)
