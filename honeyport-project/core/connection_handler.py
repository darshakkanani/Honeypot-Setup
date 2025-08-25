#!/usr/bin/env python3
"""
Connection Handler for HoneyPort
Generates dynamic responses based on AI behavior analysis
"""

import random
import json
from typing import Dict, Any
from .ai_behavior import AIBehaviorEngine

class ConnectionHandler:
    """Handles connections and generates AI-powered responses"""
    
    def __init__(self, config: Dict[str, Any], ai_engine: AIBehaviorEngine):
        self.config = config
        self.ai_engine = ai_engine
        self.fake_services = config.get('attacker_site', {}).get('fake_services', [])
        
    async def generate_response(self, request_data: Dict[str, Any], 
                              response_params: Dict[str, Any],
                              anomaly_result: Dict[str, Any]) -> str:
        """Generate AI-powered response"""
        
        url = request_data.get('url', '/')
        attack_type = request_data.get('attack_type', 'reconnaissance')
        behavior = response_params.get('behavior', 'realistic')
        
        # Route to appropriate handler
        if '/admin' in url or '/wp-admin' in url:
            return self._generate_wordpress_response(request_data, response_params)
        elif '/phpmyadmin' in url:
            return self._generate_phpmyadmin_response(request_data, response_params)
        elif '/cpanel' in url:
            return self._generate_cpanel_response(request_data, response_params)
        elif attack_type == 'sql_injection':
            return self._generate_sql_response(request_data, response_params)
        elif attack_type == 'xss':
            return self._generate_xss_response(request_data, response_params)
        else:
            return self._generate_default_response(request_data, response_params)
    
    def _generate_wordpress_response(self, request_data: Dict[str, Any], 
                                   response_params: Dict[str, Any]) -> str:
        """Generate WordPress admin response"""
        
        if response_params.get('should_fake_success'):
            return self._wordpress_dashboard()
        elif response_params.get('should_redirect'):
            return self._redirect_response('/wp-admin/dashboard.php')
        else:
            return self._wordpress_login_error()
    
    def _generate_phpmyadmin_response(self, request_data: Dict[str, Any],
                                    response_params: Dict[str, Any]) -> str:
        """Generate phpMyAdmin response"""
        
        if response_params.get('should_fake_success'):
            return self._phpmyadmin_dashboard()
        else:
            return self._phpmyadmin_error()
    
    def _generate_cpanel_response(self, request_data: Dict[str, Any],
                                response_params: Dict[str, Any]) -> str:
        """Generate cPanel response"""
        
        if response_params.get('should_fake_success'):
            return self._cpanel_dashboard()
        else:
            return self._cpanel_error()
    
    def _generate_sql_response(self, request_data: Dict[str, Any],
                             response_params: Dict[str, Any]) -> str:
        """Generate SQL injection response"""
        
        behavior = response_params.get('behavior', 'realistic')
        
        if behavior == 'enticing' and response_params.get('should_fake_success'):
            # Show fake SQL results to entice attacker
            return self._fake_sql_results()
        elif behavior == 'aggressive':
            # Quick error to waste attacker's time
            return self._sql_error_response()
        else:
            # Realistic database error
            return self._realistic_sql_error()
    
    def _generate_xss_response(self, request_data: Dict[str, Any],
                             response_params: Dict[str, Any]) -> str:
        """Generate XSS response"""
        
        if response_params.get('should_fake_success'):
            # Reflect the payload to make attacker think it worked
            payload = request_data.get('payload', {})
            return self._xss_success_response(payload)
        else:
            return self._xss_blocked_response()
    
    def _generate_default_response(self, request_data: Dict[str, Any],
                                 response_params: Dict[str, Any]) -> str:
        """Generate default response"""
        
        if response_params.get('should_error'):
            return self._generic_error()
        else:
            return self._generic_success()
    
    # Response templates
    def _wordpress_login_error(self) -> str:
        return """HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n
<!DOCTYPE html>
<html><head><title>WordPress Login</title></head>
<body><div class="login-error">
<strong>ERROR</strong>: Invalid username or password.
</div></body></html>"""
    
    def _wordpress_dashboard(self) -> str:
        return """HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n
<!DOCTYPE html>
<html><head><title>WordPress Dashboard</title></head>
<body><h1>Welcome to WordPress Dashboard</h1>
<p>Posts: 42 | Pages: 8 | Comments: 156</p>
<div>Recent activity logged...</div></body></html>"""
    
    def _phpmyadmin_error(self) -> str:
        return """HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n
<!DOCTYPE html>
<html><head><title>phpMyAdmin</title></head>
<body><div class="error">
Access denied for user 'root'@'localhost' (using password: YES)
</div></body></html>"""
    
    def _phpmyadmin_dashboard(self) -> str:
        return """HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n
<!DOCTYPE html>
<html><head><title>phpMyAdmin</title></head>
<body><h1>phpMyAdmin 5.2.1</h1>
<div>Server: localhost | Database: wordpress | Tables: 12</div>
<table><tr><th>Database</th><th>Tables</th></tr>
<tr><td>wordpress</td><td>12</td></tr>
<tr><td>users</td><td>3</td></tr></table></body></html>"""
    
    def _cpanel_error(self) -> str:
        return """HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n
<!DOCTYPE html>
<html><head><title>cPanel Login</title></head>
<body><div class="error">
Login Failed: Invalid credentials provided
</div></body></html>"""
    
    def _cpanel_dashboard(self) -> str:
        return """HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n
<!DOCTYPE html>
<html><head><title>cPanel Dashboard</title></head>
<body><h1>cPanel Control Panel</h1>
<div>Disk Usage: 2.1 GB / 10 GB | Bandwidth: 156 MB / 1000 MB</div>
<div>Domains: 3 | Email Accounts: 8 | Databases: 2</div></body></html>"""
    
    def _fake_sql_results(self) -> str:
        return """HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n
<!DOCTYPE html>
<html><head><title>Query Results</title></head>
<body><h2>Query executed successfully</h2>
<table border="1">
<tr><th>id</th><th>username</th><th>email</th><th>role</th></tr>
<tr><td>1</td><td>admin</td><td>admin@company.com</td><td>administrator</td></tr>
<tr><td>2</td><td>john_doe</td><td>john@company.com</td><td>editor</td></tr>
<tr><td>3</td><td>jane_smith</td><td>jane@company.com</td><td>author</td></tr>
</table><p>3 rows returned</p></body></html>"""
    
    def _sql_error_response(self) -> str:
        return """HTTP/1.1 500 Internal Server Error\r\nContent-Type: text/html\r\n\r\n
Database connection failed"""
    
    def _realistic_sql_error(self) -> str:
        return """HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n
<!DOCTYPE html>
<html><head><title>Database Error</title></head>
<body><h1>Database Error</h1>
<p>You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version</p>
</body></html>"""
    
    def _xss_success_response(self, payload: Dict[str, Any]) -> str:
        # Safely reflect payload (for honeypot purposes)
        reflected = str(payload).replace('<', '&lt;').replace('>', '&gt;')
        return f"""HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n
<!DOCTYPE html>
<html><head><title>Search Results</title></head>
<body><h1>Search Results</h1>
<p>You searched for: {reflected}</p>
<p>No results found.</p></body></html>"""
    
    def _xss_blocked_response(self) -> str:
        return """HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n
<!DOCTYPE html>
<html><head><title>Input Validation Error</title></head>
<body><h1>Invalid Input</h1>
<p>Your input contains potentially harmful content and has been blocked.</p>
</body></html>"""
    
    def _redirect_response(self, location: str) -> str:
        return f"""HTTP/1.1 302 Found\r\nLocation: {location}\r\nContent-Type: text/html\r\n\r\n
<!DOCTYPE html>
<html><head><title>Redirecting...</title></head>
<body><p>Redirecting to <a href="{location}">{location}</a></p></body></html>"""
    
    def _generic_error(self) -> str:
        errors = [
            "Internal Server Error",
            "Service Temporarily Unavailable", 
            "Database Connection Failed",
            "Access Denied",
            "File Not Found"
        ]
        error = random.choice(errors)
        return f"""HTTP/1.1 500 Internal Server Error\r\nContent-Type: text/html\r\n\r\n
<!DOCTYPE html>
<html><head><title>Error</title></head>
<body><h1>{error}</h1></body></html>"""
    
    def _generic_success(self) -> str:
        return """HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n
<!DOCTYPE html>
<html><head><title>Welcome</title></head>
<body><h1>Welcome to SecureCorpTech</h1>
<p>Enterprise Security Solutions</p></body></html>"""
