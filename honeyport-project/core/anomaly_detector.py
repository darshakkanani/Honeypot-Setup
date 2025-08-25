#!/usr/bin/env python3
"""
AI-based Anomaly Detection for HoneyPort
Detects unusual patterns and sophisticated attacks
"""

import numpy as np
from typing import Dict, List, Any, Optional
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
import os

class AnomalyDetector:
    """AI-powered anomaly detection for honeypot traffic"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.ai_enabled = config.get('ai', {}).get('enabled', False)
        self.models_path = config.get('ai', {}).get('models_path', 'ai_models/')
        self.sensitivity = config.get('ai', {}).get('anomaly_detection', {}).get('sensitivity', 0.8)
        
        self.detector = None
        self.scaler = StandardScaler()
        self.baseline_features = []
        
        if self.ai_enabled:
            self._load_or_create_detector()
    
    def _load_or_create_detector(self):
        """Load existing detector or create new one"""
        detector_path = os.path.join(self.models_path, 'anomaly_model.pkl')
        
        if os.path.exists(detector_path):
            self.detector = joblib.load(detector_path)
            print("🔍 Loaded existing anomaly detector")
        else:
            self.detector = IsolationForest(
                contamination=0.1,
                random_state=42,
                n_estimators=100
            )
            print("🔍 Created new anomaly detector")
    
    def analyze_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze request for anomalies"""
        if not self.ai_enabled or not self.detector:
            return {"anomaly_score": 0.0, "is_anomaly": False}
        
        features = self._extract_anomaly_features(request_data)
        
        try:
            # Get anomaly score
            anomaly_score = self.detector.decision_function([features])[0]
            is_anomaly = self.detector.predict([features])[0] == -1
            
            # Calculate confidence
            confidence = abs(anomaly_score)
            
            return {
                "anomaly_score": float(anomaly_score),
                "is_anomaly": bool(is_anomaly),
                "confidence": float(confidence),
                "features": features.tolist(),
                "analysis_timestamp": request_data.get('timestamp')
            }
            
        except Exception as e:
            print(f"❌ Anomaly detection error: {e}")
            return {"anomaly_score": 0.0, "is_anomaly": False, "error": str(e)}
    
    def _extract_anomaly_features(self, request_data: Dict[str, Any]) -> np.ndarray:
        """Extract features for anomaly detection"""
        features = []
        
        # Request characteristics
        url = request_data.get('url', '')
        method = request_data.get('method', 'GET')
        user_agent = request_data.get('user_agent', '')
        
        # URL features
        features.extend([
            len(url),
            url.count('/'),
            url.count('?'),
            url.count('&'),
            url.count('='),
            1 if any(char in url for char in ['<', '>', '"', "'", ';']) else 0,
        ])
        
        # Method features (one-hot encoding)
        methods = ['GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'OPTIONS']
        for m in methods:
            features.append(1 if method == m else 0)
        
        # Payload features
        payload = request_data.get('payload', {})
        features.extend([
            len(str(payload)),
            len(payload) if isinstance(payload, dict) else 0,
        ])
        
        # Attack pattern features
        attack_patterns = {
            'sql_keywords': ['select', 'union', 'drop', 'insert', 'delete'],
            'xss_patterns': ['script', 'alert', 'onerror', 'onload'],
            'traversal_patterns': ['../', '..\\', '%2e%2e'],
            'command_patterns': [';', '|', '&', '`', '$']
        }
        
        url_lower = url.lower()
        for pattern_type, patterns in attack_patterns.items():
            count = sum(1 for pattern in patterns if pattern in url_lower)
            features.append(count)
        
        # User agent features
        features.extend([
            len(user_agent),
            1 if 'bot' in user_agent.lower() else 0,
            1 if 'curl' in user_agent.lower() else 0,
            1 if 'python' in user_agent.lower() else 0,
            1 if user_agent == '' else 0,
        ])
        
        # Time-based features (hour of day)
        try:
            from datetime import datetime
            timestamp = request_data.get('timestamp', '')
            if timestamp:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                features.extend([
                    dt.hour,
                    1 if dt.weekday() >= 5 else 0,  # Weekend
                ])
            else:
                features.extend([12, 0])  # Default values
        except:
            features.extend([12, 0])
        
        return np.array(features, dtype=float)
    
    def update_baseline(self, normal_requests: List[Dict[str, Any]]):
        """Update baseline with normal traffic patterns"""
        if not self.ai_enabled or not normal_requests:
            return
        
        features_list = []
        for request in normal_requests:
            features = self._extract_anomaly_features(request)
            features_list.append(features)
        
        if features_list:
            X = np.array(features_list)
            self.detector.fit(X)
            
            # Save updated model
            os.makedirs(self.models_path, exist_ok=True)
            detector_path = os.path.join(self.models_path, 'anomaly_model.pkl')
            joblib.dump(self.detector, detector_path)
            
            print(f"🔍 Anomaly detector updated with {len(features_list)} normal samples")
    
    def get_anomaly_stats(self, recent_requests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get anomaly detection statistics"""
        if not self.ai_enabled:
            return {"error": "AI disabled"}
        
        anomaly_results = []
        for request in recent_requests:
            result = self.analyze_request(request)
            anomaly_results.append(result)
        
        total_requests = len(anomaly_results)
        anomalies = [r for r in anomaly_results if r.get('is_anomaly', False)]
        
        return {
            "total_analyzed": total_requests,
            "anomalies_detected": len(anomalies),
            "anomaly_rate": len(anomalies) / total_requests if total_requests > 0 else 0,
            "average_anomaly_score": np.mean([r.get('anomaly_score', 0) for r in anomaly_results]),
            "high_confidence_anomalies": len([r for r in anomalies if r.get('confidence', 0) > 0.8]),
            "detector_status": "active" if self.detector else "inactive"
        }
