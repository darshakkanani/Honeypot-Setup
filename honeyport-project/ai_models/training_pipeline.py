#!/usr/bin/env python3
"""
AI Model Training Pipeline for HoneyPort
Continuous learning system with automated retraining and model management
"""

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix
import pandas as pd
import logging
import os
import json
import pickle
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, asdict
import threading
import time
from collections import deque
import yaml

from .neural_networks import *
from .feature_extraction import AdvancedFeatureExtractor, AttackContext
from .ensemble_predictor import MasterEnsemble

@dataclass
class TrainingConfig:
    """Configuration for training pipeline"""
    batch_size: int = 32
    learning_rate: float = 0.001
    epochs: int = 100
    validation_split: float = 0.2
    early_stopping_patience: int = 10
    model_save_interval: int = 50
    continuous_learning: bool = True
    retrain_threshold: float = 0.1  # Performance drop threshold
    min_samples_retrain: int = 100
    max_training_samples: int = 10000
    feature_selection_k: int = 64
    ensemble_update_frequency: int = 24  # hours

@dataclass
class ModelPerformance:
    """Track model performance metrics"""
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    loss: float
    timestamp: datetime
    sample_count: int

class DataManager:
    """Manage training data collection and preprocessing"""
    
    def __init__(self, config: TrainingConfig):
        self.config = config
        self.training_buffer = deque(maxlen=config.max_training_samples)
        self.validation_buffer = deque(maxlen=config.max_training_samples // 5)
        self.feature_extractor = AdvancedFeatureExtractor()
        
    def add_training_sample(self, context: AttackContext, label: int, 
                          behavior_labels: Dict[str, int] = None):
        """Add new training sample to buffer"""
        sample = {
            'context': context,
            'label': label,
            'behavior_labels': behavior_labels or {},
            'timestamp': datetime.now()
        }
        self.training_buffer.append(sample)
        
    def get_training_data(self, min_samples: int = None) -> Tuple[np.ndarray, np.ndarray, Dict]:
        """Extract training data from buffer"""
        min_samples = min_samples or self.config.min_samples_retrain
        
        if len(self.training_buffer) < min_samples:
            return None, None, None
        
        # Convert buffer to training data
        contexts = [sample['context'] for sample in self.training_buffer]
        labels = np.array([sample['label'] for sample in self.training_buffer])
        
        # Extract features
        if not self.feature_extractor.fitted:
            features = self.feature_extractor.fit_transform(contexts, labels)
        else:
            features = np.array([self.feature_extractor.transform(ctx) for ctx in contexts])
        
        # Collect behavior labels
        behavior_data = {}
        behavior_keys = set()
        for sample in self.training_buffer:
            behavior_keys.update(sample['behavior_labels'].keys())
        
        for key in behavior_keys:
            behavior_data[key] = np.array([
                sample['behavior_labels'].get(key, 0) 
                for sample in self.training_buffer
            ])
        
        return features, labels, behavior_data
    
    def create_sequences(self, window_size: int = 10) -> List[List[Dict]]:
        """Create attack sequences for pattern analysis"""
        sequences = []
        
        # Group samples by source IP and time windows
        ip_groups = {}
        for sample in self.training_buffer:
            ip = sample['context'].source_ip
            if ip not in ip_groups:
                ip_groups[ip] = []
            ip_groups[ip].append(sample)
        
        # Create sequences from each IP group
        for ip, samples in ip_groups.items():
            # Sort by timestamp
            samples.sort(key=lambda x: x['timestamp'])
            
            # Create sliding windows
            for i in range(len(samples) - window_size + 1):
                sequence = []
                for j in range(window_size):
                    attack_data = {
                        'attack_type': samples[i + j]['context'].attack_type,
                        'timestamp': samples[i + j]['timestamp'],
                        'payload_complexity': samples[i + j]['context'].payload_complexity,
                        'severity_score': samples[i + j]['label'],
                        'source_ip': samples[i + j]['context'].source_ip,
                        'user_agent': samples[i + j]['context'].user_agent,
                        'url_path': samples[i + j]['context'].url_path
                    }
                    sequence.append(attack_data)
                sequences.append(sequence)
        
        return sequences

class ModelTrainer:
    """Train and manage AI models"""
    
    def __init__(self, config: TrainingConfig, models_path: str):
        self.config = config
        self.models_path = models_path
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Initialize models
        self.models = {}
        self.optimizers = {}
        self.performance_history = {}
        
        # Create models directory
        os.makedirs(models_path, exist_ok=True)
        
        self._initialize_models()
        
    def _initialize_models(self):
        """Initialize neural network models"""
        # Attacker Profiler
        self.models['attacker_profiler'] = AttackerProfiler(
            input_dim=64, hidden_dim=256, output_dim=128
        ).to(self.device)
        
        # RL Agent
        self.models['rl_agent'] = ReinforcementLearningAgent(
            state_dim=64, action_dim=10, hidden_dim=256
        ).to(self.device)
        
        # Attack Pattern Recognizer
        self.models['pattern_recognizer'] = AttackPatternRecognizer(
            input_dim=64, hidden_dim=256, num_layers=3
        ).to(self.device)
        
        # Threat Level Predictor
        self.models['threat_predictor'] = ThreatLevelPredictor(
            input_dim=64, hidden_dim=128
        ).to(self.device)
        
        # Behavior Adaptation Network
        self.models['behavior_adapter'] = BehaviorAdaptationNetwork(
            input_dim=64, hidden_dim=128
        ).to(self.device)
        
        # Initialize optimizers
        for name, model in self.models.items():
            self.optimizers[name] = optim.Adam(
                model.parameters(), 
                lr=self.config.learning_rate,
                weight_decay=1e-5
            )
            self.performance_history[name] = []
    
    def train_models(self, X: np.ndarray, y: np.ndarray, 
                    behavior_data: Dict[str, np.ndarray] = None) -> Dict[str, ModelPerformance]:
        """Train all models with provided data"""
        
        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=self.config.validation_split, random_state=42
        )
        
        # Convert to tensors
        X_train_tensor = torch.FloatTensor(X_train).to(self.device)
        X_val_tensor = torch.FloatTensor(X_val).to(self.device)
        y_train_tensor = torch.LongTensor(y_train).to(self.device)
        y_val_tensor = torch.LongTensor(y_val).to(self.device)
        
        # Create data loaders
        train_dataset = TensorDataset(X_train_tensor, y_train_tensor)
        train_loader = DataLoader(train_dataset, batch_size=self.config.batch_size, shuffle=True)
        
        val_dataset = TensorDataset(X_val_tensor, y_val_tensor)
        val_loader = DataLoader(val_dataset, batch_size=self.config.batch_size)
        
        results = {}
        
        # Train each model
        for model_name in self.models.keys():
            logging.info(f"Training {model_name}...")
            performance = self._train_single_model(
                model_name, train_loader, val_loader, behavior_data
            )
            results[model_name] = performance
            
        return results
    
    def _train_single_model(self, model_name: str, train_loader: DataLoader, 
                           val_loader: DataLoader, behavior_data: Dict = None) -> ModelPerformance:
        """Train a single model"""
        
        model = self.models[model_name]
        optimizer = self.optimizers[model_name]
        criterion = nn.CrossEntropyLoss()
        
        best_val_loss = float('inf')
        patience_counter = 0
        
        for epoch in range(self.config.epochs):
            # Training phase
            model.train()
            train_loss = 0.0
            train_correct = 0
            train_total = 0
            
            for batch_X, batch_y in train_loader:
                optimizer.zero_grad()
                
                # Forward pass
                if model_name == 'rl_agent':
                    # Special handling for RL agent
                    q_values = model(batch_X)
                    loss = criterion(q_values, batch_y)
                elif model_name == 'pattern_recognizer':
                    # LSTM model expects sequence dimension
                    batch_X_seq = batch_X.unsqueeze(1)  # Add sequence dimension
                    outputs = model(batch_X_seq)
                    loss = criterion(outputs, batch_y)
                else:
                    outputs = model(batch_X)
                    loss = criterion(outputs, batch_y)
                
                # Backward pass
                loss.backward()
                optimizer.step()
                
                train_loss += loss.item()
                
                # Calculate accuracy
                if model_name == 'rl_agent':
                    predicted = torch.argmax(q_values, 1)
                elif model_name == 'pattern_recognizer':
                    predicted = torch.argmax(outputs, 1)
                else:
                    predicted = torch.argmax(outputs, 1)
                
                train_total += batch_y.size(0)
                train_correct += (predicted == batch_y).sum().item()
            
            # Validation phase
            model.eval()
            val_loss = 0.0
            val_correct = 0
            val_total = 0
            
            with torch.no_grad():
                for batch_X, batch_y in val_loader:
                    if model_name == 'rl_agent':
                        q_values = model(batch_X)
                        loss = criterion(q_values, batch_y)
                        predicted = torch.argmax(q_values, 1)
                    elif model_name == 'pattern_recognizer':
                        batch_X_seq = batch_X.unsqueeze(1)
                        outputs = model(batch_X_seq)
                        loss = criterion(outputs, batch_y)
                        predicted = torch.argmax(outputs, 1)
                    else:
                        outputs = model(batch_X)
                        loss = criterion(outputs, batch_y)
                        predicted = torch.argmax(outputs, 1)
                    
                    val_loss += loss.item()
                    val_total += batch_y.size(0)
                    val_correct += (predicted == batch_y).sum().item()
            
            # Calculate metrics
            train_acc = train_correct / train_total
            val_acc = val_correct / val_total
            avg_train_loss = train_loss / len(train_loader)
            avg_val_loss = val_loss / len(val_loader)
            
            # Early stopping
            if avg_val_loss < best_val_loss:
                best_val_loss = avg_val_loss
                patience_counter = 0
                # Save best model
                self._save_model(model_name, model)
            else:
                patience_counter += 1
                
            if patience_counter >= self.config.early_stopping_patience:
                logging.info(f"Early stopping for {model_name} at epoch {epoch}")
                break
            
            # Log progress
            if epoch % 10 == 0:
                logging.info(f"{model_name} Epoch {epoch}: "
                           f"Train Loss: {avg_train_loss:.4f}, Train Acc: {train_acc:.4f}, "
                           f"Val Loss: {avg_val_loss:.4f}, Val Acc: {val_acc:.4f}")
        
        # Create performance record
        performance = ModelPerformance(
            accuracy=val_acc,
            precision=val_acc,  # Simplified for now
            recall=val_acc,
            f1_score=val_acc,
            loss=best_val_loss,
            timestamp=datetime.now(),
            sample_count=train_total
        )
        
        self.performance_history[model_name].append(performance)
        return performance
    
    def _save_model(self, model_name: str, model: nn.Module):
        """Save model checkpoint"""
        model_path = os.path.join(self.models_path, f"{model_name}.pth")
        torch.save({
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': self.optimizers[model_name].state_dict(),
            'timestamp': datetime.now().isoformat()
        }, model_path)
    
    def load_models(self):
        """Load saved models"""
        for model_name in self.models.keys():
            model_path = os.path.join(self.models_path, f"{model_name}.pth")
            if os.path.exists(model_path):
                checkpoint = torch.load(model_path, map_location=self.device)
                self.models[model_name].load_state_dict(checkpoint['model_state_dict'])
                self.optimizers[model_name].load_state_dict(checkpoint['optimizer_state_dict'])
                logging.info(f"Loaded {model_name} from {model_path}")

