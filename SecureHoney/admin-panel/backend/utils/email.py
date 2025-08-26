"""
Email utilities for notifications and alerts
"""

import smtplib
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Dict, Any
import structlog

from ..core.config import config

logger = structlog.get_logger()

class EmailService:
    """Email service for sending notifications"""
    
    def __init__(self):
        self.smtp_host = config.SMTP_HOST
        self.smtp_port = config.SMTP_PORT
        self.smtp_user = config.SMTP_USER
        self.smtp_password = config.SMTP_PASSWORD
        self.smtp_tls = config.SMTP_TLS
        self.from_email = config.FROM_EMAIL
        
    async def send_email(
        self,
        to_emails: List[str],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """Send email asynchronously"""
        if not self.smtp_host:
            logger.warning("SMTP not configured, skipping email")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_email
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject
            
            # Add text body
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)
            
            # Add HTML body if provided
            if html_body:
                html_part = MIMEText(html_body, 'html')
                msg.attach(html_part)
            
            # Add attachments if provided
            if attachments:
                for attachment in attachments:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment['content'])
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {attachment["filename"]}'
                    )
                    msg.attach(part)
            
            # Send email
            await aiosmtplib.send(
                msg,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                use_tls=self.smtp_tls
            )
            
            logger.info("email_sent", to=to_emails, subject=subject)
            return True
            
        except Exception as e:
            logger.error("email_send_failed", to=to_emails, subject=subject, error=str(e))
            return False
    
    async def send_attack_alert(self, attack_data: Dict[str, Any], recipients: List[str]) -> bool:
        """Send attack alert email"""
        subject = f"🚨 Security Alert: {attack_data.get('attack_type', 'Unknown')} Attack Detected"
        
        body = f"""
Security Alert - Attack Detected

Attack Details:
- Type: {attack_data.get('attack_type', 'Unknown')}
- Severity: {attack_data.get('severity', 'Unknown')}
- Source IP: {attack_data.get('source_ip', 'Unknown')}
- Target Port: {attack_data.get('target_port', 'Unknown')}
- Timestamp: {attack_data.get('timestamp', 'Unknown')}
- Location: {attack_data.get('country', 'Unknown')}

Please review the admin panel for more details.

SecureHoney Security System
        """
        
        html_body = f"""
<html>
<body>
    <h2 style="color: #d32f2f;">🚨 Security Alert - Attack Detected</h2>
    
    <table style="border-collapse: collapse; width: 100%;">
        <tr>
            <td style="border: 1px solid #ddd; padding: 8px; background-color: #f2f2f2;"><strong>Attack Type</strong></td>
            <td style="border: 1px solid #ddd; padding: 8px;">{attack_data.get('attack_type', 'Unknown')}</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 8px; background-color: #f2f2f2;"><strong>Severity</strong></td>
            <td style="border: 1px solid #ddd; padding: 8px;">{attack_data.get('severity', 'Unknown')}</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 8px; background-color: #f2f2f2;"><strong>Source IP</strong></td>
            <td style="border: 1px solid #ddd; padding: 8px;">{attack_data.get('source_ip', 'Unknown')}</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 8px; background-color: #f2f2f2;"><strong>Target Port</strong></td>
            <td style="border: 1px solid #ddd; padding: 8px;">{attack_data.get('target_port', 'Unknown')}</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 8px; background-color: #f2f2f2;"><strong>Timestamp</strong></td>
            <td style="border: 1px solid #ddd; padding: 8px;">{attack_data.get('timestamp', 'Unknown')}</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 8px; background-color: #f2f2f2;"><strong>Location</strong></td>
            <td style="border: 1px solid #ddd; padding: 8px;">{attack_data.get('country', 'Unknown')}</td>
        </tr>
    </table>
    
    <p>Please review the admin panel for more details.</p>
    
    <p><em>SecureHoney Security System</em></p>
</body>
</html>
        """
        
        return await self.send_email(recipients, subject, body, html_body)
    
    async def send_system_alert(self, alert_data: Dict[str, Any], recipients: List[str]) -> bool:
        """Send system alert email"""
        subject = f"⚠️ System Alert: {alert_data.get('title', 'System Issue')}"
        
        body = f"""
System Alert

Alert Details:
- Title: {alert_data.get('title', 'Unknown')}
- Severity: {alert_data.get('severity', 'Unknown')}
- Message: {alert_data.get('message', 'No message provided')}
- Timestamp: {alert_data.get('timestamp', 'Unknown')}

Please check the system status in the admin panel.

SecureHoney Security System
        """
        
        return await self.send_email(recipients, subject, body)

# Global email service instance
email_service = EmailService()

# Convenience functions
async def send_email(to_emails: List[str], subject: str, body: str, html_body: Optional[str] = None) -> bool:
    """Send email using global email service"""
    if isinstance(to_emails, str):
        to_emails = [to_emails]
    
    return await email_service.send_email(to_emails, subject, body, html_body)

async def send_attack_alert(attack_data: Dict[str, Any], recipients: List[str]) -> bool:
    """Send attack alert email"""
    return await email_service.send_attack_alert(attack_data, recipients)

async def send_system_alert(alert_data: Dict[str, Any], recipients: List[str]) -> bool:
    """Send system alert email"""
    return await email_service.send_system_alert(alert_data, recipients)
