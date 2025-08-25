#!/usr/bin/env python3
"""
SecureHoney AI Threat Analyzer
Advanced AI-powered attack analysis and classification
"""

import json
import logging
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
import hashlib
import re

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ThreatAnalyzer:
    def __init__(self):
        self.attack_patterns = {}
        self.ip_reputation = {}
        self.threat_signatures = self.load_threat_signatures()
        
    def load_threat_signatures(self) -> Dict[str, Any]:
        """Load known threat signatures"""
        return {
            'malware_patterns': [
                r'\.exe$', r'\.bat$', r'\.scr$', r'\.vbs$',
                r'powershell', r'cmd\.exe', r'wget', r'curl'
            ],
            'sql_injection': [
                r'union\s+select', r'or\s+1=1', r'drop\s+table',
                r'insert\s+into', r'delete\s+from', r'update\s+set'
            ],
            'xss_patterns': [
                r'<script', r'javascript:', r'onerror=', r'onload=',
                r'alert\(', r'document\.cookie', r'eval\('
            ],
            'brute_force_indicators': [
                r'admin', r'root', r'administrator', r'password',
                r'123456', r'qwerty', r'letmein'
            ]
        }
    
    def analyze_attack(self, attack_data: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive attack analysis"""
        analysis = {
            'attack_id': attack_data.get('id'),
            'timestamp': datetime.now().isoformat(),
            'original_data': attack_data,
            'threat_level': 'LOW',
            'confidence': 0.5,
            'attack_vector': 'UNKNOWN',
            'indicators': [],
            'recommendations': []
        }
        
        # Analyze based on attack type
        attack_type = attack_data.get('attack_type', '')
        source_ip = attack_data.get('source_ip', '')
        
        # Port-based analysis
        if 'port' in attack_data or 'target_port' in attack_data:
            port = attack_data.get('target_port', attack_data.get('port'))
            analysis.update(self.analyze_port_attack(port, attack_data))
        
        # IP reputation analysis
        ip_analysis = self.analyze_ip_reputation(source_ip)
        analysis['ip_reputation'] = ip_analysis
        
        # Pattern matching
        pattern_analysis = self.analyze_patterns(attack_data)
        analysis['pattern_matches'] = pattern_analysis
        
        # Update threat level based on analysis
        analysis['threat_level'] = self.calculate_threat_level(analysis)
        analysis['confidence'] = self.calculate_confidence(analysis)
        
        # Generate recommendations
        analysis['recommendations'] = self.generate_recommendations(analysis)
        
        # Update attack patterns for learning
        self.update_attack_patterns(attack_data, analysis)
        
        return analysis
    
    def analyze_port_attack(self, port: int, attack_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze port-specific attacks"""
        port_analysis = {
            'attack_vector': 'NETWORK',
            'service_targeted': self.identify_service(port),
            'risk_level': self.assess_port_risk(port)
        }
        
        critical_ports = [22, 3389, 443, 21, 23]
        if port in critical_ports:
            port_analysis['threat_level'] = 'HIGH'
            port_analysis['indicators'].append(f'Attack on critical port {port}')
        
        return port_analysis
    
    def identify_service(self, port: int) -> str:
        """Identify service running on port"""
        services = {
            22: 'SSH', 80: 'HTTP', 443: 'HTTPS', 21: 'FTP',
            23: 'Telnet', 25: 'SMTP', 53: 'DNS', 110: 'POP3',
            143: 'IMAP', 993: 'IMAPS', 995: 'POP3S', 3389: 'RDP',
            8080: 'HTTP-Alt', 8443: 'HTTPS-Alt'
        }
        return services.get(port, 'Unknown')
    
    def assess_port_risk(self, port: int) -> str:
        """Assess risk level for specific port"""
        high_risk = [22, 3389, 21, 23]
        medium_risk = [80, 443, 8080, 25, 53]
        
        if port in high_risk:
            return 'HIGH'
        elif port in medium_risk:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def analyze_ip_reputation(self, ip: str) -> Dict[str, Any]:
        """Analyze IP reputation and history"""
        reputation = {
            'ip': ip,
            'reputation_score': 0.5,
            'previous_attacks': 0,
            'geographic_risk': 'UNKNOWN',
            'is_tor': False,
            'is_vpn': False
        }
        
        # Check previous attacks from this IP
        if ip in self.ip_reputation:
            reputation['previous_attacks'] = self.ip_reputation[ip]['attack_count']
            reputation['reputation_score'] = max(0.1, 
                reputation['reputation_score'] - (reputation['previous_attacks'] * 0.1))
        
        # Simple geographic risk assessment (mock)
        high_risk_ranges = ['192.168.', '10.', '172.16.']
        if any(ip.startswith(range_) for range_ in high_risk_ranges):
            reputation['geographic_risk'] = 'LOW'  # Internal network
        else:
            reputation['geographic_risk'] = 'MEDIUM'
        
        return reputation
    
    def analyze_patterns(self, attack_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze attack for known patterns"""
        matches = []
        
        # Get text data to analyze
        text_fields = ['user_agent', 'payload', 'request', 'data']
        text_data = ""
        
        for field in text_fields:
            if field in attack_data:
                text_data += str(attack_data[field]).lower() + " "
        
        # Check each pattern category
        for category, patterns in self.threat_signatures.items():
            for pattern in patterns:
                if re.search(pattern, text_data, re.IGNORECASE):
                    matches.append({
                        'category': category,
                        'pattern': pattern,
                        'severity': self.get_pattern_severity(category)
                    })
        
        return matches
    
    def get_pattern_severity(self, category: str) -> str:
        """Get severity level for pattern category"""
        severity_map = {
            'malware_patterns': 'CRITICAL',
            'sql_injection': 'HIGH',
            'xss_patterns': 'MEDIUM',
            'brute_force_indicators': 'MEDIUM'
        }
        return severity_map.get(category, 'LOW')
    
    def calculate_threat_level(self, analysis: Dict[str, Any]) -> str:
        """Calculate overall threat level"""
        score = 0
        
        # Base score from IP reputation
        ip_rep = analysis.get('ip_reputation', {})
        score += (1 - ip_rep.get('reputation_score', 0.5)) * 30
        
        # Score from previous attacks
        score += min(ip_rep.get('previous_attacks', 0) * 5, 20)
        
        # Score from pattern matches
        pattern_matches = analysis.get('pattern_matches', [])
        for match in pattern_matches:
            severity = match.get('severity', 'LOW')
            if severity == 'CRITICAL':
                score += 25
            elif severity == 'HIGH':
                score += 15
            elif severity == 'MEDIUM':
                score += 10
            else:
                score += 5
        
        # Score from port risk
        risk_level = analysis.get('risk_level', 'LOW')
        if risk_level == 'HIGH':
            score += 20
        elif risk_level == 'MEDIUM':
            score += 10
        
        # Determine threat level
        if score >= 70:
            return 'CRITICAL'
        elif score >= 50:
            return 'HIGH'
        elif score >= 30:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def calculate_confidence(self, analysis: Dict[str, Any]) -> float:
        """Calculate confidence in analysis"""
        confidence = 0.5
        
        # Increase confidence based on pattern matches
        pattern_matches = analysis.get('pattern_matches', [])
        confidence += len(pattern_matches) * 0.1
        
        # Increase confidence based on IP history
        ip_rep = analysis.get('ip_reputation', {})
        if ip_rep.get('previous_attacks', 0) > 0:
            confidence += 0.2
        
        # Cap confidence at 0.95
        return min(confidence, 0.95)
    
    def generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate security recommendations"""
        recommendations = []
        
        threat_level = analysis.get('threat_level', 'LOW')
        ip = analysis.get('original_data', {}).get('source_ip', '')
        
        if threat_level in ['HIGH', 'CRITICAL']:
            recommendations.append(f"Immediately block IP {ip}")
            recommendations.append("Increase monitoring for similar attack patterns")
        
        if threat_level in ['MEDIUM', 'HIGH', 'CRITICAL']:
            recommendations.append("Review firewall rules")
            recommendations.append("Check for system vulnerabilities")
        
        pattern_matches = analysis.get('pattern_matches', [])
        for match in pattern_matches:
            category = match.get('category', '')
            if category == 'sql_injection':
                recommendations.append("Review database security and input validation")
            elif category == 'xss_patterns':
                recommendations.append("Implement XSS protection measures")
            elif category == 'malware_patterns':
                recommendations.append("Run full system malware scan")
        
        return list(set(recommendations))  # Remove duplicates
    
    def update_attack_patterns(self, attack_data: Dict[str, Any], analysis: Dict[str, Any]):
        """Update attack patterns for machine learning"""
        source_ip = attack_data.get('source_ip', '')
        
        if source_ip not in self.ip_reputation:
            self.ip_reputation[source_ip] = {
                'attack_count': 0,
                'first_seen': datetime.now().isoformat(),
                'attack_types': []
            }
        
        self.ip_reputation[source_ip]['attack_count'] += 1
        self.ip_reputation[source_ip]['last_seen'] = datetime.now().isoformat()
        
        attack_type = attack_data.get('attack_type', 'UNKNOWN')
        if attack_type not in self.ip_reputation[source_ip]['attack_types']:
            self.ip_reputation[source_ip]['attack_types'].append(attack_type)
    
    def get_threat_intelligence(self) -> Dict[str, Any]:
        """Get current threat intelligence summary"""
        now = datetime.now()
        last_24h = now - timedelta(hours=24)
        
        # Count recent attacks by type
        attack_types = {}
        high_risk_ips = []
        
        for ip, data in self.ip_reputation.items():
            if data['attack_count'] > 5:
                high_risk_ips.append({
                    'ip': ip,
                    'attack_count': data['attack_count'],
                    'attack_types': data['attack_types']
                })
            
            for attack_type in data['attack_types']:
                attack_types[attack_type] = attack_types.get(attack_type, 0) + 1
        
        return {
            'timestamp': now.isoformat(),
            'total_tracked_ips': len(self.ip_reputation),
            'high_risk_ips': len(high_risk_ips),
            'top_attack_types': sorted(attack_types.items(), 
                                     key=lambda x: x[1], reverse=True)[:5],
            'threat_summary': {
                'critical_threats': len([ip for ip, data in self.ip_reputation.items() 
                                       if data['attack_count'] > 10]),
                'active_campaigns': len(set(tuple(data['attack_types']) 
                                          for data in self.ip_reputation.values()))
            }
        }
    
    def save_analysis(self, analysis: Dict[str, Any]):
        """Save analysis results"""
        analysis_dir = Path("../shared-utils/logging/analysis")
        analysis_dir.mkdir(parents=True, exist_ok=True)
        
        analysis_file = analysis_dir / f"threat_analysis_{datetime.now().strftime('%Y%m%d')}.json"
        
        try:
            with open(analysis_file, 'a') as f:
                f.write(json.dumps(analysis) + '\n')
        except Exception as e:
            logger.error(f"Failed to save analysis: {e}")

def main():
    """Main entry point for testing"""
    analyzer = ThreatAnalyzer()
    
    # Test with sample attack data
    sample_attack = {
        'id': 'test_001',
        'source_ip': '192.168.1.100',
        'target_port': 22,
        'attack_type': 'SSH_BRUTE_FORCE',
        'user_agent': 'curl/7.68.0',
        'payload': 'admin:password123'
    }
    
    analysis = analyzer.analyze_attack(sample_attack)
    print(json.dumps(analysis, indent=2))
    
    # Get threat intelligence
    intel = analyzer.get_threat_intelligence()
    print(json.dumps(intel, indent=2))

if __name__ == "__main__":
    main()
