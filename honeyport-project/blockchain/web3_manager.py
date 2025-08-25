#!/usr/bin/env python3
"""
Web3 Manager for HoneyPort Solidity Integration
Handles smart contract deployment and interaction
"""

import json
import os
from typing import Dict, Any, List, Optional
from web3 import Web3
from eth_account import Account
from solcx import compile_source, install_solc
import time

class Web3Manager:
    """Manages Web3 interactions with HoneyPort smart contract"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.web3 = None
        self.contract = None
        self.account = None
        self.contract_address = None
        
        # Install Solidity compiler
        try:
            install_solc('0.8.19')
        except:
            pass  # Already installed
        
        self._setup_web3()
        self._setup_account()
    
    def _setup_web3(self):
        """Setup Web3 connection"""
        # Use Ganache or local blockchain
        rpc_url = self.config.get('blockchain', {}).get('rpc_url', 'http://127.0.0.1:8545')
        
        try:
            self.web3 = Web3(Web3.HTTPProvider(rpc_url))
            if self.web3.is_connected():
                print(f"✅ Connected to blockchain at {rpc_url}")
            else:
                print("⚠️ Starting local blockchain simulation...")
                self._start_local_blockchain()
        except Exception as e:
            print(f"⚠️ Blockchain connection failed, using simulation: {e}")
            self._start_local_blockchain()
    
    def _start_local_blockchain(self):
        """Start local blockchain simulation"""
        from web3 import Web3
        from web3.providers.eth_tester import EthereumTesterProvider
        from eth_tester import EthereumTester
        
        # Create local test blockchain
        self.web3 = Web3(EthereumTesterProvider(EthereumTester()))
        print("🔗 Local blockchain simulation started")
    
    def _setup_account(self):
        """Setup blockchain account"""
        # Use existing account or create new one
        private_key = self.config.get('blockchain', {}).get('private_key')
        
        if not private_key:
            # Create new account
            self.account = Account.create()
            print(f"🔑 Created new account: {self.account.address}")
        else:
            self.account = Account.from_key(private_key)
            print(f"🔑 Using existing account: {self.account.address}")
        
        # Fund account if using test network
        if hasattr(self.web3.eth, 'accounts') and len(self.web3.eth.accounts) > 0:
            try:
                # Transfer some ETH for gas
                self.web3.eth.send_transaction({
                    'from': self.web3.eth.accounts[0],
                    'to': self.account.address,
                    'value': self.web3.to_wei(10, 'ether')
                })
                print("💰 Account funded with test ETH")
            except:
                pass
    
    def deploy_contract(self) -> bool:
        """Deploy HoneyPort smart contract"""
        try:
            # Read and compile contract
            contract_path = os.path.join(os.path.dirname(__file__), 'contracts', 'HoneyPortLogger.sol')
            
            with open(contract_path, 'r') as f:
                contract_source = f.read()
            
            # Compile contract
            compiled_sol = compile_source(contract_source)
            contract_interface = compiled_sol['<stdin>:HoneyPortLogger']
            
            # Deploy contract
            contract = self.web3.eth.contract(
                abi=contract_interface['abi'],
                bytecode=contract_interface['bin']
            )
            
            # Build transaction
            transaction = contract.constructor().build_transaction({
                'from': self.account.address,
                'gas': 3000000,
                'gasPrice': self.web3.to_wei('20', 'gwei'),
                'nonce': self.web3.eth.get_transaction_count(self.account.address)
            })
            
            # Sign and send transaction
            signed_txn = self.web3.eth.account.sign_transaction(transaction, self.account.key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # Wait for deployment
            tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            self.contract_address = tx_receipt.contractAddress
            self.contract = self.web3.eth.contract(
                address=self.contract_address,
                abi=contract_interface['abi']
            )
            
            print(f"🚀 Smart contract deployed at: {self.contract_address}")
            
            # Save contract info
            self._save_contract_info(contract_interface['abi'])
            
            return True
            
        except Exception as e:
            print(f"❌ Contract deployment failed: {e}")
            return False
    
    def _save_contract_info(self, abi: List[Dict]):
        """Save contract ABI and address"""
        contract_info = {
            'address': self.contract_address,
            'abi': abi,
            'deployer': self.account.address
        }
        
        info_path = os.path.join(os.path.dirname(__file__), 'contract_info.json')
        with open(info_path, 'w') as f:
            json.dump(contract_info, f, indent=2)
    
    def load_contract(self) -> bool:
        """Load existing contract"""
        try:
            info_path = os.path.join(os.path.dirname(__file__), 'contract_info.json')
            
            if not os.path.exists(info_path):
                return False
            
            with open(info_path, 'r') as f:
                contract_info = json.load(f)
            
            self.contract_address = contract_info['address']
            self.contract = self.web3.eth.contract(
                address=self.contract_address,
                abi=contract_info['abi']
            )
            
            print(f"📄 Loaded contract at: {self.contract_address}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to load contract: {e}")
            return False
    
    def log_attack(self, attack_data: Dict[str, Any]) -> Optional[str]:
        """Log attack to smart contract"""
        if not self.contract:
            return None
        
        try:
            # Prepare transaction
            function = self.contract.functions.logAttack(
                attack_data.get('source_ip', 'unknown'),
                attack_data.get('attack_type', 'unknown'),
                attack_data.get('severity', 'low'),
                str(attack_data.get('payload', ''))[:500],  # Limit payload size
                attack_data.get('ai_behavior', 'realistic')
            )
            
            transaction = function.build_transaction({
                'from': self.account.address,
                'gas': 500000,
                'gasPrice': self.web3.to_wei('20', 'gwei'),
                'nonce': self.web3.eth.get_transaction_count(self.account.address)
            })
            
            # Sign and send
            signed_txn = self.web3.eth.account.sign_transaction(transaction, self.account.key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # Wait for confirmation
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            # Extract log hash from events
            log_hash = None
            for log in receipt.logs:
                try:
                    decoded = self.contract.events.AttackLogged().processLog(log)
                    log_hash = decoded['args']['logHash'].hex()
                    break
                except:
                    continue
            
            print(f"📝 Attack logged to blockchain: {log_hash[:16]}...")
            return log_hash
            
        except Exception as e:
            print(f"❌ Failed to log attack: {e}")
            return None
    
    def verify_log(self, log_hash: str) -> bool:
        """Verify log integrity"""
        if not self.contract:
            return False
        
        try:
            # Convert hex string to bytes32
            log_hash_bytes = bytes.fromhex(log_hash.replace('0x', ''))
            
            # Call verify function
            function = self.contract.functions.verifyLog(log_hash_bytes)
            
            transaction = function.build_transaction({
                'from': self.account.address,
                'gas': 200000,
                'gasPrice': self.web3.to_wei('20', 'gwei'),
                'nonce': self.web3.eth.get_transaction_count(self.account.address)
            })
            
            signed_txn = self.web3.eth.account.sign_transaction(transaction, self.account.key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            return receipt.status == 1
            
        except Exception as e:
            print(f"❌ Log verification failed: {e}")
            return False
    
    def verify_blockchain(self) -> bool:
        """Verify entire blockchain integrity"""
        if not self.contract:
            return False
        
        try:
            result = self.contract.functions.verifyBlockchain().call()
            return result
        except Exception as e:
            print(f"❌ Blockchain verification failed: {e}")
            return False
    
    def get_contract_stats(self) -> Dict[str, Any]:
        """Get contract statistics"""
        if not self.contract:
            return {}
        
        try:
            stats = self.contract.functions.getContractStats().call()
            
            return {
                'total_logs': stats[0],
                'total_blocks': stats[1],
                'verified_logs': stats[2],
                'is_active': stats[3],
                'contract_address': self.contract_address,
                'deployer_address': self.account.address
            }
        except Exception as e:
            print(f"❌ Failed to get stats: {e}")
            return {}
    
    def get_recent_logs(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent attack logs"""
        if not self.contract:
            return []
        
        try:
            log_hashes = self.contract.functions.getRecentLogs(count).call()
            
            logs = []
            for log_hash in log_hashes:
                try:
                    log_data = self.contract.functions.getAttackLog(log_hash).call()
                    
                    logs.append({
                        'log_hash': log_hash.hex(),
                        'source_ip': log_data[0],
                        'attack_type': log_data[1],
                        'severity': log_data[2],
                        'payload': log_data[3],
                        'ai_decision': log_data[4],
                        'timestamp': log_data[5],
                        'logger': log_data[6],
                        'verified': log_data[7]
                    })
                except:
                    continue
            
            return logs
            
        except Exception as e:
            print(f"❌ Failed to get recent logs: {e}")
            return []
    
    def is_connected(self) -> bool:
        """Check if connected to blockchain"""
        return self.web3 is not None and self.web3.is_connected()
    
    def get_balance(self) -> float:
        """Get account balance in ETH"""
        if not self.web3 or not self.account:
            return 0.0
        
        try:
            balance_wei = self.web3.eth.get_balance(self.account.address)
            return self.web3.from_wei(balance_wei, 'ether')
        except:
            return 0.0
