#!/usr/bin/env python3
"""
Neural Network Models for Advanced HoneyPort AI
Deep learning models for attacker profiling, pattern recognition, and adaptive responses
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Tuple, Optional
import math

class AttackerProfiler(nn.Module):
    """Deep neural network for comprehensive attacker profiling and behavior prediction"""
    
    def __init__(self, input_dim: int = 128, hidden_dims: list = [512, 256, 128, 64], output_dim: int = 32):
        super(AttackerProfiler, self).__init__()
        
        self.input_dim = input_dim
        self.output_dim = output_dim
        
        # Main feature extraction network
        layers = []
        prev_dim = input_dim
        
        for i, hidden_dim in enumerate(hidden_dims):
            layers.extend([
                nn.Linear(prev_dim, hidden_dim),
                nn.BatchNorm1d(hidden_dim),
                nn.ReLU(),
                nn.Dropout(0.3 if i < len(hidden_dims) - 1 else 0.2)
            ])
            prev_dim = hidden_dim
        
        self.feature_extractor = nn.Sequential(*layers)
        
        # Multi-head attention for feature importance
        self.attention = nn.MultiheadAttention(
            embed_dim=prev_dim, 
            num_heads=8, 
            dropout=0.1,
            batch_first=True
        )
        
        # Output projection layers
        self.profile_head = nn.Sequential(
            nn.Linear(prev_dim, output_dim),
            nn.Tanh()
        )
        
        # Specialized heads for different aspects
        self.threat_head = nn.Sequential(
            nn.Linear(prev_dim, 16),
            nn.ReLU(),
            nn.Linear(16, 1),
            nn.Sigmoid()
        )
        
        self.sophistication_head = nn.Sequential(
            nn.Linear(prev_dim, 16),
            nn.ReLU(),
            nn.Linear(16, 1),
            nn.Sigmoid()
        )
        
        self.automation_head = nn.Sequential(
            nn.Linear(prev_dim, 16),
            nn.ReLU(),
            nn.Linear(16, 1),
            nn.Sigmoid()
        )
        
    def forward(self, x: torch.Tensor) -> dict:
        """Forward pass returning comprehensive attacker profile"""
        
        # Feature extraction
        features = self.feature_extractor(x)
        
        # Self-attention for feature refinement
        features_expanded = features.unsqueeze(1)  # Add sequence dimension
        attn_output, attn_weights = self.attention(
            features_expanded, features_expanded, features_expanded
        )
        refined_features = attn_output.squeeze(1)
        
        # Generate different aspects of the profile
        profile_vector = self.profile_head(refined_features)
        threat_level = self.threat_head(refined_features)
        sophistication = self.sophistication_head(refined_features)
        automation_score = self.automation_head(refined_features)
        
        return {
            'profile_vector': profile_vector,
            'threat_level': threat_level,
            'sophistication': sophistication,
            'automation_score': automation_score,
            'attention_weights': attn_weights.squeeze(1)
        }

class ReinforcementLearningAgent(nn.Module):
    """Advanced Q-Learning agent with Double DQN and Dueling architecture"""
    
    def __init__(self, state_dim: int = 64, action_dim: int = 20, hidden_dim: int = 256):
        super(ReinforcementLearningAgent, self).__init__()
        
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.hidden_dim = hidden_dim
        
        # Shared feature extractor
        self.feature_extractor = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.BatchNorm1d(hidden_dim),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.BatchNorm1d(hidden_dim),
            nn.Dropout(0.2)
        )
        
        # Dueling DQN architecture
        # Value stream
        self.value_stream = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 1)
        )
        
        # Advantage stream
        self.advantage_stream = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, action_dim)
        )
        
        # Target network (for Double DQN)
        self.target_feature_extractor = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.BatchNorm1d(hidden_dim),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.BatchNorm1d(hidden_dim),
            nn.Dropout(0.2)
        )
        
        self.target_value_stream = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 1)
        )
        
        self.target_advantage_stream = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, action_dim)
        )
        
        # Initialize target network with same weights
        self.update_target_network()
        
        # Experience replay buffer
        self.memory = []
        self.memory_size = 50000
        self.batch_size = 64
        
        # Exploration parameters
        self.epsilon = 1.0
        self.epsilon_decay = 0.995
        self.epsilon_min = 0.01
        
        # Learning parameters
        self.gamma = 0.99
        self.tau = 0.001  # Soft update parameter
        
    def forward(self, state: torch.Tensor, target: bool = False) -> torch.Tensor:
        """Forward pass through the network"""
        
        if target:
            features = self.target_feature_extractor(state)
            value = self.target_value_stream(features)
            advantage = self.target_advantage_stream(features)
        else:
            features = self.feature_extractor(state)
            value = self.value_stream(features)
            advantage = self.advantage_stream(features)
        
        # Dueling DQN: Q(s,a) = V(s) + A(s,a) - mean(A(s,a))
        q_values = value + advantage - advantage.mean(dim=1, keepdim=True)
        
        return q_values
    
    def get_action(self, state: torch.Tensor, training: bool = True) -> int:
        """Epsilon-greedy action selection with exploration"""
        
        if training and np.random.random() < self.epsilon:
            return np.random.randint(self.action_dim)
        
        with torch.no_grad():
            q_values = self.forward(state.unsqueeze(0))
            return q_values.argmax().item()
    
    def store_experience(self, state, action, reward, next_state, done):
        """Store experience in replay buffer"""
        
        experience = (state, action, reward, next_state, done)
        
        if len(self.memory) >= self.memory_size:
            self.memory.pop(0)
        
        self.memory.append(experience)
    
    def update_target_network(self):
        """Hard update of target network"""
        self.target_feature_extractor.load_state_dict(self.feature_extractor.state_dict())
        self.target_value_stream.load_state_dict(self.value_stream.state_dict())
        self.target_advantage_stream.load_state_dict(self.advantage_stream.state_dict())
    
    def soft_update_target_network(self):
        """Soft update of target network"""
        for target_param, param in zip(self.target_feature_extractor.parameters(), 
                                     self.feature_extractor.parameters()):
            target_param.data.copy_(self.tau * param.data + (1.0 - self.tau) * target_param.data)
        
        for target_param, param in zip(self.target_value_stream.parameters(), 
                                     self.value_stream.parameters()):
            target_param.data.copy_(self.tau * param.data + (1.0 - self.tau) * target_param.data)
        
        for target_param, param in zip(self.target_advantage_stream.parameters(), 
                                     self.advantage_stream.parameters()):
            target_param.data.copy_(self.tau * param.data + (1.0 - self.tau) * target_param.data)

class AttackPatternRecognizer(nn.Module):
    """Advanced LSTM-based network for sequential attack pattern recognition"""
    
    def __init__(self, input_dim: int = 64, hidden_dim: int = 256, num_layers: int = 3, 
                 num_classes: int = 25, dropout: float = 0.3):
        super(AttackPatternRecognizer, self).__init__()
        
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.num_classes = num_classes
        
        # Input projection
        self.input_projection = nn.Linear(input_dim, hidden_dim)
        
        # Bidirectional LSTM layers
        self.lstm = nn.LSTM(
            hidden_dim, 
            hidden_dim, 
            num_layers,
            batch_first=True,
            bidirectional=True,
            dropout=dropout if num_layers > 1 else 0
        )
        
        # Self-attention mechanism
        self.attention_dim = hidden_dim * 2  # Bidirectional
        self.attention = nn.Sequential(
            nn.Linear(self.attention_dim, self.attention_dim // 2),
            nn.Tanh(),
            nn.Linear(self.attention_dim // 2, 1)
        )
        
        # Pattern classification head
        self.classifier = nn.Sequential(
            nn.Linear(self.attention_dim, hidden_dim),
            nn.ReLU(),
            nn.BatchNorm1d(hidden_dim),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.BatchNorm1d(hidden_dim // 2),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, num_classes)
        )
        
        # Sequence anomaly detector
        self.anomaly_detector = nn.Sequential(
            nn.Linear(self.attention_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 1),
            nn.Sigmoid()
        )
        
        # Pattern evolution predictor
        self.evolution_predictor = nn.Sequential(
            nn.Linear(self.attention_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, input_dim)  # Predict next pattern features
        )
        
    def forward(self, x: torch.Tensor, return_attention: bool = True) -> dict:
        """Forward pass with comprehensive pattern analysis"""
        
        batch_size, seq_len, _ = x.shape
        
        # Project input features
        x_projected = self.input_projection(x)
        
        # LSTM forward pass
        lstm_out, (hidden, cell) = self.lstm(x_projected)
        
        # Self-attention mechanism
        attention_scores = self.attention(lstm_out)  # [batch, seq_len, 1]
        attention_weights = F.softmax(attention_scores, dim=1)
        
        # Weighted sum using attention
        context_vector = torch.sum(attention_weights * lstm_out, dim=1)  # [batch, hidden_dim*2]
        
        # Pattern classification
        pattern_logits = self.classifier(context_vector)
        pattern_probs = F.softmax(pattern_logits, dim=1)
        
        # Anomaly detection
        anomaly_score = self.anomaly_detector(context_vector)
        
        # Pattern evolution prediction
        next_pattern = self.evolution_predictor(context_vector)
        
        result = {
            'pattern_logits': pattern_logits,
            'pattern_probs': pattern_probs,
            'anomaly_score': anomaly_score,
            'next_pattern_prediction': next_pattern,
            'context_vector': context_vector
        }
        
        if return_attention:
            result['attention_weights'] = attention_weights.squeeze(-1)
        
        return result

class ThreatLevelPredictor(nn.Module):
    """Specialized network for threat level prediction with uncertainty estimation"""
    
    def __init__(self, input_dim: int = 128, hidden_dims: list = [256, 128, 64]):
        super(ThreatLevelPredictor, self).__init__()
        
        # Main prediction network
        layers = []
        prev_dim = input_dim
        
        for hidden_dim in hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, hidden_dim),
                nn.BatchNorm1d(hidden_dim),
                nn.ReLU(),
                nn.Dropout(0.3)
            ])
            prev_dim = hidden_dim
        
        self.feature_network = nn.Sequential(*layers)
        
        # Threat level prediction (mean)
        self.threat_mean = nn.Sequential(
            nn.Linear(prev_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )
        
        # Uncertainty estimation (variance)
        self.threat_variance = nn.Sequential(
            nn.Linear(prev_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Softplus()  # Ensures positive variance
        )
        
        # Confidence estimation
        self.confidence = nn.Sequential(
            nn.Linear(prev_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )
        
    def forward(self, x: torch.Tensor) -> dict:
        """Forward pass with uncertainty quantification"""
        
        features = self.feature_network(x)
        
        threat_mean = self.threat_mean(features)
        threat_var = self.threat_variance(features)
        confidence = self.confidence(features)
        
        return {
            'threat_level': threat_mean,
            'uncertainty': threat_var,
            'confidence': confidence,
            'features': features
        }

class BehaviorAdaptationNetwork(nn.Module):
    """Network for learning optimal honeypot behavior adaptations"""
    
    def __init__(self, context_dim: int = 64, behavior_dim: int = 16, hidden_dim: int = 128):
        super(BehaviorAdaptationNetwork, self).__init__()
        
        self.context_dim = context_dim
        self.behavior_dim = behavior_dim
        
        # Context encoder
        self.context_encoder = nn.Sequential(
            nn.Linear(context_dim, hidden_dim),
            nn.ReLU(),
            nn.BatchNorm1d(hidden_dim),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU()
        )
        
        # Behavior parameter generators
        self.response_delay_predictor = nn.Sequential(
            nn.Linear(hidden_dim // 2, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid()  # 0-1 range for delay factor
        )
        
        self.deception_level_predictor = nn.Sequential(
            nn.Linear(hidden_dim // 2, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid()  # 0-1 range for deception level
        )
        
        self.interaction_depth_predictor = nn.Sequential(
            nn.Linear(hidden_dim // 2, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid()  # 0-1 range, will be scaled to depth levels
        )
        
        self.logging_verbosity_predictor = nn.Sequential(
            nn.Linear(hidden_dim // 2, 32),
            nn.ReLU(),
            nn.Linear(32, 3),  # 3 levels: low, medium, high
            nn.Softmax(dim=1)
        )
        
        # Effectiveness predictor
        self.effectiveness_predictor = nn.Sequential(
            nn.Linear(hidden_dim // 2 + behavior_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )
        
    def forward(self, context: torch.Tensor, current_behavior: Optional[torch.Tensor] = None) -> dict:
        """Generate optimal behavior parameters for given context"""
        
        encoded_context = self.context_encoder(context)
        
        # Generate behavior parameters
        response_delay = self.response_delay_predictor(encoded_context)
        deception_level = self.deception_level_predictor(encoded_context)
        interaction_depth = self.interaction_depth_predictor(encoded_context)
        logging_verbosity = self.logging_verbosity_predictor(encoded_context)
        
        behavior_params = {
            'response_delay': response_delay,
            'deception_level': deception_level,
            'interaction_depth': interaction_depth,
            'logging_verbosity': logging_verbosity,
            'encoded_context': encoded_context
        }
        
        # Predict effectiveness if current behavior is provided
        if current_behavior is not None:
            combined_input = torch.cat([encoded_context, current_behavior], dim=1)
            effectiveness = self.effectiveness_predictor(combined_input)
            behavior_params['predicted_effectiveness'] = effectiveness
        
        return behavior_params

class EnsembleNeuralNetwork(nn.Module):
    """Ensemble of specialized neural networks for robust predictions"""
    
    def __init__(self, input_dim: int = 128):
        super(EnsembleNeuralNetwork, self).__init__()
        
        self.input_dim = input_dim
        
        # Multiple specialized networks
        self.threat_predictor = ThreatLevelPredictor(input_dim)
        self.attacker_profiler = AttackerProfiler(input_dim)
        self.behavior_adapter = BehaviorAdaptationNetwork(input_dim // 2)
        
        # Meta-learning network for combining predictions
        self.meta_network = nn.Sequential(
            nn.Linear(64, 128),  # Combined features from all networks
            nn.ReLU(),
            nn.BatchNorm1d(128),
            nn.Dropout(0.3),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.Tanh()
        )
        
        # Final prediction heads
        self.final_threat_predictor = nn.Sequential(
            nn.Linear(32, 1),
            nn.Sigmoid()
        )
        
        self.confidence_estimator = nn.Sequential(
            nn.Linear(32, 1),
            nn.Sigmoid()
        )
        
    def forward(self, x: torch.Tensor) -> dict:
        """Ensemble forward pass combining all specialized networks"""
        
        # Get predictions from specialized networks
        threat_output = self.threat_predictor(x)
        profiler_output = self.attacker_profiler(x)
        
        # Combine key features for meta-learning
        combined_features = torch.cat([
            threat_output['features'][:, :16],  # First 16 threat features
            profiler_output['profile_vector'][:, :16],  # First 16 profile features
            threat_output['threat_level'],
            profiler_output['threat_level'],
            profiler_output['sophistication'],
            profiler_output['automation_score'],
            threat_output['confidence'][:, :16] if threat_output['confidence'].shape[1] >= 16 else 
            F.pad(threat_output['confidence'], (0, 16 - threat_output['confidence'].shape[1]))
        ], dim=1)
        
        # Meta-learning
        meta_features = self.meta_network(combined_features)
        
        # Final predictions
        final_threat = self.final_threat_predictor(meta_features)
        final_confidence = self.confidence_estimator(meta_features)
        
        return {
            'ensemble_threat_level': final_threat,
            'ensemble_confidence': final_confidence,
            'meta_features': meta_features,
            'individual_predictions': {
                'threat_predictor': threat_output,
                'attacker_profiler': profiler_output
            }
        }

# Utility functions for model initialization and training
def initialize_weights(model: nn.Module):
    """Initialize model weights using Xavier/He initialization"""
    for module in model.modules():
        if isinstance(module, nn.Linear):
            nn.init.xavier_uniform_(module.weight)
            if module.bias is not None:
                nn.init.zeros_(module.bias)
        elif isinstance(module, nn.LSTM):
            for name, param in module.named_parameters():
                if 'weight' in name:
                    nn.init.xavier_uniform_(param)
                elif 'bias' in name:
                    nn.init.zeros_(param)

def create_model_suite(input_dim: int = 128, device: str = 'cpu') -> dict:
    """Create a complete suite of neural network models"""
    
    models = {
        'attacker_profiler': AttackerProfiler(input_dim).to(device),
        'rl_agent': ReinforcementLearningAgent(input_dim // 2).to(device),
        'pattern_recognizer': AttackPatternRecognizer(input_dim // 2).to(device),
        'threat_predictor': ThreatLevelPredictor(input_dim).to(device),
        'behavior_adapter': BehaviorAdaptationNetwork(input_dim // 2).to(device),
        'ensemble_network': EnsembleNeuralNetwork(input_dim).to(device)
    }
    
    # Initialize weights
    for model in models.values():
        initialize_weights(model)
    
    return models
