#!/usr/bin/env python3
"""
Main HoneyPort Engine
AI-powered dynamic honeypot with blockchain logging
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import yaml
import uuid
from .ai_behavior import AIBehaviorEngine
from .session_manager import SessionManager
from .connection_handler import ConnectionHandler
from .anomaly_detector import AnomalyDetector
from .alert_system import AlertSystem
from blockchain.log_manager import BlockchainLogManager

class HoneyPortEngine:
    """Main honeypot engine with AI and blockchain integration"""
    
    def __init__(self, config_path: str = "config.yaml"):
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Initialize components
        self.ai_engine = AIBehaviorEngine(self.config)
        self.session_manager = SessionManager(self.config)
        self.connection_handler = ConnectionHandler(self.config, self.ai_engine)
        self.anomaly_detector = AnomalyDetector(self.config)
        self.alert_system = AlertSystem(self.config)
        self.log_manager = BlockchainLogManager(self.config)
        
        # Server state
        self.running = False
        self.servers = []
        self.stats = {
            "start_time": None,
            "total_connections": 0,
            "total_attacks": 0,
            "blocked_ips": set(),
            "active_sessions": {}
        }
        
        print("🍯 HoneyPort Engine initialized with AI and blockchain")
    
    async def start(self):
        """Start the honeypot engine"""
        if self.running:
            return
        
        self.running = True
        self.stats["start_time"] = datetime.now()
        
        # Start honeypot listeners
        honeypot_port = self.config['network']['honeypot_port']
        bind_address = self.config['network']['bind_address']
        
        # Main honeypot server
        server = await asyncio.start_server(
            self.handle_connection,
            bind_address,
            honeypot_port
        )
        self.servers.append(server)
        
        print(f"🚀 HoneyPort listening on {bind_address}:{honeypot_port}")
        
        # Start background tasks
        asyncio.create_task(self.ai_analysis_loop())
        asyncio.create_task(self.cleanup_loop())
        
        # Serve forever
        async with server:
            await server.serve_forever()
    
    async def handle_connection(self, reader, writer):
        """Handle incoming connections"""
        client_address = writer.get_extra_info('peername')
        client_ip = client_address[0] if client_address else 'unknown'
        
        # Check if IP is blocked
        if client_ip in self.stats["blocked_ips"]:
            writer.close()
            await writer.wait_closed()
            return
        
        # Create session
        session_id = str(uuid.uuid4())
        session_data = self.session_manager.create_session(session_id, client_ip)
        
        self.stats["total_connections"] += 1
        self.stats["active_sessions"][session_id] = session_data
        
        try:
            # Read request
            data = await reader.read(4096)
            if not data:
                return
            
            request_str = data.decode('utf-8', errors='ignore')
            
            # Parse and analyze request
            request_data = self._parse_request(request_str, client_ip, session_id)
            
            # AI-powered anomaly detection
            anomaly_result = self.anomaly_detector.analyze_request(request_data)
            
            # Update session
            self.session_manager.add_request(session_id, request_data)
            
            # Get AI-powered response
            ai_analysis = self.ai_engine.analyze_attacker_behavior(session_data)
            response_params = self.ai_engine.get_response_parameters(request_data)
            
            # Generate response
            response = await self.connection_handler.generate_response(
                request_data, response_params, anomaly_result
            )
            
            # Apply AI-suggested delay
            if response_params.get('response_delay', 0) > 0:
                await asyncio.sleep(response_params['response_delay'])
            
            # Send response
            writer.write(response.encode('utf-8'))
            await writer.drain()
            
            # Log to blockchain
            await self._log_interaction(request_data, response_params, ai_analysis, anomaly_result)
            
            # Check for alerts
            await self._check_alerts(request_data, anomaly_result, ai_analysis)
            
        except Exception as e:
            print(f"❌ Error handling connection from {client_ip}: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
            
            # Update session end time
            if session_id in self.stats["active_sessions"]:
                self.session_manager.end_session(session_id)
                del self.stats["active_sessions"][session_id]
    
    def _parse_request(self, request_str: str, client_ip: str, session_id: str) -> Dict[str, Any]:
        """Parse HTTP request and extract attack patterns"""
        lines = request_str.split('\n')
        if not lines:
            return {}
        
        # Parse request line
        request_line = lines[0].strip()
        parts = request_line.split(' ')
        method = parts[0] if len(parts) > 0 else 'UNKNOWN'
        url = parts[1] if len(parts) > 1 else '/'
        
        # Extract headers
        headers = {}
        for line in lines[1:]:
            if ':' in line:
                key, value = line.split(':', 1)
                headers[key.strip().lower()] = value.strip()
        
        # Detect attack patterns
        attack_type, severity = self._detect_attack_patterns(url, request_str)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "source_ip": client_ip,
            "method": method,
            "url": url,
            "headers": headers,
            "raw_request": request_str[:1000],  # Truncate for storage
            "attack_type": attack_type,
            "severity": severity,
            "user_agent": headers.get('user-agent', ''),
            "content_length": int(headers.get('content-length', 0)),
            "payload": self._extract_payload(request_str)
        }
    
    def _detect_attack_patterns(self, url: str, request_str: str) -> tuple:
        """Detect attack patterns in request"""
        url_lower = url.lower()
        request_lower = request_str.lower()
        
        # SQL Injection patterns
        sql_patterns = ["'", "union", "select", "drop", "insert", "delete", "update", "or 1=1", "--"]
        if any(pattern in url_lower for pattern in sql_patterns):
            return "sql_injection", "high"
        
        # XSS patterns
        xss_patterns = ["<script", "javascript:", "alert(", "onerror=", "onload="]
        if any(pattern in url_lower for pattern in xss_patterns):
            return "xss", "medium"
        
        # Directory traversal
        traversal_patterns = ["../", "..\\", "..%2f", "..%5c"]
        if any(pattern in url_lower for pattern in traversal_patterns):
            return "directory_traversal", "medium"
        
        # Command injection
        cmd_patterns = [";", "|", "&", "`", "$(", "${"]
        if any(pattern in url_lower for pattern in cmd_patterns):
            return "command_injection", "high"
        
        # Brute force (multiple auth attempts)
        if any(path in url_lower for path in ["/admin", "/login", "/wp-admin"]):
            return "brute_force", "medium"
        
        # Port scanning / reconnaissance
        if method := self._extract_method(request_str):
            if method in ["OPTIONS", "TRACE", "HEAD"]:
                return "reconnaissance", "low"
        
        return "reconnaissance", "low"
    
    def _extract_method(self, request_str: str) -> str:
        """Extract HTTP method from request"""
        first_line = request_str.split('\n')[0] if request_str else ''
        return first_line.split(' ')[0] if ' ' in first_line else 'UNKNOWN'
    
    def _extract_payload(self, request_str: str) -> Dict[str, Any]:
        """Extract POST payload or query parameters"""
        payload = {}
        
        # Extract query parameters
        if '?' in request_str:
            query_part = request_str.split('?')[1].split(' ')[0]
            for param in query_part.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    payload[key] = value
        
        # Extract POST data
        if '\r\n\r\n' in request_str:
            post_data = request_str.split('\r\n\r\n', 1)[1]
            if post_data:
                payload['post_data'] = post_data[:500]  # Truncate
        
        return payload
    
    async def _log_interaction(self, request_data: Dict[str, Any], 
                             response_params: Dict[str, Any],
                             ai_analysis: Dict[str, Any],
                             anomaly_result: Dict[str, Any]):
        """Log interaction to blockchain"""
        log_data = {
            **request_data,
            "response_behavior": response_params.get('behavior'),
            "response_delay": response_params.get('response_delay'),
            "ai_analysis": ai_analysis,
            "anomaly_score": anomaly_result.get('anomaly_score'),
            "geolocation": await self._get_geolocation(request_data['source_ip'])
        }
        
        if request_data['attack_type'] != 'reconnaissance':
            self.stats["total_attacks"] += 1
        
        # Log to blockchain
        log_id = self.log_manager.log_attack(log_data)
        
        # Log AI decision
        if ai_analysis.get('adaptation_needed'):
            self.log_manager.log_ai_decision({
                "model_name": "behavior_engine",
                "decision": ai_analysis['recommendation'],
                "confidence": ai_analysis['confidence'],
                "input_features": ai_analysis.get('features', []),
                "adaptation_made": True
            })
    
    async def _get_geolocation(self, ip: str) -> Dict[str, Any]:
        """Get geolocation data for IP (placeholder)"""
        # In production, integrate with IP geolocation service
        return {
            "country": "Unknown",
            "city": "Unknown",
            "latitude": 0.0,
            "longitude": 0.0
        }
    
    async def _check_alerts(self, request_data: Dict[str, Any],
                          anomaly_result: Dict[str, Any],
                          ai_analysis: Dict[str, Any]):
        """Check if alerts should be triggered"""
        # High severity attacks
        if request_data['severity'] == 'high':
            await self.alert_system.send_alert({
                "type": "high_severity_attack",
                "source_ip": request_data['source_ip'],
                "attack_type": request_data['attack_type'],
                "timestamp": request_data['timestamp'],
                "details": request_data
            })
        
        # Anomalous behavior
        if anomaly_result.get('is_anomaly') and anomaly_result.get('anomaly_score', 0) < -0.8:
            await self.alert_system.send_alert({
                "type": "anomalous_behavior",
                "source_ip": request_data['source_ip'],
                "anomaly_score": anomaly_result['anomaly_score'],
                "timestamp": request_data['timestamp'],
                "ai_analysis": ai_analysis
            })
        
        # Rate limiting
        if self._should_block_ip(request_data['source_ip']):
            self.stats["blocked_ips"].add(request_data['source_ip'])
            await self.alert_system.send_alert({
                "type": "ip_blocked",
                "source_ip": request_data['source_ip'],
                "reason": "rate_limit_exceeded",
                "timestamp": request_data['timestamp']
            })
    
    def _should_block_ip(self, ip: str) -> bool:
        """Check if IP should be blocked based on rate limiting"""
        # Simple rate limiting implementation
        # In production, use more sophisticated rate limiting
        current_time = time.time()
        session_count = sum(1 for session in self.stats["active_sessions"].values()
                          if session.get('source_ip') == ip)
        return session_count > 10
    
    async def ai_analysis_loop(self):
        """Background task for AI analysis and adaptation"""
        while self.running:
            try:
                # Analyze recent sessions for AI adaptation
                recent_sessions = self.session_manager.get_recent_sessions(minutes=30)
                
                for session in recent_sessions:
                    if len(session.get('requests', [])) > 5:  # Enough data for analysis
                        ai_analysis = self.ai_engine.analyze_attacker_behavior(session)
                        
                        # Adapt behavior if needed
                        if ai_analysis.get('adaptation_needed'):
                            adapted = self.ai_engine.adapt_behavior(ai_analysis)
                            if adapted:
                                print(f"🤖 AI adapted behavior based on session {session['session_id']}")
                
                await asyncio.sleep(300)  # Run every 5 minutes
                
            except Exception as e:
                print(f"❌ AI analysis loop error: {e}")
                await asyncio.sleep(60)
    
    async def cleanup_loop(self):
        """Background cleanup task"""
        while self.running:
            try:
                # Clean up old sessions
                self.session_manager.cleanup_old_sessions(hours=24)
                
                # Force blockchain mining if needed
                if hasattr(self.log_manager, 'blockchain') and self.log_manager.blockchain:
                    if len(self.log_manager.blockchain.pending_logs) > 50:
                        self.log_manager.blockchain.mine_pending_logs()
                
                await asyncio.sleep(3600)  # Run every hour
                
            except Exception as e:
                print(f"❌ Cleanup loop error: {e}")
                await asyncio.sleep(300)
    
    async def stop(self):
        """Stop the honeypot engine"""
        self.running = False
        
        for server in self.servers:
            server.close()
            await server.wait_closed()
        
        print("🛑 HoneyPort engine stopped")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get honeypot statistics"""
        uptime = (datetime.now() - self.stats["start_time"]).total_seconds() if self.stats["start_time"] else 0
        
        return {
            "uptime_seconds": uptime,
            "total_connections": self.stats["total_connections"],
            "total_attacks": self.stats["total_attacks"],
            "active_sessions": len(self.stats["active_sessions"]),
            "blocked_ips": len(self.stats["blocked_ips"]),
            "current_behavior": self.ai_engine.current_behavior,
            "ai_adaptations": len(self.ai_engine.adaptation_history),
            "blockchain_stats": self.log_manager.verify_chain_integrity() if self.log_manager.blockchain_enabled else None
        }
