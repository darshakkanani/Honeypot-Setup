#!/usr/bin/env python3
"""
HoneyPort Dashboard Backend
FastAPI backend with blockchain verification and AI insights
"""

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
import yaml
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from blockchain.log_manager import BlockchainLogManager
from core.ai_behavior import AIBehaviorEngine

app = FastAPI(title="HoneyPort Dashboard", version="1.0.0")
security = HTTPBasic()

# Load configuration
with open("config.yaml", 'r') as f:
    config = yaml.safe_load(f)

# Initialize components
log_manager = BlockchainLogManager(config)
ai_engine = AIBehaviorEngine(config)

# Templates and static files
templates = Jinja2Templates(directory="dashboard/templates")
app.mount("/static", StaticFiles(directory="dashboard/static"), name="static")

# Authentication
def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    """Simple authentication for dashboard"""
    dashboard_config = config.get('dashboard', {})
    correct_username = dashboard_config.get('admin_username', 'admin')
    correct_password = dashboard_config.get('admin_password', 'honeyport2024')
    
    is_correct_username = secrets.compare_digest(credentials.username, correct_username)
    is_correct_password = secrets.compare_digest(credentials.password, correct_password)
    
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

@app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request, username: str = Depends(authenticate)):
    """Main dashboard page"""
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "username": username,
        "config": config
    })

