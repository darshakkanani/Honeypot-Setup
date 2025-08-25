#!/usr/bin/env python3
"""
Blockchain Log Manager for HoneyPort
Interface for blockchain-secured logging with Solidity smart contracts
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from .blockchain import HoneyPortBlockchain
from .web3_manager import Web3Manager

class BlockchainLogManager:
    """Manages blockchain-secured logging for honeypot events with Solidity integration"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.blockchain_enabled = config.get('blockchain', {}).get('enabled', True)
        self.solidity_enabled = config.get('blockchain', {}).get('solidity_enabled', True)
        
        # Initialize blockchain components
        self.blockchain = None
        self.web3_manager = None
        self.fallback_logs = []
        
        if self.blockchain_enabled:
            if self.solidity_enabled:
                # Use Solidity smart contracts
                self.web3_manager = Web3Manager(config)
                self._setup_smart_contract()
            else:
                # Use Python blockchain
                self.blockchain = HoneyPortBlockchain(config)
            
            print("⛓️ Blockchain logging initialized with Solidity smart contracts")
        else:
            print("📝 Fallback logging mode (blockchain disabled)")
    
    def _setup_smart_contract(self):
        """Setup Solidity smart contract"""
        if not self.web3_manager:
            return
        
        # Try to load existing contract first
        if not self.web3_manager.load_contract():
            print("🚀 Deploying HoneyPort smart contract...")
            if self.web3_manager.deploy_contract():
                print("✅ Smart contract deployed successfully")
            else:
                print("❌ Smart contract deployment failed, falling back to Python blockchain")
                self.solidity_enabled = False
                self.blockchain = HoneyPortBlockchain(self.config)
    
    def log_attack(self, attack_data: Dict[str, Any]) -> str:
        """Log attack event to blockchain or smart contract"""
        log_entry = {
            "log_id": self._generate_log_id(),
            "timestamp": datetime.now().isoformat(),
            "event_type": "attack",
            **attack_data
        }
        
        if self.blockchain_enabled:
            if self.solidity_enabled and self.web3_manager:
                # Log to smart contract
                try:
                    contract_hash = self.web3_manager.log_attack(attack_data)
                    if contract_hash:
                        print(f"📝 Attack logged to smart contract: {contract_hash[:16]}...")
                        return contract_hash
                    else:
                        return self._fallback_to_python_blockchain(log_entry)
                except Exception as e:
                    print(f"⚠️ Smart contract logging failed: {e}")
                    return self._fallback_to_python_blockchain(log_entry)
            elif self.blockchain:
                # Use Python blockchain
                try:
                    log_id = self.blockchain.add_log(log_entry)
                    print(f"📝 Attack logged to blockchain: {log_id[:16]}...")
                    return log_id
                except Exception as e:
                    print(f"⚠️ Blockchain logging failed: {e}")
                    return self._fallback_log(log_entry)
            else:
                return self._fallback_log(log_entry)
        else:
            return self._fallback_log(log_entry)
    
    def _fallback_to_python_blockchain(self, log_entry: Dict[str, Any]) -> str:
        """Fallback to Python blockchain if smart contract fails"""
        if not self.blockchain:
            self.blockchain = HoneyPortBlockchain(self.config)
        
        try:
            return self.blockchain.add_log(log_entry)
        except Exception as e:
            print(f"⚠️ Python blockchain also failed: {e}")
            return self._fallback_log(log_entry)
    
    def log_session(self, session_data: Dict[str, Any]) -> str:
        """Log session data to blockchain"""
        log_entry = {
            "log_id": self._generate_log_id(),
            "timestamp": datetime.now().isoformat(),
            "event_type": "session",
            **session_data
        }
        
        # For sessions, use Python blockchain (smart contract optimized for attacks)
        if self.blockchain_enabled:
            if not self.blockchain:
                self.blockchain = HoneyPortBlockchain(self.config)
            
            try:
                return self.blockchain.add_log(log_entry)
            except Exception as e:
                print(f"⚠️ Session logging failed: {e}")
                return self._fallback_log(log_entry)
        else:
            return self._fallback_log(log_entry)
    
    def log_ai_decision(self, ai_data: Dict[str, Any]) -> str:
        """Log AI decision to blockchain"""
        log_entry = {
            "log_id": self._generate_log_id(),
            "timestamp": datetime.now().isoformat(),
            "event_type": "ai_decision",
            **ai_data
        }
        
        # For AI decisions, use Python blockchain
        if self.blockchain_enabled:
            if not self.blockchain:
                self.blockchain = HoneyPortBlockchain(self.config)
            
            try:
                return self.blockchain.add_log(log_entry)
            except Exception as e:
                print(f"⚠️ AI decision logging failed: {e}")
                return self._fallback_log(log_entry)
        else:
            return self._fallback_log(log_entry)
    
    def get_recent_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent logs from smart contract and Python blockchain"""
        all_logs = []
        
        # Get logs from smart contract
        if self.solidity_enabled and self.web3_manager:
            try:
                smart_contract_logs = self.web3_manager.get_recent_logs(limit // 2)
                for log in smart_contract_logs:
                    all_logs.append({
                        "log_id": log['log_hash'],
                        "timestamp": datetime.fromtimestamp(log['timestamp']).isoformat(),
                        "event_type": "attack",
                        "source_ip": log['source_ip'],
                        "attack_type": log['attack_type'],
                        "severity": log['severity'],
                        "payload": log['payload'],
                        "ai_behavior": log['ai_decision'],
                        "verified": log['verified'],
                        "source": "smart_contract"
                    })
            except Exception as e:
                print(f"⚠️ Failed to get smart contract logs: {e}")
        
        # Get logs from Python blockchain
        if self.blockchain:
            try:
                python_logs = self.blockchain.get_recent_logs(limit // 2)
                all_logs.extend(python_logs)
            except Exception as e:
                print(f"⚠️ Failed to get Python blockchain logs: {e}")
        
        # Add fallback logs if needed
        if not all_logs and hasattr(self, 'fallback_logs') and self.fallback_logs:
            all_logs = self.fallback_logs[-limit:]
        
        # Sort by timestamp and limit
        all_logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return all_logs[:limit]
    
    def get_attack_statistics(self) -> Dict[str, Any]:
        """Get comprehensive attack statistics"""
        logs = self.get_recent_logs(1000)
        
        stats = {
            "total_attacks": 0,
            "unique_source_ips": set(),
            "attack_type_distribution": {},
            "severity_distribution": {},
            "latest_attack_time": None,
            "total_blocks": 0,
            "blockchain_enabled": self.blockchain_enabled,
            "solidity_enabled": self.solidity_enabled,
            "smart_contract_stats": {},
            "verified_logs": 0
        }
        
        for log in logs:
            if log.get("event_type") == "attack":
                stats["total_attacks"] += 1
                
                # Track unique IPs
                source_ip = log.get("source_ip")
                if source_ip:
                    stats["unique_source_ips"].add(source_ip)
                
                # Track attack types
                attack_type = log.get("attack_type", "unknown")
                stats["attack_type_distribution"][attack_type] = \
                    stats["attack_type_distribution"].get(attack_type, 0) + 1
                
                # Track severity
                severity = log.get("severity", "unknown")
                stats["severity_distribution"][severity] = \
                    stats["severity_distribution"].get(severity, 0) + 1
                
                # Track verified logs
                if log.get("verified"):
                    stats["verified_logs"] += 1
                
                # Track latest attack
                timestamp = log.get("timestamp")
                if timestamp and (not stats["latest_attack_time"] or timestamp > stats["latest_attack_time"]):
                    stats["latest_attack_time"] = timestamp
        
        # Convert set to list for JSON serialization
        stats["unique_source_ips"] = list(stats["unique_source_ips"])
        
        # Get smart contract stats
        if hasattr(self, 'solidity_enabled') and self.solidity_enabled and self.web3_manager:
            try:
                contract_stats = self.web3_manager.get_contract_stats()
                stats["smart_contract_stats"] = contract_stats
                stats["total_blocks"] += contract_stats.get("total_blocks", 0)
            except Exception as e:
                print(f"⚠️ Failed to get smart contract stats: {e}")
        
        # Get Python blockchain stats
        if self.blockchain:
            try:
                stats["total_blocks"] += len(self.blockchain.chain)
            except:
                pass
        
        return stats
    
    def verify_chain_integrity(self) -> Dict[str, Any]:
        """Verify blockchain and smart contract integrity"""
        results = {
            "valid": True,
            "total_blocks": 0,
            "verified_blocks": 0,
            "smart_contract_valid": False,
            "python_blockchain_valid": False,
            "errors": []
        }
        
        # Verify smart contract
        if hasattr(self, 'solidity_enabled') and self.solidity_enabled and self.web3_manager:
            try:
                smart_contract_valid = self.web3_manager.verify_blockchain()
                results["smart_contract_valid"] = smart_contract_valid
                
                contract_stats = self.web3_manager.get_contract_stats()
                results["total_blocks"] += contract_stats.get("total_blocks", 0)
                
                if smart_contract_valid:
                    results["verified_blocks"] += contract_stats.get("total_blocks", 0)
                else:
                    results["errors"].append("Smart contract integrity compromised")
                    results["valid"] = False
                    
            except Exception as e:
                results["errors"].append(f"Smart contract verification failed: {e}")
                results["valid"] = False
        
        # Verify Python blockchain
        if self.blockchain:
            try:
                python_valid = self.blockchain.is_chain_valid()
                results["python_blockchain_valid"] = python_valid
                
                python_blocks = len(self.blockchain.chain)
                results["total_blocks"] += python_blocks
                
                if python_valid:
                    results["verified_blocks"] += python_blocks
                else:
                    results["errors"].append("Python blockchain integrity compromised")
                    results["valid"] = False
                    
            except Exception as e:
                results["errors"].append(f"Python blockchain verification failed: {e}")
                results["valid"] = False
        
        # Get chain hash
        try:
            if hasattr(self, 'solidity_enabled') and self.solidity_enabled and self.web3_manager:
                results["chain_hash"] = self.web3_manager.contract_address or "unknown"
            elif self.blockchain:
                results["chain_hash"] = self.blockchain.get_latest_block_hash()
            else:
                results["chain_hash"] = "no_blockchain"
        except:
            results["chain_hash"] = "unknown"
        
        return results
    
    def export_logs(self, format: str = "json") -> List[Dict[str, Any]]:
        """Export all logs from all sources"""
        all_logs = []
        
        # Export from smart contract
        if hasattr(self, 'solidity_enabled') and self.solidity_enabled and self.web3_manager:
            try:
                smart_logs = self.web3_manager.get_recent_logs(1000)
                all_logs.extend(smart_logs)
            except Exception as e:
                print(f"⚠️ Smart contract export failed: {e}")
        
        # Export from Python blockchain
        if self.blockchain:
            try:
                python_logs = self.blockchain.export_chain()
                all_logs.extend(python_logs)
            except Exception as e:
                print(f"⚠️ Python blockchain export failed: {e}")
        
        # Add fallback logs
        all_logs.extend(self.fallback_logs)
        
        return all_logs
    
    def get_latest_block_hash(self) -> str:
        """Get latest block hash from active blockchain"""
        if hasattr(self, 'solidity_enabled') and self.solidity_enabled and self.web3_manager:
            try:
                return self.web3_manager.contract_address or "smart_contract"
            except:
                pass
        
        if self.blockchain:
            try:
                return self.blockchain.get_latest_block_hash()
            except:
                pass
        
        return "no_blockchain"
    
    def get_blockchain_status(self) -> Dict[str, Any]:
        """Get comprehensive blockchain status"""
        status = {
            "blockchain_enabled": self.blockchain_enabled,
            "solidity_enabled": getattr(self, 'solidity_enabled', False),
            "smart_contract_connected": False,
            "python_blockchain_active": False,
            "web3_connected": False,
            "account_balance": 0.0,
            "contract_address": None
        }
        
        if self.web3_manager:
            status["web3_connected"] = self.web3_manager.is_connected()
            status["account_balance"] = self.web3_manager.get_balance()
            status["contract_address"] = self.web3_manager.contract_address
            status["smart_contract_connected"] = self.web3_manager.contract is not None
        
        if self.blockchain:
            status["python_blockchain_active"] = True
        
        return status
    
    def _generate_log_id(self) -> str:
        """Generate unique log ID"""
        import uuid
        return str(uuid.uuid4())
    
    def _fallback_log(self, log_entry: Dict[str, Any]) -> str:
        """Fallback logging to memory/file"""
        if not hasattr(self, 'fallback_logs'):
            self.fallback_logs = []
        
        self.fallback_logs.append(log_entry)
        
        # Also write to file
        try:
            log_file = self.config.get('logging', {}).get('file_path', 'logs/honeyport.log')
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            
            with open(log_file, 'a') as f:
                f.write(f"{json.dumps(log_entry)}\n")
            
            return log_entry["log_id"]
        except Exception as e:
            print(f"⚠️ File logging failed: {e}")
            return log_entry["log_id"]
