"""
Advanced AI/ML Attack Analysis Engine
Real-time threat detection and behavioral analysis using machine learning
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import joblib
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import structlog
import json
import hashlib
from pathlib import Path

from ..core.database import get_db
from ..core.redis import RedisCache
from ..models.attack import Attack
from .threat_intelligence import ThreatIntelligence

logger = structlog.get_logger()

class MLAttackAnalyzer:
    """Advanced ML-based attack analysis engine"""
    
    def __init__(self, model_path: str = "/app/models"):
        self.model_path = Path(model_path)
        self.model_path.mkdir(exist_ok=True)
        
        # Models
        self.anomaly_detector = None
        self.attack_classifier = None
        self.behavioral_analyzer = None
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        
        # Feature extractors
        self.feature_cache = {}
        self.behavioral_patterns = {}
        
        # Threat intelligence
        self.threat_intel = ThreatIntelligence()
        
        # Model performance tracking
        self.model_metrics = {
            "accuracy": 0.0,
            "precision": 0.0,
            "recall": 0.0,
            "f1_score": 0.0,
            "last_trained": None,
            "predictions_made": 0,
            "false_positives": 0,
            "false_negatives": 0
        }
    
    async def initialize_models(self):
        """Initialize and load ML models"""
        try:
            # Load existing models if available
            await self._load_models()
            
            # If no models exist, train initial models
            if not self.anomaly_detector:
                await self._train_initial_models()
            
            logger.info("ml_analyzer_initialized", 
                       models_loaded=bool(self.anomaly_detector),
                       model_path=str(self.model_path))
                       
        except Exception as e:
            logger.error("ml_analyzer_init_failed", error=str(e))
            # Create basic models as fallback
            self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
            self.attack_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
    
    async def analyze_attack(self, attack_data: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive attack analysis using multiple ML techniques"""
        try:
            # Extract features
            features = await self._extract_features(attack_data)
            
            # Anomaly detection
            anomaly_score = await self._detect_anomaly(features)
            
            # Attack classification
            attack_prediction = await self._classify_attack(features)
            
            # Behavioral analysis
            behavioral_analysis = await self._analyze_behavior(attack_data)
            
            # Threat intelligence enrichment
            threat_intel = await self.threat_intel.enrich_attack(attack_data)
            
            # Risk assessment
            risk_score = await self._calculate_risk_score(
                anomaly_score, attack_prediction, behavioral_analysis, threat_intel
            )
            
            # Generate recommendations
            recommendations = await self._generate_recommendations(
                attack_data, risk_score, threat_intel
            )
            
            analysis_result = {
                "attack_id": attack_data.get("id"),
                "timestamp": datetime.utcnow().isoformat(),
                "ml_analysis": {
                    "anomaly_score": float(anomaly_score),
                    "attack_type_prediction": attack_prediction,
                    "behavioral_analysis": behavioral_analysis,
                    "risk_score": float(risk_score),
                    "confidence": self._calculate_confidence(anomaly_score, attack_prediction),
                    "threat_level": self._determine_threat_level(risk_score)
                },
                "threat_intelligence": threat_intel,
                "recommendations": recommendations,
                "features_analyzed": len(features),
                "model_version": self._get_model_version()
            }
            
            # Cache analysis for future reference
            await self._cache_analysis(attack_data.get("id"), analysis_result)
            
            # Update model metrics
            self.model_metrics["predictions_made"] += 1
            
            logger.info("attack_analyzed", 
                       attack_id=attack_data.get("id"),
                       risk_score=risk_score,
                       threat_level=analysis_result["ml_analysis"]["threat_level"])
            
            return analysis_result
            
        except Exception as e:
            logger.error("attack_analysis_failed", 
                        attack_id=attack_data.get("id"), 
                        error=str(e))
            return self._get_fallback_analysis(attack_data)
    
    async def _extract_features(self, attack_data: Dict[str, Any]) -> np.ndarray:
        """Extract numerical features from attack data for ML analysis"""
        features = []
        
        # Basic features
        features.extend([
            attack_data.get("target_port", 0),
            attack_data.get("payload_size", 0),
            attack_data.get("session_duration", 0),
            attack_data.get("confidence_score", 0.0),
        ])
        
        # Time-based features
        timestamp = datetime.fromisoformat(attack_data.get("timestamp", datetime.utcnow().isoformat()))
        features.extend([
            timestamp.hour,
            timestamp.weekday(),
            timestamp.day,
            timestamp.month
        ])
        
        # IP-based features
        source_ip = attack_data.get("source_ip", "0.0.0.0")
        ip_features = await self._extract_ip_features(source_ip)
        features.extend(ip_features)
        
        # Attack type encoding
        attack_type = attack_data.get("attack_type", "UNKNOWN")
        attack_type_encoded = self._encode_attack_type(attack_type)
        features.append(attack_type_encoded)
        
        # Severity encoding
        severity = attack_data.get("severity", "LOW")
        severity_encoded = self._encode_severity(severity)
        features.append(severity_encoded)
        
        # Geographic features
        location = attack_data.get("location", {})
        features.extend([
            location.get("coordinates", {}).get("latitude", 0.0) or 0.0,
            location.get("coordinates", {}).get("longitude", 0.0) or 0.0,
        ])
        
        # Request features (if available)
        headers = attack_data.get("request_headers", {})
        features.extend([
            len(headers),
            len(attack_data.get("user_agent", "")),
            attack_data.get("response_code", 0)
        ])
        
        # Historical features for this IP
        historical_features = await self._get_historical_features(source_ip)
        features.extend(historical_features)
        
        return np.array(features, dtype=float)
    
    async def _extract_ip_features(self, ip_address: str) -> List[float]:
        """Extract features from IP address"""
        try:
            # Convert IP to numerical representation
            ip_parts = ip_address.split('.')
            if len(ip_parts) == 4:
                ip_numeric = sum(int(part) * (256 ** (3 - i)) for i, part in enumerate(ip_parts))
                
                # IP range features
                is_private = self._is_private_ip(ip_address)
                is_reserved = self._is_reserved_ip(ip_address)
                
                return [
                    float(ip_numeric),
                    float(is_private),
                    float(is_reserved),
                    float(int(ip_parts[0])),  # First octet
                    float(int(ip_parts[1])),  # Second octet
                ]
            else:
                return [0.0, 0.0, 0.0, 0.0, 0.0]
                
        except Exception:
            return [0.0, 0.0, 0.0, 0.0, 0.0]
    
    async def _get_historical_features(self, ip_address: str) -> List[float]:
        """Get historical attack features for IP address"""
        try:
            # Check cache first
            cache_key = f"ip_history:{ip_address}"
            cached = await RedisCache.get(cache_key)
            
            if cached:
                return json.loads(cached)
            
            # Query database for historical data
            async with get_db() as db:
                from sqlalchemy import text
                
                result = await db.execute(text("""
                    SELECT 
                        COUNT(*) as total_attacks,
                        COUNT(DISTINCT attack_type) as unique_attack_types,
                        AVG(payload_size) as avg_payload_size,
                        MAX(created_at) as last_attack,
                        COUNT(CASE WHEN severity = 'CRITICAL' THEN 1 END) as critical_count,
                        COUNT(CASE WHEN blocked = true THEN 1 END) as blocked_count
                    FROM attacks 
                    WHERE source_ip = $1 
                    AND created_at >= NOW() - INTERVAL '30 days'
                """), [ip_address])
                
                row = result.fetchone()
                
                if row:
                    # Calculate time since last attack
                    last_attack = row.last_attack
                    hours_since_last = 0.0
                    if last_attack:
                        hours_since_last = (datetime.utcnow() - last_attack).total_seconds() / 3600
                    
                    features = [
                        float(row.total_attacks or 0),
                        float(row.unique_attack_types or 0),
                        float(row.avg_payload_size or 0),
                        float(hours_since_last),
                        float(row.critical_count or 0),
                        float(row.blocked_count or 0)
                    ]
                else:
                    features = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
                
                # Cache for 5 minutes
                await RedisCache.set(cache_key, json.dumps(features), expire=300)
                return features
                
        except Exception as e:
            logger.error("historical_features_error", ip=ip_address, error=str(e))
            return [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    
    async def _detect_anomaly(self, features: np.ndarray) -> float:
        """Detect anomalies using Isolation Forest"""
        try:
            if self.anomaly_detector is None:
                return 0.5  # Neutral score
            
            # Reshape for single prediction
            features_scaled = self.scaler.transform(features.reshape(1, -1))
            
            # Get anomaly score (-1 for anomaly, 1 for normal)
            anomaly_prediction = self.anomaly_detector.predict(features_scaled)[0]
            
            # Get anomaly score (lower values indicate anomalies)
            anomaly_score = self.anomaly_detector.decision_function(features_scaled)[0]
            
            # Normalize to 0-1 range (higher values indicate more anomalous)
            normalized_score = max(0.0, min(1.0, (0.5 - anomaly_score) + 0.5))
            
            return normalized_score
            
        except Exception as e:
            logger.error("anomaly_detection_error", error=str(e))
            return 0.5
    
    async def _classify_attack(self, features: np.ndarray) -> Dict[str, Any]:
        """Classify attack type and predict severity"""
        try:
            if self.attack_classifier is None:
                return {"predicted_type": "UNKNOWN", "confidence": 0.0, "probabilities": {}}
            
            # Reshape for single prediction
            features_scaled = self.scaler.transform(features.reshape(1, -1))
            
            # Predict attack type
            prediction = self.attack_classifier.predict(features_scaled)[0]
            
            # Get prediction probabilities
            probabilities = self.attack_classifier.predict_proba(features_scaled)[0]
            
            # Get class names
            classes = self.attack_classifier.classes_
            
            # Create probability dictionary
            prob_dict = {str(cls): float(prob) for cls, prob in zip(classes, probabilities)}
            
            return {
                "predicted_type": str(prediction),
                "confidence": float(max(probabilities)),
                "probabilities": prob_dict
            }
            
        except Exception as e:
            logger.error("attack_classification_error", error=str(e))
            return {"predicted_type": "UNKNOWN", "confidence": 0.0, "probabilities": {}}
    
    async def _analyze_behavior(self, attack_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze behavioral patterns of the attack"""
        try:
            source_ip = attack_data.get("source_ip")
            
            # Get recent attacks from same IP
            behavioral_data = await self._get_behavioral_data(source_ip)
            
            # Analyze patterns
            patterns = {
                "attack_frequency": self._calculate_attack_frequency(behavioral_data),
                "target_diversity": self._calculate_target_diversity(behavioral_data),
                "time_pattern": self._analyze_time_patterns(behavioral_data),
                "escalation_pattern": self._detect_escalation(behavioral_data),
                "persistence_score": self._calculate_persistence(behavioral_data)
            }
            
            # Behavioral risk assessment
            behavioral_risk = self._assess_behavioral_risk(patterns)
            
            return {
                "patterns": patterns,
                "behavioral_risk": behavioral_risk,
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("behavioral_analysis_error", error=str(e))
            return {"patterns": {}, "behavioral_risk": 0.5}
    
    async def _get_behavioral_data(self, source_ip: str) -> List[Dict]:
        """Get recent behavioral data for IP address"""
        try:
            async with get_db() as db:
                from sqlalchemy import text
                
                result = await db.execute(text("""
                    SELECT 
                        target_port, attack_type, severity, created_at,
                        payload_size, session_duration
                    FROM attacks 
                    WHERE source_ip = $1 
                    AND created_at >= NOW() - INTERVAL '7 days'
                    ORDER BY created_at DESC
                    LIMIT 100
                """), [source_ip])
                
                return [dict(row) for row in result.fetchall()]
                
        except Exception as e:
            logger.error("behavioral_data_error", ip=source_ip, error=str(e))
            return []
    
    async def _calculate_risk_score(self, anomaly_score: float, attack_prediction: Dict, 
                                  behavioral_analysis: Dict, threat_intel: Dict) -> float:
        """Calculate comprehensive risk score"""
        try:
            # Weight different components
            weights = {
                "anomaly": 0.3,
                "classification": 0.25,
                "behavioral": 0.25,
                "threat_intel": 0.2
            }
            
            # Anomaly component
            anomaly_component = anomaly_score * weights["anomaly"]
            
            # Classification component
            classification_confidence = attack_prediction.get("confidence", 0.0)
            classification_component = classification_confidence * weights["classification"]
            
            # Behavioral component
            behavioral_risk = behavioral_analysis.get("behavioral_risk", 0.5)
            behavioral_component = behavioral_risk * weights["behavioral"]
            
            # Threat intelligence component
            threat_score = threat_intel.get("threat_score", 0.0)
            threat_component = threat_score * weights["threat_intel"]
            
            # Calculate final risk score
            risk_score = (anomaly_component + classification_component + 
                         behavioral_component + threat_component)
            
            # Normalize to 0-1 range
            risk_score = max(0.0, min(1.0, risk_score))
            
            return risk_score
            
        except Exception as e:
            logger.error("risk_calculation_error", error=str(e))
            return 0.5
    
    async def _generate_recommendations(self, attack_data: Dict, risk_score: float, 
                                      threat_intel: Dict) -> List[str]:
        """Generate actionable recommendations based on analysis"""
        recommendations = []
        
        try:
            # High risk recommendations
            if risk_score > 0.8:
                recommendations.extend([
                    "IMMEDIATE ACTION: Block source IP immediately",
                    "Escalate to security team for investigation",
                    "Monitor for similar attack patterns",
                    "Consider implementing additional firewall rules"
                ])
            elif risk_score > 0.6:
                recommendations.extend([
                    "Consider blocking source IP",
                    "Increase monitoring for this IP address",
                    "Review attack payload for indicators"
                ])
            elif risk_score > 0.4:
                recommendations.extend([
                    "Monitor source IP for repeated attempts",
                    "Log attack details for pattern analysis"
                ])
            
            # Threat intelligence based recommendations
            if threat_intel.get("is_known_malicious", False):
                recommendations.append("Source IP is known malicious - block immediately")
            
            if threat_intel.get("is_tor_exit", False):
                recommendations.append("Traffic from Tor exit node - consider additional scrutiny")
            
            # Attack type specific recommendations
            attack_type = attack_data.get("attack_type", "")
            if attack_type == "BRUTE_FORCE":
                recommendations.append("Implement account lockout policies")
            elif attack_type == "SQL_INJECTION":
                recommendations.append("Review database security and input validation")
            elif attack_type == "XSS":
                recommendations.append("Implement content security policies")
            
            return recommendations
            
        except Exception as e:
            logger.error("recommendation_generation_error", error=str(e))
            return ["Review attack manually for appropriate response"]
    
    async def retrain_models(self, force_retrain: bool = False) -> Dict[str, Any]:
        """Retrain ML models with latest attack data"""
        try:
            # Check if retraining is needed
            if not force_retrain and not await self._should_retrain():
                return {"status": "skipped", "reason": "No retraining needed"}
            
            logger.info("ml_model_retraining_started")
            
            # Get training data
            training_data = await self._prepare_training_data()
            
            if len(training_data) < 100:
                return {"status": "failed", "reason": "Insufficient training data"}
            
            # Prepare features and labels
            X, y = await self._prepare_features_labels(training_data)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train anomaly detector
            self.anomaly_detector = IsolationForest(
                contamination=0.1, 
                random_state=42,
                n_estimators=200
            )
            self.anomaly_detector.fit(X_train_scaled)
            
            # Train attack classifier
            self.attack_classifier = RandomForestClassifier(
                n_estimators=200,
                max_depth=10,
                random_state=42,
                class_weight='balanced'
            )
            self.attack_classifier.fit(X_train_scaled, y_train)
            
            # Evaluate models
            y_pred = self.attack_classifier.predict(X_test_scaled)
            
            # Update metrics
            from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
            
            self.model_metrics.update({
                "accuracy": float(accuracy_score(y_test, y_pred)),
                "precision": float(precision_score(y_test, y_pred, average='weighted')),
                "recall": float(recall_score(y_test, y_pred, average='weighted')),
                "f1_score": float(f1_score(y_test, y_pred, average='weighted')),
                "last_trained": datetime.utcnow().isoformat(),
                "training_samples": len(X_train)
            })
            
            # Save models
            await self._save_models()
            
            logger.info("ml_model_retraining_completed", metrics=self.model_metrics)
            
            return {
                "status": "success",
                "metrics": self.model_metrics,
                "training_samples": len(X_train),
                "test_samples": len(X_test)
            }
            
        except Exception as e:
            logger.error("ml_model_retraining_failed", error=str(e))
            return {"status": "failed", "error": str(e)}
    
    async def _save_models(self):
        """Save trained models to disk"""
        try:
            # Save models
            joblib.dump(self.anomaly_detector, self.model_path / "anomaly_detector.pkl")
            joblib.dump(self.attack_classifier, self.model_path / "attack_classifier.pkl")
            joblib.dump(self.scaler, self.model_path / "scaler.pkl")
            joblib.dump(self.label_encoder, self.model_path / "label_encoder.pkl")
            
            # Save metrics
            with open(self.model_path / "metrics.json", "w") as f:
                json.dump(self.model_metrics, f, indent=2)
            
            logger.info("ml_models_saved", path=str(self.model_path))
            
        except Exception as e:
            logger.error("ml_model_save_failed", error=str(e))
    
    async def _load_models(self):
        """Load trained models from disk"""
        try:
            model_files = {
                "anomaly_detector.pkl": "anomaly_detector",
                "attack_classifier.pkl": "attack_classifier", 
                "scaler.pkl": "scaler",
                "label_encoder.pkl": "label_encoder"
            }
            
            for filename, attr_name in model_files.items():
                file_path = self.model_path / filename
                if file_path.exists():
                    setattr(self, attr_name, joblib.load(file_path))
            
            # Load metrics
            metrics_file = self.model_path / "metrics.json"
            if metrics_file.exists():
                with open(metrics_file, "r") as f:
                    self.model_metrics.update(json.load(f))
            
            logger.info("ml_models_loaded", path=str(self.model_path))
            
        except Exception as e:
            logger.error("ml_model_load_failed", error=str(e))
    
    # Helper methods
    def _encode_attack_type(self, attack_type: str) -> float:
        """Encode attack type to numerical value"""
        attack_types = {
            "BRUTE_FORCE": 1.0, "SQL_INJECTION": 2.0, "XSS": 3.0,
            "PORT_SCAN": 4.0, "DDOS": 5.0, "MALWARE": 6.0,
            "PHISHING": 7.0, "UNKNOWN": 0.0
        }
        return attack_types.get(attack_type, 0.0)
    
    def _encode_severity(self, severity: str) -> float:
        """Encode severity to numerical value"""
        severities = {"LOW": 1.0, "MEDIUM": 2.0, "HIGH": 3.0, "CRITICAL": 4.0}
        return severities.get(severity, 1.0)
    
    def _is_private_ip(self, ip: str) -> bool:
        """Check if IP is in private range"""
        try:
            parts = [int(x) for x in ip.split('.')]
            return (parts[0] == 10 or 
                   (parts[0] == 172 and 16 <= parts[1] <= 31) or
                   (parts[0] == 192 and parts[1] == 168))
        except:
            return False
    
    def _is_reserved_ip(self, ip: str) -> bool:
        """Check if IP is in reserved range"""
        try:
            parts = [int(x) for x in ip.split('.')]
            return (parts[0] == 127 or parts[0] == 0 or parts[0] >= 224)
        except:
            return False
    
    def _calculate_confidence(self, anomaly_score: float, attack_prediction: Dict) -> float:
        """Calculate overall confidence in analysis"""
        classification_confidence = attack_prediction.get("confidence", 0.0)
        anomaly_confidence = 1.0 - abs(anomaly_score - 0.5) * 2  # Higher for extreme values
        return (classification_confidence + anomaly_confidence) / 2
    
    def _determine_threat_level(self, risk_score: float) -> str:
        """Determine threat level based on risk score"""
        if risk_score >= 0.8:
            return "CRITICAL"
        elif risk_score >= 0.6:
            return "HIGH"
        elif risk_score >= 0.4:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _get_model_version(self) -> str:
        """Get current model version"""
        return hashlib.md5(str(self.model_metrics).encode()).hexdigest()[:8]
    
    async def _cache_analysis(self, attack_id: str, analysis: Dict):
        """Cache analysis results"""
        cache_key = f"ml_analysis:{attack_id}"
        await RedisCache.set(cache_key, json.dumps(analysis), expire=3600)
    
    def _get_fallback_analysis(self, attack_data: Dict) -> Dict:
        """Get fallback analysis when ML fails"""
        return {
            "attack_id": attack_data.get("id"),
            "timestamp": datetime.utcnow().isoformat(),
            "ml_analysis": {
                "anomaly_score": 0.5,
                "attack_type_prediction": {"predicted_type": "UNKNOWN", "confidence": 0.0},
                "behavioral_analysis": {"patterns": {}, "behavioral_risk": 0.5},
                "risk_score": 0.5,
                "confidence": 0.0,
                "threat_level": "MEDIUM"
            },
            "threat_intelligence": {},
            "recommendations": ["Manual review required - ML analysis failed"],
            "features_analyzed": 0,
            "model_version": "fallback"
        }

# Global ML analyzer instance
ml_analyzer = MLAttackAnalyzer()

# Convenience functions
async def analyze_attack_ml(attack_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze attack using ML engine"""
    return await ml_analyzer.analyze_attack(attack_data)

async def retrain_ml_models(force: bool = False) -> Dict[str, Any]:
    """Retrain ML models"""
    return await ml_analyzer.retrain_models(force)

async def get_ml_metrics() -> Dict[str, Any]:
    """Get ML model metrics"""
    return ml_analyzer.model_metrics
