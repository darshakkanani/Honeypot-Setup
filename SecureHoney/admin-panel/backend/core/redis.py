"""
Redis connection and utilities
"""

import redis.asyncio as redis
from typing import Optional
import structlog

from .config import config

logger = structlog.get_logger()

# Global Redis client
redis_client: Optional[redis.Redis] = None

async def init_redis() -> Optional[redis.Redis]:
    """Initialize Redis connection"""
    global redis_client
    
    try:
        if config.REDIS_PASSWORD:
            redis_client = redis.Redis(
                host=config.REDIS_HOST,
                port=config.REDIS_PORT,
                password=config.REDIS_PASSWORD,
                db=config.REDIS_DB,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
        else:
            redis_client = redis.Redis(
                host=config.REDIS_HOST,
                port=config.REDIS_PORT,
                db=config.REDIS_DB,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
        
        # Test connection
        await redis_client.ping()
        logger.info("redis_connected", host=config.REDIS_HOST, port=config.REDIS_PORT)
        return redis_client
        
    except Exception as e:
        logger.warning("redis_connection_failed", error=str(e))
        redis_client = None
        return None

async def close_redis():
    """Close Redis connection"""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None
        logger.info("redis_connection_closed")

async def get_redis() -> Optional[redis.Redis]:
    """Redis dependency for FastAPI"""
    return redis_client

class RedisCache:
    """Redis cache utilities"""
    
    @staticmethod
    async def get(key: str) -> Optional[str]:
        """Get value from Redis"""
        if redis_client:
            try:
                return await redis_client.get(key)
            except Exception as e:
                logger.error("redis_get_error", key=key, error=str(e))
        return None
    
    @staticmethod
    async def set(key: str, value: str, expire: Optional[int] = None) -> bool:
        """Set value in Redis with optional expiration"""
        if redis_client:
            try:
                if expire:
                    await redis_client.setex(key, expire, value)
                else:
                    await redis_client.set(key, value)
                return True
            except Exception as e:
                logger.error("redis_set_error", key=key, error=str(e))
        return False
    
    @staticmethod
    async def delete(key: str) -> bool:
        """Delete key from Redis"""
        if redis_client:
            try:
                await redis_client.delete(key)
                return True
            except Exception as e:
                logger.error("redis_delete_error", key=key, error=str(e))
        return False
    
    @staticmethod
    async def exists(key: str) -> bool:
        """Check if key exists in Redis"""
        if redis_client:
            try:
                return bool(await redis_client.exists(key))
            except Exception as e:
                logger.error("redis_exists_error", key=key, error=str(e))
        return False
