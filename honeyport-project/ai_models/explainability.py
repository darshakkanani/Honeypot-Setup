#!/usr/bin/env python3
"""
AI Explainability and Interpretability Module for HoneyPort
Provides transparency into AI decision-making processes
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Any, Optional, Tuple
import json
from datetime import datetime
import logging
from dataclasses import dataclass

try:
    import shap
    import lime
    from lime.lime_text import LimeTextExplainer
    from lime.lime_tabular import LimeTabularExplainer
    EXPLAINABILITY_AVAILABLE = True
except ImportError:
    EXPLAINABILITY_AVAILABLE = False
    logging.warning("SHAP/LIME not available. Install with: pip install shap lime")

@dataclass
class ExplanationResult:
    """Container for AI explanation results"""
    prediction: float
    confidence: float
    feature_importance: Dict[str, float]
    explanation_text: str
    visualization_data: Optional[Dict] = None
    method: str = "unknown"
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class AIExplainer:
    """
    Main explainability engine for HoneyPort AI decisions
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.feature_names = []
        self.explanation_cache = {}
        
        # Initialize explainers if available
        if EXPLAINABILITY_AVAILABLE:
            self.shap_explainer = None
            self.lime_explainer = None
            self.text_explainer = None
        
    def explain_threat_prediction(self, 
                                features: np.ndarray, 
                                prediction: float,
                                model,
                                feature_names: List[str] = None) -> ExplanationResult:
        """
        Explain threat level prediction using multiple methods
        """
        if not EXPLAINABILITY_AVAILABLE:
            return self._create_simple_explanation(features, prediction, feature_names)
        
        try:
            # SHAP explanation
            shap_values = self._get_shap_explanation(model, features)
            
            # Feature importance ranking
            importance_dict = self._calculate_feature_importance(
                shap_values, feature_names or self.feature_names
            )
            
            # Generate human-readable explanation
            explanation_text = self._generate_explanation_text(
                prediction, importance_dict
            )
            
            return ExplanationResult(
                prediction=prediction,
                confidence=self._calculate_confidence(shap_values),
                feature_importance=importance_dict,
                explanation_text=explanation_text,
                visualization_data=self._prepare_visualization_data(shap_values),
                method="SHAP"
            )
            
        except Exception as e:
            self.logger.error(f"Explainability error: {e}")
            return self._create_simple_explanation(features, prediction, feature_names)
    
    def explain_attacker_profile(self,
                               session_data: Dict[str, Any],
                               profile_result: Dict[str, Any]) -> ExplanationResult:
        """
        Explain attacker profiling decisions
        """
        # Extract key behavioral indicators
        key_indicators = self._extract_behavioral_indicators(session_data)
        
        # Calculate indicator importance
        importance_scores = self._score_behavioral_indicators(
            key_indicators, profile_result
        )
        
        # Generate explanation
        explanation_text = self._generate_profile_explanation(
            profile_result, importance_scores
        )
        
        return ExplanationResult(
            prediction=profile_result.get('threat_level', 0.5),
            confidence=profile_result.get('confidence', 0.5),
            feature_importance=importance_scores,
            explanation_text=explanation_text,
            method="Behavioral Analysis"
        )
    
    def explain_response_strategy(self,
                                attack_context: Dict[str, Any],
                                strategy: Dict[str, Any]) -> ExplanationResult:
        """
        Explain why a specific response strategy was chosen
        """
        # Analyze strategy factors
        strategy_factors = {
            'threat_level': attack_context.get('threat_level', 0.5),
            'attacker_sophistication': attack_context.get('sophistication', 0.5),
            'attack_frequency': attack_context.get('frequency', 1.0),
            'payload_complexity': attack_context.get('payload_complexity', 0.5),
            'geographic_risk': attack_context.get('geographic_risk', 0.5)
        }
        
        # Calculate factor weights
        factor_weights = self._calculate_strategy_weights(strategy_factors, strategy)
        
        # Generate explanation
        explanation_text = self._generate_strategy_explanation(
            strategy, factor_weights
        )
        
        return ExplanationResult(
            prediction=strategy.get('engagement_level', 0.5),
            confidence=strategy.get('confidence', 0.5),
            feature_importance=factor_weights,
            explanation_text=explanation_text,
            method="Strategy Analysis"
        )
    
    def generate_decision_tree_explanation(self,
                                         features: np.ndarray,
                                         model) -> Dict[str, Any]:
        """
        Generate decision tree-style explanation for interpretability
        """
        if not hasattr(model, 'decision_path'):
            return {"error": "Model doesn't support decision path analysis"}
        
        try:
            # Get decision path
            decision_path = model.decision_path(features.reshape(1, -1))
            leaf = model.apply(features.reshape(1, -1))
            
            # Extract decision rules
            feature_names = self.feature_names or [f"feature_{i}" for i in range(len(features))]
            
            decision_rules = []
            for node_id in decision_path.indices:
                if leaf[0] == node_id:
                    continue
                    
                threshold = model.tree_.threshold[node_id]
                feature_id = model.tree_.feature[node_id]
                
                if features[feature_id] <= threshold:
                    rule = f"{feature_names[feature_id]} <= {threshold:.3f}"
                else:
                    rule = f"{feature_names[feature_id]} > {threshold:.3f}"
                    
                decision_rules.append(rule)
            
            return {
                "decision_path": decision_rules,
                "final_prediction": model.predict(features.reshape(1, -1))[0],
                "confidence": max(model.predict_proba(features.reshape(1, -1))[0])
            }
            
        except Exception as e:
            self.logger.error(f"Decision tree explanation error: {e}")
            return {"error": str(e)}
    
    def create_explanation_report(self,
                                explanations: List[ExplanationResult]) -> str:
        """
        Create comprehensive explanation report
        """
        report = []
        report.append("# HoneyPort AI Decision Explanation Report")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        for i, explanation in enumerate(explanations, 1):
            report.append(f"## Decision {i}: {explanation.method}")
            report.append(f"**Prediction:** {explanation.prediction:.3f}")
            report.append(f"**Confidence:** {explanation.confidence:.3f}")
            report.append("")
            report.append("### Key Factors:")
            
            # Sort features by importance
            sorted_features = sorted(
                explanation.feature_importance.items(),
                key=lambda x: abs(x[1]),
                reverse=True
            )
            
            for feature, importance in sorted_features[:5]:
                impact = "increases" if importance > 0 else "decreases"
                report.append(f"- **{feature}**: {impact} prediction by {abs(importance):.3f}")
            
            report.append("")
            report.append("### Explanation:")
            report.append(explanation.explanation_text)
            report.append("")
            report.append("---")
            report.append("")
        
        return "\n".join(report)
    
    def _get_shap_explanation(self, model, features: np.ndarray):
        """Get SHAP values for model explanation"""
        if self.shap_explainer is None:
            # Initialize SHAP explainer based on model type
            if hasattr(model, 'predict_proba'):
                self.shap_explainer = shap.Explainer(model)
            else:
                self.shap_explainer = shap.LinearExplainer(model, features.reshape(1, -1))
        
        return self.shap_explainer(features.reshape(1, -1))
    
    def _calculate_feature_importance(self,
                                    shap_values,
                                    feature_names: List[str]) -> Dict[str, float]:
        """Calculate feature importance from SHAP values"""
        if hasattr(shap_values, 'values'):
            importance_values = shap_values.values[0]
        else:
            importance_values = shap_values
        
        return dict(zip(feature_names, importance_values))
    
    def _calculate_confidence(self, shap_values) -> float:
        """Calculate confidence score from SHAP values"""
        if hasattr(shap_values, 'values'):
            values = shap_values.values[0]
        else:
            values = shap_values
        
        # Confidence based on magnitude of SHAP values
        total_magnitude = np.sum(np.abs(values))
        return min(total_magnitude / len(values), 1.0)
    
    def _generate_explanation_text(self,
                                 prediction: float,
                                 importance_dict: Dict[str, float]) -> str:
        """Generate human-readable explanation"""
        # Sort features by absolute importance
        sorted_features = sorted(
            importance_dict.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )
        
        threat_level = "HIGH" if prediction > 0.7 else "MEDIUM" if prediction > 0.4 else "LOW"
        
        explanation = f"The AI assessed this as a {threat_level} threat (score: {prediction:.3f}). "
        
        # Top contributing factors
        top_factors = sorted_features[:3]
        if top_factors:
            explanation += "Key factors: "
            factor_descriptions = []
            
            for feature, importance in top_factors:
                if importance > 0:
                    factor_descriptions.append(f"{feature} increases threat level")
                else:
                    factor_descriptions.append(f"{feature} decreases threat level")
            
            explanation += "; ".join(factor_descriptions) + "."
        
        return explanation
    
    def _extract_behavioral_indicators(self, session_data: Dict[str, Any]) -> Dict[str, float]:
        """Extract key behavioral indicators from session data"""
        indicators = {}
        
        # Request frequency
        requests = session_data.get('requests', [])
        duration = session_data.get('duration', 1)
        indicators['request_frequency'] = len(requests) / max(duration, 1)
        
        # Payload complexity
        payloads = [req.get('payload', '') for req in requests]
        avg_payload_length = np.mean([len(p) for p in payloads]) if payloads else 0
        indicators['payload_complexity'] = min(avg_payload_length / 100, 1.0)
        
        # Attack diversity
        attack_types = set(req.get('attack_type', 'unknown') for req in requests)
        indicators['attack_diversity'] = len(attack_types) / max(len(requests), 1)
        
        # Geographic risk (placeholder)
        geo_info = session_data.get('geolocation', {})
        high_risk_countries = ['CN', 'RU', 'KP', 'IR']
        indicators['geographic_risk'] = 1.0 if geo_info.get('country') in high_risk_countries else 0.3
        
        return indicators
    
    def _score_behavioral_indicators(self,
                                   indicators: Dict[str, float],
                                   profile_result: Dict[str, Any]) -> Dict[str, float]:
        """Score the importance of behavioral indicators"""
        scores = {}
        threat_level = profile_result.get('threat_level', 0.5)
        
        # Weight indicators based on correlation with threat level
        for indicator, value in indicators.items():
            # Simple correlation-based scoring
            correlation = abs(value - 0.5) * 2  # Convert to 0-1 range
            scores[indicator] = correlation * threat_level
        
        return scores
    
    def _generate_profile_explanation(self,
                                    profile_result: Dict[str, Any],
                                    importance_scores: Dict[str, float]) -> str:
        """Generate explanation for attacker profiling"""
        threat_level = profile_result.get('threat_level', 0.5)
        attacker_type = profile_result.get('attacker_type', 'unknown')
        
        explanation = f"Attacker classified as '{attacker_type}' with threat level {threat_level:.3f}. "
        
        # Top behavioral indicators
        top_indicators = sorted(importance_scores.items(), key=lambda x: x[1], reverse=True)[:2]
        
        if top_indicators:
            explanation += "Primary indicators: "
            indicator_descriptions = []
            
            for indicator, score in top_indicators:
                if indicator == 'request_frequency':
                    indicator_descriptions.append("high request frequency")
                elif indicator == 'payload_complexity':
                    indicator_descriptions.append("complex payloads")
                elif indicator == 'attack_diversity':
                    indicator_descriptions.append("diverse attack methods")
                elif indicator == 'geographic_risk':
                    indicator_descriptions.append("high-risk geographic origin")
                else:
                    indicator_descriptions.append(indicator.replace('_', ' '))
            
            explanation += ", ".join(indicator_descriptions) + "."
        
        return explanation
    
    def _calculate_strategy_weights(self,
                                  factors: Dict[str, float],
                                  strategy: Dict[str, Any]) -> Dict[str, float]:
        """Calculate weights for strategy factors"""
        weights = {}
        strategy_type = strategy.get('type', 'balanced')
        
        # Weight factors based on strategy type
        if strategy_type == 'aggressive':
            weights = {
                'threat_level': 0.4,
                'attacker_sophistication': 0.3,
                'attack_frequency': 0.2,
                'payload_complexity': 0.1,
                'geographic_risk': 0.0
            }
        elif strategy_type == 'cautious':
            weights = {
                'threat_level': 0.2,
                'attacker_sophistication': 0.2,
                'attack_frequency': 0.1,
                'payload_complexity': 0.2,
                'geographic_risk': 0.3
            }
        else:  # balanced
            weights = {
                'threat_level': 0.25,
                'attacker_sophistication': 0.25,
                'attack_frequency': 0.2,
                'payload_complexity': 0.15,
                'geographic_risk': 0.15
            }
        
        return weights
    
    def _generate_strategy_explanation(self,
                                     strategy: Dict[str, Any],
                                     factor_weights: Dict[str, float]) -> str:
        """Generate explanation for response strategy"""
        strategy_type = strategy.get('type', 'balanced')
        engagement_level = strategy.get('engagement_level', 0.5)
        
        explanation = f"Selected '{strategy_type}' strategy with {engagement_level:.1%} engagement level. "
        
        # Top influencing factors
        top_factors = sorted(factor_weights.items(), key=lambda x: x[1], reverse=True)[:2]
        
        if top_factors:
            explanation += "Primary considerations: "
            factor_descriptions = []
            
            for factor, weight in top_factors:
                factor_descriptions.append(factor.replace('_', ' '))
            
            explanation += " and ".join(factor_descriptions) + "."
        
        return explanation
    
    def _create_simple_explanation(self,
                                 features: np.ndarray,
                                 prediction: float,
                                 feature_names: List[str] = None) -> ExplanationResult:
        """Create simple explanation when advanced methods unavailable"""
        if feature_names is None:
            feature_names = [f"feature_{i}" for i in range(len(features))]
        
        # Simple feature importance based on magnitude
        importance_dict = {}
        for i, (name, value) in enumerate(zip(feature_names, features)):
            importance_dict[name] = abs(value) * (1 if prediction > 0.5 else -1)
        
        explanation_text = f"Threat assessment: {prediction:.3f}. " \
                          f"Based on {len(features)} analyzed features."
        
        return ExplanationResult(
            prediction=prediction,
            confidence=0.7,  # Default confidence
            feature_importance=importance_dict,
            explanation_text=explanation_text,
            method="Simple Analysis"
        )
    
    def _prepare_visualization_data(self, shap_values) -> Dict[str, Any]:
        """Prepare data for visualization"""
        if hasattr(shap_values, 'values'):
            values = shap_values.values[0]
        else:
            values = shap_values
        
        return {
            'shap_values': values.tolist() if hasattr(values, 'tolist') else list(values),
            'feature_names': self.feature_names,
            'base_value': getattr(shap_values, 'base_values', [0])[0] if hasattr(shap_values, 'base_values') else 0
        }

