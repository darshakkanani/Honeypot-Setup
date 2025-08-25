#!/usr/bin/env python3
"""
Ensemble Prediction System for HoneyPort AI
Advanced ensemble methods combining multiple AI models for robust predictions
"""

import numpy as np
import torch
import torch.nn as nn
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.ensemble import IsolationForest, LocalOutlierFactor
from sklearn.cluster import DBSCAN, KMeans
from sklearn.svm import OneClassSVM
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from typing import Dict, List, Any, Tuple, Optional, Union
import joblib
import os
from collections import defaultdict
import logging

class ThreatLevelEnsemble:
    """Ensemble for threat level prediction combining multiple algorithms"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Base models for threat prediction
        self.models = {
            'random_forest': RandomForestClassifier(
                n_estimators=200,
                max_depth=15,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1
            ),
            'gradient_boosting': GradientBoostingClassifier(
                n_estimators=150,
                learning_rate=0.1,
                max_depth=8,
                random_state=42
            ),
            'isolation_forest': IsolationForest(
                contamination=0.1,
                random_state=42,
                n_jobs=-1
            ),
            'one_class_svm': OneClassSVM(
                kernel='rbf',
                gamma='scale',
                nu=0.1
            ),
            'local_outlier_factor': LocalOutlierFactor(
                n_neighbors=20,
                contamination=0.1,
                novelty=True,
                n_jobs=-1
            )
        }
        
        # Model weights (learned through validation)
        self.weights = {
            'random_forest': 0.3,
            'gradient_boosting': 0.25,
            'isolation_forest': 0.2,
            'one_class_svm': 0.15,
            'local_outlier_factor': 0.1
        }
        
        # Meta-learner for combining predictions
        self.meta_learner = RandomForestClassifier(
            n_estimators=50,
            max_depth=10,
            random_state=42
        )
        
        self.fitted = False
        self.performance_history = defaultdict(list)
        
    def fit(self, X: np.ndarray, y: np.ndarray) -> 'ThreatLevelEnsemble':
        """Fit all ensemble models"""
        
        # Fit supervised models
        if len(np.unique(y)) > 1:
            self.models['random_forest'].fit(X, y)
            self.models['gradient_boosting'].fit(X, y)
        
        # Fit unsupervised models
        self.models['isolation_forest'].fit(X)
        self.models['one_class_svm'].fit(X)
        self.models['local_outlier_factor'].fit(X)
        
        # Generate meta-features for meta-learner
        meta_features = self._generate_meta_features(X)
        if meta_features.shape[1] > 0:
            self.meta_learner.fit(meta_features, y)
        
        self.fitted = True
        logging.info("Threat level ensemble fitted successfully")
        return self
    
    def predict_threat_level(self, X: np.ndarray) -> np.ndarray:
        """Predict threat levels using ensemble"""
        if not self.fitted:
            raise ValueError("Ensemble must be fitted before prediction")
        
        predictions = []
        confidences = []
        
        # Get predictions from each model
        model_predictions = {}
        
        # Supervised models
        if hasattr(self.models['random_forest'], 'predict_proba'):
            rf_proba = self.models['random_forest'].predict_proba(X)
            model_predictions['random_forest'] = rf_proba[:, 1] if rf_proba.shape[1] > 1 else rf_proba[:, 0]
        
        if hasattr(self.models['gradient_boosting'], 'predict_proba'):
            gb_proba = self.models['gradient_boosting'].predict_proba(X)
            model_predictions['gradient_boosting'] = gb_proba[:, 1] if gb_proba.shape[1] > 1 else gb_proba[:, 0]
        
        # Unsupervised models (convert to 0-1 range)
        iso_scores = self.models['isolation_forest'].decision_function(X)
        model_predictions['isolation_forest'] = (iso_scores - iso_scores.min()) / (iso_scores.max() - iso_scores.min() + 1e-8)
        
        svm_scores = self.models['one_class_svm'].decision_function(X)
        model_predictions['one_class_svm'] = (svm_scores - svm_scores.min()) / (svm_scores.max() - svm_scores.min() + 1e-8)
        
        lof_scores = self.models['local_outlier_factor'].decision_function(X)
        model_predictions['local_outlier_factor'] = (lof_scores - lof_scores.min()) / (lof_scores.max() - lof_scores.min() + 1e-8)
        
        # Weighted ensemble
        ensemble_predictions = np.zeros(X.shape[0])
        total_weight = 0
        
        for model_name, pred in model_predictions.items():
            weight = self.weights.get(model_name, 0.1)
            ensemble_predictions += weight * pred
            total_weight += weight
        
        if total_weight > 0:
            ensemble_predictions /= total_weight
        
        # Meta-learner refinement
        meta_features = self._generate_meta_features(X)
        if meta_features.shape[1] > 0 and hasattr(self.meta_learner, 'predict_proba'):
            meta_proba = self.meta_learner.predict_proba(meta_features)
            meta_pred = meta_proba[:, 1] if meta_proba.shape[1] > 1 else meta_proba[:, 0]
            ensemble_predictions = 0.7 * ensemble_predictions + 0.3 * meta_pred
        
        return np.clip(ensemble_predictions, 0, 1)
    
    def _generate_meta_features(self, X: np.ndarray) -> np.ndarray:
        """Generate meta-features for meta-learning"""
        meta_features = []
        
        if not self.fitted:
            return np.array(meta_features).reshape(X.shape[0], -1) if meta_features else np.empty((X.shape[0], 0))
        
        # Statistical features
        meta_features.extend([
            np.mean(X, axis=1),
            np.std(X, axis=1),
            np.min(X, axis=1),
            np.max(X, axis=1),
            np.median(X, axis=1)
        ])
        
        # Model agreement features
        if hasattr(self.models['random_forest'], 'predict_proba'):
            rf_pred = self.models['random_forest'].predict_proba(X)
            rf_confidence = np.max(rf_pred, axis=1)
            meta_features.append(rf_confidence)
        
        if hasattr(self.models['gradient_boosting'], 'predict_proba'):
            gb_pred = self.models['gradient_boosting'].predict_proba(X)
            gb_confidence = np.max(gb_pred, axis=1)
            meta_features.append(gb_confidence)
        
        return np.column_stack(meta_features) if meta_features else np.empty((X.shape[0], 0))
    
    def update_weights(self, X_val: np.ndarray, y_val: np.ndarray):
        """Update model weights based on validation performance"""
        if not self.fitted:
            return
        
        model_scores = {}
        
        # Evaluate each model
        for model_name, model in self.models.items():
            try:
                if model_name in ['random_forest', 'gradient_boosting']:
                    if hasattr(model, 'predict'):
                        pred = model.predict(X_val)
                        score = accuracy_score(y_val, pred)
                        model_scores[model_name] = score
                else:
                    # For unsupervised models, use anomaly detection metrics
                    pred = model.predict(X_val)
                    # Convert to binary classification
                    binary_pred = (pred == -1).astype(int)
                    if len(np.unique(y_val)) > 1:
                        score = f1_score(y_val, binary_pred, average='weighted')
                        model_scores[model_name] = score
            except Exception as e:
                logging.warning(f"Error evaluating {model_name}: {e}")
                model_scores[model_name] = 0.1
        
        # Update weights based on performance
        total_score = sum(model_scores.values())
        if total_score > 0:
            for model_name in self.weights:
                self.weights[model_name] = model_scores.get(model_name, 0.1) / total_score
        
        logging.info(f"Updated ensemble weights: {self.weights}")

class AttackerProfileEnsemble:
    """Ensemble for attacker profiling and behavior classification"""
    
    def __init__(self):
        # Clustering models for attacker categorization
        self.clustering_models = {
            'kmeans': KMeans(n_clusters=8, random_state=42, n_init=10),
            'dbscan': DBSCAN(eps=0.5, min_samples=5)
        }
        
        # Classification models for behavior prediction
        self.behavior_models = {
            'sophistication': RandomForestClassifier(n_estimators=100, random_state=42),
            'automation': GradientBoostingClassifier(n_estimators=100, random_state=42),
            'persistence': RandomForestClassifier(n_estimators=100, random_state=42)
        }
        
        self.fitted = False
        
    def fit(self, X: np.ndarray, behavior_labels: Dict[str, np.ndarray] = None) -> 'AttackerProfileEnsemble':
        """Fit attacker profiling ensemble"""
        
        # Fit clustering models
        self.clustering_models['kmeans'].fit(X)
        
        # DBSCAN doesn't need explicit fitting, but we'll store the model
        self.clustering_models['dbscan'].fit(X)
        
        # Fit behavior classification models if labels provided
        if behavior_labels:
            for behavior_type, labels in behavior_labels.items():
                if behavior_type in self.behavior_models and len(np.unique(labels)) > 1:
                    self.behavior_models[behavior_type].fit(X, labels)
        
        self.fitted = True
        logging.info("Attacker profile ensemble fitted successfully")
        return self
    
    def predict_profile(self, X: np.ndarray) -> Dict[str, np.ndarray]:
        """Predict comprehensive attacker profiles"""
        if not self.fitted:
            raise ValueError("Ensemble must be fitted before prediction")
        
        results = {}
        
        # Clustering predictions
        kmeans_clusters = self.clustering_models['kmeans'].predict(X)
        dbscan_clusters = self.clustering_models['dbscan'].fit_predict(X)
        
        results['kmeans_cluster'] = kmeans_clusters
        results['dbscan_cluster'] = dbscan_clusters
        
        # Behavior predictions
        for behavior_type, model in self.behavior_models.items():
            if hasattr(model, 'predict_proba'):
                proba = model.predict_proba(X)
                results[f'{behavior_type}_score'] = proba[:, 1] if proba.shape[1] > 1 else proba[:, 0]
            elif hasattr(model, 'predict'):
                results[f'{behavior_type}_prediction'] = model.predict(X)
        
        # Composite sophistication score
        sophistication_features = [
            np.mean(X, axis=1),  # Overall feature intensity
            np.std(X, axis=1),   # Feature diversity
            np.max(X, axis=1)    # Peak feature values
        ]
        
        sophistication_composite = np.mean(sophistication_features, axis=0)
        results['sophistication_composite'] = np.clip(sophistication_composite, 0, 1)
        
        return results

class PatternRecognitionEnsemble:
    """Ensemble for attack pattern recognition and sequence analysis"""
    
    def __init__(self):
        self.sequence_models = {
            'ngram': {},  # N-gram based pattern detection
            'statistical': {}  # Statistical pattern analysis
        }
        
        self.pattern_classifiers = {
            'attack_type': RandomForestClassifier(n_estimators=150, random_state=42),
            'campaign': GradientBoostingClassifier(n_estimators=100, random_state=42)
        }
        
        self.fitted = False
        
    def fit(self, sequences: List[List[Dict]], labels: Dict[str, List] = None) -> 'PatternRecognitionEnsemble':
        """Fit pattern recognition ensemble"""
        
        # Extract features from sequences
        sequence_features = self._extract_sequence_features(sequences)
        
        # Fit pattern classifiers
        if labels:
            for pattern_type, pattern_labels in labels.items():
                if pattern_type in self.pattern_classifiers and len(np.unique(pattern_labels)) > 1:
                    self.pattern_classifiers[pattern_type].fit(sequence_features, pattern_labels)
        
        # Build n-gram models
        self._build_ngram_models(sequences)
        
        self.fitted = True
        logging.info("Pattern recognition ensemble fitted successfully")
        return self
    
    def predict_patterns(self, sequences: List[List[Dict]]) -> Dict[str, Any]:
        """Predict attack patterns from sequences"""
        if not self.fitted:
            raise ValueError("Ensemble must be fitted before prediction")
        
        sequence_features = self._extract_sequence_features(sequences)
        results = {}
        
        # Pattern classification
        for pattern_type, model in self.pattern_classifiers.items():
            if hasattr(model, 'predict_proba'):
                proba = model.predict_proba(sequence_features)
                results[f'{pattern_type}_probabilities'] = proba
                results[f'{pattern_type}_predictions'] = np.argmax(proba, axis=1)
        
        # N-gram analysis
        ngram_scores = self._analyze_ngrams(sequences)
        results['ngram_anomaly_scores'] = ngram_scores
        
        # Sequence statistics
        results['sequence_stats'] = self._compute_sequence_statistics(sequences)
        
        return results
    
    def _extract_sequence_features(self, sequences: List[List[Dict]]) -> np.ndarray:
        """Extract features from attack sequences"""
        features = []
        
        for sequence in sequences:
            seq_features = []
            
            # Sequence length
            seq_features.append(len(sequence))
            
            # Attack type diversity
            attack_types = [event.get('attack_type', '') for event in sequence]
            type_diversity = len(set(attack_types)) / len(attack_types) if attack_types else 0
            seq_features.append(type_diversity)
            
            # Timing features
            timestamps = [event.get('timestamp') for event in sequence if event.get('timestamp')]
            if len(timestamps) > 1:
                intervals = [(timestamps[i+1] - timestamps[i]).total_seconds() 
                           for i in range(len(timestamps)-1)]
                seq_features.extend([
                    np.mean(intervals),
                    np.std(intervals),
                    np.min(intervals),
                    np.max(intervals)
                ])
            else:
                seq_features.extend([0, 0, 0, 0])
            
            # Payload complexity progression
            complexities = [event.get('payload_complexity', 0) for event in sequence]
            if complexities:
                seq_features.extend([
                    np.mean(complexities),
                    np.std(complexities),
                    np.corrcoef(range(len(complexities)), complexities)[0, 1] if len(complexities) > 1 else 0
                ])
            else:
                seq_features.extend([0, 0, 0])
            
            features.append(seq_features)
        
        return np.array(features)
    
    def _build_ngram_models(self, sequences: List[List[Dict]]):
        """Build n-gram models for pattern detection"""
        # Extract attack type sequences
        attack_sequences = []
        for sequence in sequences:
            attack_types = [event.get('attack_type', 'unknown') for event in sequence]
            attack_sequences.append(attack_types)
        
        # Build bigram and trigram frequency models
        bigram_counts = defaultdict(int)
        trigram_counts = defaultdict(int)
        
        for sequence in attack_sequences:
            # Bigrams
            for i in range(len(sequence) - 1):
                bigram = (sequence[i], sequence[i + 1])
                bigram_counts[bigram] += 1
            
            # Trigrams
            for i in range(len(sequence) - 2):
                trigram = (sequence[i], sequence[i + 1], sequence[i + 2])
                trigram_counts[trigram] += 1
        
        self.sequence_models['ngram']['bigrams'] = dict(bigram_counts)
        self.sequence_models['ngram']['trigrams'] = dict(trigram_counts)
    
    def _analyze_ngrams(self, sequences: List[List[Dict]]) -> List[float]:
        """Analyze n-gram patterns for anomaly detection"""
        scores = []
        
        bigram_model = self.sequence_models['ngram'].get('bigrams', {})
        trigram_model = self.sequence_models['ngram'].get('trigrams', {})
        
        for sequence in sequences:
            attack_types = [event.get('attack_type', 'unknown') for event in sequence]
            sequence_score = 0
            
            # Bigram scoring
            for i in range(len(attack_types) - 1):
                bigram = (attack_types[i], attack_types[i + 1])
                score = bigram_model.get(bigram, 0) / max(1, sum(bigram_model.values()))
                sequence_score += score
            
            # Trigram scoring
            for i in range(len(attack_types) - 2):
                trigram = (attack_types[i], attack_types[i + 1], attack_types[i + 2])
                score = trigram_model.get(trigram, 0) / max(1, sum(trigram_model.values()))
                sequence_score += score
            
            # Normalize by sequence length
            normalized_score = sequence_score / max(1, len(attack_types))
            scores.append(normalized_score)
        
        return scores
    
    def _compute_sequence_statistics(self, sequences: List[List[Dict]]) -> Dict[str, List[float]]:
        """Compute statistical features for sequences"""
        stats = {
            'length': [],
            'type_diversity': [],
            'temporal_regularity': [],
            'escalation_trend': []
        }
        
        for sequence in sequences:
            # Length
            stats['length'].append(len(sequence))
            
            # Type diversity
            attack_types = [event.get('attack_type', '') for event in sequence]
            diversity = len(set(attack_types)) / len(attack_types) if attack_types else 0
            stats['type_diversity'].append(diversity)
            
            # Temporal regularity
            timestamps = [event.get('timestamp') for event in sequence if event.get('timestamp')]
            if len(timestamps) > 2:
                intervals = [(timestamps[i+1] - timestamps[i]).total_seconds() 
                           for i in range(len(timestamps)-1)]
                regularity = 1 / (1 + np.std(intervals))  # Higher for more regular intervals
            else:
                regularity = 0
            stats['temporal_regularity'].append(regularity)
            
            # Escalation trend
            severities = [event.get('severity_score', 0) for event in sequence]
            if len(severities) > 1:
                correlation = np.corrcoef(range(len(severities)), severities)[0, 1]
                escalation = max(0, correlation)  # Only positive correlation indicates escalation
            else:
                escalation = 0
            stats['escalation_trend'].append(escalation)
        
        return stats

class MasterEnsemble:
    """Master ensemble combining all specialized ensembles"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Initialize specialized ensembles
        self.threat_ensemble = ThreatLevelEnsemble(config)
        self.profile_ensemble = AttackerProfileEnsemble()
        self.pattern_ensemble = PatternRecognitionEnsemble()
        
        # Meta-ensemble for final decisions
        self.meta_ensemble = VotingClassifier([
            ('threat', RandomForestClassifier(n_estimators=50, random_state=42)),
            ('profile', GradientBoostingClassifier(n_estimators=50, random_state=42))
        ], voting='soft')
        
        self.fitted = False
        
    def fit(self, X: np.ndarray, y: np.ndarray, 
            sequences: List[List[Dict]] = None,
            behavior_labels: Dict[str, np.ndarray] = None,
            pattern_labels: Dict[str, List] = None) -> 'MasterEnsemble':
        """Fit the master ensemble"""
        
        # Fit threat level ensemble
        self.threat_ensemble.fit(X, y)
        
        # Fit profile ensemble
        self.profile_ensemble.fit(X, behavior_labels)
        
        # Fit pattern ensemble if sequences provided
        if sequences:
            self.pattern_ensemble.fit(sequences, pattern_labels)
        
        # Fit meta-ensemble
        if len(np.unique(y)) > 1:
            meta_features = self._generate_meta_ensemble_features(X)
            if meta_features.shape[1] > 0:
                self.meta_ensemble.fit(meta_features, y)
        
        self.fitted = True
        logging.info("Master ensemble fitted successfully")
        return self
    
    def predict_comprehensive(self, X: np.ndarray, 
                            sequences: List[List[Dict]] = None) -> Dict[str, Any]:
        """Generate comprehensive predictions using all ensembles"""
        if not self.fitted:
            raise ValueError("Master ensemble must be fitted before prediction")
        
        results = {}
        
        # Threat level predictions
        threat_levels = self.threat_ensemble.predict_threat_level(X)
        results['threat_levels'] = threat_levels
        
        # Attacker profiles
        profiles = self.profile_ensemble.predict_profile(X)
        results['attacker_profiles'] = profiles
        
        # Pattern analysis
        if sequences and self.pattern_ensemble.fitted:
            patterns = self.pattern_ensemble.predict_patterns(sequences)
            results['attack_patterns'] = patterns
        
        # Meta-ensemble prediction
        meta_features = self._generate_meta_ensemble_features(X)
        if meta_features.shape[1] > 0 and hasattr(self.meta_ensemble, 'predict_proba'):
            meta_proba = self.meta_ensemble.predict_proba(meta_features)
            results['meta_predictions'] = meta_proba
        
        # Confidence estimation
        results['confidence_scores'] = self._estimate_confidence(X, results)
        
        return results
    
    def _generate_meta_ensemble_features(self, X: np.ndarray) -> np.ndarray:
        """Generate features for meta-ensemble"""
        meta_features = []
        
        if self.threat_ensemble.fitted:
            threat_pred = self.threat_ensemble.predict_threat_level(X)
            meta_features.append(threat_pred)
        
        if self.profile_ensemble.fitted:
            profiles = self.profile_ensemble.predict_profile(X)
            if 'sophistication_composite' in profiles:
                meta_features.append(profiles['sophistication_composite'])
        
        # Statistical features from input
        meta_features.extend([
            np.mean(X, axis=1),
            np.std(X, axis=1),
            np.max(X, axis=1)
        ])
        
        return np.column_stack(meta_features) if meta_features else np.empty((X.shape[0], 0))
    
    def _estimate_confidence(self, X: np.ndarray, predictions: Dict[str, Any]) -> np.ndarray:
        """Estimate confidence in ensemble predictions"""
        confidence_factors = []
        
        # Threat level confidence
        if 'threat_levels' in predictions:
            threat_levels = predictions['threat_levels']
            # Higher confidence for extreme values (very low or very high threat)
            threat_confidence = 1 - 2 * np.abs(threat_levels - 0.5)
            confidence_factors.append(threat_confidence)
        
        # Profile consistency confidence
        if 'attacker_profiles' in predictions:
            profiles = predictions['attacker_profiles']
            if 'sophistication_composite' in profiles:
                # Higher confidence for consistent sophistication scores
                soph_scores = profiles['sophistication_composite']
                soph_confidence = 1 - np.abs(soph_scores - np.mean(soph_scores))
                confidence_factors.append(soph_confidence)
        
        # Data quality confidence
        data_quality = 1 - np.mean(np.isnan(X), axis=1)
        confidence_factors.append(data_quality)
        
        # Combine confidence factors
        if confidence_factors:
            overall_confidence = np.mean(confidence_factors, axis=0)
        else:
            overall_confidence = np.ones(X.shape[0]) * 0.5
        
        return np.clip(overall_confidence, 0, 1)
    
    def save_ensemble(self, path: str):
        """Save the trained ensemble"""
        ensemble_data = {
            'threat_ensemble': self.threat_ensemble,
            'profile_ensemble': self.profile_ensemble,
            'pattern_ensemble': self.pattern_ensemble,
            'meta_ensemble': self.meta_ensemble,
            'fitted': self.fitted,
            'config': self.config
        }
        
        joblib.dump(ensemble_data, path)
        logging.info(f"Master ensemble saved to {path}")
    
    def load_ensemble(self, path: str):
        """Load a trained ensemble"""
        ensemble_data = joblib.load(path)
        
        self.threat_ensemble = ensemble_data['threat_ensemble']
        self.profile_ensemble = ensemble_data['profile_ensemble']
        self.pattern_ensemble = ensemble_data['pattern_ensemble']
        self.meta_ensemble = ensemble_data['meta_ensemble']
        self.fitted = ensemble_data['fitted']
        self.config = ensemble_data.get('config', {})
        
        logging.info(f"Master ensemble loaded from {path}")

def create_ensemble_suite(config: Dict[str, Any] = None) -> MasterEnsemble:
    """Create a complete ensemble suite for HoneyPort AI"""
    return MasterEnsemble(config)
