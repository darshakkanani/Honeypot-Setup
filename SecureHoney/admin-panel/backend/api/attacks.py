"""
Attack management and analysis endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, func, and_, or_
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import structlog

from ..core.database import get_db
from ..core.security import verify_token, require_admin
from ..core.redis import RedisCache
from .websocket import broadcast_attack_alert

logger = structlog.get_logger()
router = APIRouter(prefix="/api/attacks", tags=["attacks"])

class AttackFilter(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    severity: Optional[str] = None
    attack_type: Optional[str] = None
    source_ip: Optional[str] = None
    target_port: Optional[int] = None
    country: Optional[str] = None
    blocked: Optional[bool] = None
    limit: int = 100
    offset: int = 0

class AttackAnalysis(BaseModel):
    attack_id: str
    analysis_type: str
    confidence_score: float
    threat_level: str
    recommendations: List[str]

@router.get("/")
async def get_attacks(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    severity: Optional[str] = Query(None),
    attack_type: Optional[str] = Query(None),
    source_ip: Optional[str] = Query(None),
    target_port: Optional[int] = Query(None),
    country: Optional[str] = Query(None),
    blocked: Optional[bool] = Query(None),
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0, ge=0),
    username: str = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Get attacks with advanced filtering"""
    try:
        # Build dynamic query
        conditions = []
        params = []
        param_count = 0
        
        if start_date:
            param_count += 1
            conditions.append(f"created_at >= ${param_count}")
            params.append(start_date)
        
        if end_date:
            param_count += 1
            conditions.append(f"created_at <= ${param_count}")
            params.append(end_date)
        
        if severity:
            param_count += 1
            conditions.append(f"severity = ${param_count}")
            params.append(severity)
        
        if attack_type:
            param_count += 1
            conditions.append(f"attack_type = ${param_count}")
            params.append(attack_type)
        
        if source_ip:
            param_count += 1
            conditions.append(f"source_ip = ${param_count}")
            params.append(source_ip)
        
        if target_port:
            param_count += 1
            conditions.append(f"target_port = ${param_count}")
            params.append(target_port)
        
        if country:
            param_count += 1
            conditions.append(f"country = ${param_count}")
            params.append(country)
        
        if blocked is not None:
            param_count += 1
            conditions.append(f"blocked = ${param_count}")
            params.append(blocked)
        
        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        
        # Get total count
        count_query = f"SELECT COUNT(*) FROM attacks{where_clause}"
        count_result = await db.execute(text(count_query), params)
        total_count = count_result.scalar()
        
        # Get attacks
        param_count += 1
        offset_param = f"${param_count}"
        param_count += 1
        limit_param = f"${param_count}"
        
        query = f"""
            SELECT 
                id, source_ip, target_port, attack_type, severity,
                created_at, blocked, country, city, latitude, longitude,
                confidence_score, payload_size, session_duration, details,
                user_agent, request_headers, response_code
            FROM attacks
            {where_clause}
            ORDER BY created_at DESC
            OFFSET {offset_param} LIMIT {limit_param}
        """
        
        params.extend([offset, limit])
        result = await db.execute(text(query), params)
        
        attacks = []
        for row in result.fetchall():
            attacks.append({
                "id": str(row.id),
                "source_ip": row.source_ip,
                "target_port": row.target_port,
                "attack_type": row.attack_type,
                "severity": row.severity,
                "timestamp": row.created_at.isoformat(),
                "blocked": row.blocked,
                "location": {
                    "country": row.country,
                    "city": row.city,
                    "coordinates": {
                        "latitude": float(row.latitude) if row.latitude else None,
                        "longitude": float(row.longitude) if row.longitude else None
                    }
                },
                "confidence_score": float(row.confidence_score) if row.confidence_score else 0.0,
                "payload_size": row.payload_size,
                "session_duration": row.session_duration,
                "details": row.details or {},
                "user_agent": row.user_agent,
                "request_headers": row.request_headers or {},
                "response_code": row.response_code
            })
        
        return {
            "attacks": attacks,
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "filters": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
                "severity": severity,
                "attack_type": attack_type,
                "source_ip": source_ip,
                "target_port": target_port,
                "country": country,
                "blocked": blocked
            }
        }
        
    except Exception as e:
        logger.error("get_attacks_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch attacks")

