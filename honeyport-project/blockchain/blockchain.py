#!/usr/bin/env python3
"""
Blockchain Core for Secure HoneyPort Logging
Immutable log storage with cryptographic verification
"""

import hashlib
import json
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

class Block:
    """Individual block in the blockchain"""
    
    def __init__(self, index: int, logs: List[Dict], previous_hash: str, timestamp: float = None):
        self.index = index
        self.logs = logs
        self.previous_hash = previous_hash
        self.timestamp = timestamp or time.time()
        self.nonce = 0
        self.hash = self.calculate_hash()
    
    def calculate_hash(self) -> str:
        """Calculate SHA-256 hash of block contents"""
        block_string = json.dumps({
            "index": self.index,
            "logs": self.logs,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "nonce": self.nonce
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def mine_block(self, difficulty: int):
        """Mine block with proof-of-work"""
        target = "0" * difficulty
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()
        print(f"🔗 Block mined: {self.hash}")
    
    def to_dict(self) -> Dict:
        """Convert block to dictionary"""
        return {
            "index": self.index,
            "logs": self.logs,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "nonce": self.nonce,
            "hash": self.hash
        }

class HoneyPortBlockchain:
    """Blockchain for secure honeypot log storage"""
    
    def __init__(self, difficulty: int = 4, encryption_key: str = None):
        self.chain: List[Block] = []
        self.pending_logs: List[Dict] = []
        self.difficulty = difficulty
        self.block_size = 100
        self.encryption_key = encryption_key
        self.cipher = self._setup_encryption()
        
        # Create genesis block
        self.create_genesis_block()
    
    def _setup_encryption(self) -> Optional[Fernet]:
        """Setup encryption for sensitive log data"""
        if not self.encryption_key:
            return None
        
        # Derive key from password
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'honeyport_salt',
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.encryption_key.encode()))
        return Fernet(key)
    
    def create_genesis_block(self):
        """Create the first block in the chain"""
        genesis_logs = [{
            "type": "genesis",
            "message": "HoneyPort blockchain initialized",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0"
        }]
        
        genesis_block = Block(0, genesis_logs, "0")
        genesis_block.mine_block(self.difficulty)
        self.chain.append(genesis_block)
    
    def get_latest_block(self) -> Block:
        """Get the most recent block"""
        return self.chain[-1]
    
    def add_log(self, log_data: Dict[str, Any]):
        """Add a log entry to pending logs"""
        # Encrypt sensitive data
        if self.cipher and 'payload' in log_data:
            log_data['payload'] = self.cipher.encrypt(
                json.dumps(log_data['payload']).encode()
            ).decode()
            log_data['encrypted'] = True
        
        # Add metadata
        log_data.update({
            "blockchain_timestamp": datetime.now().isoformat(),
            "log_id": hashlib.sha256(
                f"{log_data.get('timestamp', '')}{log_data.get('source_ip', '')}"
                f"{log_data.get('attack_type', '')}".encode()
            ).hexdigest()[:16]
        })
        
        self.pending_logs.append(log_data)
        
        # Create new block if we have enough logs
        if len(self.pending_logs) >= self.block_size:
            self.mine_pending_logs()
    
    def mine_pending_logs(self):
        """Mine a new block with pending logs"""
        if not self.pending_logs:
            return
        
        new_block = Block(
            index=len(self.chain),
            logs=self.pending_logs.copy(),
            previous_hash=self.get_latest_block().hash
        )
        
        new_block.mine_block(self.difficulty)
        self.chain.append(new_block)
        
        print(f"📦 New block added: Index {new_block.index}, Logs: {len(self.pending_logs)}")
        self.pending_logs = []
    
    def is_chain_valid(self) -> bool:
        """Verify blockchain integrity"""
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            
            # Verify current block hash
            if current_block.hash != current_block.calculate_hash():
                print(f"❌ Invalid hash at block {i}")
                return False
            
            # Verify link to previous block
            if current_block.previous_hash != previous_block.hash:
                print(f"❌ Invalid previous hash at block {i}")
                return False
        
        return True
    
    def get_logs_by_criteria(self, criteria: Dict[str, Any]) -> List[Dict]:
        """Search logs across all blocks"""
        matching_logs = []
        
        for block in self.chain:
            for log in block.logs:
                match = True
                for key, value in criteria.items():
                    if key not in log or log[key] != value:
                        match = False
                        break
                
                if match:
                    # Decrypt if needed
                    if self.cipher and log.get('encrypted'):
                        try:
                            decrypted_payload = self.cipher.decrypt(
                                log['payload'].encode()
                            ).decode()
                            log['payload'] = json.loads(decrypted_payload)
                            log['encrypted'] = False
                        except Exception as e:
                            log['decryption_error'] = str(e)
                    
                    matching_logs.append(log)
        
        return matching_logs
    
    def get_blockchain_stats(self) -> Dict[str, Any]:
        """Get blockchain statistics"""
        total_logs = sum(len(block.logs) for block in self.chain)
        
        return {
            "total_blocks": len(self.chain),
            "total_logs": total_logs,
            "pending_logs": len(self.pending_logs),
            "chain_valid": self.is_chain_valid(),
            "latest_block_hash": self.get_latest_block().hash,
            "blockchain_size_mb": len(json.dumps([block.to_dict() for block in self.chain])) / (1024 * 1024)
        }
    
    def export_chain(self, filepath: str):
        """Export blockchain to file"""
        chain_data = {
            "metadata": {
                "version": "1.0.0",
                "created": datetime.now().isoformat(),
                "difficulty": self.difficulty,
                "total_blocks": len(self.chain)
            },
            "chain": [block.to_dict() for block in self.chain]
        }
        
        with open(filepath, 'w') as f:
            json.dump(chain_data, f, indent=2)
        
        print(f"💾 Blockchain exported to {filepath}")
    
    def import_chain(self, filepath: str) -> bool:
        """Import blockchain from file"""
        try:
            with open(filepath, 'r') as f:
                chain_data = json.load(f)
            
            # Reconstruct blocks
            imported_chain = []
            for block_data in chain_data['chain']:
                block = Block(
                    block_data['index'],
                    block_data['logs'],
                    block_data['previous_hash'],
                    block_data['timestamp']
                )
                block.nonce = block_data['nonce']
                block.hash = block_data['hash']
                imported_chain.append(block)
            
            # Verify imported chain
            temp_blockchain = HoneyPortBlockchain(self.difficulty)
            temp_blockchain.chain = imported_chain
            
            if temp_blockchain.is_chain_valid():
                self.chain = imported_chain
                print(f"✅ Blockchain imported successfully from {filepath}")
                return True
            else:
                print(f"❌ Invalid blockchain in {filepath}")
                return False
                
        except Exception as e:
            print(f"❌ Error importing blockchain: {e}")
            return False
