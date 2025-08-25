"""
Alerts API routes
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
import logging

from ..models import AlertResponse
from ..main import database, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/", response_model=Dict[str, Any])
async def get_alerts(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    severity: Optional[str] = Query(None),
    alert_type: Optional[str] = Query(None),
    user: dict = Depends(get_current_user)
):
    """Get alerts with optional filtering"""
    try:
        # For now, we'll simulate alerts from events
        # In a real implementation, this would query an alerts table
        filters = {}
        if severity:
            filters['severity'] = severity
        
        events = await database.get_events(limit=limit, offset=offset, filters=filters)
        
        # Convert high-severity events to alerts
        alerts = []
        for event in events:
            if event.get('severity') in ['high', 'critical']:
                alert = {
                    'id': event['id'],
                    'event_id': event['id'],
                    'alert_type': event.get('attack_type', 'security_event'),
                    'severity': event['severity'],
                    'message': f"Security event detected from {event['source_ip']}",
                    'created_at': event['created_at'],
                    'source_ip': event['source_ip'],
                    'event_type': event['event_type']
                }
                alerts.append(alert)
        
        return {
            "alerts": alerts,
            "count": len(alerts),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to get alerts")

@router.get("/{alert_id}")
async def get_alert(alert_id: int, user: dict = Depends(get_current_user)):
    """Get specific alert by ID"""
    try:
        # For demo, treat alert_id as event_id
        events = await database.get_events(limit=1, offset=0)
        event = next((e for e in events if e['id'] == alert_id), None)
        
        if not event:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        alert = {
            'id': event['id'],
            'event_id': event['id'],
            'alert_type': event.get('attack_type', 'security_event'),
            'severity': event['severity'],
            'message': f"Security event detected from {event['source_ip']}",
            'created_at': event['created_at'],
            'event': event
        }
        
        return alert
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get alert")

@router.get("/stats/summary")
async def get_alert_stats(user: dict = Depends(get_current_user)):
    """Get alert statistics"""
    try:
        stats = await database.get_stats()
        
        # Calculate alert stats from severity distribution
        severity_dist = stats.get('events_by_severity', {})
        total_alerts = severity_dist.get('high', 0) + severity_dist.get('critical', 0)
        
        alert_stats = {
            'total_alerts': total_alerts,
            'critical_alerts': severity_dist.get('critical', 0),
            'high_alerts': severity_dist.get('high', 0),
            'alerts_last_24h': stats.get('events_last_24h', 0) // 4,  # Estimate
            'alert_types': {
                'sql_injection': 5,
                'xss': 3,
                'brute_force': 8,
                'reconnaissance': 12
            }
        }
        
        return alert_stats
        
    except Exception as e:
        logger.error(f"Error getting alert stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get alert stats")

@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: int, user: dict = Depends(get_current_user)):
    """Acknowledge an alert"""
    try:
        # In a real implementation, this would update the alert status
        return {"message": f"Alert {alert_id} acknowledged", "acknowledged_by": user.get('username')}
        
    except Exception as e:
        logger.error(f"Error acknowledging alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to acknowledge alert")

@router.delete("/{alert_id}")
async def dismiss_alert(alert_id: int, user: dict = Depends(get_current_user)):
    """Dismiss an alert"""
    try:
        # In a real implementation, this would mark the alert as dismissed
        return {"message": f"Alert {alert_id} dismissed"}
        
    except Exception as e:
        logger.error(f"Error dismissing alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to dismiss alert")
