"""
Pydantic models for API requests and responses
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime


class EventBase(BaseModel):
    """Base event model"""
    timestamp: str
    event_type: str
    source_ip: str
    source_port: Optional[int] = None
    destination_port: int
    protocol: str
    severity: str = "low"
    attack_type: Optional[str] = None


class EventCreate(EventBase):
    """Event creation model"""
    data: Optional[Dict[str, Any]] = None
    enriched_data: Optional[Dict[str, Any]] = None


class EventResponse(EventBase):
    """Event response model"""
    id: int
    data: Optional[Dict[str, Any]] = None
    enriched_data: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class HTTPEventResponse(BaseModel):
    """HTTP-specific event response"""
    id: int
    event_id: int
    method: Optional[str] = None
    path: Optional[str] = None
    user_agent: Optional[str] = None
    headers: Optional[Dict[str, Any]] = None
    body: Optional[str] = None
    query_params: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class SSHEventResponse(BaseModel):
    """SSH-specific event response"""
    id: int
    event_id: int
    username: Optional[str] = None
    password: Optional[str] = None
    auth_method: Optional[str] = None
    client_banner: Optional[str] = None
    server_banner: Optional[str] = None
    success: bool = False

    class Config:
        from_attributes = True


class AlertBase(BaseModel):
    """Base alert model"""
    alert_type: str
    severity: str
    message: str


class AlertCreate(AlertBase):
    """Alert creation model"""
    event_id: int


class AlertResponse(AlertBase):
    """Alert response model"""
    id: int
    event_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class StatsResponse(BaseModel):
    """Statistics response model"""
    total_events: int = 0
    events_by_type: Dict[str, int] = Field(default_factory=dict)
    events_by_severity: Dict[str, int] = Field(default_factory=dict)
    top_source_ips: List[tuple] = Field(default_factory=list)
    events_last_24h: int = 0
    active_events: int = 0


class ThreatMapPoint(BaseModel):
    """Threat map data point"""
    latitude: float
    longitude: float
    country: str
    country_code: str
    event_count: int
    severity_distribution: Dict[str, int]


class ThreatMapResponse(BaseModel):
    """Threat map response"""
    points: List[ThreatMapPoint]
    total_countries: int
    total_events: int


class BlockedIPBase(BaseModel):
    """Base blocked IP model"""
    ip_address: str
    reason: str


class BlockedIPCreate(BlockedIPBase):
    """Blocked IP creation model"""
    pass


class BlockedIPResponse(BlockedIPBase):
    """Blocked IP response model"""
    id: int
    created_at: datetime
    blocked_by: str

    class Config:
        from_attributes = True


class AgentStatus(BaseModel):
    """Agent status model"""
    agent_id: str
    status: str  # online, offline, error
    last_seen: datetime
    version: str
    location: Optional[str] = None
    listeners: List[str] = Field(default_factory=list)


class AgentResponse(BaseModel):
    """Agent response model"""
    agents: List[AgentStatus]
    total_agents: int
    online_agents: int


class EventFilter(BaseModel):
    """Event filtering model"""
    source_ip: Optional[str] = None
    event_type: Optional[str] = None
    severity: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    attack_type: Optional[str] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class SearchQuery(BaseModel):
    """Search query model"""
    query: str
    filters: Optional[EventFilter] = None
    search_type: str = "events"  # events, alerts, ips


class ExportRequest(BaseModel):
    """Export request model"""
    format: str = "csv"  # csv, json
    filters: Optional[EventFilter] = None
    include_enriched: bool = True
