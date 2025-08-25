#!/usr/bin/env python3
"""
HoneyPort Attack Testing Script
Perfect for demonstrating AI behavior and blockchain logging
"""

import requests
import time
import threading
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel

console = Console()

class AttackTester:
    """Automated attack testing for demo purposes"""
    
    def __init__(self, target_url="http://localhost:8888"):
        self.target_url = target_url
        self.attack_count = 0
        self.results = []
    
    def run_sql_injection_attacks(self):
        """Run SQL injection attacks"""
        console.print("[bold red]🗄️ Running SQL Injection Attacks...[/bold red]")
        
        sql_payloads = [
            "/admin?id=1' OR 1=1--",
            "/login?user=admin' UNION SELECT * FROM users--",
            "/search?q='; DROP TABLE users; --",
            "/products?id=1' AND 1=1--",
            "/user?id=1' OR 'a'='a"
        ]
        
        for payload in sql_payloads:
            try:
                response = requests.get(f"{self.target_url}{payload}", timeout=5)
                self.attack_count += 1
                self.results.append({
                    "type": "SQL Injection",
                    "payload": payload,
                    "status": response.status_code,
                    "success": "Query executed" in response.text
                })
                time.sleep(1)
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
    
    def run_xss_attacks(self):
        """Run XSS attacks"""
        console.print("[bold yellow]🔥 Running XSS Attacks...[/bold yellow]")
        
        xss_payloads = [
            "/search?q=<script>alert('XSS')</script>",
            "/comment?text=<img src=x onerror=alert('XSS')>",
            "/profile?name=<svg onload=alert('XSS')>",
            "/feedback?msg=javascript:alert('XSS')",
            "/search?q=<iframe src=javascript:alert('XSS')></iframe>"
        ]
        
        for payload in xss_payloads:
            try:
                response = requests.get(f"{self.target_url}{payload}", timeout=5)
                self.attack_count += 1
                self.results.append({
                    "type": "XSS",
                    "payload": payload,
                    "status": response.status_code,
                    "success": "<script>" in response.text or "alert" in response.text
                })
                time.sleep(1)
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
    
    def run_brute_force_attacks(self):
        """Run brute force attacks"""
        console.print("[bold blue]🔨 Running Brute Force Attacks...[/bold blue]")
        
        credentials = [
            ("admin", "password"),
            ("admin", "123456"),
            ("admin", "admin"),
            ("root", "root"),
            ("admin", "password123")
        ]
        
        for username, password in credentials:
            try:
                data = {"username": username, "password": password}
                response = requests.post(f"{self.target_url}/wp-admin", data=data, timeout=5)
                self.attack_count += 1
                self.results.append({
                    "type": "Brute Force",
                    "payload": f"{username}:{password}",
                    "status": response.status_code,
                    "success": "Dashboard" in response.text or "Welcome" in response.text
                })
                time.sleep(1)
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
    
    def run_directory_traversal_attacks(self):
        """Run directory traversal attacks"""
        console.print("[bold magenta]📁 Running Directory Traversal Attacks...[/bold magenta]")
        
        traversal_payloads = [
            "/files?path=../../../etc/passwd",
            "/download?file=..\\..\\..\\windows\\system32\\config\\sam",
            "/view?doc=../../../../etc/shadow",
            "/read?file=../../../etc/hosts",
            "/get?path=..%2f..%2f..%2fetc%2fpasswd"
        ]
        
        for payload in traversal_payloads:
            try:
                response = requests.get(f"{self.target_url}{payload}", timeout=5)
                self.attack_count += 1
                self.results.append({
                    "type": "Directory Traversal",
                    "payload": payload,
                    "status": response.status_code,
                    "success": "root:" in response.text or "etc" in response.text
                })
                time.sleep(1)
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
    
    def display_results(self):
        """Display attack results"""
        table = Table(title="🍯 HoneyPort Attack Test Results")
        table.add_column("Attack Type", style="cyan")
        table.add_column("Payload", style="yellow")
        table.add_column("Status", style="green")
        table.add_column("Honeypot Response", style="magenta")
        
        for result in self.results:
            status_color = "green" if result["status"] == 200 else "red"
            response_text = "✅ Engaged" if result["success"] else "🛡️ Blocked"
            
            table.add_row(
                result["type"],
                result["payload"][:50] + "..." if len(result["payload"]) > 50 else result["payload"],
                f"[{status_color}]{result['status']}[/{status_color}]",
                response_text
            )
        
        console.print(table)
        
        # Summary
        total_attacks = len(self.results)
        successful_engagements = sum(1 for r in self.results if r["success"])
        
        summary = Panel(
            f"[bold green]Total Attacks: {total_attacks}[/bold green]\n"
            f"[bold yellow]Honeypot Engagements: {successful_engagements}[/bold yellow]\n"
            f"[bold blue]Engagement Rate: {(successful_engagements/total_attacks)*100:.1f}%[/bold blue]",
            title="📊 Attack Summary"
        )
        console.print(summary)

def run_continuous_attacks():
    """Run attacks continuously for demo"""
    tester = AttackTester()
    
    console.print("[bold green]🚀 Starting Continuous Attack Demo...[/bold green]")
    console.print("[bold cyan]Target: http://localhost:8888[/bold cyan]")
    console.print("[bold yellow]Press Ctrl+C to stop[/bold yellow]\n")
    
    try:
        while True:
            # Run different types of attacks
            tester.run_sql_injection_attacks()
            time.sleep(2)
            
            tester.run_xss_attacks()
            time.sleep(2)
            
            tester.run_brute_force_attacks()
            time.sleep(2)
            
            tester.run_directory_traversal_attacks()
            time.sleep(5)
            
            # Display results
            console.clear()
            tester.display_results()
            
            console.print("\n[bold green]🔄 Running next attack cycle in 10 seconds...[/bold green]")
            time.sleep(10)
            
    except KeyboardInterrupt:
        console.print("\n[bold red]🛑 Attack demo stopped[/bold red]")
        tester.display_results()

def run_single_attack_demo():
    """Run a single round of attacks"""
    tester = AttackTester()
    
    console.print("[bold green]🎯 Running Single Attack Demo...[/bold green]\n")
    
    # Run all attack types
    tester.run_sql_injection_attacks()
    tester.run_xss_attacks()
    tester.run_brute_force_attacks()
    tester.run_directory_traversal_attacks()
    
    # Display results
    console.print("\n")
    tester.display_results()

def main():
    """Main function"""
    console.print(Panel(
        "[bold cyan]🍯 HoneyPort Attack Tester[/bold cyan]\n"
        "[yellow]Perfect for demonstrating AI behavior adaptation and blockchain logging[/yellow]",
        title="HoneyPort Demo"
    ))
    
    choice = console.input("\n[bold green]Choose mode:[/bold green]\n"
                          "[1] Single attack demo\n"
                          "[2] Continuous attacks\n"
                          "Enter choice (1-2): ")
    
    if choice == "1":
        run_single_attack_demo()
    elif choice == "2":
        run_continuous_attacks()
    else:
        console.print("[red]Invalid choice[/red]")

if __name__ == "__main__":
    main()
