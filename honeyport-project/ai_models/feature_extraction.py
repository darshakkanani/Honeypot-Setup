#!/usr/bin/env python3
"""
Advanced Feature Extraction for HoneyPort AI
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.decomposition import PCA
from sklearn.feature_selection import SelectKBest, mutual_info_classif
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import Counter, defaultdict
import ipaddress
from dataclasses import dataclass

@dataclass
class AttackContext:
    source_ip: str
    attack_type: str
    payload: str
    user_agent: str
    timestamp: datetime
    session_duration: float
    request_frequency: float
    payload_complexity: float
    geographic_info: Dict[str, Any]
    previous_attacks: List[Dict]
    http_method: str = "GET"
    url_path: str = ""
    headers: Dict[str, str] = None
    response_code: int = 200
    bytes_transferred: int = 0

class TemporalFeatureExtractor:
    def __init__(self):
        self.time_windows = [60, 300, 900, 3600, 86400]
        
    def extract_temporal_features(self, timestamp: datetime, attack_history: List[Dict]) -> np.ndarray:
        features = []
        
        # Basic time features
        features.extend([
            timestamp.hour, timestamp.minute, timestamp.weekday(),
            timestamp.day, timestamp.month
        ])
        
        # Cyclical encoding
        features.extend([
            np.sin(2 * np.pi * timestamp.hour / 24),
            np.cos(2 * np.pi * timestamp.hour / 24),
            np.sin(2 * np.pi * timestamp.weekday() / 7),
            np.cos(2 * np.pi * timestamp.weekday() / 7)
        ])
        
        # Contextual features
        features.extend([
            float(9 <= timestamp.hour <= 17),  # business hours
            float(timestamp.weekday() >= 5),   # weekend
            float(timestamp.hour < 6 or timestamp.hour > 22)  # night
        ])
        
        # Attack frequency in time windows
        current_time = timestamp
        for window in self.time_windows:
            window_start = current_time - timedelta(seconds=window)
            attacks_in_window = sum(1 for attack in attack_history 
                                  if attack.get('timestamp', datetime.min) >= window_start)
            features.append(attacks_in_window)
        
        return np.array(features, dtype=float)

class PayloadFeatureExtractor:
    def __init__(self):
        self.sql_patterns = [
            r"union\s+select", r"order\s+by", r"drop\s+table", r"insert\s+into",
            r"char\s*\(", r"ascii\s*\(", r"information_schema"
        ]
        
        self.xss_patterns = [
            r"<script", r"</script>", r"javascript:", r"alert\s*\(",
            r"document\.", r"eval\s*\("
        ]
        
        self.cmd_patterns = [
            r";\s*cat\s+", r";\s*ls\s+", r";\s*pwd", r"bash\s+-c",
            r"/bin/", r"`.*`", r"\$\(.*\)"
        ]
    
    def extract_payload_features(self, payload: str) -> np.ndarray:
        if not payload:
            return np.zeros(25)
        
        features = []
        payload_lower = payload.lower()
        
        # Basic statistics
        features.extend([
            len(payload), len(payload.split()), len(set(payload)),
            payload.count(' '), payload.count("'"), payload.count('"'),
            payload.count('<'), payload.count('>'), payload.count('&'),
            payload.count('='), payload.count('/'), payload.count(';')
        ])
        
        # Pattern matching
        sql_score = sum(1 for pattern in self.sql_patterns 
                       if re.search(pattern, payload_lower, re.IGNORECASE))
        xss_score = sum(1 for pattern in self.xss_patterns 
                       if re.search(pattern, payload_lower, re.IGNORECASE))
        cmd_score = sum(1 for pattern in self.cmd_patterns 
                       if re.search(pattern, payload_lower, re.IGNORECASE))
        
        features.extend([sql_score, xss_score, cmd_score])
        
        # Entropy
        entropy = self._calculate_entropy(payload)
        features.append(entropy)
        
        # Encoding indicators
        url_encoded = len(re.findall(r'%[0-9a-fA-F]{2}', payload))
        features.append(url_encoded)
        
        return np.array(features, dtype=float)
    
    def _calculate_entropy(self, text: str) -> float:
        if not text:
            return 0.0
        
        char_counts = Counter(text)
        text_length = len(text)
        entropy = 0.0
        
        for count in char_counts.values():
            probability = count / text_length
            if probability > 0:
                entropy -= probability * np.log2(probability)
        
        return entropy

class NetworkFeatureExtractor:
    def extract_network_features(self, source_ip: str, attack_history: List[Dict]) -> np.ndarray:
        features = []
        
        # IP analysis
        try:
            ip_obj = ipaddress.ip_address(source_ip)
            features.extend([
                float(ip_obj.is_private),
                float(ip_obj.is_multicast),
                float(ip_obj.is_reserved)
            ])
            
            if isinstance(ip_obj, ipaddress.IPv4Address):
                octets = [int(x) for x in source_ip.split('.')]
                features.extend(octets)
            else:
                features.extend([0, 0, 0, 0])
                
        except ValueError:
            features.extend([0] * 7)
        
        # Attack history from this IP
        ip_attacks = [attack for attack in attack_history 
                     if attack.get('source_ip') == source_ip]
        
        features.extend([
            len(ip_attacks),
            len(set(attack.get('attack_type', '') for attack in ip_attacks)),
            np.mean([attack.get('severity_score', 0) for attack in ip_attacks]) if ip_attacks else 0
        ])
        
        return np.array(features, dtype=float)

class BehavioralFeatureExtractor:
    def extract_behavioral_features(self, context: AttackContext) -> np.ndarray:
        features = []
        
        # Session features
        features.extend([
            context.session_duration,
            context.request_frequency,
            context.payload_complexity,
            len(context.previous_attacks),
            context.bytes_transferred
        ])
        
        # User agent analysis
        ua_features = self._analyze_user_agent(context.user_agent)
        features.extend(ua_features)
        
        # HTTP features
        features.extend([
            float(context.http_method == 'GET'),
            float(context.http_method == 'POST'),
            len(context.url_path) if context.url_path else 0,
            context.response_code
        ])
        
        # Attack consistency
        if context.previous_attacks:
            attack_types = [attack.get('attack_type', '') for attack in context.previous_attacks]
            type_diversity = len(set(attack_types)) / len(attack_types)
            features.append(1 - type_diversity)
        else:
            features.append(0.5)
        
        return np.array(features, dtype=float)
    
    def _analyze_user_agent(self, user_agent: str) -> List[float]:
        if not user_agent:
            return [0.0] * 6
        
        ua_lower = user_agent.lower()
        return [
            float('mozilla' in ua_lower),
            float('bot' in ua_lower or 'crawler' in ua_lower),
            float('curl' in ua_lower or 'wget' in ua_lower),
            float('python' in ua_lower),
            len(user_agent),
            float(len(user_agent) < 10)
        ]

class AdvancedFeatureExtractor:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Initialize extractors
        self.temporal_extractor = TemporalFeatureExtractor()
        self.payload_extractor = PayloadFeatureExtractor()
        self.network_extractor = NetworkFeatureExtractor()
        self.behavioral_extractor = BehavioralFeatureExtractor()
        
        # Preprocessing
        self.scaler = StandardScaler()
        self.feature_selector = SelectKBest(mutual_info_classif, k=64)
        self.pca = PCA(n_components=64)
        
        self.fitted = False
        
    def extract_features(self, context: AttackContext) -> np.ndarray:
        """Extract comprehensive features"""
        
        temporal_features = self.temporal_extractor.extract_temporal_features(
            context.timestamp, context.previous_attacks
        )
        
        payload_features = self.payload_extractor.extract_payload_features(
            context.payload
        )
        
        network_features = self.network_extractor.extract_network_features(
            context.source_ip, context.previous_attacks
        )
        
        behavioral_features = self.behavioral_extractor.extract_behavioral_features(
            context
        )
        
        # Combine all features
        all_features = np.concatenate([
            temporal_features,
            payload_features,
            network_features,
            behavioral_features
        ])
        
        # Handle NaN values
        all_features = np.nan_to_num(all_features, nan=0.0, posinf=1e6, neginf=-1e6)
        
        return all_features
    
    def fit_transform(self, contexts: List[AttackContext], labels: Optional[List] = None) -> np.ndarray:
        """Fit and transform contexts"""
        
        feature_matrix = np.array([self.extract_features(context) for context in contexts])
        
        # Scale features
        scaled_features = self.scaler.fit_transform(feature_matrix)
        
        # Feature selection
        if labels is not None and len(set(labels)) > 1:
            selected_features = self.feature_selector.fit_transform(scaled_features, labels)
        else:
            selected_features = scaled_features
        
        # Dimensionality reduction
        if selected_features.shape[1] > 64:
            final_features = self.pca.fit_transform(selected_features)
        else:
            final_features = selected_features
            if final_features.shape[1] < 64:
                padding = np.zeros((final_features.shape[0], 64 - final_features.shape[1]))
                final_features = np.hstack([final_features, padding])
        
        self.fitted = True
        return final_features
    
    def transform(self, context: AttackContext) -> np.ndarray:
        """Transform single context"""
        features = self.extract_features(context)
        
        if not self.fitted:
            # Simple transformation if not fitted
            if len(features) > 64:
                return features[:64]
            elif len(features) < 64:
                return np.pad(features, (0, 64 - len(features)))
            return features
        
        # Full pipeline
        scaled_features = self.scaler.transform(features.reshape(1, -1))
        
        if hasattr(self.feature_selector, 'transform'):
            selected_features = self.feature_selector.transform(scaled_features)
        else:
            selected_features = scaled_features
        
        if hasattr(self.pca, 'transform') and selected_features.shape[1] > 64:
            final_features = self.pca.transform(selected_features)
        else:
            final_features = selected_features
            if final_features.shape[1] > 64:
                final_features = final_features[:, :64]
            elif final_features.shape[1] < 64:
                padding = np.zeros((1, 64 - final_features.shape[1]))
                final_features = np.hstack([final_features, padding])
        
        return final_features.flatten()
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance scores"""
        if not self.fitted:
            return {}
        
        importance_scores = {}
        
        if hasattr(self.feature_selector, 'scores_'):
            scores = self.feature_selector.scores_
            selected_indices = self.feature_selector.get_support(indices=True)
            
            for i, idx in enumerate(selected_indices):
                importance_scores[f'feature_{idx}'] = scores[idx]
        
        return importance_scores
    
    def save_extractors(self, path: str):
        """Save fitted extractors"""
        import joblib
        
        extractors = {
            'scaler': self.scaler,
            'feature_selector': self.feature_selector,
            'pca': self.pca,
            'fitted': self.fitted
        }
        
        joblib.dump(extractors, path)
    
    def load_extractors(self, path: str):
        """Load fitted extractors"""
        import joblib
        
        extractors = joblib.load(path)
        
        self.scaler = extractors['scaler']
        self.feature_selector = extractors['feature_selector']
        self.pca = extractors['pca']
        self.fitted = extractors['fitted']
