#!/usr/bin/env python3
"""
SecureHoney Database Initialization Script
Initialize database schema, create tables, and populate initial data
"""

import sys
import os
import logging
from pathlib import Path
import psycopg2
from psycopg2 import sql
import argparse
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent / 'shared-utils'))

from database.config import db_config, DatabaseHealthChecker
from database.models import DatabaseManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseInitializer:
    """Database initialization and setup"""
    
    def __init__(self, force_recreate: bool = False):
        self.config = db_config
        self.force_recreate = force_recreate
        self.schema_file = Path(__file__).parent / 'schema.sql'
        self.types_file = Path(__file__).parent.parent.parent / 'shared-utils' / 'database' / 'postgresql_types.sql'
    
    def initialize(self) -> bool:
        """Complete database initialization process"""
        try:
            logger.info("🚀 Starting SecureHoney database initialization...")
            
            # Step 1: Create database if needed
            if not self._create_database():
                return False
            
            # Step 2: Create schema
            if not self._create_schema():
                return False
            
            # Step 3: Install custom types
            if not self._install_custom_types():
                return False
            
            # Step 4: Create tables
            if not self._create_tables():
                return False
            
            # Step 5: Insert initial data
            if not self._insert_initial_data():
                return False
            
            # Step 6: Verify installation
            if not self._verify_installation():
                return False
            
            logger.info("✅ Database initialization completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            return False
    
    def _create_database(self) -> bool:
        """Create database if it doesn't exist"""
        try:
            logger.info("📊 Creating database...")
            return self.config.create_database_if_not_exists()
        except Exception as e:
            logger.error(f"Failed to create database: {e}")
            return False
    
    def _create_schema(self) -> bool:
        """Create schema if it doesn't exist"""
        try:
            logger.info("🏗️  Creating schema...")
            return self.config.create_schema_if_not_exists()
        except Exception as e:
            logger.error(f"Failed to create schema: {e}")
            return False
    
    def _install_custom_types(self) -> bool:
        """Install custom PostgreSQL types"""
        try:
            logger.info("🔧 Installing custom types...")
            
            if not self.types_file.exists():
                logger.warning(f"Types file not found: {self.types_file}")
                return True  # Continue without custom types
            
            conn = psycopg2.connect(
                host=self.config.config['host'],
                port=self.config.config['port'],
                database=self.config.config['database'],
                user=self.config.config['username'],
                password=self.config.config['password']
            )
            
            with conn.cursor() as cursor:
                # Set search path
                cursor.execute(f"SET search_path TO {self.config.config['schema']}, public;")
                
                # Read and execute types file
                with open(self.types_file, 'r') as f:
                    types_sql = f.read()
                
                # Execute in chunks to handle complex statements
                statements = [stmt.strip() for stmt in types_sql.split(';') if stmt.strip()]
                
                for statement in statements:
                    if statement:
                        try:
                            cursor.execute(statement)
                        except psycopg2.Error as e:
                            # Some statements might fail if types already exist
                            if 'already exists' not in str(e):
                                logger.warning(f"Type creation warning: {e}")
                
                conn.commit()
            
            conn.close()
            logger.info("✅ Custom types installed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to install custom types: {e}")
            return False
    
    def _create_tables(self) -> bool:
        """Create database tables from schema file"""
        try:
            logger.info("📋 Creating tables...")
            
            if not self.schema_file.exists():
                logger.error(f"Schema file not found: {self.schema_file}")
                return False
            
            conn = psycopg2.connect(
                host=self.config.config['host'],
                port=self.config.config['port'],
                database=self.config.config['database'],
                user=self.config.config['username'],
                password=self.config.config['password']
            )
            
            with conn.cursor() as cursor:
                # Set search path
                cursor.execute(f"SET search_path TO {self.config.config['schema']}, public;")
                
                # Read schema file
                with open(self.schema_file, 'r') as f:
                    schema_sql = f.read()
                
                # Replace include directive with actual file content
                if '\\i ' in schema_sql:
                    schema_sql = schema_sql.replace(
                        "\\i '../shared-utils/database/postgresql_types.sql';",
                        ""  # We already loaded types
                    )
                
                # Execute schema creation
                try:
                    cursor.execute(schema_sql)
                    conn.commit()
                except psycopg2.Error as e:
                    logger.error(f"Schema execution error: {e}")
                    return False
            
            conn.close()
            logger.info("✅ Tables created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            return False
    
    def _insert_initial_data(self) -> bool:
        """Insert initial configuration and sample data"""
        try:
            logger.info("📝 Inserting initial data...")
            
            conn = psycopg2.connect(
                host=self.config.config['host'],
                port=self.config.config['port'],
                database=self.config.config['database'],
                user=self.config.config['username'],
                password=self.config.config['password']
            )
            
            with conn.cursor() as cursor:
                # Set search path
                cursor.execute(f"SET search_path TO {self.config.config['schema']}, public;")
                
                # Insert system configuration (if not exists)
                config_data = [
                    ('honeypot.enabled', '"true"', 'boolean', 'Enable/disable honeypot system'),
                    ('honeypot.ports', '[22, 80, 443, 21, 23, 25, 53, 110, 143, 993, 995, 3306, 5432, 6379, 9200]', 'array', 'Ports to monitor'),
                    ('alerts.email_enabled', '"false"', 'boolean', 'Enable email alerts'),
                    ('alerts.email_recipients', '[]', 'array', 'Email recipients for alerts'),
                    ('alerts.threshold_critical', '10', 'integer', 'Critical alert threshold (attacks per hour)'),
                    ('alerts.threshold_high', '5', 'integer', 'High alert threshold (attacks per hour)'),
                    ('geo.api_enabled', '"true"', 'boolean', 'Enable geolocation API'),
                    ('geo.cache_duration', '86400', 'integer', 'Geolocation cache duration in seconds'),
                    ('analysis.auto_block_enabled', '"false"', 'boolean', 'Enable automatic IP blocking'),
                    ('analysis.auto_block_threshold', '20', 'integer', 'Auto-block threshold (attacks per IP)'),
                    ('dashboard.refresh_interval', '30', 'integer', 'Dashboard refresh interval in seconds'),
                    ('retention.attack_data_days', '90', 'integer', 'Days to retain attack data'),
                    ('retention.log_data_days', '30', 'integer', 'Days to retain log data')
                ]
                
                for key, value, config_type, description in config_data:
                    cursor.execute("""
                        INSERT INTO system_config (config_key, config_value, config_type, description)
                        VALUES (%s, %s::jsonb, %s, %s)
                        ON CONFLICT (config_key) DO NOTHING
                    """, (key, value, config_type, description))
                
                # Create default admin user (password: admin123 - should be changed)
                import hashlib
                import secrets
                
                salt = secrets.token_hex(16)
                password = "admin123"  # Default password
                password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()
                
                cursor.execute("""
                    INSERT INTO admin_users (username, email, password_hash, salt, role)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (username) DO NOTHING
                """, ('admin', 'admin@securehoney.local', password_hash, salt, 'admin'))
                
                # Insert sample threat intelligence data
                sample_threats = [
                    ('192.168.1.100', None, None, 'SCANNER', 'Internal', 0.8),
                    ('10.0.0.1', None, None, 'HONEYPOT', 'Internal', 0.9),
                    ('127.0.0.1', None, None, 'LOCALHOST', 'Internal', 0.1)
                ]
                
                for ip, domain, hash_val, threat_type, source, confidence in sample_threats:
                    cursor.execute("""
                        INSERT INTO threat_intelligence (ip_address, domain, hash_value, threat_type, threat_source, confidence)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT DO NOTHING
                    """, (ip, domain, hash_val, threat_type, source, confidence))
                
                conn.commit()
            
            conn.close()
            logger.info("✅ Initial data inserted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to insert initial data: {e}")
            return False
    
    def _verify_installation(self) -> bool:
        """Verify database installation"""
        try:
            logger.info("🔍 Verifying installation...")
            
            # Use health checker
            health_checker = DatabaseHealthChecker(self.config)
            health_status = health_checker.check_health()
            
            if health_status['status'] == 'healthy':
                logger.info("✅ Database verification passed")
                
                # Log some statistics
                if health_status['performance_metrics']:
                    metrics = health_status['performance_metrics']
                    logger.info(f"📊 Database size: {metrics.get('database_size', 'Unknown')}")
                    logger.info(f"🔗 Active connections: {metrics.get('active_connections', 'Unknown')}")
                    logger.info(f"📇 Indexes: {metrics.get('index_count', 'Unknown')}")
                
                return True
            else:
                logger.error(f"❌ Database verification failed: {health_status['status']}")
                for error in health_status.get('errors', []):
                    logger.error(f"  - {error}")
                for warning in health_status.get('warnings', []):
                    logger.warning(f"  - {warning}")
                return False
                
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return False
    
    def reset_database(self) -> bool:
        """Reset database (drop and recreate)"""
        try:
            logger.warning("⚠️  Resetting database - ALL DATA WILL BE LOST!")
            
            conn = psycopg2.connect(
                host=self.config.config['host'],
                port=self.config.config['port'],
                database=self.config.config['database'],
                user=self.config.config['username'],
                password=self.config.config['password']
            )
            
            with conn.cursor() as cursor:
                # Drop schema cascade
                cursor.execute(
                    sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(
                        sql.Identifier(self.config.config['schema'])
                    )
                )
                conn.commit()
            
            conn.close()
            logger.info("🗑️  Database reset completed")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reset database: {e}")
            return False

def main():
    """Main initialization function"""
    parser = argparse.ArgumentParser(description='SecureHoney Database Initialization')
    parser.add_argument('--reset', action='store_true', help='Reset database (drop all data)')
    parser.add_argument('--force', action='store_true', help='Force recreation of existing objects')
    parser.add_argument('--config', help='Database configuration file')
    parser.add_argument('--verify-only', action='store_true', help='Only verify existing installation')
    
    args = parser.parse_args()
    
    # Override config file if provided
    if args.config:
        global db_config
        from database.config import DatabaseConfig
        db_config = DatabaseConfig(args.config)
    
    initializer = DatabaseInitializer(force_recreate=args.force)
    
    try:
        if args.verify_only:
            logger.info("🔍 Verifying database installation...")
            if initializer._verify_installation():
                logger.info("✅ Database verification successful")
                sys.exit(0)
            else:
                logger.error("❌ Database verification failed")
                sys.exit(1)
        
        if args.reset:
            if not initializer.reset_database():
                logger.error("❌ Database reset failed")
                sys.exit(1)
        
        # Initialize database
        if initializer.initialize():
            logger.info("🎉 SecureHoney database initialization completed successfully!")
            logger.info("📋 Next steps:")
            logger.info("  1. Change default admin password (admin/admin123)")
            logger.info("  2. Configure email settings for alerts")
            logger.info("  3. Review system configuration")
            logger.info("  4. Start honeypot services")
            sys.exit(0)
        else:
            logger.error("❌ Database initialization failed")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("🛑 Initialization cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
