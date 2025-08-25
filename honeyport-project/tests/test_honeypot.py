#!/usr/bin/env python3
"""
Tests for core honeypot functionality
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from core.honeypot import HoneyPot
from core.connection_handler import ConnectionHandler
from core.session_manager import SessionManager

class TestHoneyPot:
    
    @pytest.fixture
    def honeypot(self, test_config):
        """Create honeypot instance for testing"""
        return HoneyPot(test_config)
    
    def test_honeypot_initialization(self, honeypot, test_config):
        """Test honeypot initialization"""
        assert honeypot.config == test_config
        assert honeypot.host == test_config['honeypot']['host']
        assert honeypot.ports == test_config['honeypot']['ports']
    
    @patch('core.honeypot.asyncio.start_server')
    async def test_start_servers(self, mock_start_server, honeypot):
        """Test starting honeypot servers"""
        mock_start_server.return_value = AsyncMock()
        
        await honeypot.start()
        
        # Should start servers for each configured port
        assert mock_start_server.call_count == len(honeypot.ports)
    
    def test_connection_logging(self, honeypot, mock_attack_data):
        """Test connection logging functionality"""
        with patch.object(honeypot, 'log_attack') as mock_log:
            honeypot.handle_connection(mock_attack_data)
            mock_log.assert_called_once()

class TestConnectionHandler:
    
    @pytest.fixture
    def handler(self, test_config):
        """Create connection handler for testing"""
        return ConnectionHandler(test_config)
    
    def test_http_request_parsing(self, handler):
        """Test HTTP request parsing"""
        http_request = b"GET /admin/login.php?id=1' OR 1=1-- HTTP/1.1\r\nHost: example.com\r\nUser-Agent: sqlmap/1.0\r\n\r\n"
        
        parsed = handler.parse_http_request(http_request)
        
        assert parsed['method'] == 'GET'
        assert '/admin/login.php' in parsed['path']
        assert 'sqlmap' in parsed['user_agent']
        assert 'OR 1=1' in parsed['path']  # SQL injection detected
    
    def test_attack_type_detection(self, handler):
        """Test attack type detection"""
        # SQL injection
        sql_payload = "admin' OR 1=1--"
        assert handler.detect_attack_type(sql_payload) == 'sql_injection'
        
        # XSS
        xss_payload = "<script>alert('xss')</script>"
        assert handler.detect_attack_type(xss_payload) == 'xss'
        
        # Directory traversal
        traversal_payload = "../../../../etc/passwd"
        assert handler.detect_attack_type(traversal_payload) == 'directory_traversal'
    
    def test_response_generation(self, handler):
        """Test response generation based on behavior"""
        request_data = {
            'method': 'GET',
            'path': '/admin/login.php',
            'attack_type': 'sql_injection'
        }
        
        response = handler.generate_response(request_data, behavior='enticing')
        
        assert response is not None
        assert isinstance(response, (str, bytes))

class TestSessionManager:
    
    @pytest.fixture
    def session_manager(self):
        """Create session manager for testing"""
        return SessionManager()
    
    def test_session_creation(self, session_manager):
        """Test session creation and tracking"""
        source_ip = "192.168.1.100"
        session_id = session_manager.create_session(source_ip)
        
        assert session_id is not None
        assert session_manager.get_session(session_id) is not None
        assert session_manager.get_session(session_id)['source_ip'] == source_ip
    
    def test_session_update(self, session_manager):
        """Test session updates"""
        source_ip = "192.168.1.100"
        session_id = session_manager.create_session(source_ip)
        
        # Add request to session
        request_data = {
            'method': 'GET',
            'path': '/admin',
            'attack_type': 'reconnaissance'
        }
        
        session_manager.add_request(session_id, request_data)
        
        session = session_manager.get_session(session_id)
        assert len(session['requests']) == 1
        assert session['requests'][0]['path'] == '/admin'
    
    def test_session_expiry(self, session_manager):
        """Test session expiry handling"""
        source_ip = "192.168.1.100"
        session_id = session_manager.create_session(source_ip)
        
        # Manually expire session
        session_manager.expire_session(session_id)
        
        session = session_manager.get_session(session_id)
        assert session['status'] == 'expired'
    
    def test_session_statistics(self, session_manager):
        """Test session statistics calculation"""
        source_ip = "192.168.1.100"
        session_id = session_manager.create_session(source_ip)
        
        # Add multiple requests
        for i in range(5):
            request_data = {
                'method': 'GET',
                'path': f'/path{i}',
                'attack_type': 'reconnaissance'
            }
            session_manager.add_request(session_id, request_data)
        
        stats = session_manager.get_session_stats(session_id)
        
        assert stats['request_count'] == 5
        assert stats['unique_paths'] == 5
        assert 'duration' in stats
