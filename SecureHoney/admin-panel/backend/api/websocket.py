"""
WebSocket endpoints for real-time communication
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from typing import Dict, List, Optional
import json
import uuid
import asyncio
from datetime import datetime
import structlog

from ..core.security import verify_token
from ..core.database import get_db
from ..core.redis import get_redis

logger = structlog.get_logger()
router = APIRouter()

class ConnectionManager:
    """Enhanced WebSocket connection manager"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[str, List[str]] = {}
        self.connection_metadata: Dict[str, Dict] = {}
        self.subscriptions: Dict[str, List[str]] = {}  # connection_id -> [channels]
        
    async def connect(self, websocket: WebSocket, connection_id: str, user_id: Optional[str] = None, metadata: Optional[Dict] = None):
        """Connect a WebSocket client"""
        await websocket.accept()
        
        self.active_connections[connection_id] = websocket
        self.connection_metadata[connection_id] = {
            "user_id": user_id,
            "connected_at": datetime.utcnow(),
            "metadata": metadata or {}
        }
        
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = []
            self.user_connections[user_id].append(connection_id)
        
        logger.info("websocket_connected", 
                   connection_id=connection_id, 
                   user_id=user_id,
                   total_connections=len(self.active_connections))
        
        # Send welcome message
        await self.send_personal_message({
            "type": "connection_established",
            "connection_id": connection_id,
            "timestamp": datetime.utcnow().isoformat()
        }, connection_id)

    def disconnect(self, connection_id: str):
        """Disconnect a WebSocket client"""
        if connection_id not in self.active_connections:
            return
            
        metadata = self.connection_metadata.get(connection_id, {})
        user_id = metadata.get("user_id")
        
        # Remove from active connections
        del self.active_connections[connection_id]
        del self.connection_metadata[connection_id]
        
        # Remove subscriptions
        if connection_id in self.subscriptions:
            del self.subscriptions[connection_id]
        
        # Remove from user connections
        if user_id and user_id in self.user_connections:
            if connection_id in self.user_connections[user_id]:
                self.user_connections[user_id].remove(connection_id)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        logger.info("websocket_disconnected", 
                   connection_id=connection_id, 
                   user_id=user_id,
                   total_connections=len(self.active_connections))

    async def send_personal_message(self, message: Dict, connection_id: str):
        """Send message to specific connection"""
        if connection_id not in self.active_connections:
            return False
            
        try:
            websocket = self.active_connections[connection_id]
            await websocket.send_text(json.dumps(message))
            return True
        except Exception as e:
            logger.error("websocket_send_failed", 
                        connection_id=connection_id, 
                        error=str(e))
            self.disconnect(connection_id)
            return False

    async def send_to_user(self, message: Dict, user_id: str):
        """Send message to all connections of a user"""
        if user_id not in self.user_connections:
            return 0
            
        sent_count = 0
        for connection_id in self.user_connections[user_id].copy():
            if await self.send_personal_message(message, connection_id):
                sent_count += 1
        
        return sent_count

    async def broadcast(self, message: Dict, exclude_connections: Optional[List[str]] = None):
        """Broadcast message to all connections"""
        exclude_connections = exclude_connections or []
        sent_count = 0
        
        for connection_id in list(self.active_connections.keys()):
            if connection_id not in exclude_connections:
                if await self.send_personal_message(message, connection_id):
                    sent_count += 1
        
        return sent_count

    async def broadcast_to_channel(self, message: Dict, channel: str):
        """Broadcast message to all connections subscribed to a channel"""
        sent_count = 0
        
        for connection_id, channels in self.subscriptions.items():
            if channel in channels:
                if await self.send_personal_message(message, connection_id):
                    sent_count += 1
        
        return sent_count

    def subscribe(self, connection_id: str, channel: str):
        """Subscribe connection to a channel"""
        if connection_id not in self.subscriptions:
            self.subscriptions[connection_id] = []
        
        if channel not in self.subscriptions[connection_id]:
            self.subscriptions[connection_id].append(channel)
            logger.info("websocket_subscribed", 
                       connection_id=connection_id, 
                       channel=channel)

    def unsubscribe(self, connection_id: str, channel: str):
        """Unsubscribe connection from a channel"""
        if connection_id in self.subscriptions:
            if channel in self.subscriptions[connection_id]:
                self.subscriptions[connection_id].remove(channel)
                logger.info("websocket_unsubscribed", 
                           connection_id=connection_id, 
                           channel=channel)

    def get_stats(self) -> Dict:
        """Get connection statistics"""
        return {
            "total_connections": len(self.active_connections),
            "unique_users": len(self.user_connections),
            "total_subscriptions": sum(len(channels) for channels in self.subscriptions.values()),
            "channels": list(set(channel for channels in self.subscriptions.values() for channel in channels))
        }

