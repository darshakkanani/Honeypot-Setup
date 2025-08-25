#!/usr/bin/env python3
"""
SecureHoney Decoy Website
Attractive banking website target for attackers
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
import logging
from datetime import datetime
from pathlib import Path
import urllib.parse

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DecoyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests"""
        self.log_request_details('GET')
        
        if self.path == '/':
            self.serve_homepage()
        elif self.path == '/login':
            self.serve_login_page()
        elif self.path == '/admin':
            self.serve_admin_panel()
        elif self.path.startswith('/api/'):
            self.serve_api_endpoint()
        elif self.path.endswith('.css'):
            self.serve_css()
        elif self.path.endswith('.js'):
            self.serve_js()
        else:
            self.serve_404()
    
    def do_POST(self):
        """Handle POST requests"""
        self.log_request_details('POST')
        
        if self.path == '/login':
            self.handle_login_attempt()
        elif self.path.startswith('/api/'):
            self.handle_api_post()
        else:
            self.serve_404()
    
    def log_request_details(self, method: str):
        """Log detailed request information"""
        client_ip = self.client_address[0]
        user_agent = self.headers.get('User-Agent', 'Unknown')
        
        attack_data = {
            'timestamp': datetime.now().isoformat(),
            'source_ip': client_ip,
            'method': method,
            'path': self.path,
            'user_agent': user_agent,
            'headers': dict(self.headers),
            'attack_type': 'WEB_PROBE'
        }
        
        # Save to attack log
        self.save_attack_log(attack_data)
        logger.info(f"🌐 {method} {self.path} from {client_ip}")
    
    def save_attack_log(self, attack_data):
        """Save attack data to shared logging"""
        log_dir = Path("../shared-utils/logging/web-attacks")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"web_attacks_{datetime.now().strftime('%Y%m%d')}.json"
        
        try:
            with open(log_file, 'a') as f:
                f.write(json.dumps(attack_data) + '\n')
        except Exception as e:
            logger.error(f"Failed to save web attack log: {e}")
    
    def serve_homepage(self):
        """Serve attractive banking homepage"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>SecureBank - Online Banking</title>
            <link rel="stylesheet" href="/styles.css">
        </head>
        <body>
            <header>
                <h1>🏦 SecureBank</h1>
                <nav>
                    <a href="/">Home</a>
                    <a href="/login">Login</a>
                    <a href="/admin">Admin</a>
                </nav>
            </header>
            <main>
                <h2>Welcome to SecureBank Online</h2>
                <p>Your trusted partner for secure online banking.</p>
                <div class="features">
                    <div class="feature">
                        <h3>💳 Account Management</h3>
                        <p>Manage your accounts securely online</p>
                    </div>
                    <div class="feature">
                        <h3>💰 Transfers</h3>
                        <p>Quick and secure money transfers</p>
                    </div>
                    <div class="feature">
                        <h3>📊 Reports</h3>
                        <p>Detailed financial reports and analytics</p>
                    </div>
                </div>
                <a href="/login" class="cta-button">Login to Your Account</a>
            </main>
        </body>
        </html>
        """
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def serve_login_page(self):
        """Serve login page with form"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>SecureBank - Login</title>
            <link rel="stylesheet" href="/styles.css">
        </head>
        <body>
            <div class="login-container">
                <h1>🏦 SecureBank Login</h1>
                <form method="POST" action="/login">
                    <div class="form-group">
                        <label>Username:</label>
                        <input type="text" name="username" required>
                    </div>
                    <div class="form-group">
                        <label>Password:</label>
                        <input type="password" name="password" required>
                    </div>
                    <div class="form-group">
                        <label>Account Number:</label>
                        <input type="text" name="account" placeholder="Optional">
                    </div>
                    <button type="submit">Login</button>
                </form>
                <p><a href="/admin">Admin Access</a></p>
            </div>
        </body>
        </html>
        """
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def serve_admin_panel(self):
        """Serve fake admin panel"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>SecureBank - Admin Panel</title>
            <link rel="stylesheet" href="/styles.css">
        </head>
        <body>
            <div class="admin-panel">
                <h1>🔐 Admin Panel</h1>
                <div class="admin-stats">
                    <div class="stat">
                        <h3>Active Users</h3>
                        <span>1,247</span>
                    </div>
                    <div class="stat">
                        <h3>Total Accounts</h3>
                        <span>$2,847,392</span>
                    </div>
                    <div class="stat">
                        <h3>Transactions Today</h3>
                        <span>89</span>
                    </div>
                </div>
                <div class="admin-actions">
                    <a href="/api/users" class="admin-btn">View Users</a>
                    <a href="/api/accounts" class="admin-btn">Account Data</a>
                    <a href="/api/logs" class="admin-btn">System Logs</a>
                    <a href="/api/backup" class="admin-btn">Database Backup</a>
                </div>
            </div>
        </body>
        </html>
        """
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def serve_api_endpoint(self):
        """Serve fake API endpoints"""
        fake_data = {
            '/api/users': {
                'users': [
                    {'id': 1, 'username': 'admin', 'email': 'admin@securebank.com'},
                    {'id': 2, 'username': 'manager', 'email': 'manager@securebank.com'},
                    {'id': 3, 'username': 'user1', 'email': 'user1@securebank.com'}
                ]
            },
            '/api/accounts': {
                'accounts': [
                    {'id': '12345', 'balance': 50000, 'type': 'checking'},
                    {'id': '67890', 'balance': 125000, 'type': 'savings'},
                    {'id': '11111', 'balance': 75000, 'type': 'business'}
                ]
            },
            '/api/logs': {
                'logs': [
                    {'timestamp': '2024-01-15 10:30:00', 'action': 'login', 'user': 'admin'},
                    {'timestamp': '2024-01-15 10:25:00', 'action': 'transfer', 'amount': 5000},
                    {'timestamp': '2024-01-15 10:20:00', 'action': 'backup', 'status': 'completed'}
                ]
            }
        }
        
        data = fake_data.get(self.path, {'error': 'Endpoint not found'})
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def serve_css(self):
        """Serve CSS styles"""
        css = """
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        
        header {
            background: white;
            padding: 1rem 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        nav a {
            margin: 0 1rem;
            text-decoration: none;
            color: #333;
            font-weight: 500;
        }
        
        main {
            padding: 2rem;
            text-align: center;
            color: white;
        }
        
        .features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 2rem;
            margin: 2rem 0;
        }
        
        .feature {
            background: rgba(255,255,255,0.1);
            padding: 2rem;
            border-radius: 10px;
            backdrop-filter: blur(10px);
        }
        
        .cta-button {
            display: inline-block;
            background: #ff6b6b;
            color: white;
            padding: 1rem 2rem;
            text-decoration: none;
            border-radius: 5px;
            font-weight: bold;
            margin-top: 2rem;
        }
        
        .login-container, .admin-panel {
            max-width: 400px;
            margin: 5rem auto;
            background: white;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        
        .form-group {
            margin-bottom: 1rem;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: bold;
        }
        
        .form-group input {
            width: 100%;
            padding: 0.75rem;
            border: 1px solid #ddd;
            border-radius: 5px;
            box-sizing: border-box;
        }
        
        button {
            width: 100%;
            background: #667eea;
            color: white;
            padding: 1rem;
            border: none;
            border-radius: 5px;
            font-size: 1rem;
            cursor: pointer;
        }
        
        .admin-stats {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1rem;
            margin: 2rem 0;
        }
        
        .stat {
            text-align: center;
            padding: 1rem;
            background: #f8f9fa;
            border-radius: 5px;
        }
        
        .admin-actions {
            display: grid;
            gap: 1rem;
        }
        
        .admin-btn {
            display: block;
            background: #28a745;
            color: white;
            padding: 1rem;
            text-decoration: none;
            border-radius: 5px;
            text-align: center;
        }
        """
        self.send_response(200)
        self.send_header('Content-type', 'text/css')
        self.end_headers()
        self.wfile.write(css.encode())
    
    def serve_js(self):
        """Serve JavaScript"""
        js = """
        console.log('SecureBank Online Banking System');
        
        // Fake login validation
        document.addEventListener('DOMContentLoaded', function() {
            const form = document.querySelector('form');
            if (form) {
                form.addEventListener('submit', function(e) {
                    console.log('Login attempt detected');
                });
            }
        });
        """
        self.send_response(200)
        self.send_header('Content-type', 'application/javascript')
        self.end_headers()
        self.wfile.write(js.encode())
    
    def handle_login_attempt(self):
        """Handle login form submission"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        
        # Parse form data
        form_data = urllib.parse.parse_qs(post_data)
        username = form_data.get('username', [''])[0]
        password = form_data.get('password', [''])[0]
        account = form_data.get('account', [''])[0]
        
        # Log credential theft attempt
        attack_data = {
            'timestamp': datetime.now().isoformat(),
            'source_ip': self.client_address[0],
            'attack_type': 'CREDENTIAL_THEFT',
            'severity': 'HIGH',
            'username': username,
            'password_length': len(password),
            'account_number': account,
            'user_agent': self.headers.get('User-Agent', 'Unknown')
        }
        
        self.save_attack_log(attack_data)
        logger.warning(f"🚨 Credential theft attempt from {self.client_address[0]}: {username}")
        
        # Return fake error
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Login Error</title>
            <link rel="stylesheet" href="/styles.css">
        </head>
        <body>
            <div class="login-container">
                <h1>Login Failed</h1>
                <p>Invalid credentials. Please try again.</p>
                <a href="/login">Back to Login</a>
            </div>
        </body>
        </html>
        """
        self.send_response(401)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def handle_api_post(self):
        """Handle API POST requests"""
        self.send_response(403)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'error': 'Access denied'}).encode())
    
    def serve_404(self):
        """Serve 404 page"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Page Not Found</title>
            <link rel="stylesheet" href="/styles.css">
        </head>
        <body>
            <div class="login-container">
                <h1>404 - Page Not Found</h1>
                <p>The requested page could not be found.</p>
                <a href="/">Back to Home</a>
            </div>
        </body>
        </html>
        """
        self.send_response(404)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())

def run_decoy_server(port=8080):
    """Run the decoy web server"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, DecoyHandler)
    
    logger.info(f"🌐 SecureHoney Decoy Server running on port {port}")
    logger.info(f"🎯 Decoy site: http://localhost:{port}")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down decoy server")
        httpd.shutdown()

if __name__ == "__main__":
    run_decoy_server()
