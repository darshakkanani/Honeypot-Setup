#!/usr/bin/env python3
"""
Tests for AI models and components
"""

import pytest
import numpy as np
import torch
from unittest.mock import Mock, patch
from datetime import datetime

from ai_models.feature_extraction import AdvancedFeatureExtractor, AttackContext
from ai_models.neural_networks import AttackerProfiler, ThreatLevelPredictor
from ai_models.ensemble_predictor import ThreatLevelEnsemble, MasterEnsemble
from core.ai_behavior import AdvancedAIEngine

class TestFeatureExtraction:
    
    def test_attack_context_creation(self):
        """Test AttackContext creation"""
        context = AttackContext(
            source_ip="192.168.1.100",
            attack_type="sql_injection",
            payload="' OR 1=1--",
            user_agent="sqlmap/1.0",
            timestamp=datetime.now(),
            session_duration=300.0,
            request_frequency=0.5,
            payload_complexity=50.0,
            geographic_info={"country": "US"},
            previous_attacks=[]
        )
        
        assert context.source_ip == "192.168.1.100"
        assert context.attack_type == "sql_injection"
        assert context.payload_complexity == 50.0
    
    def test_feature_extractor_initialization(self):
        """Test feature extractor initialization"""
        extractor = AdvancedFeatureExtractor()
        assert extractor is not None
        assert not extractor.fitted
    
    def test_feature_extraction(self):
        """Test feature extraction from attack context"""
        extractor = AdvancedFeatureExtractor()
        context = AttackContext(
            source_ip="192.168.1.100",
            attack_type="sql_injection",
            payload="' OR 1=1--",
            user_agent="sqlmap/1.0",
            timestamp=datetime.now(),
            session_duration=300.0,
            request_frequency=0.5,
            payload_complexity=50.0,
            geographic_info={"country": "US"},
            previous_attacks=[]
        )
        
        features = extractor.extract_features(context)
        assert isinstance(features, np.ndarray)
        assert len(features) > 0

class TestNeuralNetworks:
    
    def test_attacker_profiler_creation(self):
        """Test AttackerProfiler model creation"""
        model = AttackerProfiler(input_dim=64, hidden_dim=128, output_dim=64)
        assert model is not None
        
        # Test forward pass
        x = torch.randn(1, 64)
        output = model(x)
        assert output.shape == (1, 64)
    
    def test_threat_level_predictor(self):
        """Test ThreatLevelPredictor model"""
        model = ThreatLevelPredictor(input_dim=64, hidden_dim=128)
        assert model is not None
        
        # Test forward pass
        x = torch.randn(1, 64)
        output = model(x)
        assert output.shape == (1, 1)
        
        # Test output is in valid range after sigmoid
        with torch.no_grad():
            sigmoid_output = torch.sigmoid(output)
            assert 0 <= sigmoid_output.item() <= 1

class TestEnsembleMethods:
    
    def test_threat_level_ensemble_creation(self):
        """Test ThreatLevelEnsemble creation"""
        ensemble = ThreatLevelEnsemble()
        assert ensemble is not None
        assert not ensemble.fitted
    
    def test_ensemble_fitting(self):
        """Test ensemble fitting with mock data"""
        ensemble = ThreatLevelEnsemble()
        
        # Create mock training data
        X = np.random.rand(100, 10)
        y = np.random.randint(0, 2, 100)
        
        ensemble.fit(X, y)
        assert ensemble.fitted
    
    def test_ensemble_prediction(self):
        """Test ensemble prediction"""
        ensemble = ThreatLevelEnsemble()
        
        # Create and fit with mock data
        X_train = np.random.rand(100, 10)
        y_train = np.random.randint(0, 2, 100)
        ensemble.fit(X_train, y_train)
        
        # Test prediction
        X_test = np.random.rand(10, 10)
        predictions = ensemble.predict_threat_level(X_test)
        
        assert len(predictions) == 10
        assert all(0 <= p <= 1 for p in predictions)

class TestAdvancedAIEngine:
    
    def test_ai_engine_initialization(self, test_config):
        """Test AI engine initialization"""
        engine = AdvancedAIEngine(test_config)
        assert engine is not None
        assert engine.ai_enabled == test_config['ai']['enabled']
    
    @patch('core.ai_behavior.ADVANCED_AI_AVAILABLE', True)
    def test_attack_analysis(self, test_config, mock_session_data):
        """Test attack analysis functionality"""
        engine = AdvancedAIEngine(test_config)
        
        # Mock the advanced AI components
        engine.feature_extractor = Mock()
        engine.feature_extractor.transform.return_value = np.random.rand(64)
        
        engine.ensemble = Mock()
        engine.ensemble.fitted = True
        engine.ensemble.predict_comprehensive.return_value = {
            'threat_levels': [0.8],
            'confidence_scores': [0.9]
        }
        
        engine.neural_models = {
            'threat_predictor': Mock(),
            'attacker_profiler': Mock()
        }
        
        result = engine.analyze_attack(mock_session_data)
        
        assert 'threat_level' in result
        assert 'confidence' in result
        assert 'recommendation' in result
    
    def test_legacy_analysis_fallback(self, test_config, mock_session_data):
        """Test fallback to legacy analysis"""
        with patch('core.ai_behavior.ADVANCED_AI_AVAILABLE', False):
            engine = AdvancedAIEngine(test_config)
            
            # Mock legacy models
            engine.anomaly_detector = Mock()
            engine.anomaly_detector.decision_function.return_value = [0.5]
            engine.anomaly_detector.predict.return_value = [-1]
            
            result = engine.analyze_attack(mock_session_data)
            
            assert 'anomaly_score' in result
            assert 'is_anomaly' in result
            assert 'recommendation' in result

class TestIntegration:
    
    def test_end_to_end_analysis(self, test_config):
        """Test end-to-end AI analysis pipeline"""
        # Create attack context
        context = AttackContext(
            source_ip="192.168.1.100",
            attack_type="sql_injection",
            payload="' OR 1=1-- DROP TABLE users",
            user_agent="sqlmap/1.0",
            timestamp=datetime.now(),
            session_duration=300.0,
            request_frequency=2.0,
            payload_complexity=100.0,
            geographic_info={"country": "CN"},
            previous_attacks=[]
        )
        
        # Test feature extraction
        extractor = AdvancedFeatureExtractor()
        features = extractor.extract_features(context)
        
        assert isinstance(features, np.ndarray)
        assert len(features) > 0
        
        # Features should be numeric and finite
        assert np.all(np.isfinite(features))
    
    def test_model_integration(self):
        """Test integration between different AI components"""
        # Create mock data
        X = np.random.rand(50, 64)
        y = np.random.randint(0, 2, 50)
        
        # Test ensemble creation and fitting
        ensemble = MasterEnsemble()
        ensemble.fit(X, y)
        
        # Test prediction
        X_test = np.random.rand(5, 64)
        results = ensemble.predict_comprehensive(X_test)
        
        assert 'threat_levels' in results
        assert 'confidence_scores' in results
