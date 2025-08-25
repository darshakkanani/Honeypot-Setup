#!/usr/bin/env python3
"""
Monitoring and metrics utilities for HoneyPort
"""

import time
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from collections import defaultdict, deque
from dataclasses import dataclass
import logging

@dataclass
class MetricPoint:
    """Single metric data point"""
    timestamp: datetime
    value: float
    labels: Dict[str, str] = None

class MetricsCollector:
    """Collect and store system and application metrics"""
    
    def __init__(self, retention_hours: int = 24):
        self.retention_hours = retention_hours
        self.metrics = defaultdict(lambda: deque(maxlen=retention_hours * 3600))  # 1 point per second
        self.lock = threading.RLock()
        self.running = False
        self.collection_thread = None
        
    def start_collection(self, interval: float = 1.0):
        """Start metrics collection thread"""
        if self.running:
            return
            
        self.running = True
        self.collection_thread = threading.Thread(target=self._collection_loop, args=(interval,))
        self.collection_thread.daemon = True
        self.collection_thread.start()
        logging.info("Metrics collection started")
    
    def stop_collection(self):
        """Stop metrics collection"""
        self.running = False
        if self.collection_thread:
            self.collection_thread.join(timeout=5)
        logging.info("Metrics collection stopped")
    
    def _collection_loop(self, interval: float):
        """Main collection loop"""
        while self.running:
            try:
                self._collect_system_metrics()
                time.sleep(interval)
            except Exception as e:
                logging.error(f"Error collecting metrics: {e}")
                time.sleep(interval)
    
    def _collect_system_metrics(self):
        """Collect system performance metrics"""
        now = datetime.now()
        
        # CPU metrics
        cpu_percent = psutil.cpu_percent()
        self.record_metric('system_cpu_percent', cpu_percent, now)
        
        # Memory metrics
        memory = psutil.virtual_memory()
        self.record_metric('system_memory_percent', memory.percent, now)
        self.record_metric('system_memory_used_bytes', memory.used, now)
        self.record_metric('system_memory_available_bytes', memory.available, now)
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        self.record_metric('system_disk_percent', disk.percent, now)
        self.record_metric('system_disk_used_bytes', disk.used, now)
        self.record_metric('system_disk_free_bytes', disk.free, now)
        
        # Network metrics
        network = psutil.net_io_counters()
        self.record_metric('system_network_bytes_sent', network.bytes_sent, now)
        self.record_metric('system_network_bytes_recv', network.bytes_recv, now)
        
        # Process count
        process_count = len(psutil.pids())
        self.record_metric('system_process_count', process_count, now)
    
    def record_metric(self, name: str, value: float, timestamp: datetime = None, labels: Dict[str, str] = None):
        """Record a metric value"""
        if timestamp is None:
            timestamp = datetime.now()
            
        with self.lock:
            metric_point = MetricPoint(timestamp, value, labels or {})
            self.metrics[name].append(metric_point)
    
    def get_metric_values(self, name: str, since: datetime = None) -> List[MetricPoint]:
        """Get metric values since timestamp"""
        if since is None:
            since = datetime.now() - timedelta(hours=1)
            
        with self.lock:
            if name not in self.metrics:
                return []
            
            return [point for point in self.metrics[name] if point.timestamp >= since]
    
    def get_metric_summary(self, name: str, since: datetime = None) -> Dict[str, float]:
        """Get metric summary statistics"""
        values = self.get_metric_values(name, since)
        if not values:
            return {}
        
        metric_values = [point.value for point in values]
        return {
            'count': len(metric_values),
            'min': min(metric_values),
            'max': max(metric_values),
            'avg': sum(metric_values) / len(metric_values),
            'current': metric_values[-1] if metric_values else 0
        }
    
    def get_all_metrics_summary(self) -> Dict[str, Dict[str, float]]:
        """Get summary for all metrics"""
        with self.lock:
            return {name: self.get_metric_summary(name) for name in self.metrics.keys()}