@app.get("/api/stats")
async def get_stats(username: str = Depends(authenticate)):
    """Get honeypot statistics"""
    try:
        # Get blockchain stats
        blockchain_stats = log_manager.get_attack_statistics()
        
        # Get AI insights
        ai_insights = ai_engine.get_ai_insights()
        
        # Calculate additional metrics
        total_attacks = blockchain_stats.get('total_attacks', 0)
        unique_ips = len(blockchain_stats.get('unique_source_ips', []))
        
        return {
            "total_attacks": total_attacks,
            "unique_attackers": unique_ips,
            "blocked_ips": blockchain_stats.get('blocked_ips', 0),
            "ai_adaptations": ai_insights.get('total_adaptations', 0),
            "current_behavior": ai_insights.get('current_behavior', 'realistic'),
            "blockchain_blocks": blockchain_stats.get('total_blocks', 0),
            "last_attack": blockchain_stats.get('latest_attack_time', 'Never'),
            "attack_types": blockchain_stats.get('attack_type_distribution', {}),
            "severity_distribution": blockchain_stats.get('severity_distribution', {}),
            "uptime": _calculate_uptime()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")

@app.get("/api/events")
async def get_recent_events(limit: int = 50, username: str = Depends(authenticate)):
    """Get recent attack events"""
    try:
        events = log_manager.get_recent_logs(limit=limit)
        
        # Format events for frontend
        formatted_events = []
        for event in events:
            formatted_events.append({
                "id": event.get('log_id', 'unknown'),
                "timestamp": event.get('timestamp', ''),
                "source_ip": event.get('source_ip', 'unknown'),
                "attack_type": event.get('attack_type', 'unknown'),
                "severity": event.get('severity', 'low'),
                "url": event.get('url', '/'),
                "method": event.get('method', 'GET'),
                "user_agent": event.get('user_agent', '')[:50] + '...' if len(event.get('user_agent', '')) > 50 else event.get('user_agent', ''),
                "geolocation": event.get('geolocation', {}),
                "ai_behavior": event.get('response_behavior', 'realistic')
            })
        
        return {"events": formatted_events}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching events: {str(e)}")

@app.get("/api/blockchain/verify")
async def verify_blockchain():
    """Verify blockchain integrity"""
    try:
        verification = log_manager.verify_chain_integrity()
        return verification
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Blockchain verification error: {str(e)}")

@app.get("/api/blockchain/status")
async def get_blockchain_status():
    """Get comprehensive blockchain status"""
    try:
        status = log_manager.get_blockchain_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Blockchain status error: {str(e)}")

@app.get("/api/smart-contract/stats")
async def get_smart_contract_stats():
    """Get smart contract statistics"""
    try:
        if hasattr(log_manager, 'web3_manager') and log_manager.web3_manager:
            stats = log_manager.web3_manager.get_contract_stats()
            return stats
        else:
            return {"error": "Smart contract not available"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Smart contract stats error: {str(e)}")

@app.post("/api/smart-contract/verify-log")
async def verify_smart_contract_log(request: dict):
    """Verify a specific log in smart contract"""
    try:
        log_hash = request.get("log_hash")
        if not log_hash:
            raise HTTPException(status_code=400, detail="log_hash required")
        
        if hasattr(log_manager, 'web3_manager') and log_manager.web3_manager:
            verified = log_manager.web3_manager.verify_log(log_hash)
            return {"verified": verified, "log_hash": log_hash}
        else:
            return {"error": "Smart contract not available"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Log verification error: {str(e)}")

@app.get("/api/ai/insights")
async def get_ai_insights(username: str = Depends(authenticate)):
    """Get AI behavior insights"""
    try:
        insights = ai_engine.get_ai_insights()
        
        return {
            "ai_enabled": insights.get('ai_enabled', False),
            "current_behavior": insights.get('current_behavior', 'realistic'),
            "total_adaptations": insights.get('total_adaptations', 0),
            "recent_adaptations": insights.get('recent_adaptations', []),
            "behavior_distribution": insights.get('behavior_distribution', {}),
            "model_status": insights.get('model_status', {}),
            "adaptation_history": [
                {
                    "timestamp": adapt.get('timestamp', ''),
                    "from_behavior": adapt.get('from_behavior', ''),
                    "to_behavior": adapt.get('to_behavior', ''),
                    "confidence": adapt.get('confidence', 0.0)
                }
                for adapt in insights.get('recent_adaptations', [])
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching AI insights: {str(e)}")

@app.get("/api/alerts")
async def get_alerts(username: str = Depends(authenticate)):
    """Get recent alerts"""
    try:
        # In production, this would fetch from alert system
        # For now, return mock data based on recent high-severity events
        events = log_manager.get_recent_logs(limit=20)
        alerts = []
        
        for event in events:
            if event.get('severity') in ['high', 'medium']:
                alerts.append({
                    "id": f"alert_{event.get('log_id', 'unknown')}",
                    "type": f"{event.get('attack_type', 'unknown')}_detected",
                    "severity": event.get('severity', 'low'),
                    "message": f"{event.get('attack_type', 'Attack').title()} detected from {event.get('source_ip', 'unknown')}",
                    "timestamp": event.get('timestamp', ''),
                    "source_ip": event.get('source_ip', 'unknown'),
                    "resolved": False
                })
        
        return {"alerts": alerts[:10]}  # Return last 10 alerts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching alerts: {str(e)}")

@app.get("/api/geolocation")
async def get_geolocation_data(username: str = Depends(authenticate)):
    """Get attack geolocation data"""
    try:
        events = log_manager.get_recent_logs(limit=100)
        geo_data = []
        
        for event in events:
            geo = event.get('geolocation', {})
            if geo.get('latitude') and geo.get('longitude'):
                geo_data.append({
                    "lat": geo.get('latitude', 0),
                    "lng": geo.get('longitude', 0),
                    "country": geo.get('country', 'Unknown'),
                    "city": geo.get('city', 'Unknown'),
                    "attack_type": event.get('attack_type', 'unknown'),
                    "severity": event.get('severity', 'low'),
                    "timestamp": event.get('timestamp', '')
                })
        
        return {"locations": geo_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching geolocation data: {str(e)}")

@app.post("/api/ai/retrain")
async def retrain_ai_models(username: str = Depends(authenticate)):
    """Trigger AI model retraining"""
    try:
        # Get recent training data
        recent_events = log_manager.get_recent_logs(limit=1000)
        
        # Format for training
        training_data = []
        for event in recent_events:
            training_data.append({
                **event,
                "optimal_behavior": _determine_optimal_behavior(event)
            })
        
        # Retrain models
        success = ai_engine.train_model(training_data)
        
        return {
            "success": success,
            "training_samples": len(training_data),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model retraining error: {str(e)}")

@app.get("/api/export/logs")
async def export_logs(format: str = "json", username: str = Depends(authenticate)):
    """Export logs in various formats"""
    try:
        if format not in ["json", "csv"]:
            raise HTTPException(status_code=400, detail="Unsupported format")
        
        logs = log_manager.export_logs()
        
        if format == "json":
            return JSONResponse(content=logs)
        else:
            # Convert to CSV format
            import csv
            import io
            
            output = io.StringIO()
            if logs:
                writer = csv.DictWriter(output, fieldnames=logs[0].keys())
                writer.writeheader()
                writer.writerows(logs)
            
            return JSONResponse(content={"csv_data": output.getvalue()})
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export error: {str(e)}")

def _calculate_uptime() -> str:
    """Calculate system uptime"""
    # In production, track actual start time
    # For now, return a placeholder
    return "2h 34m"

def _determine_optimal_behavior(event: Dict[str, Any]) -> str:
    """Determine optimal behavior for training data"""
    attack_type = event.get('attack_type', 'reconnaissance')
    severity = event.get('severity', 'low')
    
    if severity == 'high':
        return 'cautious'
    elif attack_type in ['sql_injection', 'xss']:
        return 'enticing'
    elif attack_type == 'brute_force':
        return 'aggressive'
    else:
        return 'realistic'

if __name__ == "__main__":
    import uvicorn
    
    dashboard_config = config.get('dashboard', {})
    host = dashboard_config.get('host', '127.0.0.1')
    port = dashboard_config.get('port', 8080)
    
    print(f"🚀 Starting HoneyPort Dashboard on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
