"""
Advanced Reporting and Analytics Engine
Comprehensive attack analytics, trend analysis, and executive reporting
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
from dataclasses import dataclass, asdict
import structlog
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import io
import base64

from ..core.config import config
from ..core.database import get_db
from ..core.redis import RedisCache
from ..models.attack import Attack
from ..models.system import SystemMetrics

logger = structlog.get_logger()

@dataclass
class ReportMetrics:
    """Report metrics data structure"""
    total_attacks: int
    unique_attackers: int
    blocked_attacks: int
    threat_score_avg: float
    geographic_distribution: Dict[str, int]
    attack_type_distribution: Dict[str, int]
    hourly_distribution: Dict[int, int]
    top_attack_sources: List[Dict[str, Any]]
    severity_breakdown: Dict[str, int]
    response_effectiveness: Dict[str, float]

@dataclass
class TrendAnalysis:
    """Trend analysis results"""
    period: str
    growth_rate: float
    seasonal_patterns: Dict[str, float]
    anomalies: List[Dict[str, Any]]
    predictions: Dict[str, float]
    confidence_intervals: Dict[str, Tuple[float, float]]

class AdvancedReportingEngine:
    """Advanced analytics and reporting engine"""
    
    def __init__(self):
        self.report_cache_ttl = 3600  # 1 hour
        self.supported_formats = ["json", "pdf", "html", "csv", "excel"]
        self.chart_themes = {
            "dark": "plotly_dark",
            "light": "plotly_white",
            "corporate": "seaborn"
        }
        
        # Analytics models
        self.trend_models = {}
        self.anomaly_detectors = {}
        
        # Report templates
        self.report_templates = self._load_report_templates()
        
    async def initialize(self):
        """Initialize reporting engine"""
        try:
            # Load historical data for trend analysis
            await self._initialize_trend_models()
            
            # Load anomaly detection models
            await self._initialize_anomaly_detectors()
            
            # Start background report generation
            asyncio.create_task(self._scheduled_report_generator())
            
            logger.info("reporting_engine_initialized")
            
        except Exception as e:
            logger.error("reporting_engine_init_failed", error=str(e))
    
    async def generate_executive_report(self, 
                                      period_days: int = 30,
                                      format: str = "json") -> Dict[str, Any]:
        """Generate executive summary report"""
        try:
            # Check cache first
            cache_key = f"exec_report:{period_days}:{format}"
            cached = await RedisCache.get(cache_key)
            if cached:
                return json.loads(cached)
            
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=period_days)
            
            # Gather comprehensive metrics
            metrics = await self._gather_executive_metrics(start_date, end_date)
            
            # Generate trend analysis
            trends = await self._analyze_attack_trends(start_date, end_date)
            
            # Risk assessment
            risk_assessment = await self._generate_risk_assessment(metrics, trends)
            
            # ROI analysis
            roi_analysis = await self._calculate_security_roi(start_date, end_date)
            
            # Recommendations
            recommendations = await self._generate_recommendations(metrics, trends, risk_assessment)
            
            # Compliance status
            compliance = await self._assess_compliance_status()
            
            report = {
                "report_type": "executive_summary",
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": period_days
                },
                "executive_summary": {
                    "key_findings": await self._extract_key_findings(metrics, trends),
                    "threat_landscape": await self._analyze_threat_landscape(metrics),
                    "security_posture": await self._assess_security_posture(metrics, trends),
                    "business_impact": await self._calculate_business_impact(metrics)
                },
                "metrics": asdict(metrics),
                "trend_analysis": asdict(trends),
                "risk_assessment": risk_assessment,
                "roi_analysis": roi_analysis,
                "recommendations": recommendations,
                "compliance_status": compliance,
                "charts": await self._generate_executive_charts(metrics, trends),
                "generated_at": datetime.utcnow().isoformat(),
                "format": format
            }
            
            # Format report based on requested format
            if format != "json":
                report = await self._format_report(report, format)
            
            # Cache report
            await RedisCache.set(cache_key, json.dumps(report), expire=self.report_cache_ttl)
            
            logger.info("executive_report_generated", 
                       period_days=period_days,
                       format=format,
                       total_attacks=metrics.total_attacks)
            
            return report
            
        except Exception as e:
            logger.error("executive_report_failed", error=str(e))
            return {"error": str(e)}
    
    async def generate_technical_report(self, 
                                      attack_types: List[str] = None,
                                      period_days: int = 7,
                                      include_raw_data: bool = False) -> Dict[str, Any]:
        """Generate detailed technical analysis report"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=period_days)
            
            # Detailed attack analysis
            attack_analysis = await self._analyze_attack_patterns(
                start_date, end_date, attack_types
            )
            
            # Payload analysis
            payload_analysis = await self._analyze_attack_payloads(
                start_date, end_date, attack_types
            )
            
            # Attribution analysis
            attribution = await self._analyze_threat_attribution(
                start_date, end_date
            )
            
            # IOC analysis
            ioc_analysis = await self._analyze_indicators_of_compromise(
                start_date, end_date
            )
            
            # Network analysis
            network_analysis = await self._analyze_network_patterns(
                start_date, end_date
            )
            
            # ML model performance
            ml_performance = await self._analyze_ml_performance(
                start_date, end_date
            )
            
            report = {
                "report_type": "technical_analysis",
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": period_days
                },
                "filters": {
                    "attack_types": attack_types or "all",
                    "include_raw_data": include_raw_data
                },
                "attack_analysis": attack_analysis,
                "payload_analysis": payload_analysis,
                "threat_attribution": attribution,
                "ioc_analysis": ioc_analysis,
                "network_analysis": network_analysis,
                "ml_performance": ml_performance,
                "technical_charts": await self._generate_technical_charts(
                    attack_analysis, payload_analysis, network_analysis
                ),
                "generated_at": datetime.utcnow().isoformat()
            }
            
            # Include raw data if requested
            if include_raw_data:
                report["raw_data"] = await self._extract_raw_attack_data(
                    start_date, end_date, attack_types
                )
            
            logger.info("technical_report_generated", 
                       period_days=period_days,
                       attack_types=len(attack_types) if attack_types else "all")
            
            return report
            
        except Exception as e:
            logger.error("technical_report_failed", error=str(e))
            return {"error": str(e)}
    
    async def generate_compliance_report(self, 
                                       framework: str = "iso27001",
                                       period_days: int = 90) -> Dict[str, Any]:
        """Generate compliance and audit report"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=period_days)
            
            # Framework-specific requirements
            requirements = self._get_compliance_requirements(framework)
            
            # Assess compliance status
            compliance_status = {}
            for req_id, requirement in requirements.items():
                status = await self._assess_requirement_compliance(
                    requirement, start_date, end_date
                )
                compliance_status[req_id] = status
            
            # Generate evidence
            evidence = await self._collect_compliance_evidence(
                requirements, start_date, end_date
            )
            
            # Risk and gap analysis
            gaps = await self._identify_compliance_gaps(compliance_status)
            risks = await self._assess_compliance_risks(gaps)
            
            # Remediation plan
            remediation = await self._generate_remediation_plan(gaps, risks)
            
            report = {
                "report_type": "compliance_audit",
                "framework": framework,
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": period_days
                },
                "overall_compliance_score": self._calculate_compliance_score(compliance_status),
                "compliance_status": compliance_status,
                "evidence_summary": evidence,
                "gap_analysis": gaps,
                "risk_assessment": risks,
                "remediation_plan": remediation,
                "audit_trail": await self._generate_audit_trail(start_date, end_date),
                "generated_at": datetime.utcnow().isoformat()
            }
            
            logger.info("compliance_report_generated", 
                       framework=framework,
                       compliance_score=report["overall_compliance_score"])
            
            return report
            
        except Exception as e:
            logger.error("compliance_report_failed", error=str(e))
            return {"error": str(e)}
    
    async def _gather_executive_metrics(self, start_date: datetime, end_date: datetime) -> ReportMetrics:
        """Gather comprehensive metrics for executive reporting"""
        try:
            async with get_db() as db:
                # Query attack data
                attacks = await db.execute("""
                    SELECT * FROM attacks 
                    WHERE timestamp BETWEEN %s AND %s
                """, (start_date, end_date))
                
                attack_data = attacks.fetchall()
                
                if not attack_data:
                    return ReportMetrics(
                        total_attacks=0, unique_attackers=0, blocked_attacks=0,
                        threat_score_avg=0.0, geographic_distribution={},
                        attack_type_distribution={}, hourly_distribution={},
                        top_attack_sources=[], severity_breakdown={},
                        response_effectiveness={}
                    )
                
                # Convert to DataFrame for analysis
                df = pd.DataFrame(attack_data)
                
                # Calculate metrics
                total_attacks = len(df)
                unique_attackers = df['source_ip'].nunique()
                blocked_attacks = len(df[df['blocked'] == True])
                threat_score_avg = df['threat_score'].mean() if 'threat_score' in df.columns else 0.0
                
                # Geographic distribution
                geo_dist = df.groupby('country').size().to_dict() if 'country' in df.columns else {}
                
                # Attack type distribution
                attack_type_dist = df.groupby('attack_type').size().to_dict()
                
                # Hourly distribution
                df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
                hourly_dist = df.groupby('hour').size().to_dict()
                
                # Top attack sources
                top_sources = df.groupby('source_ip').agg({
                    'id': 'count',
                    'threat_score': 'mean',
                    'severity': lambda x: x.mode().iloc[0] if not x.empty else 'unknown'
                }).rename(columns={'id': 'attack_count'}).reset_index()
                top_sources = top_sources.nlargest(10, 'attack_count').to_dict('records')
                
                # Severity breakdown
                severity_breakdown = df.groupby('severity').size().to_dict()
                
                # Response effectiveness (placeholder - would need response data)
                response_effectiveness = {
                    "block_success_rate": 0.95,
                    "alert_response_time": 120,
                    "mitigation_effectiveness": 0.87
                }
                
                return ReportMetrics(
                    total_attacks=total_attacks,
                    unique_attackers=unique_attackers,
                    blocked_attacks=blocked_attacks,
                    threat_score_avg=threat_score_avg,
                    geographic_distribution=geo_dist,
                    attack_type_distribution=attack_type_dist,
                    hourly_distribution=hourly_dist,
                    top_attack_sources=top_sources,
                    severity_breakdown=severity_breakdown,
                    response_effectiveness=response_effectiveness
                )
                
        except Exception as e:
            logger.error("metrics_gathering_failed", error=str(e))
            return ReportMetrics(
                total_attacks=0, unique_attackers=0, blocked_attacks=0,
                threat_score_avg=0.0, geographic_distribution={},
                attack_type_distribution={}, hourly_distribution={},
                top_attack_sources=[], severity_breakdown={},
                response_effectiveness={}
            )
    
    async def _analyze_attack_trends(self, start_date: datetime, end_date: datetime) -> TrendAnalysis:
        """Analyze attack trends and patterns"""
        try:
            async with get_db() as db:
                # Get historical data for trend analysis
                historical_data = await db.execute("""
                    SELECT DATE(timestamp) as date, COUNT(*) as attack_count,
                           AVG(threat_score) as avg_threat_score
                    FROM attacks 
                    WHERE timestamp BETWEEN %s AND %s
                    GROUP BY DATE(timestamp)
                    ORDER BY date
                """, (start_date, end_date))
                
                df = pd.DataFrame(historical_data.fetchall())
                
                if df.empty:
                    return TrendAnalysis(
                        period=f"{start_date.date()}_to_{end_date.date()}",
                        growth_rate=0.0, seasonal_patterns={},
                        anomalies=[], predictions={},
                        confidence_intervals={}
                    )
                
                # Calculate growth rate
                if len(df) > 1:
                    first_week = df.head(7)['attack_count'].mean()
                    last_week = df.tail(7)['attack_count'].mean()
                    growth_rate = ((last_week - first_week) / first_week * 100) if first_week > 0 else 0
                else:
                    growth_rate = 0.0
                
                # Seasonal patterns (day of week, hour of day)
                seasonal_patterns = await self._detect_seasonal_patterns(df)
                
                # Anomaly detection
                anomalies = await self._detect_anomalies(df)
                
                # Simple predictions (next 7 days)
                predictions = await self._generate_predictions(df)
                
                # Confidence intervals
                confidence_intervals = await self._calculate_confidence_intervals(df, predictions)
                
                return TrendAnalysis(
                    period=f"{start_date.date()}_to_{end_date.date()}",
                    growth_rate=growth_rate,
                    seasonal_patterns=seasonal_patterns,
                    anomalies=anomalies,
                    predictions=predictions,
                    confidence_intervals=confidence_intervals
                )
                
        except Exception as e:
            logger.error("trend_analysis_failed", error=str(e))
            return TrendAnalysis(
                period=f"{start_date.date()}_to_{end_date.date()}",
                growth_rate=0.0, seasonal_patterns={},
                anomalies=[], predictions={},
                confidence_intervals={}
            )
    
    async def _generate_executive_charts(self, metrics: ReportMetrics, trends: TrendAnalysis) -> Dict[str, str]:
        """Generate executive-level charts"""
        try:
            charts = {}
            
            # Attack trend chart
            if trends.predictions:
                fig = go.Figure()
                dates = list(trends.predictions.keys())
                values = list(trends.predictions.values())
                
                fig.add_trace(go.Scatter(
                    x=dates, y=values,
                    mode='lines+markers',
                    name='Attack Trend',
                    line=dict(color='#FF6B6B', width=3)
                ))
                
                fig.update_layout(
                    title="Attack Trend Analysis",
                    xaxis_title="Date",
                    yaxis_title="Number of Attacks",
                    template="plotly_white"
                )
                
                charts["attack_trend"] = self._fig_to_base64(fig)
            
            # Geographic distribution pie chart
            if metrics.geographic_distribution:
                fig = px.pie(
                    values=list(metrics.geographic_distribution.values()),
                    names=list(metrics.geographic_distribution.keys()),
                    title="Attack Sources by Country"
                )
                charts["geographic_distribution"] = self._fig_to_base64(fig)
            
            # Attack type distribution bar chart
            if metrics.attack_type_distribution:
                fig = px.bar(
                    x=list(metrics.attack_type_distribution.keys()),
                    y=list(metrics.attack_type_distribution.values()),
                    title="Attack Types Distribution"
                )
                charts["attack_types"] = self._fig_to_base64(fig)
            
            # Hourly activity heatmap
            if metrics.hourly_distribution:
                hours = list(range(24))
                values = [metrics.hourly_distribution.get(h, 0) for h in hours]
                
                fig = go.Figure(data=go.Heatmap(
                    z=[values],
                    x=hours,
                    y=["Activity"],
                    colorscale="Reds"
                ))
                
                fig.update_layout(
                    title="Attack Activity by Hour",
                    xaxis_title="Hour of Day"
                )
                
                charts["hourly_activity"] = self._fig_to_base64(fig)
            
            return charts
            
        except Exception as e:
            logger.error("chart_generation_failed", error=str(e))
            return {}
    
    def _fig_to_base64(self, fig) -> str:
        """Convert plotly figure to base64 string"""
        try:
            img_bytes = fig.to_image(format="png", width=800, height=600)
            img_base64 = base64.b64encode(img_bytes).decode()
            return f"data:image/png;base64,{img_base64}"
        except Exception as e:
            logger.error("chart_conversion_failed", error=str(e))
            return ""
    
    def _load_report_templates(self) -> Dict[str, str]:
        """Load report templates"""
        return {
            "executive": """
            # Executive Security Report
            
            ## Executive Summary
            {executive_summary}
            
            ## Key Metrics
            {key_metrics}
            
            ## Risk Assessment
            {risk_assessment}
            
            ## Recommendations
            {recommendations}
            """,
            "technical": """
            # Technical Analysis Report
            
            ## Attack Analysis
            {attack_analysis}
            
            ## Payload Analysis
            {payload_analysis}
            
            ## Network Analysis
            {network_analysis}
            """,
            "compliance": """
            # Compliance Audit Report
            
            ## Compliance Status
            {compliance_status}
            
            ## Gap Analysis
            {gap_analysis}
            
            ## Remediation Plan
            {remediation_plan}
            """
        }
    
    async def get_reporting_statistics(self) -> Dict[str, Any]:
        """Get reporting engine statistics"""
        try:
            # Count generated reports
            report_counts = await RedisCache.get("report_counts") or "{}"
            report_counts = json.loads(report_counts)
            
            stats = {
                "reports_generated": {
                    "executive": report_counts.get("executive", 0),
                    "technical": report_counts.get("technical", 0),
                    "compliance": report_counts.get("compliance", 0)
                },
                "supported_formats": self.supported_formats,
                "cache_hit_rate": await self._calculate_cache_hit_rate(),
                "average_generation_time": await self._calculate_avg_generation_time(),
                "last_updated": datetime.utcnow().isoformat()
            }
            
            return stats
            
        except Exception as e:
            logger.error("reporting_stats_failed", error=str(e))
            return {}

# Global reporting engine instance
reporting_engine = AdvancedReportingEngine()

# Convenience functions
async def generate_executive_dashboard_report(days: int = 30) -> Dict[str, Any]:
    """Generate executive report for dashboard"""
    return await reporting_engine.generate_executive_report(period_days=days)

async def generate_attack_analysis_report(attack_types: List[str] = None, days: int = 7) -> Dict[str, Any]:
    """Generate technical attack analysis report"""
    return await reporting_engine.generate_technical_report(
        attack_types=attack_types, period_days=days
    )

async def generate_compliance_audit_report(framework: str = "iso27001", days: int = 90) -> Dict[str, Any]:
    """Generate compliance audit report"""
    return await reporting_engine.generate_compliance_report(
        framework=framework, period_days=days
    )

async def get_reporting_engine_stats() -> Dict[str, Any]:
    """Get reporting engine statistics"""
    return await reporting_engine.get_reporting_statistics()
