#!/usr/bin/env python3
"""
Alert System for HoneyPort
Real-time alerting for security events and anomalies
"""

import asyncio
import json
import smtplib
from datetime import datetime
from typing import Dict, List, Any, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class AlertSystem:
    """Real-time alerting system for honeypot events"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.alert_config = config.get('alerts', {})
        self.enabled = self.alert_config.get('enabled', True)
        
        # Alert channels
        self.email_enabled = self.alert_config.get('email', {}).get('enabled', False)
        self.webhook_enabled = self.alert_config.get('webhook', {}).get('enabled', False)
        self.log_enabled = self.alert_config.get('log_alerts', True)
        
        # Alert thresholds
        self.severity_threshold = self.alert_config.get('severity_threshold', 'medium')
        self.rate_limit = self.alert_config.get('rate_limit', 10)  # Max alerts per minute
        
        # State tracking
        self.alert_count = 0
        self.last_reset = datetime.now()
        self.recent_alerts = []
        
    async def send_alert(self, alert_data: Dict[str, Any]):
        """Send alert through configured channels"""
        if not self.enabled:
            return
        
        # Rate limiting
        if not self._check_rate_limit():
            return
        
        # Enrich alert data
        enriched_alert = self._enrich_alert(alert_data)
        
        # Send through channels
        tasks = []
        
        if self.email_enabled:
            tasks.append(self._send_email_alert(enriched_alert))
        
        if self.webhook_enabled:
            tasks.append(self._send_webhook_alert(enriched_alert))
        
        if self.log_enabled:
            tasks.append(self._log_alert(enriched_alert))
        
        # Execute all alert tasks
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        # Track alert
        self.recent_alerts.append(enriched_alert)
        if len(self.recent_alerts) > 100:  # Keep last 100 alerts
            self.recent_alerts.pop(0)
    
    def _check_rate_limit(self) -> bool:
        """Check if alert rate limit is exceeded"""
        now = datetime.now()
        
        # Reset counter every minute
        if (now - self.last_reset).total_seconds() >= 60:
            self.alert_count = 0
            self.last_reset = now
        
        if self.alert_count >= self.rate_limit:
            return False
        
        self.alert_count += 1
        return True
    
    def _enrich_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich alert with additional context"""
        enriched = {
            "alert_id": f"hp_{int(datetime.now().timestamp())}",
            "timestamp": datetime.now().isoformat(),
            "honeypot_id": self.config.get('honeypot_id', 'honeyport-001'),
            "severity": self._determine_severity(alert_data),
            **alert_data
        }
        
        return enriched
    
    def _determine_severity(self, alert_data: Dict[str, Any]) -> str:
        """Determine alert severity"""
        alert_type = alert_data.get('type', '')
        
        high_severity_types = [
            'high_severity_attack',
            'multiple_attack_vectors',
            'persistent_attacker',
            'anomalous_behavior'
        ]
        
        medium_severity_types = [
            'sql_injection',
            'xss_attempt',
            'brute_force',
            'directory_traversal'
        ]
        
        if alert_type in high_severity_types:
            return 'high'
        elif alert_type in medium_severity_types:
            return 'medium'
        else:
            return 'low'
    
    async def _send_email_alert(self, alert_data: Dict[str, Any]):
        """Send email alert"""
        try:
            email_config = self.alert_config.get('email', {})
            
            msg = MIMEMultipart()
            msg['From'] = email_config.get('from_address')
            msg['To'] = ', '.join(email_config.get('to_addresses', []))
            msg['Subject'] = f"HoneyPort Alert: {alert_data.get('type', 'Security Event')}"
            
            # Create email body
            body = self._format_email_body(alert_data)
            msg.attach(MIMEText(body, 'html'))
            
            # Send email
            server = smtplib.SMTP(email_config.get('smtp_server'), email_config.get('smtp_port', 587))
            server.starttls()
            server.login(email_config.get('username'), email_config.get('password'))
            server.send_message(msg)
            server.quit()
            
            print(f"📧 Email alert sent: {alert_data.get('type')}")
            
        except Exception as e:
            print(f"❌ Failed to send email alert: {e}")
    
    async def _send_webhook_alert(self, alert_data: Dict[str, Any]):
        """Send webhook alert"""
        try:
            import aiohttp
            
            webhook_config = self.alert_config.get('webhook', {})
            webhook_url = webhook_config.get('url')
            
            if not webhook_url:
                return
            
            payload = {
                "text": f"🚨 HoneyPort Alert: {alert_data.get('type')}",
                "attachments": [{
                    "color": self._get_color_for_severity(alert_data.get('severity')),
                    "fields": [
                        {"title": "Type", "value": alert_data.get('type'), "short": True},
                        {"title": "Source IP", "value": alert_data.get('source_ip'), "short": True},
                        {"title": "Timestamp", "value": alert_data.get('timestamp'), "short": True},
                        {"title": "Severity", "value": alert_data.get('severity'), "short": True}
                    ]
                }]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status == 200:
                        print(f"🔗 Webhook alert sent: {alert_data.get('type')}")
                    else:
                        print(f"❌ Webhook alert failed: {response.status}")
                        
        except Exception as e:
            print(f"❌ Failed to send webhook alert: {e}")
    
    async def _log_alert(self, alert_data: Dict[str, Any]):
        """Log alert to file"""
        try:
            log_file = self.alert_config.get('log_file', 'logs/alerts.log')
            
            with open(log_file, 'a') as f:
                f.write(f"{json.dumps(alert_data)}\n")
            
            print(f"📝 Alert logged: {alert_data.get('type')}")
            
        except Exception as e:
            print(f"❌ Failed to log alert: {e}")
    
    def _format_email_body(self, alert_data: Dict[str, Any]) -> str:
        """Format email body"""
        return f"""
        <html>
        <body>
        <h2>🚨 HoneyPort Security Alert</h2>
        
        <table border="1" cellpadding="5">
        <tr><td><strong>Alert Type:</strong></td><td>{alert_data.get('type', 'Unknown')}</td></tr>
        <tr><td><strong>Severity:</strong></td><td>{alert_data.get('severity', 'Unknown')}</td></tr>
        <tr><td><strong>Source IP:</strong></td><td>{alert_data.get('source_ip', 'Unknown')}</td></tr>
        <tr><td><strong>Timestamp:</strong></td><td>{alert_data.get('timestamp', 'Unknown')}</td></tr>
        <tr><td><strong>Attack Type:</strong></td><td>{alert_data.get('attack_type', 'N/A')}</td></tr>
        </table>
        
        <h3>Details:</h3>
        <pre>{json.dumps(alert_data.get('details', {}), indent=2)}</pre>
        
        <p><em>This alert was generated by HoneyPort honeypot system.</em></p>
        </body>
        </html>
        """
    
    def _get_color_for_severity(self, severity: str) -> str:
        """Get color code for severity"""
        colors = {
            'high': '#ff0000',
            'medium': '#ff8800', 
            'low': '#ffff00'
        }
        return colors.get(severity, '#808080')
    
    def get_alert_stats(self) -> Dict[str, Any]:
        """Get alert system statistics"""
        return {
            "enabled": self.enabled,
            "total_alerts_sent": len(self.recent_alerts),
            "alerts_last_hour": len([a for a in self.recent_alerts 
                                   if (datetime.now() - datetime.fromisoformat(a['timestamp'])).total_seconds() < 3600]),
            "severity_breakdown": {
                severity: len([a for a in self.recent_alerts if a.get('severity') == severity])
                for severity in ['high', 'medium', 'low']
            },
            "channels": {
                "email": self.email_enabled,
                "webhook": self.webhook_enabled,
                "log": self.log_enabled
            },
            "rate_limit": {
                "max_per_minute": self.rate_limit,
                "current_count": self.alert_count
            }
        }
