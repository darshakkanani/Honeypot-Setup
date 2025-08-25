#!/usr/bin/env python3
"""
Smart Contract Deployment Script for HoneyPort
Deploys and tests the Solidity smart contract integration
"""

import asyncio
import sys
import os
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from blockchain.web3_manager import Web3Manager
from blockchain.log_manager import BlockchainLogManager

console = Console()

def load_config():
    """Load configuration"""
    try:
        with open('config.yaml', 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        console.print(f"[red]Error loading config: {e}[/red]")
        return {}

async def test_smart_contract_deployment():
    """Test smart contract deployment and functionality"""
    
    console.print(Panel.fit(
        "[bold blue]HoneyPort Smart Contract Deployment & Testing[/bold blue]",
        border_style="blue"
    ))
    
    # Load configuration
    config = load_config()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        # Step 1: Initialize Web3 Manager
        task1 = progress.add_task("Initializing Web3 Manager...", total=None)
        try:
            web3_manager = Web3Manager(config)
            progress.update(task1, description="✅ Web3 Manager initialized")
            await asyncio.sleep(1)
        except Exception as e:
            progress.update(task1, description=f"❌ Web3 initialization failed: {e}")
            return False
        
        # Step 2: Deploy Smart Contract
        task2 = progress.add_task("Deploying smart contract...", total=None)
        try:
            if web3_manager.deploy_contract():
                progress.update(task2, description="✅ Smart contract deployed successfully")
            else:
                progress.update(task2, description="❌ Smart contract deployment failed")
                return False
            await asyncio.sleep(1)
        except Exception as e:
            progress.update(task2, description=f"❌ Deployment error: {e}")
            return False
        
        # Step 3: Test Contract Functionality
        task3 = progress.add_task("Testing contract functionality...", total=None)
        try:
            # Test logging an attack
            test_attack = {
                'source_ip': '192.168.1.100',
                'attack_type': 'sql_injection',
                'severity': 'high',
                'payload': "'; DROP TABLE users; --",
                'ai_behavior': 'aggressive'
            }
            
            log_hash = web3_manager.log_attack(test_attack)
            if log_hash:
                progress.update(task3, description="✅ Attack logging test passed")
            else:
                progress.update(task3, description="❌ Attack logging test failed")
                return False
            await asyncio.sleep(1)
        except Exception as e:
            progress.update(task3, description=f"❌ Testing error: {e}")
            return False
        
        # Step 4: Test Verification
        task4 = progress.add_task("Testing log verification...", total=None)
        try:
            if log_hash and web3_manager.verify_log(log_hash):
                progress.update(task4, description="✅ Log verification test passed")
            else:
                progress.update(task4, description="❌ Log verification test failed")
                return False
            await asyncio.sleep(1)
        except Exception as e:
            progress.update(task4, description=f"❌ Verification error: {e}")
            return False
        
        # Step 5: Test Blockchain Verification
        task5 = progress.add_task("Testing blockchain verification...", total=None)
        try:
            if web3_manager.verify_blockchain():
                progress.update(task5, description="✅ Blockchain verification test passed")
            else:
                progress.update(task5, description="❌ Blockchain verification test failed")
                return False
            await asyncio.sleep(1)
        except Exception as e:
            progress.update(task5, description=f"❌ Blockchain verification error: {e}")
            return False
    
    # Display contract statistics
    console.print("\n")
    stats = web3_manager.get_contract_stats()
    
    stats_table = Table(title="Smart Contract Statistics")
    stats_table.add_column("Metric", style="cyan")
    stats_table.add_column("Value", style="green")
    
    stats_table.add_row("Contract Address", stats.get('contract_address', 'N/A'))
    stats_table.add_row("Total Logs", str(stats.get('total_logs', 0)))
    stats_table.add_row("Total Blocks", str(stats.get('total_blocks', 0)))
    stats_table.add_row("Verified Logs", str(stats.get('verified_logs', 0)))
    stats_table.add_row("Contract Active", str(stats.get('is_active', False)))
    stats_table.add_row("Account Balance", f"{web3_manager.get_balance():.4f} ETH")
    
    console.print(stats_table)
    
    return True

async def test_log_manager_integration():
    """Test the integrated log manager with smart contracts"""
    
    console.print(Panel.fit(
        "[bold green]Testing Log Manager Integration[/bold green]",
        border_style="green"
    ))
    
    config = load_config()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        # Initialize Log Manager
        task1 = progress.add_task("Initializing Log Manager...", total=None)
        try:
            log_manager = BlockchainLogManager(config)
            progress.update(task1, description="✅ Log Manager initialized")
            await asyncio.sleep(1)
        except Exception as e:
            progress.update(task1, description=f"❌ Log Manager initialization failed: {e}")
            return False
        
        # Test attack logging
        task2 = progress.add_task("Testing attack logging...", total=None)
        try:
            test_attacks = [
                {
                    'source_ip': '10.0.0.1',
                    'attack_type': 'xss',
                    'severity': 'medium',
                    'payload': '<script>alert("XSS")</script>',
                    'user_agent': 'Mozilla/5.0 (Malicious Browser)',
                },
                {
                    'source_ip': '172.16.0.1',
                    'attack_type': 'brute_force',
                    'severity': 'high',
                    'payload': 'admin:password123',
                    'user_agent': 'curl/7.68.0',
                },
                {
                    'source_ip': '192.168.1.50',
                    'attack_type': 'directory_traversal',
                    'severity': 'high',
                    'payload': '../../../etc/passwd',
                    'user_agent': 'Wget/1.20.3',
                }
            ]
            
            logged_attacks = []
            for attack in test_attacks:
                log_id = log_manager.log_attack(attack)
                logged_attacks.append(log_id)
            
            progress.update(task2, description=f"✅ Logged {len(logged_attacks)} attacks")
            await asyncio.sleep(1)
        except Exception as e:
            progress.update(task2, description=f"❌ Attack logging failed: {e}")
            return False
        
        # Test statistics
        task3 = progress.add_task("Testing statistics retrieval...", total=None)
        try:
            stats = log_manager.get_attack_statistics()
            progress.update(task3, description="✅ Statistics retrieved successfully")
            await asyncio.sleep(1)
        except Exception as e:
            progress.update(task3, description=f"❌ Statistics retrieval failed: {e}")
            return False
        
        # Test blockchain status
        task4 = progress.add_task("Testing blockchain status...", total=None)
        try:
            status = log_manager.get_blockchain_status()
            progress.update(task4, description="✅ Blockchain status retrieved")
            await asyncio.sleep(1)
        except Exception as e:
            progress.update(task4, description=f"❌ Blockchain status failed: {e}")
            return False
    
    # Display comprehensive statistics
    console.print("\n")
    
    # Attack Statistics
    attack_stats_table = Table(title="Attack Statistics")
    attack_stats_table.add_column("Metric", style="cyan")
    attack_stats_table.add_column("Value", style="green")
    
    attack_stats_table.add_row("Total Attacks", str(stats.get('total_attacks', 0)))
    attack_stats_table.add_row("Unique IPs", str(len(stats.get('unique_source_ips', []))))
    attack_stats_table.add_row("Verified Logs", str(stats.get('verified_logs', 0)))
    attack_stats_table.add_row("Total Blocks", str(stats.get('total_blocks', 0)))
    
    console.print(attack_stats_table)
    
    # Blockchain Status
    blockchain_status_table = Table(title="Blockchain Status")
    blockchain_status_table.add_column("Component", style="cyan")
    blockchain_status_table.add_column("Status", style="green")
    
    blockchain_status_table.add_row("Blockchain Enabled", str(status.get('blockchain_enabled', False)))
    blockchain_status_table.add_row("Solidity Enabled", str(status.get('solidity_enabled', False)))
    blockchain_status_table.add_row("Smart Contract Connected", str(status.get('smart_contract_connected', False)))
    blockchain_status_table.add_row("Web3 Connected", str(status.get('web3_connected', False)))
    blockchain_status_table.add_row("Python Blockchain Active", str(status.get('python_blockchain_active', False)))
    
    console.print(blockchain_status_table)
    
    return True

async def main():
    """Main deployment and testing function"""
    
    console.print("[bold blue]🚀 HoneyPort Smart Contract Integration Testing[/bold blue]\n")
    
    # Test 1: Smart Contract Deployment
    console.print("[bold yellow]Phase 1: Smart Contract Deployment[/bold yellow]")
    success1 = await test_smart_contract_deployment()
    
    if not success1:
        console.print("[red]❌ Smart contract deployment failed. Exiting.[/red]")
        return
    
    console.print("\n" + "="*60 + "\n")
    
    # Test 2: Log Manager Integration
    console.print("[bold yellow]Phase 2: Log Manager Integration[/bold yellow]")
    success2 = await test_log_manager_integration()
    
    if not success2:
        console.print("[red]❌ Log manager integration failed.[/red]")
        return
    
    console.print("\n" + "="*60 + "\n")
    
    # Final Summary
    console.print(Panel.fit(
        "[bold green]✅ All Tests Passed! Smart Contract Integration Complete[/bold green]\n\n"
        "[yellow]Next Steps:[/yellow]\n"
        "1. Start the HoneyPort engine: python main.py\n"
        "2. Start the dashboard: python run_dashboard.py\n"
        "3. Run attack tests: python test_attacks.py\n"
        "4. Monitor smart contract logs in the dashboard",
        title="🎉 Success!",
        border_style="green"
    ))

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Deployment interrupted by user.[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Deployment failed with error: {e}[/red]")