@router.get("/{attack_id}")
async def get_attack_details(
    attack_id: str,
    username: str = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed information about a specific attack"""
    try:
        query = """
            SELECT 
                a.*,
                ap.threat_score, ap.risk_level, ap.first_seen, ap.last_seen,
                ap.total_attacks, ap.blocked_count, ap.countries, ap.attack_types
            FROM attacks a
            LEFT JOIN attacker_profiles ap ON a.source_ip = ap.ip_address
            WHERE a.id = $1
        """
        
        result = await db.execute(text(query), [attack_id])
        row = result.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Attack not found")
        
        # Get related attacks from same IP
        related_query = """
            SELECT id, attack_type, severity, created_at
            FROM attacks
            WHERE source_ip = $1 AND id != $2
            ORDER BY created_at DESC
            LIMIT 10
        """
        
        related_result = await db.execute(text(related_query), [row.source_ip, attack_id])
        related_attacks = []
        
        for related_row in related_result.fetchall():
            related_attacks.append({
                "id": str(related_row.id),
                "attack_type": related_row.attack_type,
                "severity": related_row.severity,
                "timestamp": related_row.created_at.isoformat()
            })
        
        attack_details = {
            "id": str(row.id),
            "source_ip": row.source_ip,
            "target_port": row.target_port,
            "attack_type": row.attack_type,
            "severity": row.severity,
            "timestamp": row.created_at.isoformat(),
            "blocked": row.blocked,
            "location": {
                "country": row.country,
                "city": row.city,
                "coordinates": {
                    "latitude": float(row.latitude) if row.latitude else None,
                    "longitude": float(row.longitude) if row.longitude else None
                }
            },
            "confidence_score": float(row.confidence_score) if row.confidence_score else 0.0,
            "payload_size": row.payload_size,
            "session_duration": row.session_duration,
            "details": row.details or {},
            "user_agent": row.user_agent,
            "request_headers": row.request_headers or {},
            "response_code": row.response_code,
            "raw_payload": row.raw_payload,
            "attacker_profile": {
                "threat_score": float(row.threat_score) if row.threat_score else None,
                "risk_level": row.risk_level,
                "first_seen": row.first_seen.isoformat() if row.first_seen else None,
                "last_seen": row.last_seen.isoformat() if row.last_seen else None,
                "total_attacks": row.total_attacks,
                "blocked_count": row.blocked_count,
                "countries": row.countries or [],
                "attack_types": row.attack_types or []
            },
            "related_attacks": related_attacks
        }
        
        return attack_details
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_attack_details_error", attack_id=attack_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch attack details")

@router.post("/{attack_id}/block")
async def block_attack_source(
    attack_id: str,
    background_tasks: BackgroundTasks,
    username: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Block the source IP of an attack"""
    try:
        # Get attack details
        attack_query = "SELECT source_ip FROM attacks WHERE id = $1"
        result = await db.execute(text(attack_query), [attack_id])
        attack = result.fetchone()
        
        if not attack:
            raise HTTPException(status_code=404, detail="Attack not found")
        
        source_ip = attack.source_ip
        
        # Update attack as blocked
        await db.execute(
            text("UPDATE attacks SET blocked = true WHERE source_ip = $1"),
            [source_ip]
        )
        
        # Add to blocked IPs table
        await db.execute(text("""
            INSERT INTO blocked_ips (ip_address, blocked_by, reason, created_at)
            VALUES ($1, $2, $3, NOW())
            ON CONFLICT (ip_address) DO UPDATE SET
                blocked_by = $2,
                reason = $3,
                updated_at = NOW()
        """), [source_ip, username, f"Manual block from attack {attack_id}"])
        
        await db.commit()
        
        # Cache blocked IP in Redis
        await RedisCache.set(f"blocked_ip:{source_ip}", "true", expire=86400)
        
        # Broadcast alert
        background_tasks.add_task(broadcast_attack_alert, {
            "type": "ip_blocked",
            "source_ip": source_ip,
            "blocked_by": username,
            "attack_id": attack_id
        })
        
        logger.info("ip_blocked", source_ip=source_ip, blocked_by=username, attack_id=attack_id)
        
        return {
            "message": f"IP {source_ip} has been blocked",
            "source_ip": source_ip,
            "blocked_by": username
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("block_attack_error", attack_id=attack_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to block attack source")

@router.delete("/{attack_id}/unblock")
async def unblock_attack_source(
    attack_id: str,
    background_tasks: BackgroundTasks,
    username: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Unblock the source IP of an attack"""
    try:
        # Get attack details
        attack_query = "SELECT source_ip FROM attacks WHERE id = $1"
        result = await db.execute(text(attack_query), [attack_id])
        attack = result.fetchone()
        
        if not attack:
            raise HTTPException(status_code=404, detail="Attack not found")
        
        source_ip = attack.source_ip
        
        # Update attacks as unblocked
        await db.execute(
            text("UPDATE attacks SET blocked = false WHERE source_ip = $1"),
            [source_ip]
        )
        
        # Remove from blocked IPs table
        await db.execute(
            text("DELETE FROM blocked_ips WHERE ip_address = $1"),
            [source_ip]
        )
        
        await db.commit()
        
        # Remove from Redis cache
        await RedisCache.delete(f"blocked_ip:{source_ip}")
        
        # Broadcast alert
        background_tasks.add_task(broadcast_attack_alert, {
            "type": "ip_unblocked",
            "source_ip": source_ip,
            "unblocked_by": username,
            "attack_id": attack_id
        })
        
        logger.info("ip_unblocked", source_ip=source_ip, unblocked_by=username, attack_id=attack_id)
        
        return {
            "message": f"IP {source_ip} has been unblocked",
            "source_ip": source_ip,
            "unblocked_by": username
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("unblock_attack_error", attack_id=attack_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to unblock attack source")

@router.get("/statistics/summary")
async def get_attack_statistics(
    period: str = Query(default="24h", regex="^(1h|6h|24h|7d|30d)$"),
    username: str = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive attack statistics"""
    try:
        # Convert period to interval
        interval_map = {
            "1h": "1 hour",
            "6h": "6 hours",
            "24h": "24 hours", 
            "7d": "7 days",
            "30d": "30 days"
        }
        
        interval = interval_map[period]
        
        # Get basic statistics
        stats_query = f"""
            SELECT 
                COUNT(*) as total_attacks,
                COUNT(DISTINCT source_ip) as unique_attackers,
                COUNT(CASE WHEN severity = 'CRITICAL' THEN 1 END) as critical_attacks,
                COUNT(CASE WHEN severity = 'HIGH' THEN 1 END) as high_attacks,
                COUNT(CASE WHEN severity = 'MEDIUM' THEN 1 END) as medium_attacks,
                COUNT(CASE WHEN severity = 'LOW' THEN 1 END) as low_attacks,
                COUNT(CASE WHEN blocked = true THEN 1 END) as blocked_attacks,
                AVG(confidence_score) as avg_confidence,
                AVG(payload_size) as avg_payload_size,
                AVG(session_duration) as avg_session_duration
            FROM attacks
            WHERE created_at >= NOW() - INTERVAL '{interval}'
        """
        
        result = await db.execute(text(stats_query))
        stats = result.fetchone()
        
        # Get attack type distribution
        type_query = f"""
            SELECT attack_type, COUNT(*) as count
            FROM attacks
            WHERE created_at >= NOW() - INTERVAL '{interval}'
            GROUP BY attack_type
            ORDER BY count DESC
        """
        
        type_result = await db.execute(text(type_query))
        attack_types = {}
        for row in type_result.fetchall():
            attack_types[row.attack_type] = row.count
        
        # Get top source countries
        country_query = f"""
            SELECT country, COUNT(*) as count
            FROM attacks
            WHERE created_at >= NOW() - INTERVAL '{interval}'
            AND country IS NOT NULL
            GROUP BY country
            ORDER BY count DESC
            LIMIT 10
        """
        
        country_result = await db.execute(text(country_query))
        top_countries = []
        for row in country_result.fetchall():
            top_countries.append({
                "country": row.country,
                "attack_count": row.count
            })
        
        # Get top target ports
        port_query = f"""
            SELECT target_port, COUNT(*) as count
            FROM attacks
            WHERE created_at >= NOW() - INTERVAL '{interval}'
            GROUP BY target_port
            ORDER BY count DESC
            LIMIT 10
        """
        
        port_result = await db.execute(text(port_query))
        top_ports = []
        for row in port_result.fetchall():
            top_ports.append({
                "port": row.target_port,
                "attack_count": row.count
            })
        
        return {
            "period": period,
            "statistics": {
                "total_attacks": stats.total_attacks or 0,
                "unique_attackers": stats.unique_attackers or 0,
                "critical_attacks": stats.critical_attacks or 0,
                "high_attacks": stats.high_attacks or 0,
                "medium_attacks": stats.medium_attacks or 0,
                "low_attacks": stats.low_attacks or 0,
                "blocked_attacks": stats.blocked_attacks or 0,
                "avg_confidence": float(stats.avg_confidence) if stats.avg_confidence else 0.0,
                "avg_payload_size": float(stats.avg_payload_size) if stats.avg_payload_size else 0.0,
                "avg_session_duration": float(stats.avg_session_duration) if stats.avg_session_duration else 0.0
            },
            "attack_types": attack_types,
            "top_countries": top_countries,
            "top_ports": top_ports
        }
        
    except Exception as e:
        logger.error("get_attack_statistics_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch attack statistics")

@router.post("/{attack_id}/analyze")
async def analyze_attack(
    attack_id: str,
    analysis: AttackAnalysis,
    username: str = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Add analysis to an attack"""
    try:
        # Verify attack exists
        attack_query = "SELECT id FROM attacks WHERE id = $1"
        result = await db.execute(text(attack_query), [attack_id])
        
        if not result.fetchone():
            raise HTTPException(status_code=404, detail="Attack not found")
        
        # Insert analysis
        await db.execute(text("""
            INSERT INTO attack_analysis 
            (attack_id, analysis_type, confidence_score, threat_level, recommendations, analyzed_by, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, NOW())
        """), [
            attack_id, analysis.analysis_type, analysis.confidence_score,
            analysis.threat_level, analysis.recommendations, username
        ])
        
        await db.commit()
        
        logger.info("attack_analyzed", attack_id=attack_id, analyzed_by=username)
        
        return {
            "message": "Attack analysis added successfully",
            "attack_id": attack_id,
            "analysis": analysis.dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("analyze_attack_error", attack_id=attack_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to analyze attack")

@router.get("/export/csv")
async def export_attacks_csv(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    severity: Optional[str] = Query(None),
    username: str = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Export attacks to CSV format"""
    try:
        # Build query with filters
        conditions = []
        params = []
        param_count = 0
        
        if start_date:
            param_count += 1
            conditions.append(f"created_at >= ${param_count}")
            params.append(start_date)
        
        if end_date:
            param_count += 1
            conditions.append(f"created_at <= ${param_count}")
            params.append(end_date)
        
        if severity:
            param_count += 1
            conditions.append(f"severity = ${param_count}")
            params.append(severity)
        
        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        
        query = f"""
            SELECT 
                id, source_ip, target_port, attack_type, severity,
                created_at, blocked, country, city, confidence_score
            FROM attacks
            {where_clause}
            ORDER BY created_at DESC
            LIMIT 10000
        """
        
        result = await db.execute(text(query), params)
        
        # Generate CSV content
        csv_lines = ["ID,Source IP,Target Port,Attack Type,Severity,Timestamp,Blocked,Country,City,Confidence Score"]
        
        for row in result.fetchall():
            csv_lines.append(f"{row.id},{row.source_ip},{row.target_port},{row.attack_type},{row.severity},{row.created_at},{row.blocked},{row.country or ''},{row.city or ''},{row.confidence_score or 0}")
        
        csv_content = "\n".join(csv_lines)
        
        return {
            "filename": f"attacks_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "content": csv_content,
            "total_records": len(csv_lines) - 1
        }
        
    except Exception as e:
        logger.error("export_attacks_csv_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to export attacks")
