"""
Automated Response and Mitigation Engine
Real-time threat response, IP blocking, and security automation
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
import structlog
from enum import Enum
import aiohttp
import subprocess
from dataclasses import dataclass, asdict

from ..core.config import config
from ..core.redis import RedisCache
from ..core.database import get_db
from ..models.attack import Attack
from ..utils.email import send_alert_email

logger = structlog.get_logger()

class ResponseAction(Enum):
    """Available automated response actions"""
    BLOCK_IP = "block_ip"
    RATE_LIMIT = "rate_limit"
    QUARANTINE = "quarantine"
    ALERT_ADMIN = "alert_admin"
    UPDATE_FIREWALL = "update_firewall"
    DEPLOY_DECOY = "deploy_decoy"
    ISOLATE_NETWORK = "isolate_network"
    CAPTURE_TRAFFIC = "capture_traffic"
    THREAT_HUNT = "threat_hunt"
    COUNTER_ATTACK = "counter_attack"

class ThreatLevel(Enum):
    """Threat severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ResponseRule:
    """Automated response rule configuration"""
    id: str
    name: str
    description: str
    conditions: Dict[str, Any]
    actions: List[ResponseAction]
    threat_level: ThreatLevel
    cooldown_minutes: int
    max_executions_per_hour: int
    enabled: bool
    priority: int

@dataclass
class ResponseExecution:
    """Response execution record"""
    id: str
    rule_id: str
    attack_id: str
    actions_taken: List[str]
    timestamp: datetime
    success: bool
    details: Dict[str, Any]
    execution_time_ms: int

