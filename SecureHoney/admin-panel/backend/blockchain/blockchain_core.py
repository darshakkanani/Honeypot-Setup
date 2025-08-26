"""
Advanced Blockchain Integration for Attack Verification and Immutable Logging
Distributed consensus for attack validation and tamper-proof audit trails
"""

import hashlib
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import asyncio
import aiohttp
import structlog
from dataclasses import dataclass, asdict
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.exceptions import InvalidSignature
import base64

from ..core.config import config
from ..core.redis import RedisCache
from ..core.database import get_db

logger = structlog.get_logger()

@dataclass
class Transaction:
    """Blockchain transaction for attack data"""
    id: str
    timestamp: float
    attack_id: str
    source_ip: str
    attack_type: str
    severity: str
    data_hash: str
    validator_signature: str
    consensus_score: float
    metadata: Dict[str, Any]

@dataclass
class Block:
    """Blockchain block containing attack transactions"""
    index: int
    timestamp: float
    transactions: List[Transaction]
    previous_hash: str
    merkle_root: str
    nonce: int
    hash: str
    validator: str
    consensus_signatures: List[str]

class BlockchainConsensus:
    """Distributed consensus mechanism for attack validation"""
    
    def __init__(self):
        self.validators = {}  # validator_id -> public_key
        self.consensus_threshold = 0.67  # 67% consensus required
        self.validation_timeout = 30  # seconds
        
    async def validate_attack(self, attack_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate attack through distributed consensus"""
        try:
            # Create validation request
            validation_request = {
                "attack_id": attack_data.get("id"),
                "timestamp": time.time(),
                "data_hash": self._hash_attack_data(attack_data),
                "attack_data": attack_data,
                "validator_id": config.VALIDATOR_ID or "primary"
            }
            
            # Get validator responses
            validator_responses = await self._collect_validator_responses(validation_request)
            
            # Calculate consensus
            consensus_result = await self._calculate_consensus(validator_responses)
            
            # Create consensus transaction
            if consensus_result["valid"]:
                transaction = await self._create_consensus_transaction(
                    attack_data, consensus_result
                )
                return {
                    "validated": True,
                    "consensus_score": consensus_result["score"],
                    "transaction": asdict(transaction),
                    "validators": len(validator_responses),
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "validated": False,
                    "consensus_score": consensus_result["score"],
                    "reason": consensus_result.get("reason", "Consensus not reached"),
                    "validators": len(validator_responses)
                }
                
        except Exception as e:
            logger.error("consensus_validation_failed", 
                        attack_id=attack_data.get("id"), 
                        error=str(e))
            return {"validated": False, "error": str(e)}
    
    def _hash_attack_data(self, attack_data: Dict[str, Any]) -> str:
        """Create cryptographic hash of attack data"""
        # Extract relevant fields for hashing
        hash_data = {
            "source_ip": attack_data.get("source_ip"),
            "target_port": attack_data.get("target_port"),
            "attack_type": attack_data.get("attack_type"),
            "timestamp": attack_data.get("timestamp"),
            "payload_hash": hashlib.sha256(
                str(attack_data.get("raw_payload", "")).encode()
            ).hexdigest()
        }
        
        # Create deterministic hash
        data_string = json.dumps(hash_data, sort_keys=True)
        return hashlib.sha256(data_string.encode()).hexdigest()

class SecureHoneyBlockchain:
    """Main blockchain implementation for SecureHoney"""
    
    def __init__(self):
        self.chain: List[Block] = []
        self.pending_transactions: List[Transaction] = []
        self.mining_reward = 1.0
        self.difficulty = 4  # Number of leading zeros required
        self.block_time = 600  # 10 minutes target block time
        
        # Cryptographic keys
        self.private_key = None
        self.public_key = None
        
        # Consensus mechanism
        self.consensus = BlockchainConsensus()
        
        # Network peers
        self.peers = set()
        self.sync_in_progress = False
        
        # Performance metrics
        self.metrics = {
            "blocks_mined": 0,
            "transactions_processed": 0,
            "consensus_validations": 0,
            "chain_integrity_checks": 0,
            "last_block_time": None
        }
    
    async def initialize(self):
        """Initialize blockchain with genesis block"""
        try:
            # Generate cryptographic keys
            await self._generate_keys()
            
            # Load existing chain or create genesis
            await self._load_or_create_chain()
            
            # Initialize consensus validators
            await self._initialize_validators()
            
            # Start background processes
            asyncio.create_task(self._mining_process())
            asyncio.create_task(self._sync_process())
            asyncio.create_task(self._integrity_monitor())
            
            logger.info("blockchain_initialized", 
                       blocks=len(self.chain),
                       pending_transactions=len(self.pending_transactions))
                       
        except Exception as e:
            logger.error("blockchain_init_failed", error=str(e))
    
    async def add_attack_transaction(self, attack_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add attack data as blockchain transaction"""
        try:
            # Validate attack through consensus
            consensus_result = await self.consensus.validate_attack(attack_data)
            
            if not consensus_result.get("validated", False):
                return {
                    "success": False,
                    "reason": "Consensus validation failed",
                    "consensus_result": consensus_result
                }
            
            # Create transaction
            transaction = Transaction(
                id=self._generate_transaction_id(),
                timestamp=time.time(),
                attack_id=attack_data.get("id", ""),
                source_ip=attack_data.get("source_ip", ""),
                attack_type=attack_data.get("attack_type", ""),
                severity=attack_data.get("severity", ""),
                data_hash=self.consensus._hash_attack_data(attack_data),
                validator_signature=await self._sign_data(attack_data),
                consensus_score=consensus_result.get("consensus_score", 0.0),
                metadata={
                    "target_port": attack_data.get("target_port"),
                    "payload_size": attack_data.get("payload_size"),
                    "location": attack_data.get("location", {}),
                    "ml_analysis": attack_data.get("ml_analysis", {}),
                    "threat_intelligence": attack_data.get("threat_intelligence", {})
                }
            )
            
            # Add to pending transactions
            self.pending_transactions.append(transaction)
            
            # Cache transaction
            await self._cache_transaction(transaction)
            
            # Update metrics
            self.metrics["transactions_processed"] += 1
            
            logger.info("attack_transaction_added", 
                       transaction_id=transaction.id,
                       attack_id=attack_data.get("id"),
                       consensus_score=consensus_result.get("consensus_score"))
            
            return {
                "success": True,
                "transaction_id": transaction.id,
                "consensus_score": consensus_result.get("consensus_score"),
                "pending_transactions": len(self.pending_transactions)
            }
            
        except Exception as e:
            logger.error("add_transaction_failed", 
                        attack_id=attack_data.get("id"), 
                        error=str(e))
            return {"success": False, "error": str(e)}
    
    async def mine_block(self) -> Optional[Block]:
        """Mine a new block with pending transactions"""
        try:
            if not self.pending_transactions:
                return None
            
            # Get transactions for this block
            transactions = self.pending_transactions[:100]  # Max 100 transactions per block
            
            # Create new block
            previous_block = self.chain[-1] if self.chain else None
            previous_hash = previous_block.hash if previous_block else "0" * 64
            
            block = Block(
                index=len(self.chain),
                timestamp=time.time(),
                transactions=transactions,
                previous_hash=previous_hash,
                merkle_root=self._calculate_merkle_root(transactions),
                nonce=0,
                hash="",
                validator=config.VALIDATOR_ID or "primary",
                consensus_signatures=[]
            )
            
            # Proof of work mining
            start_time = time.time()
            block.hash, block.nonce = await self._mine_proof_of_work(block)
            mining_time = time.time() - start_time
            
            # Get consensus signatures from other validators
            block.consensus_signatures = await self._get_consensus_signatures(block)
            
            # Validate block
            if await self._validate_block(block):
                # Add to chain
                self.chain.append(block)
                
                # Remove mined transactions from pending
                self.pending_transactions = self.pending_transactions[len(transactions):]
                
                # Update metrics
                self.metrics["blocks_mined"] += 1
                self.metrics["last_block_time"] = datetime.utcnow().isoformat()
                
                # Broadcast to network
                await self._broadcast_block(block)
                
                # Cache block
                await self._cache_block(block)
                
                logger.info("block_mined", 
                           block_index=block.index,
                           transactions=len(block.transactions),
                           mining_time=mining_time,
                           hash=block.hash[:16])
                
                return block
            else:
                logger.error("block_validation_failed", block_index=block.index)
                return None
                
        except Exception as e:
            logger.error("block_mining_failed", error=str(e))
            return None
    
    async def verify_attack_integrity(self, attack_id: str) -> Dict[str, Any]:
        """Verify attack data integrity using blockchain"""
        try:
            # Find transaction in blockchain
            transaction = await self._find_transaction(attack_id)
            
            if not transaction:
                return {
                    "verified": False,
                    "reason": "Transaction not found in blockchain"
                }
            
            # Verify transaction signature
            signature_valid = await self._verify_signature(transaction)
            
            # Verify block containing transaction
            block = await self._find_block_containing_transaction(transaction.id)
            block_valid = await self._validate_block(block) if block else False
            
            # Verify chain integrity up to this block
            chain_valid = await self._verify_chain_integrity(block.index if block else 0)
            
            verification_result = {
                "verified": signature_valid and block_valid and chain_valid,
                "transaction_id": transaction.id,
                "block_index": block.index if block else None,
                "signature_valid": signature_valid,
                "block_valid": block_valid,
                "chain_valid": chain_valid,
                "consensus_score": transaction.consensus_score,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info("attack_integrity_verified", 
                       attack_id=attack_id,
                       verified=verification_result["verified"])
            
            return verification_result
            
        except Exception as e:
            logger.error("integrity_verification_failed", 
                        attack_id=attack_id, 
                        error=str(e))
            return {"verified": False, "error": str(e)}
    
    async def get_blockchain_stats(self) -> Dict[str, Any]:
        """Get comprehensive blockchain statistics"""
        try:
            # Calculate chain statistics
            total_transactions = sum(len(block.transactions) for block in self.chain)
            
            # Get recent activity
            recent_blocks = self.chain[-10:] if len(self.chain) >= 10 else self.chain
            recent_activity = []
            
            for block in recent_blocks:
                recent_activity.append({
                    "block_index": block.index,
                    "timestamp": datetime.fromtimestamp(block.timestamp).isoformat(),
                    "transactions": len(block.transactions),
                    "hash": block.hash[:16] + "...",
                    "validator": block.validator
                })
            
            # Calculate network health
            network_health = await self._calculate_network_health()
            
            stats = {
                "chain_length": len(self.chain),
                "total_transactions": total_transactions,
                "pending_transactions": len(self.pending_transactions),
                "network_peers": len(self.peers),
                "consensus_threshold": self.consensus.consensus_threshold,
                "mining_difficulty": self.difficulty,
                "average_block_time": self._calculate_average_block_time(),
                "network_health": network_health,
                "recent_activity": recent_activity,
                "metrics": self.metrics,
                "last_updated": datetime.utcnow().isoformat()
            }
            
            return stats
            
        except Exception as e:
            logger.error("blockchain_stats_failed", error=str(e))
            return {}
    
    async def _mine_proof_of_work(self, block: Block) -> Tuple[str, int]:
        """Mine block using proof of work algorithm"""
        target = "0" * self.difficulty
        nonce = 0
        
        while True:
            # Create block hash candidate
            block_string = json.dumps({
                "index": block.index,
                "timestamp": block.timestamp,
                "transactions": [asdict(tx) for tx in block.transactions],
                "previous_hash": block.previous_hash,
                "merkle_root": block.merkle_root,
                "nonce": nonce
            }, sort_keys=True)
            
            block_hash = hashlib.sha256(block_string.encode()).hexdigest()
            
            # Check if hash meets difficulty requirement
            if block_hash.startswith(target):
                return block_hash, nonce
            
            nonce += 1
            
            # Prevent infinite loop and allow other tasks
            if nonce % 10000 == 0:
                await asyncio.sleep(0.001)
    
    def _calculate_merkle_root(self, transactions: List[Transaction]) -> str:
        """Calculate Merkle root of transactions"""
        if not transactions:
            return hashlib.sha256(b"").hexdigest()
        
        # Create leaf hashes
        hashes = []
        for tx in transactions:
            tx_string = json.dumps(asdict(tx), sort_keys=True)
            hashes.append(hashlib.sha256(tx_string.encode()).hexdigest())
        
        # Build Merkle tree
        while len(hashes) > 1:
            new_hashes = []
            for i in range(0, len(hashes), 2):
                left = hashes[i]
                right = hashes[i + 1] if i + 1 < len(hashes) else left
                combined = hashlib.sha256((left + right).encode()).hexdigest()
                new_hashes.append(combined)
            hashes = new_hashes
        
        return hashes[0]
    
    async def _validate_block(self, block: Block) -> bool:
        """Validate block integrity and consensus"""
        try:
            # Validate block hash
            if not await self._validate_block_hash(block):
                return False
            
            # Validate previous hash
            if block.index > 0:
                previous_block = self.chain[block.index - 1]
                if block.previous_hash != previous_block.hash:
                    return False
            
            # Validate Merkle root
            calculated_merkle = self._calculate_merkle_root(block.transactions)
            if block.merkle_root != calculated_merkle:
                return False
            
            # Validate transactions
            for transaction in block.transactions:
                if not await self._validate_transaction(transaction):
                    return False
            
            # Validate consensus signatures
            if not await self._validate_consensus_signatures(block):
                return False
            
            return True
            
        except Exception as e:
            logger.error("block_validation_error", error=str(e))
            return False
    
    async def _generate_keys(self):
        """Generate RSA key pair for signing"""
        try:
            self.private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )
            self.public_key = self.private_key.public_key()
            
            logger.info("cryptographic_keys_generated")
            
        except Exception as e:
            logger.error("key_generation_failed", error=str(e))
    
    async def _sign_data(self, data: Dict[str, Any]) -> str:
        """Sign data with private key"""
        try:
            if not self.private_key:
                return ""
            
            data_string = json.dumps(data, sort_keys=True)
            signature = self.private_key.sign(
                data_string.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            return base64.b64encode(signature).decode()
            
        except Exception as e:
            logger.error("data_signing_failed", error=str(e))
            return ""
    
    def _generate_transaction_id(self) -> str:
        """Generate unique transaction ID"""
        return hashlib.sha256(
            f"{time.time()}{len(self.pending_transactions)}".encode()
        ).hexdigest()[:16]
    
    # Additional helper methods for blockchain operations...
    # (Implementation details for network sync, caching, etc.)

# Global blockchain instance
blockchain = SecureHoneyBlockchain()

# Convenience functions
async def add_attack_to_blockchain(attack_data: Dict[str, Any]) -> Dict[str, Any]:
    """Add attack to blockchain with consensus validation"""
    return await blockchain.add_attack_transaction(attack_data)

async def verify_attack_blockchain_integrity(attack_id: str) -> Dict[str, Any]:
    """Verify attack integrity using blockchain"""
    return await blockchain.verify_attack_integrity(attack_id)

async def get_blockchain_statistics() -> Dict[str, Any]:
    """Get blockchain statistics"""
    return await blockchain.get_blockchain_stats()

async def mine_pending_transactions() -> Optional[Block]:
    """Mine pending transactions into a new block"""
    return await blockchain.mine_block()
