#!/usr/bin/env python3
"""
Pytest configuration and fixtures for HoneyPort tests
"""

import pytest
import tempfile
import os
import shutil
from unittest.mock import Mock, patch
from datetime import datetime
import yaml

@pytest.fixture
def temp_dir():
    """Create temporary directory for tests"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def test_config():
    """Test configuration"""
    return {
        'honeypot': {
            'host': '127.0.0.1',
            'ports': [8080, 2222],
            'ssh_port': 2222,
            'http_port': 8080
        },
        'database': {
            'url': 'sqlite:///:memory:'
        },
        'ai': {
            'enabled': True,
            'models_path': './test_models'
        },
        'blockchain': {
            'enabled': False
        },
        'logging': {
            'level': 'DEBUG'
        }
    }

@pytest.fixture
def mock_attack_data():
    """Mock attack data for testing"""
    return {
        'source_ip': '192.168.1.100',
        'source_port': 12345,
        'destination_port': 80,
        'protocol': 'HTTP',
        'attack_type': 'sql_injection',
        'payload': "' OR 1=1--",
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'timestamp': datetime.now(),
        'session_id': 'test_session_123'
    }

@pytest.fixture
def mock_session_data():
    """Mock session data for AI testing"""
    return {
        'source_ip': '192.168.1.100',
        'attack_type': 'sql_injection',
        'payload': "' OR 1=1--",
        'user_agent': 'sqlmap/1.0',
        'duration': 300,
        'requests': [
            {
                'url': '/login.php',
                'payload': "admin' OR 1=1--",
                'timestamp': datetime.now().timestamp(),
                'attack_type': 'sql_injection'
            }
        ],
        'geolocation': {
            'country': 'US',
            'city': 'New York'
        }
    }

@pytest.fixture
def mock_blockchain():
    """Mock blockchain for testing"""
    with patch('blockchain.log_manager.BlockchainLogManager') as mock:
        mock_instance = Mock()
        mock_instance.log_attack.return_value = 'mock_hash_123'
        mock_instance.verify_integrity.return_value = True
        mock.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_ai_engine():
    """Mock AI engine for testing"""
    with patch('core.ai_behavior.AdvancedAIEngine') as mock:
        mock_instance = Mock()
        mock_instance.analyze_attack.return_value = {
            'threat_level': 0.8,
            'recommendation': 'cautious',
            'confidence': 0.9
        }
        mock.return_value = mock_instance
        yield mock_instance
