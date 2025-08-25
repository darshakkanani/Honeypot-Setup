#!/usr/bin/env python3
"""
SecureHoney Centralized Log Manager
Unified logging system for all SecureHoney components
"""

import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import gzip
import shutil

class SecureHoneyLogger:
    def __init__(self, component_name: str):
        self.component_name = component_name
        self.log_dir = Path(__file__).parent
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging configuration"""
        # Create log directories
        (self.log_dir / "attacks").mkdir(exist_ok=True)
        (self.log_dir / "web-attacks").mkdir(exist_ok=True)
        (self.log_dir / "analysis").mkdir(exist_ok=True)
        (self.log_dir / "blockchain").mkdir(exist_ok=True)
        (self.log_dir / "system").mkdir(exist_ok=True)
        
        # Setup logger
        self.logger = logging.getLogger(f"SecureHoney.{self.component_name}")
        self.logger.setLevel(logging.INFO)
        
        # File handler
        log_file = self.log_dir / "system" / f"{self.component_name}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def log_attack(self, attack_data: Dict[str, Any], attack_type: str = "network"):
        """Log attack data"""
        log_subdir = "attacks" if attack_type == "network" else "web-attacks"
        log_file = self.log_dir / log_subdir / f"{attack_type}_attacks_{datetime.now().strftime('%Y%m%d')}.json"
        
        try:
            with open(log_file, 'a') as f:
                f.write(json.dumps(attack_data) + '\n')
            self.logger.info(f"Attack logged: {attack_data.get('id', 'unknown')}")
        except Exception as e:
            self.logger.error(f"Failed to log attack: {e}")
    
    def get_recent_attacks(self, hours: int = 24, attack_type: str = "all") -> List[Dict[str, Any]]:
        """Get recent attacks from logs"""
        attacks = []
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # Determine which log directories to search
        search_dirs = []
        if attack_type in ["all", "network"]:
            search_dirs.append("attacks")
        if attack_type in ["all", "web"]:
            search_dirs.append("web-attacks")
        
        for log_subdir in search_dirs:
            log_dir = self.log_dir / log_subdir
            if not log_dir.exists():
                continue
                
            for log_file in log_dir.glob("*.json"):
                try:
                    with open(log_file, 'r') as f:
                        for line in f:
                            try:
                                attack = json.loads(line.strip())
                                attack_time = datetime.fromisoformat(attack.get('timestamp', ''))
                                if attack_time >= cutoff_time:
                                    attacks.append(attack)
                            except (json.JSONDecodeError, ValueError):
                                continue
                except Exception as e:
                    self.logger.error(f"Error reading log file {log_file}: {e}")
        
        return sorted(attacks, key=lambda x: x.get('timestamp', ''), reverse=True)
    
    def compress_old_logs(self, days_old: int = 7):
        """Compress logs older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        for log_subdir in ["attacks", "web-attacks", "analysis", "system"]:
            log_dir = self.log_dir / log_subdir
            if not log_dir.exists():
                continue
            
            for log_file in log_dir.glob("*.json"):
                try:
                    file_date = datetime.fromtimestamp(log_file.stat().st_mtime)
                    if file_date < cutoff_date and not log_file.name.endswith('.gz'):
                        # Compress the file
                        with open(log_file, 'rb') as f_in:
                            with gzip.open(f"{log_file}.gz", 'wb') as f_out:
                                shutil.copyfileobj(f_in, f_out)
                        
                        # Remove original file
                        log_file.unlink()
                        self.logger.info(f"Compressed old log: {log_file.name}")
                        
                except Exception as e:
                    self.logger.error(f"Error compressing log {log_file}: {e}")
    
    def get_log_statistics(self) -> Dict[str, Any]:
        """Get logging statistics"""
        stats = {
            'total_log_files': 0,
            'total_size_mb': 0,
            'attacks_today': 0,
            'web_attacks_today': 0,
            'log_directories': {}
        }
        
        today = datetime.now().strftime('%Y%m%d')
        
        for log_subdir in ["attacks", "web-attacks", "analysis", "blockchain", "system"]:
            log_dir = self.log_dir / log_subdir
            if not log_dir.exists():
                continue
            
            dir_stats = {
                'file_count': 0,
                'size_mb': 0,
                'latest_file': None
            }
            
            for log_file in log_dir.iterdir():
                if log_file.is_file():
                    dir_stats['file_count'] += 1
                    file_size = log_file.stat().st_size / (1024 * 1024)  # MB
                    dir_stats['size_mb'] += file_size
                    stats['total_size_mb'] += file_size
                    
                    if not dir_stats['latest_file'] or log_file.stat().st_mtime > dir_stats['latest_file']:
                        dir_stats['latest_file'] = log_file.stat().st_mtime
            
            stats['log_directories'][log_subdir] = dir_stats
            stats['total_log_files'] += dir_stats['file_count']
        
        # Count today's attacks
        try:
            attack_file = self.log_dir / "attacks" / f"attacks_{today}.json"
            if attack_file.exists():
                with open(attack_file, 'r') as f:
                    stats['attacks_today'] = len(f.readlines())
        except:
            pass
        
        try:
            web_attack_file = self.log_dir / "web-attacks" / f"web_attacks_{today}.json"
            if web_attack_file.exists():
                with open(web_attack_file, 'r') as f:
                    stats['web_attacks_today'] = len(f.readlines())
        except:
            pass
        
        return stats
