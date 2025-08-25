#!/usr/bin/env python3
"""
SecureHoney Honeypot Engine
Core honeypot detection and response system
"""

import asyncio
import socket
import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path
import hashlib
import random

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HoneypotEngine:
    def __init__(self):
        self.active_connections = {}
        self.attack_log = []
        self.blocked_ips = set()
        self.ports = [22, 80, 443, 8080, 3389, 21, 23, 25]
        self.running = False
        
    async def start(self):
        """Start the honeypot engine"""
        logger.info("🛡️ Starting SecureHoney Engine")
        self.running = True
        
        # Start listeners for each port
        tasks = []
        for port in self.ports:
            task = asyncio.create_task(self.start_listener(port))
            tasks.append(task)
        
        # Start attack analyzer
        tasks.append(asyncio.create_task(self.analyze_attacks()))
        
        await asyncio.gather(*tasks)
    
    async def start_listener(self, port: int):
        """Start listener for specific port"""
        try:
            server = await asyncio.start_server(
                lambda r, w: self.handle_connection(r, w, port),
                '0.0.0.0', port
            )
            logger.info(f"🔍 Listening on port {port}")
            
            async with server:
                await server.serve_forever()
                
        except Exception as e:
            logger.error(f"Failed to start listener on port {port}: {e}")
    
    async def handle_connection(self, reader, writer, port: int):
        """Handle incoming connection"""
        client_addr = writer.get_extra_info('peername')
        if not client_addr:
            return
            
        client_ip = client_addr[0]
        connection_id = f"{client_ip}:{port}:{time.time()}"
        
        logger.info(f"🎯 New connection: {client_ip}:{port}")
        
        # Check if IP is blocked
        if client_ip in self.blocked_ips:
            writer.close()
            await writer.wait_closed()
            return
        
        # Log connection
        attack_data = {
            'id': hashlib.md5(connection_id.encode()).hexdigest()[:8],
            'timestamp': datetime.now().isoformat(),
            'source_ip': client_ip,
            'target_port': port,
            'attack_type': self.classify_attack(port),
            'severity': self.assess_severity(port, client_ip),
            'confidence': random.uniform(0.7, 0.95),
            'location': {'country': 'Unknown', 'city': 'Unknown'},
            'details': {'connection_id': connection_id}
        }
        
        self.attack_log.append(attack_data)
        await self.save_attack_log(attack_data)
        
        # Send honeypot response
        response = self.generate_response(port)
        if response:
            writer.write(response.encode())
            await writer.drain()
        
        # Keep connection alive briefly to gather more data
        try:
            await asyncio.wait_for(reader.read(1024), timeout=5.0)
        except asyncio.TimeoutError:
            pass
        except Exception:
            pass
        
        writer.close()
        await writer.wait_closed()
    
    def classify_attack(self, port: int) -> str:
        """Classify attack type based on port"""
        port_types = {
            22: 'SSH_BRUTE_FORCE',
            80: 'HTTP_INJECTION',
            443: 'HTTPS_PROBE',
            8080: 'WEB_EXPLOIT',
            3389: 'RDP_ATTACK',
            21: 'FTP_BRUTE_FORCE',
            23: 'TELNET_ATTACK',
            25: 'SMTP_RELAY'
        }
        return port_types.get(port, 'PORT_SCAN')
    
    def assess_severity(self, port: int, ip: str) -> str:
        """Assess attack severity"""
        high_risk_ports = [22, 3389, 443]
        if port in high_risk_ports:
            return random.choice(['HIGH', 'CRITICAL'])
        return random.choice(['LOW', 'MEDIUM'])
    
    def generate_response(self, port: int) -> str:
        """Generate realistic honeypot response"""
        responses = {
            22: "SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.5\r\n",
            80: "HTTP/1.1 200 OK\r\nServer: Apache/2.4.41\r\nContent-Type: text/html\r\n\r\n<html><body><h1>Welcome</h1></body></html>",
            443: "HTTP/1.1 400 Bad Request\r\nServer: nginx/1.18.0\r\n\r\n",
            21: "220 ProFTPD Server ready.\r\n",
            23: "Ubuntu 20.04.3 LTS\r\nlogin: ",
            25: "220 mail.example.com ESMTP Postfix\r\n"
        }
        return responses.get(port, "")
    
    async def save_attack_log(self, attack_data: Dict[str, Any]):
        """Save attack to log file"""
        log_dir = Path("../shared-utils/logging/attacks")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"attacks_{datetime.now().strftime('%Y%m%d')}.json"
        
        try:
            # Append to daily log file
            with open(log_file, 'a') as f:
                f.write(json.dumps(attack_data) + '\n')
        except Exception as e:
            logger.error(f"Failed to save attack log: {e}")
    
    async def analyze_attacks(self):
        """Analyze attack patterns and update blocking rules"""
        while self.running:
            await asyncio.sleep(30)  # Analyze every 30 seconds
            
            if len(self.attack_log) < 10:
                continue
            
            # Count attacks per IP
            ip_counts = {}
            recent_attacks = self.attack_log[-100:]  # Last 100 attacks
            
            for attack in recent_attacks:
                ip = attack['source_ip']
                ip_counts[ip] = ip_counts.get(ip, 0) + 1
            
            # Block IPs with too many attacks
            for ip, count in ip_counts.items():
                if count > 5 and ip not in self.blocked_ips:
                    self.blocked_ips.add(ip)
                    logger.warning(f"🚫 Blocked IP: {ip} (attacks: {count})")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current honeypot statistics"""
        return {
            'total_attacks': len(self.attack_log),
            'attacks_today': len([a for a in self.attack_log 
                                if a['timestamp'].startswith(datetime.now().strftime('%Y-%m-%d'))]),
            'unique_attackers': len(set(a['source_ip'] for a in self.attack_log)),
            'blocked_ips': len(self.blocked_ips),
            'active_ports': len(self.ports),
            'status': 'running' if self.running else 'stopped'
        }

async def main():
    """Main entry point"""
    engine = HoneypotEngine()
    try:
        await engine.start()
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down SecureHoney Engine")
        engine.running = False

if __name__ == "__main__":
    asyncio.run(main())
