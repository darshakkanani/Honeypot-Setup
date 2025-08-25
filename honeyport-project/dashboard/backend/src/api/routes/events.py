"""
Events API routes
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
import logging

from ..models import EventResponse, EventFilter, SearchQuery, ExportRequest
from ..main import database, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/", response_model=Dict[str, Any])
async def get_events(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    source_ip: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    start_time: Optional[str] = Query(None),
    end_time: Optional[str] = Query(None),
    user: dict = Depends(get_current_user)
):
    """Get events with optional filtering"""
    try:
        filters = {}
        if source_ip:
            filters['source_ip'] = source_ip
        if event_type:
            filters['event_type'] = event_type
        if severity:
            filters['severity'] = severity
        if start_time:
            filters['start_time'] = start_time
        if end_time:
            filters['end_time'] = end_time
        
        events = await database.get_events(limit=limit, offset=offset, filters=filters)
        
        return {
            "events": events,
            "count": len(events),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Error getting events: {e}")
        raise HTTPException(status_code=500, detail="Failed to get events")

@router.get("/{event_id}")
async def get_event(event_id: int, user: dict = Depends(get_current_user)):
    """Get specific event by ID"""
    try:
        events = await database.get_events(limit=1, offset=0, filters={'id': event_id})
        
        if not events:
            raise HTTPException(status_code=404, detail="Event not found")
        
        return events[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting event {event_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get event")

@router.post("/search")
async def search_events(
    search_query: SearchQuery,
    user: dict = Depends(get_current_user)
):
    """Search events by text query"""
    try:
        filters = None
        if search_query.filters:
            filters = search_query.filters.dict(exclude_unset=True)
        
        events = await database.search_events(search_query.query, filters)
        
        return {
            "events": events,
            "count": len(events),
            "query": search_query.query
        }
        
    except Exception as e:
        logger.error(f"Error searching events: {e}")
        raise HTTPException(status_code=500, detail="Failed to search events")

@router.get("/types/list")
async def get_event_types(user: dict = Depends(get_current_user)):
    """Get list of available event types"""
    try:
        # This would typically come from database
        event_types = [
            "http_request",
            "ssh_connection", 
            "ssh_auth_attempt",
            "tcp_connection"
        ]
        
        return {"event_types": event_types}
        
    except Exception as e:
        logger.error(f"Error getting event types: {e}")
        raise HTTPException(status_code=500, detail="Failed to get event types")

@router.get("/severity/distribution")
async def get_severity_distribution(user: dict = Depends(get_current_user)):
    """Get distribution of events by severity"""
    try:
        stats = await database.get_stats()
        severity_dist = stats.get('events_by_severity', {})
        
        return {"severity_distribution": severity_dist}
        
    except Exception as e:
        logger.error(f"Error getting severity distribution: {e}")
        raise HTTPException(status_code=500, detail="Failed to get severity distribution")

@router.post("/export")
async def export_events(
    export_request: ExportRequest,
    user: dict = Depends(get_current_user)
):
    """Export events in specified format"""
    try:
        filters = None
        if export_request.filters:
            filters = export_request.filters.dict(exclude_unset=True)
        
        # Get events for export
        events = await database.get_events(
            limit=export_request.filters.limit if export_request.filters else 1000,
            offset=export_request.filters.offset if export_request.filters else 0,
            filters=filters
        )
        
        if export_request.format.lower() == 'csv':
            # Convert to CSV format
            import csv
            import io
            
            output = io.StringIO()
            if events:
                fieldnames = list(events[0].keys())
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                
                for event in events:
                    # Convert complex fields to strings
                    row = {}
                    for key, value in event.items():
                        if isinstance(value, (dict, list)):
                            row[key] = str(value)
                        else:
                            row[key] = value
                    writer.writerow(row)
            
            return {
                "format": "csv",
                "data": output.getvalue(),
                "count": len(events)
            }
        
        else:  # JSON format
            return {
                "format": "json",
                "data": events,
                "count": len(events)
            }
        
    except Exception as e:
        logger.error(f"Error exporting events: {e}")
        raise HTTPException(status_code=500, detail="Failed to export events")
