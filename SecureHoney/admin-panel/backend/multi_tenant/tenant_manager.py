"""
Multi-Tenant Architecture for SecureHoney
Tenant isolation, resource management, and scalable deployment
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
import structlog
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import uuid

from ..core.config import config
from ..core.database import get_db
from ..core.redis import RedisCache
from ..models.user import User
from ..models.attack import Attack

logger = structlog.get_logger()

class TenantPlan(Enum):
    """Tenant subscription plans"""
    FREE = "free"
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"

class TenantStatus(Enum):
    """Tenant status"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    EXPIRED = "expired"

@dataclass
class TenantLimits:
    """Resource limits for tenant"""
    max_users: int
    max_honeypots: int
    max_attacks_per_month: int
    max_storage_gb: int
    max_api_calls_per_hour: int
    retention_days: int
    features: List[str]

@dataclass
class TenantUsage:
    """Current tenant resource usage"""
    users_count: int
    honeypots_count: int
    attacks_this_month: int
    storage_used_gb: float
    api_calls_this_hour: int
    last_activity: datetime

@dataclass
class Tenant:
    """Tenant configuration and metadata"""
    id: str
    name: str
    domain: str
    plan: TenantPlan
    status: TenantStatus
    created_at: datetime
    updated_at: datetime
    owner_email: str
    limits: TenantLimits
    usage: TenantUsage
    settings: Dict[str, Any]
    billing_info: Dict[str, Any]

class TenantIsolation:
    """Handles tenant data isolation and security"""
    
    def __init__(self):
        self.tenant_contexts = {}
        self.isolation_keys = {}
    
    async def get_tenant_context(self, tenant_id: str) -> Dict[str, Any]:
        """Get tenant-specific context"""
        if tenant_id not in self.tenant_contexts:
            context = await self._create_tenant_context(tenant_id)
            self.tenant_contexts[tenant_id] = context
        
        return self.tenant_contexts[tenant_id]
    
    async def _create_tenant_context(self, tenant_id: str) -> Dict[str, Any]:
        """Create isolated context for tenant"""
        return {
            "database_schema": f"tenant_{tenant_id}",
            "redis_prefix": f"tenant:{tenant_id}:",
            "storage_path": f"/data/tenants/{tenant_id}/",
            "encryption_key": self._generate_tenant_key(tenant_id),
            "api_namespace": f"/api/v1/tenant/{tenant_id}"
        }
    
    def _generate_tenant_key(self, tenant_id: str) -> str:
        """Generate tenant-specific encryption key"""
        base_key = config.MASTER_ENCRYPTION_KEY or "default_key"
        tenant_key = hashlib.sha256(f"{base_key}:{tenant_id}".encode()).hexdigest()
        return tenant_key[:32]  # 256-bit key
    
    async def isolate_query(self, query: str, tenant_id: str) -> str:
        """Add tenant isolation to database query"""
        context = await self.get_tenant_context(tenant_id)
        schema = context["database_schema"]
        
        # Add schema prefix to table names
        isolated_query = query.replace("FROM attacks", f"FROM {schema}.attacks")
        isolated_query = isolated_query.replace("FROM users", f"FROM {schema}.users")
        isolated_query = isolated_query.replace("FROM system_metrics", f"FROM {schema}.system_metrics")
        
        return isolated_query
    
    async def isolate_cache_key(self, key: str, tenant_id: str) -> str:
        """Add tenant isolation to cache keys"""
        context = await self.get_tenant_context(tenant_id)
        prefix = context["redis_prefix"]
        return f"{prefix}{key}"