class ExplanationVisualizer:
    """
    Visualization tools for AI explanations
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def create_feature_importance_plot(self,
                                     importance_dict: Dict[str, float],
                                     title: str = "Feature Importance") -> str:
        """Create feature importance visualization"""
        try:
            plt.figure(figsize=(10, 6))
            
            # Sort features by importance
            sorted_items = sorted(importance_dict.items(), key=lambda x: abs(x[1]), reverse=True)
            features, importances = zip(*sorted_items[:10])  # Top 10 features
            
            # Create horizontal bar plot
            colors = ['red' if imp < 0 else 'green' for imp in importances]
            plt.barh(range(len(features)), importances, color=colors, alpha=0.7)
            
            plt.yticks(range(len(features)), features)
            plt.xlabel('Importance Score')
            plt.title(title)
            plt.grid(axis='x', alpha=0.3)
            
            # Save plot
            filename = f"feature_importance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(filename, dpi=150, bbox_inches='tight')
            plt.close()
            
            return filename
            
        except Exception as e:
            self.logger.error(f"Visualization error: {e}")
            return None
    
    def create_explanation_dashboard(self,
                                   explanations: List[ExplanationResult]) -> Dict[str, Any]:
        """Create comprehensive explanation dashboard data"""
        dashboard_data = {
            'summary': {
                'total_explanations': len(explanations),
                'avg_confidence': np.mean([exp.confidence for exp in explanations]),
                'methods_used': list(set(exp.method for exp in explanations))
            },
            'explanations': [],
            'visualizations': []
        }
        
        for explanation in explanations:
            exp_data = {
                'prediction': explanation.prediction,
                'confidence': explanation.confidence,
                'explanation_text': explanation.explanation_text,
                'method': explanation.method,
                'timestamp': explanation.timestamp.isoformat(),
                'top_features': dict(sorted(
                    explanation.feature_importance.items(),
                    key=lambda x: abs(x[1]),
                    reverse=True
                )[:5])
            }
            dashboard_data['explanations'].append(exp_data)
        
        return dashboard_data