class AttackMetrics:
    """Track attack-specific metrics"""
    
    def __init__(self):
        self.attack_counts = defaultdict(int)
        self.ip_counts = defaultdict(int)
        self.hourly_attacks = defaultdict(int)
        self.attack_types = defaultdict(int)
        self.threat_levels = deque(maxlen=1000)
        self.response_times = deque(maxlen=1000)
        self.lock = threading.RLock()
    
    def record_attack(self, source_ip: str, attack_type: str, threat_level: float, response_time: float = None):
        """Record an attack event"""
        with self.lock:
            current_hour = datetime.now().replace(minute=0, second=0, microsecond=0)
            
            self.attack_counts['total'] += 1
            self.ip_counts[source_ip] += 1
            self.hourly_attacks[current_hour] += 1
            self.attack_types[attack_type] += 1
            self.threat_levels.append(threat_level)
            
            if response_time is not None:
                self.response_times.append(response_time)
    
    def get_attack_stats(self) -> Dict[str, Any]:
        """Get comprehensive attack statistics"""
        with self.lock:
            now = datetime.now()
            last_hour = now - timedelta(hours=1)
            last_24h = now - timedelta(hours=24)
            
            # Recent attack counts
            recent_hourly = {k: v for k, v in self.hourly_attacks.items() if k >= last_24h}
            attacks_last_hour = sum(v for k, v in recent_hourly.items() if k >= last_hour)
            attacks_last_24h = sum(recent_hourly.values())
            
            # Top attackers
            top_ips = sorted(self.ip_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # Top attack types
            top_attack_types = sorted(self.attack_types.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # Threat level statistics
            threat_stats = {}
            if self.threat_levels:
                threat_values = list(self.threat_levels)
                threat_stats = {
                    'avg': sum(threat_values) / len(threat_values),
                    'min': min(threat_values),
                    'max': max(threat_values),
                    'high_threat_count': sum(1 for t in threat_values if t >= 0.7)
                }
            
            # Response time statistics
            response_stats = {}
            if self.response_times:
                response_values = list(self.response_times)
                response_stats = {
                    'avg_ms': sum(response_values) / len(response_values),
                    'min_ms': min(response_values),
                    'max_ms': max(response_values)
                }
            
            return {
                'total_attacks': self.attack_counts['total'],
                'unique_ips': len(self.ip_counts),
                'attacks_last_hour': attacks_last_hour,
                'attacks_last_24h': attacks_last_24h,
                'top_attackers': top_ips,
                'top_attack_types': top_attack_types,
                'threat_level_stats': threat_stats,
                'response_time_stats': response_stats,
                'hourly_distribution': dict(recent_hourly)
            }

class HealthChecker:
    """System health monitoring"""
    
    def __init__(self):
        self.checks = {}
        self.last_check_time = {}
        self.lock = threading.RLock()
    
    def register_check(self, name: str, check_func, interval: int = 60):
        """Register a health check function"""
        with self.lock:
            self.checks[name] = {
                'func': check_func,
                'interval': interval,
                'last_result': None,
                'last_error': None
            }
    
    def run_check(self, name: str) -> Dict[str, Any]:
        """Run a specific health check"""
        if name not in self.checks:
            return {'status': 'unknown', 'error': 'Check not found'}
        
        check = self.checks[name]
        try:
            result = check['func']()
            check['last_result'] = result
            check['last_error'] = None
            return {'status': 'healthy', 'result': result}
        except Exception as e:
            check['last_error'] = str(e)
            return {'status': 'unhealthy', 'error': str(e)}
    
    def run_all_checks(self) -> Dict[str, Dict[str, Any]]:
        """Run all registered health checks"""
        results = {}
        with self.lock:
            for name in self.checks.keys():
                results[name] = self.run_check(name)
        return results
    
    def get_overall_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        check_results = self.run_all_checks()
        
        healthy_count = sum(1 for result in check_results.values() if result['status'] == 'healthy')
        total_count = len(check_results)
        
        overall_status = 'healthy' if healthy_count == total_count else 'degraded'
        if healthy_count == 0:
            overall_status = 'unhealthy'
        
        return {
            'status': overall_status,
            'healthy_checks': healthy_count,
            'total_checks': total_count,
            'checks': check_results,
            'timestamp': datetime.now().isoformat()
        }

# Global instances
metrics_collector = MetricsCollector()
attack_metrics = AttackMetrics()
health_checker = HealthChecker()

def init_monitoring():
    """Initialize monitoring components"""
    # Start metrics collection
    metrics_collector.start_collection()
    
    # Register default health checks
    health_checker.register_check('cpu_usage', lambda: psutil.cpu_percent() < 90)
    health_checker.register_check('memory_usage', lambda: psutil.virtual_memory().percent < 90)
    health_checker.register_check('disk_usage', lambda: psutil.disk_usage('/').percent < 90)
    
    logging.info("Monitoring initialized")

def shutdown_monitoring():
    """Shutdown monitoring components"""
    metrics_collector.stop_collection()
    logging.info("Monitoring shutdown")

def get_prometheus_metrics() -> str:
    """Export metrics in Prometheus format"""
    lines = []
    
    # System metrics
    system_metrics = metrics_collector.get_all_metrics_summary()
    for metric_name, stats in system_metrics.items():
        if 'current' in stats:
            lines.append(f"{metric_name} {stats['current']}")
    
    # Attack metrics
    attack_stats = attack_metrics.get_attack_stats()
    lines.append(f"honeyport_total_attacks {attack_stats['total_attacks']}")
    lines.append(f"honeyport_unique_ips {attack_stats['unique_ips']}")
    lines.append(f"honeyport_attacks_last_hour {attack_stats['attacks_last_hour']}")
    lines.append(f"honeyport_attacks_last_24h {attack_stats['attacks_last_24h']}")
    
    if attack_stats['threat_level_stats']:
        threat_stats = attack_stats['threat_level_stats']
        lines.append(f"honeyport_avg_threat_level {threat_stats['avg']}")
        lines.append(f"honeyport_high_threat_attacks {threat_stats['high_threat_count']}")
    
    if attack_stats['response_time_stats']:
        response_stats = attack_stats['response_time_stats']
        lines.append(f"honeyport_avg_response_time_ms {response_stats['avg_ms']}")
    
    # Health status
    health = health_checker.get_overall_health()
    health_status = 1 if health['status'] == 'healthy' else 0
    lines.append(f"honeyport_health_status {health_status}")
    
    return '\n'.join(lines)
