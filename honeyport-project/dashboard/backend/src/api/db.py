"""
Database operations for the dashboard API
"""

import asyncio
import logging
import aiosqlite
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class Database:
    """Database interface for dashboard API"""
    
    def __init__(self, db_url: str):
        self.db_url = db_url.replace('sqlite:///', '')
        self.db = None
        
    async def initialize(self):
        """Initialize database connection and create tables"""
        try:
            self.db = await aiosqlite.connect(self.db_url)
            await self._create_tables()
            logger.info(f"Database initialized: {self.db_url}")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def _create_tables(self):
        """Create database tables"""
        # Events table (same as honeypot recorder)
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                source_ip TEXT NOT NULL,
                source_port INTEGER,
                destination_port INTEGER NOT NULL,
                protocol TEXT NOT NULL,
                severity TEXT DEFAULT 'low',
                attack_type TEXT,
                data TEXT,
                enriched_data TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Blocked IPs table
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS blocked_ips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip_address TEXT UNIQUE NOT NULL,
                reason TEXT NOT NULL,
                blocked_by TEXT DEFAULT 'system',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Agent status table
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS agents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT UNIQUE NOT NULL,
                status TEXT NOT NULL,
                last_seen DATETIME NOT NULL,
                version TEXT,
                location TEXT,
                listeners TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes
        await self.db.execute('CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)')
        await self.db.execute('CREATE INDEX IF NOT EXISTS idx_events_source_ip ON events(source_ip)')
        await self.db.execute('CREATE INDEX IF NOT EXISTS idx_blocked_ips_ip ON blocked_ips(ip_address)')
        
        await self.db.commit()
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics"""
        try:
            stats = {}
            
            # Total events
            cursor = await self.db.execute('SELECT COUNT(*) FROM events')
            stats['total_events'] = (await cursor.fetchone())[0]
            
            # Events by type
            cursor = await self.db.execute('''
                SELECT event_type, COUNT(*) 
                FROM events 
                GROUP BY event_type
            ''')
            stats['events_by_type'] = dict(await cursor.fetchall())
            
            # Events by severity
            cursor = await self.db.execute('''
                SELECT severity, COUNT(*) 
                FROM events 
                GROUP BY severity
            ''')
            stats['events_by_severity'] = dict(await cursor.fetchall())
            
            # Top source IPs
            cursor = await self.db.execute('''
                SELECT source_ip, COUNT(*) as count
                FROM events 
                GROUP BY source_ip 
                ORDER BY count DESC 
                LIMIT 10
            ''')
            stats['top_source_ips'] = await cursor.fetchall()
            
            # Recent activity (last 24 hours)
            cursor = await self.db.execute('''
                SELECT COUNT(*) 
                FROM events 
                WHERE datetime(timestamp) > datetime('now', '-1 day')
            ''')
            stats['events_last_24h'] = (await cursor.fetchone())[0]
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}
    
    async def get_events(self, limit: int = 100, offset: int = 0, 
                        filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get events with optional filtering"""
        try:
            query = 'SELECT * FROM events'
            params = []
            
            if filters:
                conditions = []
                if filters.get('source_ip'):
                    conditions.append('source_ip = ?')
                    params.append(filters['source_ip'])
                if filters.get('event_type'):
                    conditions.append('event_type = ?')
                    params.append(filters['event_type'])
                if filters.get('severity'):
                    conditions.append('severity = ?')
                    params.append(filters['severity'])
                if filters.get('start_time'):
                    conditions.append('timestamp >= ?')
                    params.append(filters['start_time'])
                if filters.get('end_time'):
                    conditions.append('timestamp <= ?')
                    params.append(filters['end_time'])
                
                if conditions:
                    query += ' WHERE ' + ' AND '.join(conditions)
            
            query += ' ORDER BY timestamp DESC LIMIT ? OFFSET ?'
            params.extend([limit, offset])
            
            cursor = await self.db.execute(query, params)
            rows = await cursor.fetchall()
            
            # Convert to dictionaries
            columns = [desc[0] for desc in cursor.description]
            events = []
            
            for row in rows:
                event = dict(zip(columns, row))
                # Parse JSON fields
                if event.get('data'):
                    try:
                        event['data'] = json.loads(event['data'])
                    except json.JSONDecodeError:
                        pass
                if event.get('enriched_data'):
                    try:
                        event['enriched_data'] = json.loads(event['enriched_data'])
                    except json.JSONDecodeError:
                        pass
                events.append(event)
            
            return events
            
        except Exception as e:
            logger.error(f"Failed to get events: {e}")
            return []
    
    async def get_geographic_stats(self) -> List[Dict[str, Any]]:
        """Get geographic distribution of events"""
        try:
            # This would typically query enriched_data for geo information
            cursor = await self.db.execute('''
                SELECT enriched_data, COUNT(*) as event_count
                FROM events 
                WHERE enriched_data IS NOT NULL
                GROUP BY enriched_data
            ''')
            
            geo_stats = []
            for row in await cursor.fetchall():
                enriched_data_str, event_count = row
                try:
                    enriched_data = json.loads(enriched_data_str)
                    geo_data = enriched_data.get('geo', {})
                    
                    if geo_data.get('latitude') and geo_data.get('longitude'):
                        geo_stats.append({
                            'latitude': geo_data['latitude'],
                            'longitude': geo_data['longitude'],
                            'country': geo_data.get('country', 'Unknown'),
                            'country_code': geo_data.get('country_code', 'XX'),
                            'event_count': event_count
                        })
                except json.JSONDecodeError:
                    continue
            
            return geo_stats
            
        except Exception as e:
            logger.error(f"Failed to get geographic stats: {e}")
            return []
    
    async def add_blocked_ip(self, ip_address: str, reason: str, blocked_by: str = 'admin'):
        """Add IP to blocked list"""
        try:
            await self.db.execute('''
                INSERT OR REPLACE INTO blocked_ips (ip_address, reason, blocked_by)
                VALUES (?, ?, ?)
            ''', (ip_address, reason, blocked_by))
            
            await self.db.commit()
            logger.info(f"Blocked IP: {ip_address}")
            
        except Exception as e:
            logger.error(f"Failed to block IP {ip_address}: {e}")
            raise
    
    async def get_blocked_ips(self) -> List[Dict[str, Any]]:
        """Get list of blocked IPs"""
        try:
            cursor = await self.db.execute('''
                SELECT ip_address, reason, blocked_by, created_at
                FROM blocked_ips
                ORDER BY created_at DESC
            ''')
            
            rows = await cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            return [dict(zip(columns, row)) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get blocked IPs: {e}")
            return []
    
    async def remove_blocked_ip(self, ip_address: str):
        """Remove IP from blocked list"""
        try:
            await self.db.execute('DELETE FROM blocked_ips WHERE ip_address = ?', (ip_address,))
            await self.db.commit()
            logger.info(f"Unblocked IP: {ip_address}")
            
        except Exception as e:
            logger.error(f"Failed to unblock IP {ip_address}: {e}")
            raise
    
    async def update_agent_status(self, agent_id: str, status: str, version: str = None, 
                                 location: str = None, listeners: List[str] = None):
        """Update agent status"""
        try:
            listeners_json = json.dumps(listeners) if listeners else None
            
            await self.db.execute('''
                INSERT OR REPLACE INTO agents 
                (agent_id, status, last_seen, version, location, listeners)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (agent_id, status, datetime.utcnow().isoformat(), version, location, listeners_json))
            
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to update agent status: {e}")
    
    async def get_agents(self) -> List[Dict[str, Any]]:
        """Get agent status information"""
        try:
            cursor = await self.db.execute('''
                SELECT agent_id, status, last_seen, version, location, listeners
                FROM agents
                ORDER BY last_seen DESC
            ''')
            
            rows = await cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            agents = []
            for row in rows:
                agent = dict(zip(columns, row))
                if agent.get('listeners'):
                    try:
                        agent['listeners'] = json.loads(agent['listeners'])
                    except json.JSONDecodeError:
                        agent['listeners'] = []
                agents.append(agent)
            
            return agents
            
        except Exception as e:
            logger.error(f"Failed to get agents: {e}")
            return []
    
    async def search_events(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search events by text query"""
        try:
            # Simple text search in data and enriched_data fields
            base_query = '''
                SELECT * FROM events 
                WHERE (data LIKE ? OR enriched_data LIKE ? OR source_ip LIKE ?)
            '''
            
            search_term = f'%{query}%'
            params = [search_term, search_term, search_term]
            
            # Add filters if provided
            if filters:
                if filters.get('event_type'):
                    base_query += ' AND event_type = ?'
                    params.append(filters['event_type'])
                if filters.get('severity'):
                    base_query += ' AND severity = ?'
                    params.append(filters['severity'])
            
            base_query += ' ORDER BY timestamp DESC LIMIT 100'
            
            cursor = await self.db.execute(base_query, params)
            rows = await cursor.fetchall()
            
            columns = [desc[0] for desc in cursor.description]
            events = []
            
            for row in rows:
                event = dict(zip(columns, row))
                # Parse JSON fields
                if event.get('data'):
                    try:
                        event['data'] = json.loads(event['data'])
                    except json.JSONDecodeError:
                        pass
                if event.get('enriched_data'):
                    try:
                        event['enriched_data'] = json.loads(event['enriched_data'])
                    except json.JSONDecodeError:
                        pass
                events.append(event)
            
            return events
            
        except Exception as e:
            logger.error(f"Failed to search events: {e}")
            return []
    
    async def cleanup(self):
        """Cleanup database connection"""
        if self.db:
            await self.db.close()
            logger.info("Database cleanup completed")