class AutomatedResponseEngine:
    """Main automated response and mitigation engine"""
    
    def __init__(self):
        self.response_rules: List[ResponseRule] = []
        self.execution_history: List[ResponseExecution] = []
        self.blocked_ips: Set[str] = set()
        self.quarantined_assets: Set[str] = set()
        
        # Rate limiting for response actions
        self.action_counters = {}
        self.cooldown_timers = {}
        
        # Integration endpoints
        self.firewall_api = config.FIREWALL_API_URL
        self.siem_api = config.SIEM_API_URL
        self.network_api = config.NETWORK_API_URL
        
        # Response metrics
        self.metrics = {
            "total_responses": 0,
            "successful_responses": 0,
            "failed_responses": 0,
            "ips_blocked": 0,
            "alerts_sent": 0,
            "last_response_time": None
        }
        
        # Load default rules
        self._load_default_rules()
    
    async def initialize(self):
        """Initialize the response engine"""
        try:
            # Load response rules from database
            await self._load_response_rules()
            
            # Load blocked IPs from cache
            await self._load_blocked_ips()
            
            # Start background processes
            asyncio.create_task(self._cleanup_expired_blocks())
            asyncio.create_task(self._response_metrics_collector())
            
            logger.info("response_engine_initialized", 
                       rules=len(self.response_rules),
                       blocked_ips=len(self.blocked_ips))
                       
        except Exception as e:
            logger.error("response_engine_init_failed", error=str(e))
    
    async def process_attack(self, attack_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process attack and trigger automated responses"""
        try:
            attack_id = attack_data.get("id", "")
            source_ip = attack_data.get("source_ip", "")
            
            logger.info("processing_attack_for_response", 
                       attack_id=attack_id,
                       source_ip=source_ip)
            
            # Evaluate response rules
            triggered_rules = await self._evaluate_rules(attack_data)
            
            if not triggered_rules:
                return {
                    "responses_triggered": 0,
                    "actions_taken": [],
                    "message": "No response rules triggered"
                }
            
            # Execute responses
            execution_results = []
            total_actions = 0
            
            for rule in triggered_rules:
                # Check cooldown and rate limits
                if not await self._check_execution_limits(rule):
                    continue
                
                # Execute rule actions
                result = await self._execute_rule(rule, attack_data)
                execution_results.append(result)
                total_actions += len(result.actions_taken)
                
                # Update metrics
                self.metrics["total_responses"] += 1
                if result.success:
                    self.metrics["successful_responses"] += 1
                else:
                    self.metrics["failed_responses"] += 1
            
            # Update last response time
            self.metrics["last_response_time"] = datetime.utcnow().isoformat()
            
            # Log response summary
            logger.info("automated_responses_completed", 
                       attack_id=attack_id,
                       rules_triggered=len(triggered_rules),
                       actions_taken=total_actions)
            
            return {
                "responses_triggered": len(triggered_rules),
                "actions_taken": total_actions,
                "execution_results": [asdict(result) for result in execution_results],
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("attack_response_processing_failed", 
                        attack_id=attack_data.get("id"), 
                        error=str(e))
            return {"error": str(e)}
    
    async def _evaluate_rules(self, attack_data: Dict[str, Any]) -> List[ResponseRule]:
        """Evaluate which response rules should be triggered"""
        triggered_rules = []
        
        for rule in self.response_rules:
            if not rule.enabled:
                continue
            
            try:
                if await self._evaluate_rule_conditions(rule, attack_data):
                    triggered_rules.append(rule)
                    logger.debug("response_rule_triggered", 
                               rule_id=rule.id,
                               rule_name=rule.name)
            except Exception as e:
                logger.error("rule_evaluation_failed", 
                           rule_id=rule.id, 
                           error=str(e))
        
        # Sort by priority (higher priority first)
        triggered_rules.sort(key=lambda r: r.priority, reverse=True)
        
        return triggered_rules
    
    async def _evaluate_rule_conditions(self, rule: ResponseRule, attack_data: Dict[str, Any]) -> bool:
        """Evaluate if rule conditions are met"""
        conditions = rule.conditions
        
        # Check threat score threshold
        if "min_threat_score" in conditions:
            threat_score = attack_data.get("threat_intelligence", {}).get("threat_score", 0.0)
            if threat_score < conditions["min_threat_score"]:
                return False
        
        # Check attack types
        if "attack_types" in conditions:
            attack_type = attack_data.get("attack_type", "")
            if attack_type not in conditions["attack_types"]:
                return False
        
        # Check source IP patterns
        if "ip_patterns" in conditions:
            source_ip = attack_data.get("source_ip", "")
            if not any(pattern in source_ip for pattern in conditions["ip_patterns"]):
                return False
        
        # Check geographic conditions
        if "blocked_countries" in conditions:
            country = attack_data.get("geolocation", {}).get("country_code", "")
            if country in conditions["blocked_countries"]:
                return True
        
        # Check reputation conditions
        if "min_reputation_score" in conditions:
            reputation = attack_data.get("threat_intelligence", {}).get("reputation", {})
            rep_score = reputation.get("overall_score", 0.5)
            if rep_score < conditions["min_reputation_score"]:
                return False
        
        # Check IOC matches
        if "require_ioc_match" in conditions and conditions["require_ioc_match"]:
            ioc_matches = attack_data.get("threat_intelligence", {}).get("ioc_matches", [])
            if not ioc_matches:
                return False
        
        # Check frequency conditions
        if "max_attacks_per_hour" in conditions:
            source_ip = attack_data.get("source_ip", "")
            recent_attacks = await self._count_recent_attacks(source_ip, hours=1)
            if recent_attacks >= conditions["max_attacks_per_hour"]:
                return True
        
        # Check payload conditions
        if "payload_patterns" in conditions:
            payload = attack_data.get("raw_payload", "")
            if any(pattern in payload for pattern in conditions["payload_patterns"]):
                return True
        
        return True
    
    async def _execute_rule(self, rule: ResponseRule, attack_data: Dict[str, Any]) -> ResponseExecution:
        """Execute a response rule's actions"""
        start_time = datetime.utcnow()
        execution_id = f"exec_{int(start_time.timestamp())}_{rule.id}"
        
        actions_taken = []
        success = True
        details = {}
        
        try:
            for action in rule.actions:
                try:
                    action_result = await self._execute_action(action, attack_data, rule)
                    actions_taken.append(f"{action.value}:{action_result['status']}")
                    details[action.value] = action_result
                    
                    if not action_result.get("success", False):
                        success = False
                        
                except Exception as e:
                    logger.error("action_execution_failed", 
                               action=action.value, 
                               error=str(e))
                    actions_taken.append(f"{action.value}:failed")
                    details[action.value] = {"success": False, "error": str(e)}
                    success = False
            
            # Record execution
            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            execution = ResponseExecution(
                id=execution_id,
                rule_id=rule.id,
                attack_id=attack_data.get("id", ""),
                actions_taken=actions_taken,
                timestamp=start_time,
                success=success,
                details=details,
                execution_time_ms=execution_time
            )
            
            # Store execution record
            await self._store_execution_record(execution)
            
            # Update cooldown timer
            self.cooldown_timers[rule.id] = datetime.utcnow() + timedelta(minutes=rule.cooldown_minutes)
            
            return execution
            
        except Exception as e:
            logger.error("rule_execution_failed", rule_id=rule.id, error=str(e))
            return ResponseExecution(
                id=execution_id,
                rule_id=rule.id,
                attack_id=attack_data.get("id", ""),
                actions_taken=["execution_failed"],
                timestamp=start_time,
                success=False,
                details={"error": str(e)},
                execution_time_ms=0
            )
    
    async def _execute_action(self, action: ResponseAction, attack_data: Dict[str, Any], rule: ResponseRule) -> Dict[str, Any]:
        """Execute a specific response action"""
        source_ip = attack_data.get("source_ip", "")
        
        if action == ResponseAction.BLOCK_IP:
            return await self._block_ip(source_ip, rule)
        
        elif action == ResponseAction.RATE_LIMIT:
            return await self._apply_rate_limit(source_ip, rule)
        
        elif action == ResponseAction.QUARANTINE:
            return await self._quarantine_asset(source_ip, rule)
        
        elif action == ResponseAction.ALERT_ADMIN:
            return await self._send_admin_alert(attack_data, rule)
        
        elif action == ResponseAction.UPDATE_FIREWALL:
            return await self._update_firewall_rules(source_ip, rule)
        
        elif action == ResponseAction.DEPLOY_DECOY:
            return await self._deploy_decoy_service(attack_data, rule)
        
        elif action == ResponseAction.ISOLATE_NETWORK:
            return await self._isolate_network_segment(source_ip, rule)
        
        elif action == ResponseAction.CAPTURE_TRAFFIC:
            return await self._capture_network_traffic(source_ip, rule)
        
        elif action == ResponseAction.THREAT_HUNT:
            return await self._initiate_threat_hunt(attack_data, rule)
        
        elif action == ResponseAction.COUNTER_ATTACK:
            return await self._execute_counter_attack(attack_data, rule)
        
        else:
            return {"success": False, "error": f"Unknown action: {action}"}
    
    async def _block_ip(self, ip_address: str, rule: ResponseRule) -> Dict[str, Any]:
        """Block IP address through multiple mechanisms"""
        try:
            # Add to local blocked set
            self.blocked_ips.add(ip_address)
            
            # Cache blocked IP with expiration
            block_duration = rule.conditions.get("block_duration_hours", 24)
            await RedisCache.set(
                f"blocked_ip:{ip_address}", 
                json.dumps({
                    "blocked_at": datetime.utcnow().isoformat(),
                    "rule_id": rule.id,
                    "duration_hours": block_duration
                }),
                expire=block_duration * 3600
            )
            
            # Update firewall if configured
            if self.firewall_api:
                await self._add_firewall_block(ip_address, block_duration)
            
            # Update iptables (if running on Linux)
            await self._add_iptables_block(ip_address)
            
            # Update metrics
            self.metrics["ips_blocked"] += 1
            
            logger.info("ip_blocked", 
                       ip=ip_address, 
                       rule_id=rule.id,
                       duration_hours=block_duration)
            
            return {
                "success": True,
                "status": "blocked",
                "ip_address": ip_address,
                "duration_hours": block_duration,
                "mechanisms": ["local", "firewall", "iptables"]
            }
            
        except Exception as e:
            logger.error("ip_blocking_failed", ip=ip_address, error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _send_admin_alert(self, attack_data: Dict[str, Any], rule: ResponseRule) -> Dict[str, Any]:
        """Send alert to administrators"""
        try:
            # Prepare alert data
            alert_data = {
                "attack_id": attack_data.get("id"),
                "source_ip": attack_data.get("source_ip"),
                "attack_type": attack_data.get("attack_type"),
                "severity": attack_data.get("severity"),
                "threat_score": attack_data.get("threat_intelligence", {}).get("threat_score", 0.0),
                "rule_triggered": rule.name,
                "timestamp": datetime.utcnow().isoformat(),
                "recommended_actions": self._get_recommended_actions(attack_data)
            }
            
            # Send email alert
            await send_alert_email(
                subject=f"SecureHoney Alert: {rule.name}",
                alert_type="automated_response",
                alert_data=alert_data
            )
            
            # Send to SIEM if configured
            if self.siem_api:
                await self._send_siem_alert(alert_data)
            
            # Update metrics
            self.metrics["alerts_sent"] += 1
            
            logger.info("admin_alert_sent", 
                       attack_id=attack_data.get("id"),
                       rule_id=rule.id)
            
            return {
                "success": True,
                "status": "alert_sent",
                "recipients": ["admin"],
                "channels": ["email", "siem"]
            }
            
        except Exception as e:
            logger.error("admin_alert_failed", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _update_firewall_rules(self, ip_address: str, rule: ResponseRule) -> Dict[str, Any]:
        """Update firewall rules to block IP"""
        try:
            if not self.firewall_api:
                return {"success": False, "error": "Firewall API not configured"}
            
            # Prepare firewall rule
            firewall_rule = {
                "action": "block",
                "source_ip": ip_address,
                "duration_hours": rule.conditions.get("block_duration_hours", 24),
                "reason": f"SecureHoney automated response: {rule.name}",
                "priority": rule.priority
            }
            
            # Send to firewall API
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.firewall_api}/rules",
                    json=firewall_rule,
                    headers={"Authorization": f"Bearer {config.FIREWALL_API_KEY}"}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info("firewall_rule_added", 
                                   ip=ip_address,
                                   rule_id=result.get("rule_id"))
                        return {
                            "success": True,
                            "status": "firewall_updated",
                            "firewall_rule_id": result.get("rule_id")
                        }
                    else:
                        error_msg = await response.text()
                        return {"success": False, "error": f"Firewall API error: {error_msg}"}
            
        except Exception as e:
            logger.error("firewall_update_failed", ip=ip_address, error=str(e))
            return {"success": False, "error": str(e)}
    
    def _load_default_rules(self):
        """Load default response rules"""
        self.response_rules = [
            ResponseRule(
                id="high_threat_block",
                name="High Threat IP Block",
                description="Block IPs with high threat scores",
                conditions={
                    "min_threat_score": 0.8,
                    "block_duration_hours": 24
                },
                actions=[ResponseAction.BLOCK_IP, ResponseAction.ALERT_ADMIN],
                threat_level=ThreatLevel.HIGH,
                cooldown_minutes=5,
                max_executions_per_hour=100,
                enabled=True,
                priority=90
            ),
            ResponseRule(
                id="malware_detection",
                name="Malware Detection Response",
                description="Respond to malware-related attacks",
                conditions={
                    "attack_types": ["MALWARE", "TROJAN", "BACKDOOR"],
                    "require_ioc_match": True
                },
                actions=[ResponseAction.QUARANTINE, ResponseAction.CAPTURE_TRAFFIC, ResponseAction.ALERT_ADMIN],
                threat_level=ThreatLevel.CRITICAL,
                cooldown_minutes=1,
                max_executions_per_hour=50,
                enabled=True,
                priority=95
            ),
            ResponseRule(
                id="brute_force_mitigation",
                name="Brute Force Mitigation",
                description="Mitigate brute force attacks",
                conditions={
                    "attack_types": ["BRUTE_FORCE", "CREDENTIAL_STUFFING"],
                    "max_attacks_per_hour": 10
                },
                actions=[ResponseAction.RATE_LIMIT, ResponseAction.BLOCK_IP],
                threat_level=ThreatLevel.MEDIUM,
                cooldown_minutes=10,
                max_executions_per_hour=20,
                enabled=True,
                priority=70
            ),
            ResponseRule(
                id="tor_exit_response",
                name="Tor Exit Node Response",
                description="Respond to attacks from Tor exit nodes",
                conditions={
                    "require_ioc_match": True,
                    "ioc_types": ["tor_exit"]
                },
                actions=[ResponseAction.RATE_LIMIT, ResponseAction.DEPLOY_DECOY],
                threat_level=ThreatLevel.MEDIUM,
                cooldown_minutes=30,
                max_executions_per_hour=10,
                enabled=True,
                priority=60
            )
        ]
    
    async def get_response_statistics(self) -> Dict[str, Any]:
        """Get comprehensive response engine statistics"""
        try:
            # Calculate recent activity
            recent_executions = [
                exec for exec in self.execution_history 
                if exec.timestamp > datetime.utcnow() - timedelta(hours=24)
            ]
            
            # Group by rule
            rule_stats = {}
            for rule in self.response_rules:
                rule_executions = [e for e in recent_executions if e.rule_id == rule.id]
                rule_stats[rule.id] = {
                    "name": rule.name,
                    "executions_24h": len(rule_executions),
                    "success_rate": sum(1 for e in rule_executions if e.success) / len(rule_executions) if rule_executions else 0,
                    "enabled": rule.enabled,
                    "priority": rule.priority
                }
            
            stats = {
                "total_rules": len(self.response_rules),
                "enabled_rules": len([r for r in self.response_rules if r.enabled]),
                "blocked_ips": len(self.blocked_ips),
                "quarantined_assets": len(self.quarantined_assets),
                "executions_24h": len(recent_executions),
                "success_rate_24h": sum(1 for e in recent_executions if e.success) / len(recent_executions) if recent_executions else 0,
                "rule_statistics": rule_stats,
                "metrics": self.metrics,
                "last_updated": datetime.utcnow().isoformat()
            }
            
            return stats
            
        except Exception as e:
            logger.error("response_stats_failed", error=str(e))
            return {}

# Global response engine instance
response_engine = AutomatedResponseEngine()

# Convenience functions
async def process_attack_for_response(attack_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process attack through automated response engine"""
    return await response_engine.process_attack(attack_data)

async def get_response_engine_stats() -> Dict[str, Any]:
    """Get response engine statistics"""
    return await response_engine.get_response_statistics()

async def block_ip_address(ip_address: str, duration_hours: int = 24) -> Dict[str, Any]:
    """Manually block IP address"""
    rule = ResponseRule(
        id="manual_block",
        name="Manual IP Block",
        description="Manually triggered IP block",
        conditions={"block_duration_hours": duration_hours},
        actions=[ResponseAction.BLOCK_IP],
        threat_level=ThreatLevel.HIGH,
        cooldown_minutes=0,
        max_executions_per_hour=1000,
        enabled=True,
        priority=100
    )
    
    attack_data = {"source_ip": ip_address, "id": f"manual_{int(datetime.utcnow().timestamp())}"}
    return await response_engine._execute_action(ResponseAction.BLOCK_IP, attack_data, rule)
