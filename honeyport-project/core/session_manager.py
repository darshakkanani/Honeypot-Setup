#!/usr/bin/env python3
"""
Session Manager for HoneyPort
Tracks attacker sessions and behavior patterns
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import uuid

class SessionManager:
    """Manages honeypot sessions and tracks attacker behavior"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.session_timeout = 3600  # 1 hour default
        
    def create_session(self, session_id: str, source_ip: str) -> Dict[str, Any]:
        """Create a new session"""
        session_data = {
            "session_id": session_id,
            "source_ip": source_ip,
            "start_time": datetime.now(),
            "last_activity": datetime.now(),
            "requests": [],
            "attack_types": set(),
            "total_requests": 0,
            "success_attempts": 0,
            "failed_attempts": 0,
            "user_agents": set(),
            "unique_urls": set(),
            "geolocation": {},
            "status": "active"
        }
        
        self.sessions[session_id] = session_data
        return session_data
    
    def add_request(self, session_id: str, request_data: Dict[str, Any]):
        """Add a request to session"""
        if session_id not in self.sessions:
            return
        
        session = self.sessions[session_id]
        session["requests"].append(request_data)
        session["last_activity"] = datetime.now()
        session["total_requests"] += 1
        session["attack_types"].add(request_data.get("attack_type", "unknown"))
        session["user_agents"].add(request_data.get("user_agent", ""))
        session["unique_urls"].add(request_data.get("url", ""))
        
        # Track success/failure
        if request_data.get("response_success"):
            session["success_attempts"] += 1
        else:
            session["failed_attempts"] += 1
    
    def end_session(self, session_id: str):
        """End a session"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session["end_time"] = datetime.now()
            session["duration"] = (session["end_time"] - session["start_time"]).total_seconds()
            session["status"] = "ended"
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        return self.sessions.get(session_id)
    
    def get_recent_sessions(self, minutes: int = 60) -> List[Dict[str, Any]]:
        """Get sessions from last N minutes"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        return [session for session in self.sessions.values()
                if session["start_time"] >= cutoff_time]
    
    def cleanup_old_sessions(self, hours: int = 24):
        """Remove old sessions"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        old_sessions = [sid for sid, session in self.sessions.items()
                       if session["start_time"] < cutoff_time]
        
        for session_id in old_sessions:
            del self.sessions[session_id]
        
        if old_sessions:
            print(f"🧹 Cleaned up {len(old_sessions)} old sessions")
