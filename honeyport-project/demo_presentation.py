#!/usr/bin/env python3
"""
HoneyPort AI-Powered Honeypot - Complete Demo for Presentation
Perfect streamlined version with all features working
"""

import asyncio
import json
import time
import uuid
from datetime import datetime
from typing import Dict, Any
import yaml
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.ai_behavior import AIBehaviorEngine
from blockchain.log_manager import BlockchainLogManager

class HoneyPortDemo:
    """Complete HoneyPort demo for presentation"""
    
    def __init__(self):
        # Load configuration
        with open("config.yaml", 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Initialize components
        self.ai_engine = AIBehaviorEngine(self.config)
        self.log_manager = BlockchainLogManager(self.config)
        
        # Demo state
        self.running = False
        self.attack_count = 0
        self.sessions = {}
        
        print("🍯 HoneyPort AI-Powered Honeypot Demo Initialized")
        print("🤖 AI Behavior Engine: ACTIVE")
        print("⛓️  Blockchain Logger: ACTIVE")
        print("=" * 60)
    
    async def start_demo(self):
        """Start the complete demo"""
        self.running = True
        
        # Start HTTP server for honeypot
        server = await asyncio.start_server(
            self.handle_connection,
            self.config['network']['bind_address'],
            self.config['network']['honeypot_port']
        )
        
        print(f"🚀 HoneyPort Demo running on port {self.config['network']['honeypot_port']}")
        print("🎯 Try these attacks:")
        print(f"   SQL Injection: curl \"http://localhost:{self.config['network']['honeypot_port']}/admin?id=1' OR 1=1--\"")
        print(f"   XSS Attack: curl \"http://localhost:{self.config['network']['honeypot_port']}/search?q=<script>alert('xss')</script>\"")
        print(f"   Brute Force: curl -X POST \"http://localhost:{self.config['network']['honeypot_port']}/wp-admin\" -d \"user=admin&pass=123\"")
        print("=" * 60)
        
        # Start background tasks
        asyncio.create_task(self.demo_ai_adaptation())
        asyncio.create_task(self.demo_blockchain_mining())
        
        async with server:
            await server.serve_forever()
    
    async def handle_connection(self, reader, writer):
        """Handle incoming connections with AI and blockchain logging"""
        client_address = writer.get_extra_info('peername')
        client_ip = client_address[0] if client_address else 'unknown'
        
        try:
            # Read request
            data = await reader.read(4096)
            if not data:
                return
            
            request_str = data.decode('utf-8', errors='ignore')
            
            # Parse request
            request_data = self._parse_request(request_str, client_ip)
            
            # AI Analysis
            session_data = self._get_or_create_session(client_ip, request_data)
            ai_analysis = self.ai_engine.analyze_attacker_behavior(session_data)
            response_params = self.ai_engine.get_response_parameters(request_data)
            
            # Generate AI-powered response
            response = self._generate_response(request_data, response_params)
            
            # Apply AI delay
            if response_params.get('response_delay', 0) > 0:
                await asyncio.sleep(response_params['response_delay'])
            
            # Send response
            writer.write(response.encode('utf-8'))
            await writer.drain()
            
            # Log to blockchain
            log_data = {
                **request_data,
                "ai_behavior": response_params.get('behavior'),
                "ai_confidence": ai_analysis.get('confidence', 0),
                "response_delay": response_params.get('response_delay'),
                "blockchain_block": self.log_manager.get_latest_block_hash()
            }
            
            log_id = self.log_manager.log_attack(log_data)
            
            # Console output for demo
            self.attack_count += 1
            print(f"\n🚨 Attack #{self.attack_count} Detected!")
            print(f"   Source: {client_ip}")
            print(f"   Type: {request_data.get('attack_type', 'unknown').upper()}")
            print(f"   AI Behavior: {response_params.get('behavior', 'realistic').upper()}")
            print(f"   Blockchain Log: {log_id[:16]}...")
            
            # Adapt AI behavior if needed
            if ai_analysis.get('adaptation_needed'):
                adapted = self.ai_engine.adapt_behavior(ai_analysis)
                if adapted:
                    print(f"🤖 AI Adapted: {ai_analysis['current_behavior']} → {ai_analysis['recommendation']}")
            
        except Exception as e:
            print(f"❌ Error handling connection: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
    
    def _parse_request(self, request_str: str, client_ip: str) -> Dict[str, Any]:
        """Parse HTTP request and detect attack patterns"""
        lines = request_str.split('\n')
        if not lines:
            return {}
        
        # Parse request line
        request_line = lines[0].strip()
        parts = request_line.split(' ')
        method = parts[0] if len(parts) > 0 else 'GET'
        url = parts[1] if len(parts) > 1 else '/'
        
        # Detect attack type
        attack_type, severity = self._detect_attack_type(url, request_str)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "source_ip": client_ip,
            "method": method,
            "url": url,
            "attack_type": attack_type,
            "severity": severity,
            "raw_request": request_str[:500],
            "user_agent": self._extract_user_agent(request_str)
        }
    
    def _detect_attack_type(self, url: str, request_str: str) -> tuple:
        """Detect attack patterns"""
        url_lower = url.lower()
        
        # SQL Injection
        sql_patterns = ["'", "union", "select", "drop", "or 1=1", "--"]
        if any(pattern in url_lower for pattern in sql_patterns):
            return "sql_injection", "high"
        
        # XSS
        xss_patterns = ["<script", "javascript:", "alert(", "onerror="]
        if any(pattern in url_lower for pattern in xss_patterns):
            return "xss", "medium"
        
        # Directory Traversal
        if "../" in url_lower or "..%2f" in url_lower:
            return "directory_traversal", "medium"
        
        # Admin/Login attempts
        if any(path in url_lower for path in ["/admin", "/wp-admin", "/login"]):
            return "brute_force", "medium"
        
        return "reconnaissance", "low"
    
    def _extract_user_agent(self, request_str: str) -> str:
        """Extract User-Agent header"""
        for line in request_str.split('\n'):
            if line.lower().startswith('user-agent:'):
                return line.split(':', 1)[1].strip()
        return "Unknown"
    
    def _get_or_create_session(self, client_ip: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get or create session for client"""
        if client_ip not in self.sessions:
            self.sessions[client_ip] = {
                "session_id": str(uuid.uuid4()),
                "source_ip": client_ip,
                "start_time": datetime.now(),
                "requests": [],
                "attack_types": set(),
                "total_requests": 0
            }
        
        session = self.sessions[client_ip]
        session["requests"].append(request_data)
        session["attack_types"].add(request_data.get("attack_type", "unknown"))
        session["total_requests"] += 1
        session["duration"] = (datetime.now() - session["start_time"]).total_seconds()
        
        return session
    
    def _generate_response(self, request_data: Dict[str, Any], response_params: Dict[str, Any]) -> str:
        """Generate AI-powered response"""
        url = request_data.get('url', '/')
        attack_type = request_data.get('attack_type', 'reconnaissance')
        behavior = response_params.get('behavior', 'realistic')
        
        # WordPress Admin Panel
        if '/wp-admin' in url or '/admin' in url:
            if response_params.get('should_fake_success'):
                return self._wordpress_success_response()
            else:
                return self._wordpress_error_response()
        
        # SQL Injection Response
        elif attack_type == 'sql_injection':
            if behavior == 'enticing' and response_params.get('should_fake_success'):
                return self._sql_fake_data_response()
            else:
                return self._sql_error_response()
        
        # XSS Response
        elif attack_type == 'xss':
            return self._xss_response(request_data.get('url', ''))
        
        # Default response
        else:
            return self._default_response()
    
    def _wordpress_success_response(self) -> str:
        """Fake WordPress success"""
        return """HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n
<!DOCTYPE html><html><head><title>WordPress Dashboard</title></head>
<body style="font-family:Arial;background:#f1f1f1;margin:0;padding:20px;">
<div style="background:white;padding:20px;border-radius:5px;max-width:800px;margin:0 auto;">
<h1 style="color:#23282d;">🎯 WordPress Dashboard</h1>
<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:20px;margin:20px 0;">
<div style="background:#0073aa;color:white;padding:15px;border-radius:5px;text-align:center;">
<h3>Posts</h3><p style="font-size:24px;margin:5px 0;">42</p></div>
<div style="background:#00a32a;color:white;padding:15px;border-radius:5px;text-align:center;">
<h3>Pages</h3><p style="font-size:24px;margin:5px 0;">8</p></div>
<div style="background:#ff6900;color:white;padding:15px;border-radius:5px;text-align:center;">
<h3>Comments</h3><p style="font-size:24px;margin:5px 0;">156</p></div>
</div>
<p>✅ Login successful! Welcome back, admin.</p>
<p>🔒 Last login: 2 hours ago from 192.168.1.100</p>
</div></body></html>"""
    
    def _wordpress_error_response(self) -> str:
        """WordPress login error"""
        return """HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n
<!DOCTYPE html><html><head><title>WordPress Login</title></head>
<body style="font-family:Arial;background:#f1f1f1;margin:0;padding:20px;">
<div style="background:white;padding:30px;border-radius:5px;max-width:400px;margin:100px auto;">
<h1 style="color:#23282d;text-align:center;">WordPress</h1>
<div style="background:#dc3232;color:white;padding:10px;border-radius:3px;margin:20px 0;">
<strong>ERROR:</strong> Invalid username or password.
</div>
<form><input type="text" placeholder="Username" style="width:100%;padding:10px;margin:10px 0;border:1px solid #ddd;">
<input type="password" placeholder="Password" style="width:100%;padding:10px;margin:10px 0;border:1px solid #ddd;">
<button style="width:100%;padding:10px;background:#0073aa;color:white;border:none;border-radius:3px;">Log In</button>
</form></div></body></html>"""
    
    def _sql_fake_data_response(self) -> str:
        """Fake SQL data to entice attacker"""
        return """HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n
<!DOCTYPE html><html><head><title>Database Query Results</title></head>
<body style="font-family:Arial;margin:20px;">
<h2>🗄️ Query Results</h2>
<table border="1" style="border-collapse:collapse;width:100%;">
<tr style="background:#f0f0f0;"><th>ID</th><th>Username</th><th>Email</th><th>Role</th><th>Last Login</th></tr>
<tr><td>1</td><td>admin</td><td>admin@company.com</td><td>administrator</td><td>2024-08-25 10:30:15</td></tr>
<tr><td>2</td><td>john_doe</td><td>john@company.com</td><td>editor</td><td>2024-08-25 09:15:42</td></tr>
<tr><td>3</td><td>jane_smith</td><td>jane@company.com</td><td>author</td><td>2024-08-24 16:22:18</td></tr>
<tr><td>4</td><td>mike_wilson</td><td>mike@company.com</td><td>subscriber</td><td>2024-08-23 14:45:33</td></tr>
</table>
<p>✅ Query executed successfully. 4 rows returned.</p>
</body></html>"""
    
    def _sql_error_response(self) -> str:
        """SQL error response"""
        return """HTTP/1.1 500 Internal Server Error\r\nContent-Type: text/html\r\n\r\n
<!DOCTYPE html><html><head><title>Database Error</title></head>
<body style="font-family:Arial;margin:20px;">
<h1 style="color:#d63384;">Database Error</h1>
<p>You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near '' at line 1</p>
<p><strong>Error Code:</strong> 1064</p>
</body></html>"""
    
    def _xss_response(self, url: str) -> str:
        """XSS response (safely handled)"""
        # Safely reflect the URL without executing scripts
        safe_url = url.replace('<', '&lt;').replace('>', '&gt;')
        return f"""HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n
<!DOCTYPE html><html><head><title>Search Results</title></head>
<body style="font-family:Arial;margin:20px;">
<h1>🔍 Search Results</h1>
<p>You searched for: <code>{safe_url}</code></p>
<p>No results found for your query.</p>
<p><em>Search processed and logged for security analysis.</em></p>
</body></html>"""
    
    def _default_response(self) -> str:
        """Default honeypot response"""
        return """HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n
<!DOCTYPE html><html><head><title>SecureCorpTech</title></head>
<body style="font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);margin:0;padding:50px;">
<div style="background:white;padding:40px;border-radius:10px;max-width:600px;margin:0 auto;text-align:center;">
<h1 style="color:#333;margin-bottom:20px;">🛡️ SecureCorpTech</h1>
<h2 style="color:#666;">Enterprise Security Solutions</h2>
<p style="color:#888;line-height:1.6;">Protecting businesses with advanced cybersecurity technologies and threat intelligence.</p>
<div style="margin:30px 0;padding:20px;background:#f8f9fa;border-radius:5px;">
<h3>Our Services</h3>
<p>• Network Security Monitoring</p>
<p>• Threat Detection & Response</p>
<p>• Security Consulting</p>
</div>
<p style="font-size:12px;color:#aaa;">© 2024 SecureCorpTech. All rights reserved.</p>
</div></body></html>"""
    
    async def demo_ai_adaptation(self):
        """Demo AI adaptation in background"""
        while self.running:
            await asyncio.sleep(30)  # Every 30 seconds
            
            if self.sessions:
                # Show AI insights
                insights = self.ai_engine.get_ai_insights()
                print(f"\n🤖 AI Status Update:")
                print(f"   Current Behavior: {insights['current_behavior'].upper()}")
                print(f"   Total Adaptations: {insights['total_adaptations']}")
                print(f"   Active Sessions: {len(self.sessions)}")
    
    async def demo_blockchain_mining(self):
        """Demo blockchain mining in background"""
        while self.running:
            await asyncio.sleep(60)  # Every minute
            
            # Force mining if we have pending logs
            if hasattr(self.log_manager, 'blockchain') and self.log_manager.blockchain:
                pending_count = len(self.log_manager.blockchain.pending_logs)
                if pending_count > 0:
                    print(f"\n⛓️  Mining blockchain block with {pending_count} logs...")
                    self.log_manager.blockchain.mine_pending_logs()
                    print(f"✅ Block mined! Chain length: {len(self.log_manager.blockchain.chain)}")

async def main():
    """Main demo function"""
    print("🍯 HoneyPort AI-Powered Honeypot - Presentation Demo")
    print("=" * 60)
    
    demo = HoneyPortDemo()
    
    try:
        await demo.start_demo()
    except KeyboardInterrupt:
        print("\n🛑 Demo stopped by user")
        demo.running = False
    except Exception as e:
        print(f"❌ Demo error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
