#!/usr/bin/env python3
"""
SecureHoney Blockchain Logger
Immutable attack record storage using blockchain technology
"""

import json
import hashlib
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Block:
    def __init__(self, index: int, transactions: List[Dict], previous_hash: str):
        self.index = index
        self.timestamp = time.time()
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = 0
        self.hash = self.calculate_hash()
    
    def calculate_hash(self) -> str:
        """Calculate block hash"""
        block_string = json.dumps({
            'index': self.index,
            'timestamp': self.timestamp,
            'transactions': self.transactions,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def mine_block(self, difficulty: int = 4):
        """Mine block with proof of work"""
        target = "0" * difficulty
        
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()
        
        logger.info(f"⛏️ Block mined: {self.hash}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert block to dictionary"""
        return {
            'index': self.index,
            'timestamp': self.timestamp,
            'transactions': self.transactions,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce,
            'hash': self.hash
        }

class SecureHoneyBlockchain:
    def __init__(self):
        self.chain: List[Block] = []
        self.pending_transactions: List[Dict] = []
        self.mining_reward = 1
        self.difficulty = 2  # Lower for faster mining
        
        # Create genesis block
        self.create_genesis_block()
        
        # Load existing chain
        self.load_chain()
    
    def create_genesis_block(self):
        """Create the first block in the chain"""
        genesis_block = Block(0, [], "0")
        genesis_block.mine_block(self.difficulty)
        self.chain = [genesis_block]
    
    def get_latest_block(self) -> Block:
        """Get the latest block in the chain"""
        return self.chain[-1]
    
    def add_transaction(self, transaction: Dict[str, Any]):
        """Add transaction to pending transactions"""
        # Add timestamp if not present
        if 'timestamp' not in transaction:
            transaction['timestamp'] = datetime.now().isoformat()
        
        # Add transaction ID
        transaction_string = json.dumps(transaction, sort_keys=True)
        transaction['tx_id'] = hashlib.sha256(transaction_string.encode()).hexdigest()[:16]
        
        self.pending_transactions.append(transaction)
        logger.info(f"📝 Transaction added: {transaction['tx_id']}")
    
    def mine_pending_transactions(self, mining_reward_address: str = "SecureHoney"):
        """Mine pending transactions into a new block"""
        if not self.pending_transactions:
            logger.info("No pending transactions to mine")
            return
        
        # Add mining reward transaction
        reward_transaction = {
            'type': 'mining_reward',
            'to': mining_reward_address,
            'amount': self.mining_reward,
            'timestamp': datetime.now().isoformat()
        }
        
        transactions = self.pending_transactions + [reward_transaction]
        
        # Create new block
        block = Block(
            len(self.chain),
            transactions,
            self.get_latest_block().hash
        )
        
        # Mine the block
        block.mine_block(self.difficulty)
        
        # Add to chain
        self.chain.append(block)
        
        # Clear pending transactions
        self.pending_transactions = []
        
        # Save chain
        self.save_chain()
        
        logger.info(f"⛓️ New block added: #{block.index}")
    
    def log_attack(self, attack_data: Dict[str, Any]):
        """Log attack data to blockchain"""
        attack_transaction = {
            'type': 'attack_log',
            'attack_id': attack_data.get('id', 'unknown'),
            'source_ip': attack_data.get('source_ip', 'unknown'),
            'target_port': attack_data.get('target_port', 0),
            'attack_type': attack_data.get('attack_type', 'unknown'),
            'severity': attack_data.get('severity', 'unknown'),
            'timestamp': attack_data.get('timestamp', datetime.now().isoformat()),
            'details': attack_data
        }
        
        self.add_transaction(attack_transaction)
        
        # Auto-mine if we have enough transactions
        if len(self.pending_transactions) >= 5:
            self.mine_pending_transactions()
    
    def validate_chain(self) -> bool:
        """Validate the entire blockchain"""
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            
            # Check if current block's hash is valid
            if current_block.hash != current_block.calculate_hash():
                logger.error(f"Invalid hash at block {i}")
                return False
            
            # Check if current block points to previous block
            if current_block.previous_hash != previous_block.hash:
                logger.error(f"Invalid previous hash at block {i}")
                return False
        
        return True
    
    def get_attacks_by_ip(self, ip: str) -> List[Dict[str, Any]]:
        """Get all attacks from specific IP"""
        attacks = []
        
        for block in self.chain:
            for transaction in block.transactions:
                if (transaction.get('type') == 'attack_log' and 
                    transaction.get('source_ip') == ip):
                    attacks.append(transaction)
        
        return attacks
    
    def get_attack_statistics(self) -> Dict[str, Any]:
        """Get blockchain attack statistics"""
        total_attacks = 0
        attack_types = {}
        severity_counts = {}
        unique_ips = set()
        
        for block in self.chain:
            for transaction in block.transactions:
                if transaction.get('type') == 'attack_log':
                    total_attacks += 1
                    
                    # Count attack types
                    attack_type = transaction.get('attack_type', 'unknown')
                    attack_types[attack_type] = attack_types.get(attack_type, 0) + 1
                    
                    # Count severities
                    severity = transaction.get('severity', 'unknown')
                    severity_counts[severity] = severity_counts.get(severity, 0) + 1
                    
                    # Track unique IPs
                    source_ip = transaction.get('source_ip')
                    if source_ip:
                        unique_ips.add(source_ip)
        
        return {
            'total_blocks': len(self.chain),
            'total_attacks': total_attacks,
            'unique_attackers': len(unique_ips),
            'attack_types': attack_types,
            'severity_distribution': severity_counts,
            'chain_valid': self.validate_chain(),
            'pending_transactions': len(self.pending_transactions)
        }
    
    def search_attacks(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search attacks by criteria"""
        results = []
        
        for block in self.chain:
            for transaction in block.transactions:
                if transaction.get('type') != 'attack_log':
                    continue
                
                match = True
                for key, value in criteria.items():
                    if key in transaction and transaction[key] != value:
                        match = False
                        break
                
                if match:
                    results.append({
                        'block_index': block.index,
                        'block_hash': block.hash,
                        'transaction': transaction
                    })
        
        return results
    
    def export_chain(self, format: str = 'json') -> str:
        """Export blockchain in specified format"""
        if format == 'json':
            chain_data = {
                'chain': [block.to_dict() for block in self.chain],
                'pending_transactions': self.pending_transactions,
                'metadata': {
                    'total_blocks': len(self.chain),
                    'chain_valid': self.validate_chain(),
                    'export_timestamp': datetime.now().isoformat()
                }
            }
            return json.dumps(chain_data, indent=2)
        
        return "Unsupported format"
    
    def save_chain(self):
        """Save blockchain to file"""
        chain_dir = Path("../shared-utils/logging/blockchain")
        chain_dir.mkdir(parents=True, exist_ok=True)
        
        chain_file = chain_dir / "securehoney_chain.json"
        
        try:
            chain_data = {
                'chain': [block.to_dict() for block in self.chain],
                'pending_transactions': self.pending_transactions
            }
            
            with open(chain_file, 'w') as f:
                json.dump(chain_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save blockchain: {e}")
    
    def load_chain(self):
        """Load blockchain from file"""
        chain_dir = Path("../shared-utils/logging/blockchain")
        chain_file = chain_dir / "securehoney_chain.json"
        
        if not chain_file.exists():
            return
        
        try:
            with open(chain_file, 'r') as f:
                data = json.load(f)
            
            # Reconstruct chain
            self.chain = []
            for block_data in data.get('chain', []):
                block = Block(
                    block_data['index'],
                    block_data['transactions'],
                    block_data['previous_hash']
                )
                block.timestamp = block_data['timestamp']
                block.nonce = block_data['nonce']
                block.hash = block_data['hash']
                self.chain.append(block)
            
            # Load pending transactions
            self.pending_transactions = data.get('pending_transactions', [])
            
            logger.info(f"📚 Loaded blockchain with {len(self.chain)} blocks")
            
        except Exception as e:
            logger.error(f"Failed to load blockchain: {e}")
            # Reset to genesis block
            self.create_genesis_block()
    
    def get_recent_blocks(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent blocks"""
        recent_blocks = self.chain[-count:] if len(self.chain) > count else self.chain
        return [block.to_dict() for block in recent_blocks]

def main():
    """Main entry point for testing"""
    blockchain = SecureHoneyBlockchain()
    
    # Test with sample attack data
    sample_attacks = [
        {
            'id': 'attack_001',
            'source_ip': '192.168.1.100',
            'target_port': 22,
            'attack_type': 'SSH_BRUTE_FORCE',
            'severity': 'HIGH'
        },
        {
            'id': 'attack_002',
            'source_ip': '10.0.0.50',
            'target_port': 80,
            'attack_type': 'HTTP_INJECTION',
            'severity': 'MEDIUM'
        }
    ]
    
    # Log attacks
    for attack in sample_attacks:
        blockchain.log_attack(attack)
    
    # Mine remaining transactions
    blockchain.mine_pending_transactions()
    
    # Get statistics
    stats = blockchain.get_attack_statistics()
    print("Blockchain Statistics:")
    print(json.dumps(stats, indent=2))
    
    # Validate chain
    is_valid = blockchain.validate_chain()
    print(f"\nBlockchain valid: {is_valid}")

if __name__ == "__main__":
    main()
