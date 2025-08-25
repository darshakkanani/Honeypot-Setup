#!/usr/bin/env python3
"""
SecureHoney Database Configuration
Database connection and configuration management
"""

import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path
import json
from urllib.parse import urlparse
import psycopg2
from psycopg2 import sql
import asyncpg

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseConfig:
    """Database configuration management"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or os.getenv('DB_CONFIG_FILE', 'database_config.json')
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load database configuration from file or environment"""
        config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', '5432')),
            'database': os.getenv('DB_NAME', 'securehoney'),
            'username': os.getenv('DB_USER', 'securehoney'),
            'password': os.getenv('DB_PASSWORD', 'securehoney123'),
            'schema': os.getenv('DB_SCHEMA', 'securehoney'),
            'pool_size': int(os.getenv('DB_POOL_SIZE', '10')),
            'max_overflow': int(os.getenv('DB_MAX_OVERFLOW', '20')),
            'pool_timeout': int(os.getenv('DB_POOL_TIMEOUT', '30')),
            'pool_recycle': int(os.getenv('DB_POOL_RECYCLE', '3600')),
            'ssl_mode': os.getenv('DB_SSL_MODE', 'prefer'),
            'ssl_cert': os.getenv('DB_SSL_CERT'),
            'ssl_key': os.getenv('DB_SSL_KEY'),
            'ssl_ca': os.getenv('DB_SSL_CA'),
            'application_name': 'SecureHoney-AdminPanel',
            'connect_timeout': int(os.getenv('DB_CONNECT_TIMEOUT', '10')),
            'command_timeout': int(os.getenv('DB_COMMAND_TIMEOUT', '60')),
            'auto_create_schema': os.getenv('DB_AUTO_CREATE_SCHEMA', 'true').lower() == 'true',
            'enable_logging': os.getenv('DB_ENABLE_LOGGING', 'false').lower() == 'true'
        }
        
        # Try to load from config file if it exists
        config_path = Path(self.config_file)
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    file_config = json.load(f)
                    config.update(file_config)
                logger.info(f"Loaded database config from {config_path}")
            except Exception as e:
                logger.warning(f"Failed to load config file {config_path}: {e}")
        
        return config
    
    def get_connection_string(self, async_driver: bool = False) -> str:
        """Get database connection string"""
        driver = 'postgresql+asyncpg' if async_driver else 'postgresql+psycopg2'
        
        conn_str = (
            f"{driver}://{self.config['username']}:{self.config['password']}"
            f"@{self.config['host']}:{self.config['port']}/{self.config['database']}"
        )
        
        # Add SSL parameters if configured
        params = []
        if self.config['ssl_mode']:
            params.append(f"sslmode={self.config['ssl_mode']}")
        if self.config['ssl_cert']:
            params.append(f"sslcert={self.config['ssl_cert']}")
        if self.config['ssl_key']:
            params.append(f"sslkey={self.config['ssl_key']}")
        if self.config['ssl_ca']:
            params.append(f"sslrootcert={self.config['ssl_ca']}")
        
        if params:
            conn_str += "?" + "&".join(params)
        
        return conn_str
    
    def get_async_connection_params(self) -> Dict[str, Any]:
        """Get asyncpg connection parameters"""
        params = {
            'host': self.config['host'],
            'port': self.config['port'],
            'database': self.config['database'],
            'user': self.config['username'],
            'password': self.config['password'],
            'command_timeout': self.config['command_timeout'],
            'server_settings': {
                'application_name': self.config['application_name'],
                'search_path': self.config['schema']
            }
        }
        
        # Add SSL parameters
        if self.config['ssl_mode'] != 'disable':
            ssl_context = {}
            if self.config['ssl_cert']:
                ssl_context['ssl_cert'] = self.config['ssl_cert']
            if self.config['ssl_key']:
                ssl_context['ssl_key'] = self.config['ssl_key']
            if self.config['ssl_ca']:
                ssl_context['ssl_ca'] = self.config['ssl_ca']
            
            if ssl_context:
                params['ssl'] = ssl_context
        
        return params
    
    def get_sqlalchemy_config(self) -> Dict[str, Any]:
        """Get SQLAlchemy engine configuration"""
        return {
            'pool_size': self.config['pool_size'],
            'max_overflow': self.config['max_overflow'],
            'pool_timeout': self.config['pool_timeout'],
            'pool_recycle': self.config['pool_recycle'],
            'pool_pre_ping': True,
            'echo': self.config['enable_logging'],
            'connect_args': {
                'connect_timeout': self.config['connect_timeout'],
                'application_name': self.config['application_name'],
                'options': f'-csearch_path={self.config["schema"]}'
            }
        }
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            conn = psycopg2.connect(
                host=self.config['host'],
                port=self.config['port'],
                database=self.config['database'],
                user=self.config['username'],
                password=self.config['password'],
                connect_timeout=self.config['connect_timeout']
            )
            
            with conn.cursor() as cursor:
                cursor.execute('SELECT version();')
                version = cursor.fetchone()[0]
                logger.info(f"Database connection successful: {version}")
            
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    async def test_async_connection(self) -> bool:
        """Test async database connection"""
        try:
            params = self.get_async_connection_params()
            conn = await asyncpg.connect(**params)
            
            version = await conn.fetchval('SELECT version();')
            logger.info(f"Async database connection successful: {version}")
            
            await conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Async database connection failed: {e}")
            return False
    
    def create_database_if_not_exists(self) -> bool:
        """Create database if it doesn't exist"""
        try:
            # Connect to postgres database to create our database
            conn = psycopg2.connect(
                host=self.config['host'],
                port=self.config['port'],
                database='postgres',
                user=self.config['username'],
                password=self.config['password'],
                connect_timeout=self.config['connect_timeout']
            )
            conn.autocommit = True
            
            with conn.cursor() as cursor:
                # Check if database exists
                cursor.execute(
                    "SELECT 1 FROM pg_database WHERE datname = %s",
                    (self.config['database'],)
                )
                
                if not cursor.fetchone():
                    # Create database
                    cursor.execute(
                        sql.SQL("CREATE DATABASE {}").format(
                            sql.Identifier(self.config['database'])
                        )
                    )
                    logger.info(f"Created database: {self.config['database']}")
                else:
                    logger.info(f"Database already exists: {self.config['database']}")
            
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Failed to create database: {e}")
            return False
    
    def create_schema_if_not_exists(self) -> bool:
        """Create schema if it doesn't exist"""
        try:
            conn = psycopg2.connect(
                host=self.config['host'],
                port=self.config['port'],
                database=self.config['database'],
                user=self.config['username'],
                password=self.config['password'],
                connect_timeout=self.config['connect_timeout']
            )
            
            with conn.cursor() as cursor:
                # Create schema
                cursor.execute(
                    sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(
                        sql.Identifier(self.config['schema'])
                    )
                )
                conn.commit()
                logger.info(f"Schema ensured: {self.config['schema']}")
            
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Failed to create schema: {e}")
            return False
    
    def save_config(self, config_path: Optional[str] = None) -> bool:
        """Save current configuration to file"""
        try:
            path = Path(config_path or self.config_file)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Remove sensitive data from saved config
            save_config = self.config.copy()
            save_config['password'] = '***REDACTED***'
            
            with open(path, 'w') as f:
                json.dump(save_config, f, indent=2)
            
            logger.info(f"Configuration saved to {path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False

class DatabaseHealthChecker:
    """Database health monitoring"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
    
    def check_health(self) -> Dict[str, Any]:
        """Comprehensive database health check"""
        health_status = {
            'status': 'healthy',
            'timestamp': None,
            'connection': False,
            'schema_exists': False,
            'tables_exist': False,
            'indexes_healthy': False,
            'performance_metrics': {},
            'warnings': [],
            'errors': []
        }
        
        try:
            from datetime import datetime
            health_status['timestamp'] = datetime.utcnow().isoformat()
            
            # Test connection
            if self.config.test_connection():
                health_status['connection'] = True
            else:
                health_status['errors'].append('Database connection failed')
                health_status['status'] = 'unhealthy'
                return health_status
            
            # Check schema and tables
            conn = psycopg2.connect(
                host=self.config.config['host'],
                port=self.config.config['port'],
                database=self.config.config['database'],
                user=self.config.config['username'],
                password=self.config.config['password']
            )
            
            with conn.cursor() as cursor:
                # Check schema exists
                cursor.execute(
                    "SELECT 1 FROM information_schema.schemata WHERE schema_name = %s",
                    (self.config.config['schema'],)
                )
                if cursor.fetchone():
                    health_status['schema_exists'] = True
                else:
                    health_status['warnings'].append('Schema does not exist')
                
                # Check critical tables exist
                critical_tables = [
                    'attacks', 'attacker_profiles', 'attack_sessions',
                    'admin_users', 'system_config'
                ]
                
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = %s AND table_name = ANY(%s)
                """, (self.config.config['schema'], critical_tables))
                
                existing_tables = [row[0] for row in cursor.fetchall()]
                missing_tables = set(critical_tables) - set(existing_tables)
                
                if not missing_tables:
                    health_status['tables_exist'] = True
                else:
                    health_status['warnings'].append(f'Missing tables: {list(missing_tables)}')
                
                # Check index health
                cursor.execute("""
                    SELECT schemaname, tablename, indexname, idx_tup_read, idx_tup_fetch
                    FROM pg_stat_user_indexes 
                    WHERE schemaname = %s
                """, (self.config.config['schema'],))
                
                index_stats = cursor.fetchall()
                if index_stats:
                    health_status['indexes_healthy'] = True
                    health_status['performance_metrics']['index_count'] = len(index_stats)
                
                # Get database size
                cursor.execute(
                    "SELECT pg_size_pretty(pg_database_size(%s))",
                    (self.config.config['database'],)
                )
                db_size = cursor.fetchone()[0]
                health_status['performance_metrics']['database_size'] = db_size
                
                # Get connection count
                cursor.execute(
                    "SELECT count(*) FROM pg_stat_activity WHERE datname = %s",
                    (self.config.config['database'],)
                )
                conn_count = cursor.fetchone()[0]
                health_status['performance_metrics']['active_connections'] = conn_count
            
            conn.close()
            
            # Determine overall status
            if health_status['errors']:
                health_status['status'] = 'unhealthy'
            elif health_status['warnings']:
                health_status['status'] = 'degraded'
            
        except Exception as e:
            health_status['errors'].append(f'Health check failed: {str(e)}')
            health_status['status'] = 'unhealthy'
        
        return health_status

# Global configuration instance
db_config = DatabaseConfig()

# Convenience functions
def get_connection_string(async_driver: bool = False) -> str:
    """Get database connection string"""
    return db_config.get_connection_string(async_driver)

def get_sqlalchemy_config() -> Dict[str, Any]:
    """Get SQLAlchemy configuration"""
    return db_config.get_sqlalchemy_config()

def test_connection() -> bool:
    """Test database connection"""
    return db_config.test_connection()

def initialize_database() -> bool:
    """Initialize database and schema"""
    try:
        # Create database if needed
        if db_config.config['auto_create_schema']:
            if not db_config.create_database_if_not_exists():
                return False
            
            if not db_config.create_schema_if_not_exists():
                return False
        
        # Test final connection
        return db_config.test_connection()
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False

def get_health_status() -> Dict[str, Any]:
    """Get database health status"""
    health_checker = DatabaseHealthChecker(db_config)
    return health_checker.check_health()