# Global connection manager
manager = ConnectionManager()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: Optional[str] = None):
    """Main WebSocket endpoint"""
    connection_id = str(uuid.uuid4())
    user_id = None
    
    # Verify token if provided
    if token:
        try:
            import jwt
            from ..core.config import config
            payload = jwt.decode(token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])
            user_id = payload.get("user_id")
        except Exception as e:
            logger.warning("websocket_auth_failed", error=str(e))
    
    await manager.connect(websocket, connection_id, user_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                await handle_websocket_message(message, connection_id, user_id)
            except json.JSONDecodeError:
                await manager.send_personal_message({
                    "type": "error",
                    "message": "Invalid JSON format"
                }, connection_id)
            except Exception as e:
                logger.error("websocket_message_error", 
                            connection_id=connection_id, 
                            error=str(e))
                await manager.send_personal_message({
                    "type": "error",
                    "message": "Message processing failed"
                }, connection_id)
                
    except WebSocketDisconnect:
        manager.disconnect(connection_id)
    except Exception as e:
        logger.error("websocket_connection_error", 
                    connection_id=connection_id, 
                    error=str(e))
        manager.disconnect(connection_id)

async def handle_websocket_message(message: Dict, connection_id: str, user_id: Optional[str]):
    """Handle incoming WebSocket messages"""
    message_type = message.get("type")
    
    if message_type == "ping":
        await manager.send_personal_message({
            "type": "pong",
            "timestamp": datetime.utcnow().isoformat()
        }, connection_id)
    
    elif message_type == "subscribe":
        channel = message.get("channel")
        if channel:
            manager.subscribe(connection_id, channel)
            await manager.send_personal_message({
                "type": "subscribed",
                "channel": channel
            }, connection_id)
    
    elif message_type == "unsubscribe":
        channel = message.get("channel")
        if channel:
            manager.unsubscribe(connection_id, channel)
            await manager.send_personal_message({
                "type": "unsubscribed",
                "channel": channel
            }, connection_id)
    
    elif message_type == "get_stats":
        stats = manager.get_stats()
        await manager.send_personal_message({
            "type": "stats",
            "data": stats
        }, connection_id)
    
    else:
        await manager.send_personal_message({
            "type": "error",
            "message": f"Unknown message type: {message_type}"
        }, connection_id)

# Background task for periodic updates
async def periodic_updates():
    """Send periodic updates to connected clients"""
    while True:
        try:
            # Send stats update every 30 seconds
            await asyncio.sleep(30)
            
            stats_update = {
                "type": "stats_update",
                "data": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "connections": manager.get_stats()
                }
            }
            
            await manager.broadcast_to_channel(stats_update, "stats")
            
        except Exception as e:
            logger.error("periodic_updates_error", error=str(e))
            await asyncio.sleep(60)

# Utility functions for other modules to use
async def broadcast_attack_alert(attack_data: Dict):
    """Broadcast new attack alert to all connected clients"""
    message = {
        "type": "attack_alert",
        "data": attack_data,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    sent_count = await manager.broadcast_to_channel(message, "attacks")
    logger.info("attack_alert_broadcasted", sent_count=sent_count)

async def broadcast_system_alert(alert_data: Dict):
    """Broadcast system alert to all connected clients"""
    message = {
        "type": "system_alert",
        "data": alert_data,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    sent_count = await manager.broadcast_to_channel(message, "alerts")
    logger.info("system_alert_broadcasted", sent_count=sent_count)

async def send_user_notification(user_id: str, notification: Dict):
    """Send notification to specific user"""
    message = {
        "type": "notification",
        "data": notification,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    sent_count = await manager.send_to_user(message, user_id)
    logger.info("user_notification_sent", user_id=user_id, sent_count=sent_count)

# Get connection manager for other modules
def get_connection_manager() -> ConnectionManager:
    """Get the global connection manager"""
    return manager
