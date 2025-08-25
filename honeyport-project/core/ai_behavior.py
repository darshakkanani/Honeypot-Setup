#!/usr/bin/env python3
"""
AI-Powered Dynamic Honeypot Behavior
Advanced AI system with deep learning, reinforcement learning, and ensemble methods
"""

import json
import numpy as np
import pickle
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
import logging

# Add ai_models to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'ai_models'))

try:
    from ai_models.neural_networks import *
    from ai_models.feature_extraction import AdvancedFeatureExtractor, AttackContext
    from ai_models.ensemble_predictor import MasterEnsemble
    from ai_models.training_pipeline import ContinuousLearningManager, create_training_pipeline
    ADVANCED_AI_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Advanced AI modules not available: {e}")
    ADVANCED_AI_AVAILABLE = False

class AdvancedAIEngine:
    """Advanced AI engine with deep learning and ensemble methods"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.ai_enabled = config.get('ai', {}).get('enabled', False)
        self.models_path = config.get('ai', {}).get('models_path', 'ai_models/')
        self.adaptation_threshold = config.get('ai', {}).get('behavior_model', {}).get('adaptation_threshold', 0.7)
        
        # Legacy models (fallback)
        self.behavior_model = None
        self.anomaly_detector = None
        self.scaler = StandardScaler()
        
        # Advanced AI components
        self.feature_extractor = None
        self.ensemble = None
        self.training_manager = None
        self.neural_models = {}
        
        # Initialize advanced AI if available
        if ADVANCED_AI_AVAILABLE and self.ai_enabled:
            self._initialize_advanced_ai()
        elif self.ai_enabled:
            self._initialize_legacy_models()
        
        # Behavior patterns
        self.response_templates = {
            'aggressive': {
                'delay_range': (0.1, 0.5),
                'error_rate': 0.8,
                'fake_success_rate': 0.1,
                'redirect_probability': 0.3
            },
            'cautious': {
                'delay_range': (2.0, 5.0),
                'error_rate': 0.9,
                'fake_success_rate': 0.05,
                'redirect_probability': 0.1
            },
            'enticing': {
                'delay_range': (0.5, 1.5),
                'error_rate': 0.3,
                'fake_success_rate': 0.4,
                'redirect_probability': 0.6
            },
            'realistic': {
                'delay_range': (1.0, 3.0),
                'error_rate': 0.6,
                'fake_success_rate': 0.2,
                'redirect_probability': 0.4
            }
        }
        
        self.current_behavior = 'realistic'
        self.adaptation_history = []
        
    
    def _initialize_advanced_ai(self):
        """Initialize advanced AI components"""
        try:
            # Initialize feature extractor
            self.feature_extractor = AdvancedFeatureExtractor(self.config)
            
            # Initialize ensemble
            self.ensemble = MasterEnsemble(self.config)
            
            # Initialize training pipeline
            self.training_manager = create_training_pipeline()
            if self.config.get('ai', {}).get('continuous_learning', True):
                self.training_manager.start_continuous_learning()
            
            # Initialize neural models
            self._initialize_neural_models()
            
            logging.info("🧠 Advanced AI system initialized successfully")
            
        except Exception as e:
            logging.error(f"Failed to initialize advanced AI: {e}")
            self._initialize_legacy_models()
    
    def _initialize_neural_models(self):
        """Initialize neural network models"""
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Initialize models
        self.neural_models = {
            'attacker_profiler': AttackerProfiler(64, 256, 128).to(device),
            'rl_agent': ReinforcementLearningAgent(64, 10, 256).to(device),
            'pattern_recognizer': AttackPatternRecognizer(64, 256, 3).to(device),
            'threat_predictor': ThreatLevelPredictor(64, 128).to(device),
            'behavior_adapter': BehaviorAdaptationNetwork(64, 128).to(device)
        }
        
        # Load pre-trained models if available
        for model_name, model in self.neural_models.items():
            model_path = os.path.join(self.models_path, f"{model_name}.pth")
            if os.path.exists(model_path):
                try:
                    checkpoint = torch.load(model_path, map_location=device)
                    model.load_state_dict(checkpoint['model_state_dict'])
                    logging.info(f"Loaded {model_name} from checkpoint")
                except Exception as e:
                    logging.warning(f"Failed to load {model_name}: {e}")
    
    def _initialize_legacy_models(self):
        """Initialize or load AI models"""
        behavior_model_path = os.path.join(self.models_path, 'honeypot_model.pkl')
        anomaly_model_path = os.path.join(self.models_path, 'anomaly_model.pkl')
        
        # Load existing models or create new ones
        if os.path.exists(behavior_model_path):
            self.behavior_model = joblib.load(behavior_model_path)
            print("🤖 Loaded existing behavior model")
        else:
            self.behavior_model = RandomForestClassifier(n_estimators=100, random_state=42)
            print("🤖 Created new behavior model")
        
        if os.path.exists(anomaly_model_path):
            self.anomaly_detector = joblib.load(anomaly_model_path)
            print("🔍 Loaded existing anomaly detector")
        else:
            self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
            print("🔍 Created new anomaly detector")
    
    def _create_attack_context(self, session_data: Dict[str, Any]) -> AttackContext:
        """Create AttackContext from session data"""
        requests = session_data.get('requests', [])
        
        # Extract basic info
        source_ip = session_data.get('source_ip', '127.0.0.1')
        attack_type = session_data.get('attack_type', 'reconnaissance')
        payload = session_data.get('payload', '')
        user_agent = session_data.get('user_agent', '')
        timestamp = datetime.now()
        
        # Calculate session metrics
        session_duration = session_data.get('duration', 0)
        request_frequency = len(requests) / max(session_duration, 1)
        payload_complexity = np.mean([len(req.get('payload', '')) for req in requests]) if requests else 0
        
        # Geographic info
        geographic_info = session_data.get('geolocation', {})
        
        # Previous attacks (simplified)
        previous_attacks = session_data.get('previous_attacks', [])
        
        return AttackContext(
            source_ip=source_ip,
            attack_type=attack_type,
            payload=payload,
            user_agent=user_agent,
            timestamp=timestamp,
            session_duration=session_duration,
            request_frequency=request_frequency,
            payload_complexity=payload_complexity,
            geographic_info=geographic_info,
            previous_attacks=previous_attacks,
            http_method=session_data.get('method', 'GET'),
            url_path=session_data.get('url_path', '/'),
            response_code=session_data.get('response_code', 200),
            bytes_transferred=session_data.get('bytes_transferred', 0)
        )
    
    def extract_features(self, session_data: Dict[str, Any]) -> np.ndarray:
        """Extract features from session data for AI analysis"""
        features = []
        
        # Request frequency features
        requests = session_data.get('requests', [])
        features.extend([
            len(requests),  # Total requests
            len(set(req.get('url', '') for req in requests)),  # Unique URLs
            np.mean([len(req.get('payload', '')) for req in requests]) if requests else 0,  # Avg payload size
        ])
        
        # Timing features
        timestamps = [req.get('timestamp', 0) for req in requests]
        if len(timestamps) > 1:
            intervals = np.diff(timestamps)
            features.extend([
                np.mean(intervals),  # Average interval
                np.std(intervals),   # Interval variance
                np.max(intervals),   # Max interval
            ])
        else:
            features.extend([0, 0, 0])
        
        # Attack pattern features
        attack_types = [req.get('attack_type', 'none') for req in requests]
        features.extend([
            attack_types.count('sql_injection'),
            attack_types.count('xss'),
            attack_types.count('directory_traversal'),
            attack_types.count('brute_force'),
        ])
        
        # Session characteristics
        features.extend([
            session_data.get('duration', 0),
            session_data.get('success_rate', 0),
            session_data.get('error_rate', 0),
            len(session_data.get('unique_ips', [])),
        ])
        
        # Geographic and technical features
        geo_data = session_data.get('geolocation', {})
        features.extend([
            1 if geo_data.get('country') in ['CN', 'RU', 'KP'] else 0,  # High-risk countries
            1 if 'bot' in session_data.get('user_agent', '').lower() else 0,  # Bot detection
            session_data.get('port_scan_detected', 0),
        ])
        
        return np.array(features).reshape(1, -1)
    
    def analyze_attack(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive AI-driven attack analysis"""
        if not self.ai_enabled:
            return {"analysis": "AI disabled", "recommendation": self.current_behavior}
        
        # Use advanced AI if available
        if ADVANCED_AI_AVAILABLE and self.feature_extractor:
            return self._advanced_analysis(session_data)
        else:
            return self._legacy_analysis(session_data)
    
    def _advanced_analysis(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Advanced AI analysis using neural networks and ensemble methods"""
        # Create attack context
        context = self._create_attack_context(session_data)
        
        # Extract features
        features = self.feature_extractor.transform(context)
        
        # Ensemble prediction
        if self.ensemble and self.ensemble.fitted:
            ensemble_results = self.ensemble.predict_comprehensive(
                features.reshape(1, -1)
            )
        else:
            ensemble_results = {}
        
        # Neural network predictions
        neural_predictions = self._neural_predictions(features)
        
        # Assess threat level
        threat_level = self._assess_threat_level(features, context)
        
        # Profile attacker
        attacker_profile = self._profile_attacker(features, context)
        
        # Recognize patterns
        pattern_analysis = self._recognize_pattern(features, context)
        
        # Generate response strategy
        response_strategy = self._generate_response_strategy(features, context)
        
        # Add to training data
        if self.training_manager:
            self.training_manager.add_attack_sample(
                context, threat_level, 
                {'sophistication': int(attacker_profile.get('sophistication', 0) > 0.5)}
            )
        
        return {
            "timestamp": datetime.now().isoformat(),
            "threat_level": float(threat_level),
            "attacker_profile": attacker_profile,
            "pattern_analysis": pattern_analysis,
            "response_strategy": response_strategy,
            "ensemble_results": ensemble_results,
            "neural_predictions": neural_predictions,
            "confidence": float(ensemble_results.get('confidence_scores', [0.5])[0]),
            "recommendation": response_strategy.get('behavior', self.current_behavior),
            "adaptation_needed": response_strategy.get('behavior', self.current_behavior) != self.current_behavior,
            "behavioral_insights": self._extract_behavioral_insights(context, neural_predictions)
        }
    
    def _legacy_analysis(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Legacy analysis using traditional ML"""
        features = self.extract_features(session_data)
        
        # Anomaly detection
        anomaly_score = self.anomaly_detector.decision_function(features)[0] if self.anomaly_detector else 0
        is_anomaly = self.anomaly_detector.predict(features)[0] == -1 if self.anomaly_detector else False
        
        # Behavior prediction
        behavior_prediction = None
        confidence = 0.0
        
        if hasattr(self.behavior_model, 'predict_proba'):
            try:
                probabilities = self.behavior_model.predict_proba(features)[0]
                behavior_classes = self.behavior_model.classes_
                max_prob_idx = np.argmax(probabilities)
                behavior_prediction = behavior_classes[max_prob_idx]
                confidence = probabilities[max_prob_idx]
            except Exception:
                behavior_prediction = self.current_behavior
                confidence = 0.5
        
        recommendation = self._get_behavior_recommendation(
            session_data, anomaly_score, is_anomaly, behavior_prediction, confidence
        )
        
        return {
            "timestamp": datetime.now().isoformat(),
            "anomaly_score": float(anomaly_score),
            "is_anomaly": bool(is_anomaly),
            "behavior_prediction": behavior_prediction,
            "confidence": float(confidence),
            "current_behavior": self.current_behavior,
            "recommendation": recommendation,
            "features": features.tolist()[0],
            "adaptation_needed": recommendation != self.current_behavior
        }
    
    def _get_behavior_recommendation(self, session_data: Dict[str, Any], 
                                   anomaly_score: float, is_anomaly: bool,
                                   behavior_prediction: str, confidence: float) -> str:
        """Determine behavior recommendation based on analysis"""
        
        # High-confidence AI prediction
        if confidence > self.adaptation_threshold and behavior_prediction:
            return behavior_prediction
        
        # Anomaly-based recommendations
        if is_anomaly:
            if anomaly_score < -0.5:  # Very anomalous
                return 'cautious'
            else:
                return 'realistic'
        
        # Pattern-based recommendations
        requests = session_data.get('requests', [])
        if not requests:
            return self.current_behavior
        
        # Aggressive attackers (many requests, short intervals)
        if len(requests) > 20 and session_data.get('duration', 0) < 300:
            return 'aggressive'
        
        # Persistent attackers (long sessions)
        if session_data.get('duration', 0) > 1800:  # 30 minutes
            return 'enticing'
        
        # Sophisticated attackers (diverse attack types)
        attack_types = set(req.get('attack_type', 'none') for req in requests)
        if len(attack_types) > 3:
            return 'realistic'
        
        # Default to current behavior
        return self.current_behavior
    
    def adapt_behavior(self, analysis: Dict[str, Any]) -> bool:
        """Adapt honeypot behavior based on AI analysis"""
        if not analysis.get('adaptation_needed', False):
            return False
        
        new_behavior = analysis['recommendation']
        if new_behavior == self.current_behavior:
            return False
        
        # Record adaptation
        adaptation_record = {
            "timestamp": datetime.now().isoformat(),
            "from_behavior": self.current_behavior,
            "to_behavior": new_behavior,
            "trigger": analysis,
            "confidence": analysis.get('confidence', 0.0)
        }
        
        self.adaptation_history.append(adaptation_record)
        self.current_behavior = new_behavior
        
        print(f"🔄 Behavior adapted: {adaptation_record['from_behavior']} → {new_behavior}")
        return True
    
    def get_response_parameters(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get response parameters based on current behavior"""
        behavior_config = self.response_templates.get(self.current_behavior, 
                                                     self.response_templates['realistic'])
        
        # Add randomization
        import random
        
        delay_min, delay_max = behavior_config['delay_range']
        response_delay = random.uniform(delay_min, delay_max)
        
        should_error = random.random() < behavior_config['error_rate']
        should_fake_success = random.random() < behavior_config['fake_success_rate']
        should_redirect = random.random() < behavior_config['redirect_probability']
        
        # Customize based on attack type
        attack_type = request_data.get('attack_type', 'reconnaissance')
        if attack_type == 'sql_injection' and self.current_behavior == 'enticing':
            should_fake_success = True  # Show fake SQL results
        elif attack_type == 'brute_force' and self.current_behavior == 'aggressive':
            response_delay = 0.1  # Quick responses to waste attacker time
        
        return {
            "behavior": self.current_behavior,
            "response_delay": response_delay,
            "should_error": should_error,
            "should_fake_success": should_fake_success,
            "should_redirect": should_redirect,
            "error_message": self._get_error_message(attack_type),
            "success_message": self._get_success_message(attack_type),
            "redirect_url": self._get_redirect_url(attack_type)
        }
    
    def _get_error_message(self, attack_type: str) -> str:
        """Get appropriate error message"""
        error_messages = {
            'sql_injection': "Database connection failed",
            'xss': "Invalid input detected",
            'directory_traversal': "Access denied",
            'brute_force': "Too many login attempts",
            'default': "Internal server error"
        }
        return error_messages.get(attack_type, error_messages['default'])
    
    def _get_success_message(self, attack_type: str) -> str:
        """Get fake success message"""
        success_messages = {
            'sql_injection': "Query executed successfully",
            'brute_force': "Login successful",
            'directory_traversal': "File accessed",
            'default': "Operation completed"
        }
        return success_messages.get(attack_type, success_messages['default'])
    
    def _get_redirect_url(self, attack_type: str) -> str:
        """Get redirect URL"""
        redirect_urls = {
            'sql_injection': "/admin/database",
            'brute_force': "/admin/dashboard",
            'directory_traversal': "/files/",
            'default': "/admin/"
        }
        return redirect_urls.get(attack_type, redirect_urls['default'])
    
    def train_model(self, training_data: List[Dict[str, Any]]) -> bool:
        """Train AI models with historical data"""
        if not self.ai_enabled or not training_data:
            return False
        
        try:
            # Prepare training data
            X = []
            y = []
            
            for session in training_data:
                features = self.extract_features(session).flatten()
                X.append(features)
                y.append(session.get('optimal_behavior', 'realistic'))
            
            X = np.array(X)
            y = np.array(y)
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train behavior model
            if len(set(y)) > 1:  # Need multiple classes
                X_train, X_test, y_train, y_test = train_test_split(
                    X_scaled, y, test_size=0.2, random_state=42
                )
                
                self.behavior_model.fit(X_train, y_train)
                score = self.behavior_model.score(X_test, y_test)
                print(f"🎯 Behavior model trained with accuracy: {score:.3f}")
            
            # Train anomaly detector
            self.anomaly_detector.fit(X_scaled)
            print("🔍 Anomaly detector trained")
            
            # Save models
            os.makedirs(self.models_path, exist_ok=True)
            joblib.dump(self.behavior_model, os.path.join(self.models_path, 'honeypot_model.pkl'))
            joblib.dump(self.anomaly_detector, os.path.join(self.models_path, 'anomaly_model.pkl'))
            joblib.dump(self.scaler, os.path.join(self.models_path, 'scaler.pkl'))
            
            return True
            
        except Exception as e:
            print(f"❌ Model training failed: {e}")
            return False
    
    def get_ai_insights(self) -> Dict[str, Any]:
        """Get comprehensive AI insights and statistics"""
        insights = {
            "ai_enabled": self.ai_enabled,
            "advanced_ai_available": ADVANCED_AI_AVAILABLE,
            "current_behavior": self.current_behavior,
            "total_adaptations": len(self.adaptation_history),
            "recent_adaptations": self.adaptation_history[-10:],
            "behavior_distribution": {
                behavior: sum(1 for a in self.adaptation_history 
                            if a['to_behavior'] == behavior)
                for behavior in self.response_templates.keys()
            },
            "model_status": {
                "behavior_model_loaded": self.behavior_model is not None,
                "anomaly_detector_loaded": self.anomaly_detector is not None,
                "models_path": self.models_path
            }
        }
        
        # Advanced AI status
        if ADVANCED_AI_AVAILABLE:
            insights["advanced_ai_status"] = {
                "feature_extractor_loaded": self.feature_extractor is not None,
                "ensemble_loaded": self.ensemble is not None,
                "training_manager_active": self.training_manager is not None,
                "neural_models_loaded": list(self.neural_models.keys()),
                "continuous_learning_active": (
                    self.training_manager.running if self.training_manager else False
                )
            }
            
            if self.training_manager:
                insights["training_status"] = self.training_manager.get_training_status()
        
        return insights

# Backward compatibility alias
AIBehaviorEngine = AdvancedAIEngine
