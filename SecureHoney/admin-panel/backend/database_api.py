#!/usr/bin/env python3
"""
SecureHoney Admin Panel Database API
Enhanced API endpoints for database analytics and visualization
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import sys
import os

# Add database path to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../shared-utils/database'))

from database_integration import honeypot_db
from analytics import HackerPatternAnalyzer
from geolocation import GeolocationService

router = APIRouter(prefix="/api/database", tags=["database"])

@router.get("/statistics")
async def get_database_statistics():
    """Get comprehensive database statistics"""
    try:
        stats = honeypot_db.get_dashboard_data()
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/attacks/search")
async def search_attacks(
    source_ip: Optional[str] = Query(None),
    attack_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    target_port: Optional[int] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    limit: int = Query(100, le=1000)
):
    """Search attacks with advanced filtering"""
    try:
        criteria = {}
        
        if source_ip:
            criteria['source_ip'] = source_ip
        if attack_type:
            criteria['attack_type'] = attack_type
        if severity:
            criteria['severity'] = severity
        if target_port:
            criteria['target_port'] = target_port
        if date_from:
            criteria['date_from'] = datetime.fromisoformat(date_from)
        if date_to:
            criteria['date_to'] = datetime.fromisoformat(date_to)
        
        results = honeypot_db.search_attacks(criteria)
        
        return {
            "success": True,
            "total_results": len(results),
            "attacks": results[:limit]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/attackers/{ip_address}/profile")
async def get_attacker_profile(ip_address: str):
    """Get detailed attacker profile and analysis"""
    try:
        profile = honeypot_db.analyzer.generate_threat_profile(ip_address)
        
        if 'error' in profile:
            raise HTTPException(status_code=404, detail=profile['error'])
        
        return {
            "success": True,
            "profile": profile
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/patterns/analysis")
async def get_attack_patterns(
    ip_address: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365)
):
    """Get comprehensive attack pattern analysis"""
    try:
        patterns = honeypot_db.analyzer.analyze_attack_patterns(
            ip_address=ip_address,
            days=days
        )
        
        return {
            "success": True,
            "analysis_period": days,
            "target_ip": ip_address,
            "patterns": patterns
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/geographic/analysis")
async def get_geographic_analysis(days: int = Query(30, ge=1, le=365)):
    """Get geographic attack pattern analysis"""
    try:
        geo_analysis = honeypot_db.geo_service.analyze_geographic_patterns(days)
        
        return {
            "success": True,
            "geographic_analysis": geo_analysis
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/geographic/heatmap")
async def get_attack_heatmap():
    """Get attack heatmap data for visualization"""
    try:
        heatmap_data = honeypot_db.geo_service.get_attack_heatmap_data()
        
        return {
            "success": True,
            "heatmap_points": heatmap_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reports/daily")
async def get_daily_report(date: Optional[str] = Query(None)):
    """Get daily security report"""
    try:
        report_date = datetime.fromisoformat(date).date() if date else datetime.utcnow().date()
        report = honeypot_db.reporter.generate_daily_report(report_date)
        
        return {
            "success": True,
            "report": report
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/threat-intelligence/export")
async def export_threat_intelligence():
    """Export threat intelligence data"""
    try:
        intel_data = honeypot_db.export_threat_intelligence()
        
        return {
            "success": True,
            "threat_intelligence": intel_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/attackers/top-threats")
async def get_top_threats(limit: int = Query(20, ge=1, le=100)):
    """Get top threat actors"""
    try:
        session = honeypot_db.db.get_session()
        from models import AttackerProfile
        
        top_threats = session.query(AttackerProfile).filter(
            AttackerProfile.threat_level.in_(['HIGH', 'CRITICAL'])
        ).order_by(
            AttackerProfile.reputation_score.desc(),
            AttackerProfile.total_attacks.desc()
        ).limit(limit).all()
        
        threat_list = []
        for threat in top_threats:
            threat_list.append({
                'ip_address': threat.source_ip,
                'threat_level': threat.threat_level,
                'reputation_score': threat.reputation_score,
                'total_attacks': threat.total_attacks,
                'skill_level': threat.skill_level,
                'first_seen': threat.first_seen.isoformat(),
                'last_seen': threat.last_seen.isoformat(),
                'preferred_ports': threat.preferred_ports,
                'attack_types': threat.attack_patterns.get('types', []) if threat.attack_patterns else []
            })
        
        honeypot_db.db.close_session(session)
        
        return {
            "success": True,
            "top_threats": threat_list
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/trends")
async def get_attack_trends(
    period: str = Query("24h", regex="^(1h|6h|24h|7d|30d)$"),
    metric: str = Query("attacks", regex="^(attacks|unique_ips|severity|ports)$")
):
    """Get attack trends and analytics"""
    try:
        # Convert period to hours
        period_hours = {
            "1h": 1, "6h": 6, "24h": 24, "7d": 168, "30d": 720
        }[period]
        
        session = honeypot_db.db.get_session()
        from models import Attack
        from sqlalchemy import func
        
        since_time = datetime.utcnow() - timedelta(hours=period_hours)
        
        if metric == "attacks":
            # Hourly attack counts
            trends = session.query(
                func.date_trunc('hour', Attack.timestamp).label('hour'),
                func.count(Attack.id).label('count')
            ).filter(
                Attack.timestamp >= since_time
            ).group_by(
                func.date_trunc('hour', Attack.timestamp)
            ).order_by('hour').all()
            
            trend_data = [
                {
                    'timestamp': hour.isoformat(),
                    'value': count
                }
                for hour, count in trends
            ]
            
        elif metric == "unique_ips":
            # Unique attackers over time
            trends = session.query(
                func.date_trunc('hour', Attack.timestamp).label('hour'),
                func.count(func.distinct(Attack.source_ip)).label('count')
            ).filter(
                Attack.timestamp >= since_time
            ).group_by(
                func.date_trunc('hour', Attack.timestamp)
            ).order_by('hour').all()
            
            trend_data = [
                {
                    'timestamp': hour.isoformat(),
                    'value': count
                }
                for hour, count in trends
            ]
            
        elif metric == "severity":
            # Severity distribution over time
            trends = session.query(
                func.date_trunc('hour', Attack.timestamp).label('hour'),
                Attack.severity,
                func.count(Attack.id).label('count')
            ).filter(
                Attack.timestamp >= since_time
            ).group_by(
                func.date_trunc('hour', Attack.timestamp),
                Attack.severity
            ).order_by('hour').all()
            
            # Group by hour and severity
            trend_data = {}
            for hour, severity, count in trends:
                hour_str = hour.isoformat()
                if hour_str not in trend_data:
                    trend_data[hour_str] = {}
                trend_data[hour_str][severity] = count
        
        else:  # ports
            # Most targeted ports over time
            trends = session.query(
                func.date_trunc('hour', Attack.timestamp).label('hour'),
                Attack.target_port,
                func.count(Attack.id).label('count')
            ).filter(
                Attack.timestamp >= since_time
            ).group_by(
                func.date_trunc('hour', Attack.timestamp),
                Attack.target_port
            ).order_by('hour').all()
            
            # Group by hour and port
            trend_data = {}
            for hour, port, count in trends:
                hour_str = hour.isoformat()
                if hour_str not in trend_data:
                    trend_data[hour_str] = {}
                trend_data[hour_str][str(port)] = count
        
        honeypot_db.db.close_session(session)
        
        return {
            "success": True,
            "period": period,
            "metric": metric,
            "trends": trend_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/maintenance/cleanup")
async def cleanup_old_data(days_to_keep: int = Query(90, ge=7, le=365)):
    """Clean up old database records"""
    try:
        honeypot_db.cleanup_old_data(days_to_keep)
        
        return {
            "success": True,
            "message": f"Cleanup completed. Data older than {days_to_keep} days removed."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/interactions/detailed")
async def get_detailed_interactions(
    attack_id: Optional[str] = Query(None),
    service_type: Optional[str] = Query(None),
    limit: int = Query(50, le=200)
):
    """Get detailed honeypot interactions"""
    try:
        session = honeypot_db.db.get_session()
        from models import HoneypotInteraction
        
        query = session.query(HoneypotInteraction)
        
        if attack_id:
            query = query.filter(HoneypotInteraction.attack_id == attack_id)
        if service_type:
            query = query.filter(HoneypotInteraction.service_type == service_type)
        
        interactions = query.order_by(
            HoneypotInteraction.timestamp.desc()
        ).limit(limit).all()
        
        interaction_data = []
        for interaction in interactions:
            interaction_data.append({
                'id': interaction.id,
                'attack_id': interaction.attack_id,
                'service_type': interaction.service_type,
                'interaction_type': interaction.interaction_type,
                'timestamp': interaction.timestamp.isoformat(),
                'username_attempted': interaction.username_attempted,
                'password_attempted': interaction.password_attempted,
                'command_executed': interaction.command_executed,
                'file_uploaded': interaction.file_uploaded,
                'http_method': interaction.http_method,
                'http_path': interaction.http_path,
                'response_code': interaction.response_code,
                'interaction_success': interaction.interaction_success,
                'data_extracted': interaction.data_extracted
            })
        
        honeypot_db.db.close_session(session)
        
        return {
            "success": True,
            "interactions": interaction_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/malware/samples")
async def get_malware_samples(limit: int = Query(50, le=200)):
    """Get collected malware samples"""
    try:
        session = honeypot_db.db.get_session()
        from models import MalwareAnalysis
        
        samples = session.query(MalwareAnalysis).order_by(
            MalwareAnalysis.upload_timestamp.desc()
        ).limit(limit).all()
        
        sample_data = []
        for sample in samples:
            sample_data.append({
                'file_hash': sample.file_hash,
                'file_name': sample.file_name,
                'file_size': sample.file_size,
                'file_type': sample.file_type,
                'upload_timestamp': sample.upload_timestamp.isoformat(),
                'source_ip': sample.source_ip,
                'malware_family': sample.malware_family,
                'threat_level': sample.threat_level,
                'analysis_status': sample.analysis_status
            })
        
        honeypot_db.db.close_session(session)
        
        return {
            "success": True,
            "malware_samples": sample_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