class MultiTenantManager:
    """Main multi-tenant management system"""
    
    def __init__(self):
        self.tenants: Dict[str, Tenant] = {}
        self.tenant_limits = self._define_plan_limits()
        self.isolation = TenantIsolation()
        
        # Resource monitoring
        self.usage_monitors = {}
        self.billing_calculators = {}
        
        # Tenant metrics
        self.metrics = {
            "total_tenants": 0,
            "active_tenants": 0,
            "resource_utilization": {},
            "billing_totals": {}
        }
    
    async def initialize(self):
        """Initialize multi-tenant system"""
        try:
            # Load existing tenants
            await self._load_tenants()
            
            # Initialize tenant databases
            await self._initialize_tenant_databases()
            
            # Start monitoring processes
            asyncio.create_task(self._usage_monitor())
            asyncio.create_task(self._billing_calculator())
            asyncio.create_task(self._cleanup_expired_tenants())
            
            logger.info("multi_tenant_system_initialized", 
                       tenants=len(self.tenants))
                       
        except Exception as e:
            logger.error("multi_tenant_init_failed", error=str(e))
    
    async def create_tenant(self, 
                          name: str, 
                          domain: str, 
                          owner_email: str,
                          plan: TenantPlan = TenantPlan.FREE) -> Dict[str, Any]:
        """Create new tenant"""
        try:
            # Generate tenant ID
            tenant_id = str(uuid.uuid4())
            
            # Check domain availability
            if await self._domain_exists(domain):
                return {
                    "success": False,
                    "error": "Domain already exists"
                }
            
            # Create tenant configuration
            tenant = Tenant(
                id=tenant_id,
                name=name,
                domain=domain,
                plan=plan,
                status=TenantStatus.TRIAL,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                owner_email=owner_email,
                limits=self.tenant_limits[plan],
                usage=TenantUsage(
                    users_count=0,
                    honeypots_count=0,
                    attacks_this_month=0,
                    storage_used_gb=0.0,
                    api_calls_this_hour=0,
                    last_activity=datetime.utcnow()
                ),
                settings={
                    "timezone": "UTC",
                    "notification_preferences": {
                        "email_alerts": True,
                        "sms_alerts": False,
                        "webhook_url": None
                    },
                    "security_settings": {
                        "mfa_required": False,
                        "ip_whitelist": [],
                        "session_timeout": 3600
                    }
                },
                billing_info={
                    "billing_email": owner_email,
                    "payment_method": None,
                    "billing_cycle": "monthly",
                    "next_billing_date": None
                }
            )
            
            # Initialize tenant infrastructure
            await self._initialize_tenant_infrastructure(tenant)
            
            # Store tenant
            self.tenants[tenant_id] = tenant
            await self._store_tenant(tenant)
            
            # Create default admin user
            await self._create_tenant_admin(tenant, owner_email)
            
            # Update metrics
            self.metrics["total_tenants"] += 1
            if tenant.status == TenantStatus.ACTIVE:
                self.metrics["active_tenants"] += 1
            
            logger.info("tenant_created", 
                       tenant_id=tenant_id,
                       name=name,
                       domain=domain,
                       plan=plan.value)
            
            return {
                "success": True,
                "tenant_id": tenant_id,
                "tenant": asdict(tenant),
                "admin_setup_url": f"https://{domain}/setup/{tenant_id}"
            }
            
        except Exception as e:
            logger.error("tenant_creation_failed", 
                        name=name, 
                        domain=domain, 
                        error=str(e))
            return {"success": False, "error": str(e)}
    
    async def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID"""
        if tenant_id in self.tenants:
            return self.tenants[tenant_id]
        
        # Try loading from database
        tenant = await self._load_tenant(tenant_id)
        if tenant:
            self.tenants[tenant_id] = tenant
        
        return tenant
    
    async def update_tenant_usage(self, tenant_id: str, usage_type: str, increment: int = 1) -> bool:
        """Update tenant resource usage"""
        try:
            tenant = await self.get_tenant(tenant_id)
            if not tenant:
                return False
            
            # Update usage counters
            if usage_type == "attacks":
                tenant.usage.attacks_this_month += increment
            elif usage_type == "api_calls":
                tenant.usage.api_calls_this_hour += increment
            elif usage_type == "users":
                tenant.usage.users_count += increment
            elif usage_type == "honeypots":
                tenant.usage.honeypots_count += increment
            
            # Update last activity
            tenant.usage.last_activity = datetime.utcnow()
            
            # Check limits
            limit_exceeded = await self._check_usage_limits(tenant)
            if limit_exceeded:
                await self._handle_limit_exceeded(tenant, usage_type)
            
            # Store updated usage
            await self._store_tenant_usage(tenant)
            
            return True
            
        except Exception as e:
            logger.error("usage_update_failed", 
                        tenant_id=tenant_id, 
                        usage_type=usage_type, 
                        error=str(e))
            return False
    
    async def check_tenant_permissions(self, tenant_id: str, feature: str) -> bool:
        """Check if tenant has access to specific feature"""
        try:
            tenant = await self.get_tenant(tenant_id)
            if not tenant:
                return False
            
            # Check tenant status
            if tenant.status not in [TenantStatus.ACTIVE, TenantStatus.TRIAL]:
                return False
            
            # Check feature availability in plan
            if feature not in tenant.limits.features:
                return False
            
            # Check usage limits
            if await self._is_usage_limit_exceeded(tenant, feature):
                return False
            
            return True
            
        except Exception as e:
            logger.error("permission_check_failed", 
                        tenant_id=tenant_id, 
                        feature=feature, 
                        error=str(e))
            return False
    
    async def upgrade_tenant_plan(self, tenant_id: str, new_plan: TenantPlan) -> Dict[str, Any]:
        """Upgrade tenant to new plan"""
        try:
            tenant = await self.get_tenant(tenant_id)
            if not tenant:
                return {"success": False, "error": "Tenant not found"}
            
            old_plan = tenant.plan
            
            # Update plan and limits
            tenant.plan = new_plan
            tenant.limits = self.tenant_limits[new_plan]
            tenant.updated_at = datetime.utcnow()
            
            # If upgrading from trial, activate tenant
            if tenant.status == TenantStatus.TRIAL and new_plan != TenantPlan.FREE:
                tenant.status = TenantStatus.ACTIVE
            
            # Update billing information
            await self._update_billing_for_plan_change(tenant, old_plan, new_plan)
            
            # Store updated tenant
            await self._store_tenant(tenant)
            
            logger.info("tenant_plan_upgraded", 
                       tenant_id=tenant_id,
                       old_plan=old_plan.value,
                       new_plan=new_plan.value)
            
            return {
                "success": True,
                "old_plan": old_plan.value,
                "new_plan": new_plan.value,
                "new_limits": asdict(tenant.limits)
            }
            
        except Exception as e:
            logger.error("plan_upgrade_failed", 
                        tenant_id=tenant_id, 
                        new_plan=new_plan.value, 
                        error=str(e))
            return {"success": False, "error": str(e)}
    
    async def suspend_tenant(self, tenant_id: str, reason: str) -> Dict[str, Any]:
        """Suspend tenant access"""
        try:
            tenant = await self.get_tenant(tenant_id)
            if not tenant:
                return {"success": False, "error": "Tenant not found"}
            
            tenant.status = TenantStatus.SUSPENDED
            tenant.updated_at = datetime.utcnow()
            tenant.settings["suspension_reason"] = reason
            tenant.settings["suspended_at"] = datetime.utcnow().isoformat()
            
            # Store updated tenant
            await self._store_tenant(tenant)
            
            # Notify tenant
            await self._notify_tenant_suspension(tenant, reason)
            
            # Update metrics
            self.metrics["active_tenants"] -= 1
            
            logger.info("tenant_suspended", 
                       tenant_id=tenant_id,
                       reason=reason)
            
            return {"success": True, "reason": reason}
            
        except Exception as e:
            logger.error("tenant_suspension_failed", 
                        tenant_id=tenant_id, 
                        error=str(e))
            return {"success": False, "error": str(e)}
    
    def _define_plan_limits(self) -> Dict[TenantPlan, TenantLimits]:
        """Define resource limits for each plan"""
        return {
            TenantPlan.FREE: TenantLimits(
                max_users=2,
                max_honeypots=1,
                max_attacks_per_month=1000,
                max_storage_gb=1,
                max_api_calls_per_hour=100,
                retention_days=7,
                features=["basic_honeypots", "basic_analytics"]
            ),
            TenantPlan.BASIC: TenantLimits(
                max_users=5,
                max_honeypots=3,
                max_attacks_per_month=10000,
                max_storage_gb=10,
                max_api_calls_per_hour=1000,
                retention_days=30,
                features=["basic_honeypots", "basic_analytics", "email_alerts", "api_access"]
            ),
            TenantPlan.PROFESSIONAL: TenantLimits(
                max_users=20,
                max_honeypots=10,
                max_attacks_per_month=100000,
                max_storage_gb=100,
                max_api_calls_per_hour=10000,
                retention_days=90,
                features=[
                    "advanced_honeypots", "advanced_analytics", "threat_intelligence",
                    "automated_response", "custom_integrations", "priority_support"
                ]
            ),
            TenantPlan.ENTERPRISE: TenantLimits(
                max_users=-1,  # Unlimited
                max_honeypots=-1,  # Unlimited
                max_attacks_per_month=-1,  # Unlimited
                max_storage_gb=1000,
                max_api_calls_per_hour=100000,
                retention_days=365,
                features=[
                    "all_features", "blockchain_verification", "ml_analysis",
                    "compliance_reporting", "dedicated_support", "custom_deployment"
                ]
            )
        }
    
    async def _initialize_tenant_infrastructure(self, tenant: Tenant):
        """Initialize tenant-specific infrastructure"""
        try:
            # Create tenant database schema
            await self._create_tenant_schema(tenant.id)
            
            # Initialize tenant-specific tables
            await self._create_tenant_tables(tenant.id)
            
            # Set up tenant storage
            await self._create_tenant_storage(tenant.id)
            
            # Initialize tenant cache namespace
            await self._initialize_tenant_cache(tenant.id)
            
            logger.info("tenant_infrastructure_initialized", tenant_id=tenant.id)
            
        except Exception as e:
            logger.error("tenant_infrastructure_init_failed", 
                        tenant_id=tenant.id, 
                        error=str(e))
            raise
    
    async def get_tenant_statistics(self) -> Dict[str, Any]:
        """Get comprehensive tenant statistics"""
        try:
            # Plan distribution
            plan_distribution = {}
            status_distribution = {}
            
            for tenant in self.tenants.values():
                plan = tenant.plan.value
                status = tenant.status.value
                
                plan_distribution[plan] = plan_distribution.get(plan, 0) + 1
                status_distribution[status] = status_distribution.get(status, 0) + 1
            
            # Resource utilization
            total_usage = {
                "users": sum(t.usage.users_count for t in self.tenants.values()),
                "honeypots": sum(t.usage.honeypots_count for t in self.tenants.values()),
                "attacks": sum(t.usage.attacks_this_month for t in self.tenants.values()),
                "storage_gb": sum(t.usage.storage_used_gb for t in self.tenants.values())
            }
            
            # Revenue metrics (placeholder)
            revenue_metrics = {
                "monthly_recurring_revenue": 0,
                "annual_recurring_revenue": 0,
                "average_revenue_per_user": 0
            }
            
            stats = {
                "tenant_counts": {
                    "total": len(self.tenants),
                    "active": len([t for t in self.tenants.values() if t.status == TenantStatus.ACTIVE]),
                    "trial": len([t for t in self.tenants.values() if t.status == TenantStatus.TRIAL]),
                    "suspended": len([t for t in self.tenants.values() if t.status == TenantStatus.SUSPENDED])
                },
                "plan_distribution": plan_distribution,
                "status_distribution": status_distribution,
                "resource_utilization": total_usage,
                "revenue_metrics": revenue_metrics,
                "system_metrics": self.metrics,
                "last_updated": datetime.utcnow().isoformat()
            }
            
            return stats
            
        except Exception as e:
            logger.error("tenant_stats_failed", error=str(e))
            return {}

# Global multi-tenant manager instance
tenant_manager = MultiTenantManager()

# Convenience functions
async def get_tenant_by_id(tenant_id: str) -> Optional[Tenant]:
    """Get tenant by ID"""
    return await tenant_manager.get_tenant(tenant_id)

async def create_new_tenant(name: str, domain: str, owner_email: str, plan: str = "free") -> Dict[str, Any]:
    """Create new tenant"""
    plan_enum = TenantPlan(plan.lower())
    return await tenant_manager.create_tenant(name, domain, owner_email, plan_enum)

async def check_tenant_feature_access(tenant_id: str, feature: str) -> bool:
    """Check tenant feature access"""
    return await tenant_manager.check_tenant_permissions(tenant_id, feature)

async def update_tenant_resource_usage(tenant_id: str, resource: str, amount: int = 1) -> bool:
    """Update tenant resource usage"""
    return await tenant_manager.update_tenant_usage(tenant_id, resource, amount)

async def get_multi_tenant_statistics() -> Dict[str, Any]:
    """Get multi-tenant system statistics"""
    return await tenant_manager.get_tenant_statistics()