class ContinuousLearningManager:
    """Manage continuous learning and model updates"""
    
    def __init__(self, config: TrainingConfig, models_path: str):
        self.config = config
        self.models_path = models_path
        self.data_manager = DataManager(config)
        self.model_trainer = ModelTrainer(config, models_path)
        self.ensemble = MasterEnsemble()
        
        self.running = False
        self.last_retrain = datetime.now()
        self.performance_baseline = {}
        
        # Load existing models
        self.model_trainer.load_models()
        
    def start_continuous_learning(self):
        """Start continuous learning thread"""
        self.running = True
        learning_thread = threading.Thread(target=self._continuous_learning_loop)
        learning_thread.daemon = True
        learning_thread.start()
        logging.info("Continuous learning started")
    
    def stop_continuous_learning(self):
        """Stop continuous learning"""
        self.running = False
        logging.info("Continuous learning stopped")
    
    def add_attack_sample(self, context: AttackContext, threat_level: float,
                         behavior_labels: Dict[str, int] = None):
        """Add new attack sample for learning"""
        # Convert threat level to classification label
        label = 1 if threat_level > 0.5 else 0
        
        self.data_manager.add_training_sample(context, label, behavior_labels)
        
        # Check if immediate retraining is needed
        if self._should_retrain():
            self._trigger_retraining()
    
    def _continuous_learning_loop(self):
        """Main continuous learning loop"""
        while self.running:
            try:
                # Check if retraining is needed
                if self._should_retrain():
                    self._trigger_retraining()
                
                # Update ensemble periodically
                if self._should_update_ensemble():
                    self._update_ensemble()
                
                # Sleep for a while
                time.sleep(3600)  # Check every hour
                
            except Exception as e:
                logging.error(f"Error in continuous learning loop: {e}")
                time.sleep(300)  # Wait 5 minutes before retrying
    
    def _should_retrain(self) -> bool:
        """Determine if models should be retrained"""
        # Check if enough new samples
        if len(self.data_manager.training_buffer) < self.config.min_samples_retrain:
            return False
        
        # Check time since last retrain
        time_since_retrain = datetime.now() - self.last_retrain
        if time_since_retrain.total_seconds() < 3600:  # At least 1 hour
            return False
        
        # Check performance degradation
        if self._detect_performance_degradation():
            return True
        
        # Periodic retraining
        if time_since_retrain.total_seconds() > 24 * 3600:  # 24 hours
            return True
        
        return False
    
    def _should_update_ensemble(self) -> bool:
        """Check if ensemble should be updated"""
        time_since_retrain = datetime.now() - self.last_retrain
        return time_since_retrain.total_seconds() > self.config.ensemble_update_frequency * 3600
    
    def _detect_performance_degradation(self) -> bool:
        """Detect if model performance has degraded"""
        # Simple implementation - check recent performance vs baseline
        for model_name, history in self.model_trainer.performance_history.items():
            if len(history) < 2:
                continue
            
            recent_performance = history[-1].accuracy
            baseline = self.performance_baseline.get(model_name, recent_performance)
            
            if recent_performance < baseline - self.config.retrain_threshold:
                logging.info(f"Performance degradation detected for {model_name}")
                return True
        
        return False
    
    def _trigger_retraining(self):
        """Trigger model retraining"""
        logging.info("Triggering model retraining...")
        
        try:
            # Get training data
            X, y, behavior_data = self.data_manager.get_training_data()
            
            if X is None:
                logging.warning("Insufficient training data for retraining")
                return
            
            # Train models
            results = self.model_trainer.train_models(X, y, behavior_data)
            
            # Update performance baseline
            for model_name, performance in results.items():
                if model_name not in self.performance_baseline:
                    self.performance_baseline[model_name] = performance.accuracy
                else:
                    # Update baseline if performance improved
                    if performance.accuracy > self.performance_baseline[model_name]:
                        self.performance_baseline[model_name] = performance.accuracy
            
            self.last_retrain = datetime.now()
            logging.info("Model retraining completed successfully")
            
        except Exception as e:
            logging.error(f"Error during retraining: {e}")
    
    def _update_ensemble(self):
        """Update ensemble models"""
        try:
            logging.info("Updating ensemble models...")
            
            # Get training data
            X, y, behavior_data = self.data_manager.get_training_data()
            
            if X is None:
                return
            
            # Create sequences for pattern analysis
            sequences = self.data_manager.create_sequences()
            
            # Fit ensemble
            self.ensemble.fit(X, y, sequences, behavior_data)
            
            # Save ensemble
            ensemble_path = os.path.join(self.models_path, "ensemble.pkl")
            self.ensemble.save_ensemble(ensemble_path)
            
            logging.info("Ensemble update completed")
            
        except Exception as e:
            logging.error(f"Error updating ensemble: {e}")
    
    def get_training_status(self) -> Dict[str, Any]:
        """Get current training status"""
        return {
            'running': self.running,
            'samples_collected': len(self.data_manager.training_buffer),
            'last_retrain': self.last_retrain.isoformat(),
            'performance_baseline': self.performance_baseline,
            'models_trained': list(self.model_trainer.models.keys())
        }

def create_training_pipeline(config_path: str = None) -> ContinuousLearningManager:
    """Create and configure training pipeline"""
    
    # Load configuration
    if config_path and os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        config = TrainingConfig(**config_data.get('training', {}))
    else:
        config = TrainingConfig()
    
    # Determine models path
    models_path = os.path.join(os.path.dirname(__file__), '..', 'models')
    
    # Create training manager
    training_manager = ContinuousLearningManager(config, models_path)
    
    return training_manager
