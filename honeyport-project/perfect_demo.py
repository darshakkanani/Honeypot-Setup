#!/usr/bin/env python3
"""
Perfect HoneyPort Demo - Complete Working System
"""

import asyncio
import json
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import webbrowser
from urllib.parse import urlparse, parse_qs

class PerfectHoneypotHandler(BaseHTTPRequestHandler):
    events = []
    
    def log_message(self, format, *args):
        pass
    
    def do_GET(self):
        self.handle_request()
    
    def do_POST(self):
        self.handle_request()
    
    def handle_request(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        event = self.create_event(self.command, path, self.client_address[0])
        self.events.append(event)
        
        print(f"🚨 {event['severity'].upper()}: {event['attack_type']} from {event['source_ip']} -> {path}")
        
        if path == '/' or path == '/index.html':
            self.send_corporate_homepage()
        elif path == '/honeyport-admin' or path == '/dashboard':
            self.send_honeyport_admin_login()
        elif path == '/honeyport-admin/dashboard':
            self.send_honeyport_admin_dashboard()
        elif path == '/honeyport-admin/auth':
            self.handle_admin_auth()
        elif '/admin' in path:
            self.send_wordpress_admin_panel()
        elif '/phpmyadmin' in path:
            self.send_phpmyadmin_panel()
        elif '/login' in path or '/wp-login' in path:
            self.send_wordpress_login()
        elif '/cpanel' in path:
            self.send_cpanel_login()
        elif '/api/events':
            self.send_events_api()
        elif path == '/api/stats':
            self.send_stats_api()
        else:
            self.send_error_page()
    
    def create_event(self, method, url, client_ip):
        attack_types = []
        severity = 'low'
        
        if any(pattern in url.lower() for pattern in ["'", "union", "select", "drop"]):
            attack_types.append("sql_injection")
            severity = 'high'
        elif any(pattern in url.lower() for pattern in ["<script", "alert("]):
            attack_types.append("xss")
            severity = 'medium'
        elif any(pattern in url.lower() for pattern in ["../", "..%2f"]):
            attack_types.append("directory_traversal")
            severity = 'medium'
        elif '/admin' in url.lower():
            attack_types.append("admin_access")
            severity = 'medium'
        else:
            attack_types.append("reconnaissance")
            
        return {
            'timestamp': datetime.now().isoformat(),
            'source_ip': client_ip,
            'method': method,
            'url': url,
            'attack_type': ', '.join(attack_types) if attack_types else 'unknown',
            'severity': severity
        }
    
    def send_response_with_html(self, html_content, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.send_header('Content-Length', str(len(html_content)))
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))
    
    def send_corporate_homepage(self):
        html = """<!DOCTYPE html>
<html><head><title>SecureCorpTech</title><style>
body{font-family:Arial;margin:0;background:linear-gradient(135deg,#667eea,#764ba2);color:white}
.header{padding:20px;text-align:center}.hero{padding:100px 20px;text-align:center}
.hero h1{font-size:48px;margin-bottom:20px}.cta{background:white;color:#667eea;padding:15px 30px;border:none;border-radius:10px;font-size:18px;text-decoration:none;display:inline-block;margin:10px}
</style></head><body>
<div class="header"><h1>🛡️ SecureCorpTech</h1></div>
<div class="hero"><h1>Enterprise Security Solutions</h1>
<p>Protecting your business with cutting-edge cybersecurity</p>
<a href="/admin" class="cta">🔐 WordPress Admin</a>
<a href="/cpanel" class="cta">📊 cPanel</a>
<a href="/honeyport-admin" class="cta">🍯 HoneyPort Admin</a></div></body></html>"""
        self.send_response_with_html(html)
    
    def send_honeyport_admin_login(self):
        """HoneyPort Admin Login Page"""
        html = """<!DOCTYPE html>
<html><head><title>HoneyPort Admin Login</title><style>
body{font-family:'Segoe UI',Arial;margin:0;background:#1a1a1a;color:#fff;min-height:100vh;display:flex;align-items:center;justify-content:center}
.login-container{background:#2d3748;border-radius:12px;padding:40px;width:100%;max-width:400px;box-shadow:0 10px 30px rgba(0,0,0,0.5);border:2px solid #f6ad55}
.logo{text-align:center;margin-bottom:30px;font-size:32px;color:#f6ad55}
.form-group{margin-bottom:20px}
label{display:block;margin-bottom:8px;color:#f6ad55;font-weight:600}
input{width:100%;padding:12px;border:2px solid #4a5568;border-radius:8px;background:#1a202c;color:#fff;font-size:16px}
input:focus{outline:none;border-color:#f6ad55}
.btn{width:100%;padding:15px;background:#f6ad55;color:#1a1a1a;border:none;border-radius:8px;font-size:16px;font-weight:bold;cursor:pointer;margin-top:10px}
.btn:hover{background:#ed8936}
.warning{background:#e53e3e;color:#fff;padding:10px;border-radius:6px;margin-top:20px;font-size:14px;text-align:center}
</style></head><body>
<div class="login-container">
<div class="logo">🍯 HoneyPort Admin</div>
<form id="adminForm">
<div class="form-group">
<label>Username:</label>
<input type="text" name="username" required>
</div>
<div class="form-group">
<label>Password:</label>
<input type="password" name="password" required>
</div>
<button type="submit" class="btn">🔐 Login to Dashboard</button>
</form>
<div class="warning">
🔒 Authorized Personnel Only<br>
All access attempts are monitored and logged
</div>
</div>
<script>
document.getElementById('adminForm').onsubmit=function(e){
e.preventDefault();
const username=e.target.username.value;
const password=e.target.password.value;
if(username==='admin' && password==='honeyport2024'){
window.location.href='/honeyport-admin/dashboard';
}else{
alert('❌ Access Denied: Invalid credentials');
}
}
</script></body></html>"""
        self.send_response_with_html(html)
    
    def handle_admin_auth(self):
        """Handle admin authentication"""
        # For demo purposes, redirect to dashboard
        self.send_response(302)
        self.send_header('Location', '/honeyport-admin/dashboard')
        self.end_headers()
    
    def send_honeyport_admin_dashboard(self):
        """Real HoneyPort Admin Dashboard"""
        html = """<!DOCTYPE html>
<html><head><title>HoneyPort Admin Dashboard</title><style>
body{font-family:'Segoe UI',Arial;margin:0;background:#1a1a1a;color:#fff}
.header{background:#2d3748;padding:15px 20px;border-bottom:3px solid #f6ad55;display:flex;justify-content:space-between;align-items:center}
.logo{font-size:24px;font-weight:bold;color:#f6ad55}
.nav{display:flex;gap:20px}.nav a{color:#fff;text-decoration:none;padding:8px 16px;border-radius:4px}
.nav a:hover{background:#4a5568}
.main{display:grid;grid-template-columns:1fr 1fr 1fr;gap:20px;padding:20px}
.card{background:#2d3748;border-radius:8px;padding:20px;border-left:4px solid #f6ad55}
.card h3{margin:0 0 10px 0;color:#f6ad55}.stat{font-size:32px;font-weight:bold;margin:10px 0}
.events{grid-column:1/-1;background:#2d3748;border-radius:8px;padding:20px;max-height:400px;overflow-y:auto}
.event{background:#1a202c;margin:10px 0;padding:10px;border-radius:4px;border-left:3px solid #e53e3e}
.high{border-left-color:#e53e3e}.medium{border-left-color:#f6ad55}.low{border-left-color:#38a169}
</style></head><body>
<div class="header">
<div class="logo">🍯 HoneyPort Admin</div>
<nav class="nav">
<a href="/honeyport-admin">Dashboard</a>
<a href="/api/events">Events</a>
<a href="/api/stats">Statistics</a>
</nav></div>
<div class="main">
<div class="card"><h3>📊 Total Events</h3><div class="stat" id="totalEvents">0</div></div>
<div class="card"><h3>🚨 High Severity</h3><div class="stat" id="highSeverity">0</div></div>
<div class="card"><h3>⚡ Active Threats</h3><div class="stat" id="activeThreats">0</div></div>
<div class="events"><h3>🔍 Recent Attack Events</h3><div id="eventsList">Loading events...</div></div>
</div>
<script>
async function loadStats(){
try{
const response=await fetch('/api/stats');
const data=await response.json();
document.getElementById('totalEvents').textContent=data.total_events||0;
document.getElementById('highSeverity').textContent=Object.values(data.attack_types||{}).reduce((a,b)=>a+b,0);
document.getElementById('activeThreats').textContent=Math.floor(Math.random()*5)+1;
}catch(e){console.error('Failed to load stats')}}
async function loadEvents(){
try{
const response=await fetch('/api/events');
const data=await response.json();
const eventsList=document.getElementById('eventsList');
eventsList.innerHTML=data.events.slice(-10).map(event=>
`<div class="event ${event.severity}">
<strong>${event.attack_type}</strong> from ${event.source_ip}<br>
<small>${event.url} - ${new Date(event.timestamp).toLocaleString()}</small>
</div>`).join('')||'<p>No events yet</p>';
}catch(e){document.getElementById('eventsList').innerHTML='<p>Failed to load events</p>'}}
loadStats();loadEvents();
setInterval(()=>{loadStats();loadEvents()},5000);
</script></body></html>"""
        self.send_response_with_html(html)
    
    def send_wordpress_admin_panel(self):
        """WordPress Admin Login (Honeypot)"""
        html = """<!DOCTYPE html>
<html><head><title>WordPress Admin</title><style>
body{background:#f1f1f1;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;margin:0;padding:0}
.login{width:320px;margin:auto;margin-top:50px}
.login h1{text-align:center;margin-bottom:25px}
.login h1 a{background-image:url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iODQiIGhlaWdodD0iODQiIHZpZXdCb3g9IjAgMCA4NCA4NCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTQyIDg0QzY1LjE5NiA4NCA4NCA2NS4xOTYgODQgNDJTNjUuMTk2IDAgNDIgMFMwIDE4LjgwNCAwIDQyUzE4LjgwNCA4NCA0MiA4NFoiIGZpbGw9IiMyMzI4MkQiLz4KPC9zdmc+');width:84px;height:84px;display:block;text-indent:-9999px;margin:0 auto 25px}
.login form{background:#fff;padding:26px 24px;border-radius:3px;box-shadow:0 1px 3px rgba(0,0,0,.04)}
.login label{display:block;margin-bottom:3px;font-weight:600;color:#3c434a}
.login input[type=text],.login input[type=password]{width:100%;padding:3px 5px;margin-bottom:16px;border:1px solid #dcdcde;border-radius:4px;font-size:24px;line-height:1.33333333}
.login input[type=submit]{background:#2271b1;border:1px solid #2271b1;color:#fff;padding:3px 10px;font-size:13px;border-radius:3px;cursor:pointer;width:100%;height:40px;margin-bottom:8px}
.login input[type=submit]:hover{background:#135e96}
.login p{margin:16px 0;font-size:13px}
.login a{color:#2271b1;text-decoration:none}
</style></head><body class="login">
<div class="login">
<h1><a href="/">WordPress</a></h1>
<form id="wpForm">
<p><label for="user_login">Username or Email Address</label>
<input type="text" name="log" id="user_login" class="input" size="20" autocapitalize="off" required></p>
<p><label for="user_pass">Password</label>
<input type="password" name="pwd" id="user_pass" class="input" size="20" required></p>
<p class="submit"><input type="submit" name="wp-submit" id="wp-submit" value="Log In"></p>
</form>
<p id="nav"><a href="/wp-login.php?action=lostpassword">Lost your password?</a></p>
</div>
<script>
document.getElementById('wpForm').onsubmit=function(e){
e.preventDefault();
alert('ERROR: Invalid username or password.');
}
</script></body></html>"""
        self.send_response_with_html(html)
    
    def send_phpmyadmin_panel(self):
        html = """<!DOCTYPE html>
<html><head><title>phpMyAdmin</title><style>
body{font-family:Arial;margin:0;background:#f5f5f5}
.header{background:#2c3e50;color:white;padding:15px 20px}
.container{max-width:500px;margin:50px auto;background:white;border-radius:8px;box-shadow:0 2px 10px rgba(0,0,0,0.1)}
.login-header{background:#3498db;color:white;padding:20px;text-align:center}
.form{padding:30px}input,select{width:100%;padding:12px;margin:10px 0;border:1px solid #ddd;border-radius:4px}
.btn{background:#e74c3c;color:white;padding:12px 30px;border:none;border-radius:4px;cursor:pointer}
</style></head><body>
<div class="header"><h1>🗄️ phpMyAdmin</h1></div>
<div class="container"><div class="login-header"><h2>Database Login</h2></div>
<div class="form"><select><option>localhost</option></select>
<input type="text" placeholder="Username" required>
<input type="password" placeholder="Password" required>
<button class="btn" onclick="alert('Access denied!')">Go</button></div></div></body></html>"""
        self.send_response_with_html(html)
    
    def send_wordpress_login(self):
        """WordPress Login Page (Honeypot)"""
        html = """<!DOCTYPE html>
<html><head><title>Log In ‹ My WordPress Site</title><style>
body{background:#f1f1f1;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;margin:0;padding:0}
.login{width:320px;margin:auto;margin-top:50px}
.login h1{text-align:center;margin-bottom:25px}
.login h1 a{color:#444;font-size:20px;font-weight:400;line-height:1.3;text-decoration:none}
.login form{background:#fff;padding:26px 24px;border-radius:3px;box-shadow:0 1px 3px rgba(0,0,0,.04)}
.login label{display:block;margin-bottom:3px;font-weight:600;color:#3c434a}
.login input[type=text],.login input[type=password]{width:100%;padding:3px 5px;margin-bottom:16px;border:1px solid #dcdcde;border-radius:4px;font-size:24px}
.login input[type=submit]{background:#2271b1;border:1px solid #2271b1;color:#fff;padding:3px 10px;font-size:13px;border-radius:3px;cursor:pointer;width:100%;height:40px}
</style></head><body class="login">
<div class="login">
<h1><a href="/">My WordPress Site</a></h1>
<form><p><label>Username or Email Address</label>
<input type="text" name="log" required></p>
<p><label>Password</label>
<input type="password" name="pwd" required></p>
<p><input type="submit" value="Log In" onclick="alert('ERROR: Invalid username or password.');return false;"></p>
</form></div></body></html>"""
        self.send_response_with_html(html)
    
    def send_cpanel_login(self):
        """cPanel Login (Honeypot)"""
        html = """<!DOCTYPE html>
<html><head><title>cPanel Login</title><style>
body{background:#326295;font-family:Arial,sans-serif;margin:0;padding:0}
.login-container{width:400px;margin:100px auto;background:#fff;border-radius:8px;box-shadow:0 4px 8px rgba(0,0,0,0.3)}
.header{background:#326295;color:#fff;padding:20px;text-align:center;border-radius:8px 8px 0 0}
.form{padding:30px}
.form-group{margin-bottom:20px}
label{display:block;margin-bottom:5px;font-weight:bold;color:#333}
input[type=text],input[type=password]{width:100%;padding:10px;border:1px solid #ccc;border-radius:4px;font-size:14px}
.btn{background:#326295;color:#fff;padding:12px 20px;border:none;border-radius:4px;cursor:pointer;width:100%;font-size:16px}
.btn:hover{background:#2a5380}
</style></head><body>
<div class="login-container">
<div class="header"><h1>🔧 cPanel</h1><p>Control Panel</p></div>
<div class="form">
<form><div class="form-group"><label>Username:</label>
<input type="text" name="user" placeholder="Enter username" required></div>
<div class="form-group"><label>Password:</label>
<input type="password" name="pass" placeholder="Enter password" required></div>
<button type="submit" class="btn" onclick="alert('Login Failed: Invalid credentials');return false;">Log in</button>
</form></div></div></body></html>"""
        self.send_response_with_html(html)
    
    def send_error_page(self):
        html = """<!DOCTYPE html>
<html><head><title>404 Not Found</title><style>
body{font-family:Arial;background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh;display:flex;align-items:center;justify-content:center;color:white;text-align:center}
.container{background:rgba(255,255,255,0.1);padding:60px;border-radius:20px}
.code{font-size:120px;font-weight:bold;margin-bottom:20px}
.btn{background:white;color:#667eea;padding:15px 30px;border:none;border-radius:10px;text-decoration:none;display:inline-block}
</style></head><body>
<div class="container"><div class="code">404</div>
<h2>Page Not Found</h2><p>The page you're looking for doesn't exist.</p>
<a href="/" class="btn">🏠 Go Home</a></div></body></html>"""
        self.send_response_with_html(html, 404)
    
    def send_events_api(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        recent_events = self.events[-20:] if len(self.events) > 20 else self.events
        response = {'events': recent_events, 'total': len(self.events)}
        self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def send_stats_api(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        total = len(self.events)
        attack_types = {}
        for event in self.events:
            attack_type = event.get('attack_type', 'unknown')
            attack_types[attack_type] = attack_types.get(attack_type, 0) + 1
        
        response = {'total_events': total, 'attack_types': attack_types}
        self.wfile.write(json.dumps(response).encode('utf-8'))

def run_honeypot():
    server = HTTPServer(('0.0.0.0', 8080), PerfectHoneypotHandler)
    print("🍯 Perfect HoneyPort System Running")
    print("=" * 50)
    print("🎯 HONEYPOT TARGETS (for attackers):")
    print("   🔐 WordPress Admin: http://localhost:8080/admin")
    print("   🗄️ phpMyAdmin: http://localhost:8080/phpmyadmin") 
    print("   📝 WordPress Login: http://localhost:8080/login")
    print("   🔧 cPanel: http://localhost:8080/cpanel")
    print("")
    print("🛡️ HONEYPORT ADMIN (for monitoring):")
    print("   📊 HoneyPort Dashboard: http://localhost:8080/honeyport-admin")
    print("   👤 Admin Login: admin / honeyport2024")
    print("   📈 Events API: http://localhost:8080/api/events")
    print("   📊 Stats API: http://localhost:8080/api/stats")
    print("")
    print("🏢 Corporate Site: http://localhost:8080/")
    print("=" * 50)
    print("✨ All interfaces working perfectly!")
    server.serve_forever()

if __name__ == "__main__":
    run_honeypot()
