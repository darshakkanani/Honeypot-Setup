#!/usr/bin/env python3
"""
SecureHoney PostgreSQL Migration Script
Applies custom data types and schema to PostgreSQL database
"""

import psycopg2
import logging
from pathlib import Path
from typing import Optional
import os
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PostgreSQLMigrator:
    """PostgreSQL database migration manager for SecureHoney"""
    
    def __init__(self, connection_string: Optional[str] = None):
        self.connection_string = connection_string or self._get_default_connection()
        self.migration_dir = Path(__file__).parent
        
    def _get_default_connection(self) -> str:
        """Get default PostgreSQL connection string from environment"""
        host = os.getenv('POSTGRES_HOST', 'localhost')
        port = os.getenv('POSTGRES_PORT', '5432')
        database = os.getenv('POSTGRES_DB', 'securehoney')
        user = os.getenv('POSTGRES_USER', 'postgres')
        password = os.getenv('POSTGRES_PASSWORD', 'securehoney')
        
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"
    
    def connect(self):
        """Create database connection"""
        try:
            conn = psycopg2.connect(self.connection_string)
            conn.autocommit = True
            return conn
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise
    
    def create_database_if_not_exists(self):
        """Create SecureHoney database if it doesn't exist"""
        try:
            # Connect to postgres database to create securehoney database
            base_conn_string = self.connection_string.rsplit('/', 1)[0] + '/postgres'
            conn = psycopg2.connect(base_conn_string)
            conn.autocommit = True
            
            with conn.cursor() as cursor:
                # Check if database exists
                cursor.execute(
                    "SELECT 1 FROM pg_database WHERE datname = 'securehoney'"
                )
                
                if not cursor.fetchone():
                    logger.info("Creating SecureHoney database...")
                    cursor.execute("CREATE DATABASE securehoney")
                    logger.info("Database created successfully")
                else:
                    logger.info("SecureHoney database already exists")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to create database: {e}")
            raise
    
    def apply_custom_types(self):
        """Apply custom PostgreSQL types and functions"""
        types_file = self.migration_dir / 'postgresql_types.sql'
        
        if not types_file.exists():
            logger.error(f"Types file not found: {types_file}")
            return False
        
        try:
            conn = self.connect()
            
            with conn.cursor() as cursor:
                # Read and execute the types SQL file
                with open(types_file, 'r') as f:
                    sql_content = f.read()
                
                logger.info("Applying custom PostgreSQL types...")
                cursor.execute(sql_content)
                logger.info("Custom types applied successfully")
            
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply custom types: {e}")
            return False
    
    def create_tables_with_types(self):
        """Create tables using custom PostgreSQL types"""
        try:
            conn = self.connect()
            
            with conn.cursor() as cursor:
                # Create tables with custom types
                tables_sql = """
                -- Attack Sessions Table with custom types
                CREATE TABLE IF NOT EXISTS attack_sessions (
                    session_id VARCHAR(64) PRIMARY KEY,
                    source_ip securehoney.ip_address NOT NULL,
                    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_time TIMESTAMP,
                    duration_seconds INTEGER,
                    total_attacks INTEGER DEFAULT 0,
                    session_fingerprint VARCHAR(64),
                    geolocation securehoney.geolocation,
                    threat_score securehoney.reputation_score DEFAULT 0,
                    session_metadata JSONB
                );
                
                -- Attacks Table with enhanced types
                CREATE TABLE IF NOT EXISTS attacks (
                    id SERIAL PRIMARY KEY,
                    attack_id VARCHAR(64) UNIQUE NOT NULL,
                    session_id VARCHAR(64) REFERENCES attack_sessions(session_id),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    source_ip securehoney.ip_address NOT NULL,
                    target_port securehoney.port_number NOT NULL,
                    attack_type securehoney.attack_type NOT NULL,
                    severity securehoney.attack_severity NOT NULL,
                    confidence securehoney.confidence_score DEFAULT 0.5,
                    payload TEXT,
                    payload_size INTEGER,
                    payload_hash securehoney.hash_sha256,
                    attack_metadata securehoney.attack_metadata,
                    attack_signatures TEXT[],
                    blocked BOOLEAN DEFAULT FALSE,
                    honeypot_response TEXT
                );
                
                -- Attacker Profiles with enhanced profiling
                CREATE TABLE IF NOT EXISTS attacker_profiles (
                    id SERIAL PRIMARY KEY,
                    source_ip securehoney.ip_address UNIQUE NOT NULL,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_attacks INTEGER DEFAULT 0,
                    unique_sessions INTEGER DEFAULT 0,
                    threat_level securehoney.threat_level DEFAULT 'UNKNOWN',
                    skill_level securehoney.skill_level DEFAULT 'SCRIPT_KIDDIE',
                    reputation_score securehoney.reputation_score DEFAULT 0,
                    behavioral_patterns securehoney.behavioral_pattern,
                    threat_intelligence securehoney.threat_intel,
                    preferred_ports INTEGER[],
                    attack_patterns JSONB,
                    notes TEXT,
                    CONSTRAINT valid_attack_patterns CHECK (
                        attack_patterns IS NULL OR 
                        securehoney.validate_attack_pattern(attack_patterns)
                    )
                );
                
                -- Honeypot Interactions with service types
                CREATE TABLE IF NOT EXISTS honeypot_interactions (
                    id SERIAL PRIMARY KEY,
                    attack_id VARCHAR(64) REFERENCES attacks(attack_id),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    service_type securehoney.service_type NOT NULL,
                    interaction_type securehoney.interaction_type NOT NULL,
                    username_attempted VARCHAR(255),
                    password_attempted VARCHAR(255),
                    command_executed TEXT,
                    file_uploaded TEXT,
                    file_hash securehoney.hash_sha256,
                    http_method VARCHAR(10),
                    http_path TEXT,
                    http_headers JSONB,
                    response_code INTEGER,
                    interaction_success BOOLEAN DEFAULT FALSE,
                    data_extracted JSONB
                );
                
                -- Malware Analysis with enhanced tracking
                CREATE TABLE IF NOT EXISTS malware_analysis (
                    id SERIAL PRIMARY KEY,
                    file_hash securehoney.hash_sha256 UNIQUE NOT NULL,
                    file_name VARCHAR(255),
                    file_size BIGINT,
                    file_type VARCHAR(100),
                    upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    source_ip securehoney.ip_address,
                    attack_id VARCHAR(64) REFERENCES attacks(attack_id),
                    malware_family VARCHAR(100),
                    threat_level securehoney.threat_level DEFAULT 'UNKNOWN',
                    analysis_status securehoney.analysis_status DEFAULT 'PENDING',
                    analysis_results JSONB,
                    sandbox_report JSONB,
                    yara_matches TEXT[],
                    behavioral_indicators JSONB
                );
                
                -- System Metrics with typed metrics
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metric_type securehoney.metric_type NOT NULL,
                    metric_value DECIMAL(10, 4) NOT NULL,
                    metric_unit VARCHAR(50),
                    component VARCHAR(100),
                    additional_data JSONB
                );
                
                -- Geolocation Data with composite type
                CREATE TABLE IF NOT EXISTS geolocation_data (
                    id SERIAL PRIMARY KEY,
                    ip_address securehoney.ip_address UNIQUE NOT NULL,
                    country VARCHAR(100),
                    country_code CHAR(2),
                    region VARCHAR(100),
                    city VARCHAR(100),
                    latitude DECIMAL(10, 8),
                    longitude DECIMAL(11, 8),
                    timezone VARCHAR(50),
                    isp VARCHAR(200),
                    organization VARCHAR(200),
                    asn VARCHAR(50),
                    is_proxy BOOLEAN DEFAULT FALSE,
                    is_tor BOOLEAN DEFAULT FALSE,
                    is_vpn BOOLEAN DEFAULT FALSE,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Attack Campaigns tracking
                CREATE TABLE IF NOT EXISTS attack_campaigns (
                    id SERIAL PRIMARY KEY,
                    campaign_id VARCHAR(64) UNIQUE NOT NULL,
                    name VARCHAR(200),
                    description TEXT,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    attack_type securehoney.attack_type,
                    target_ports INTEGER[],
                    source_ips INET[],
                    campaign_fingerprint VARCHAR(64),
                    threat_level securehoney.threat_level DEFAULT 'MEDIUM',
                    attribution VARCHAR(200),
                    indicators_of_compromise JSONB,
                    mitigation_recommendations TEXT[]
                );
                """
                
                logger.info("Creating tables with custom types...")
                cursor.execute(tables_sql)
                
                # Create triggers
                trigger_sql = """
                -- Create trigger for automatic threat score updates
                DROP TRIGGER IF EXISTS update_threat_score ON attacks;
                CREATE TRIGGER update_threat_score
                    AFTER INSERT ON attacks
                    FOR EACH ROW
                    EXECUTE FUNCTION securehoney.update_threat_score_trigger();
                """
                
                logger.info("Creating triggers...")
                cursor.execute(trigger_sql)
                
                logger.info("Tables and triggers created successfully")
            
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            return False
    
    def create_indexes(self):
        """Create performance indexes"""
        try:
            conn = self.connect()
            
            with conn.cursor() as cursor:
                indexes_sql = """
                -- Performance indexes
                CREATE INDEX IF NOT EXISTS idx_attacks_source_ip_time ON attacks(source_ip, timestamp DESC);
                CREATE INDEX IF NOT EXISTS idx_attacks_type_severity ON attacks(attack_type, severity);
                CREATE INDEX IF NOT EXISTS idx_attacks_payload_hash ON attacks(payload_hash) WHERE payload_hash IS NOT NULL;
                CREATE INDEX IF NOT EXISTS idx_attacker_profiles_threat ON attacker_profiles(threat_level, reputation_score DESC);
                CREATE INDEX IF NOT EXISTS idx_interactions_service_type ON honeypot_interactions(service_type, timestamp DESC);
                CREATE INDEX IF NOT EXISTS idx_malware_threat_level ON malware_analysis(threat_level, upload_timestamp DESC);
                CREATE INDEX IF NOT EXISTS idx_geolocation_country ON geolocation_data(country_code, country);
                CREATE INDEX IF NOT EXISTS idx_campaigns_time_range ON attack_campaigns(start_time, end_time);
                
                -- GIN indexes for JSONB columns
                CREATE INDEX IF NOT EXISTS idx_attacks_metadata_gin ON attacks USING GIN(attack_metadata);
                CREATE INDEX IF NOT EXISTS idx_profiles_patterns_gin ON attacker_profiles USING GIN(attack_patterns);
                CREATE INDEX IF NOT EXISTS idx_interactions_data_gin ON honeypot_interactions USING GIN(data_extracted);
                CREATE INDEX IF NOT EXISTS idx_malware_results_gin ON malware_analysis USING GIN(analysis_results);
                """
                
                logger.info("Creating performance indexes...")
                cursor.execute(indexes_sql)
                logger.info("Indexes created successfully")
            
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
            return False
    
    def insert_sample_data(self):
        """Insert sample data for testing"""
        try:
            conn = self.connect()
            
            with conn.cursor() as cursor:
                sample_data_sql = """
                -- Insert sample geolocation data
                INSERT INTO geolocation_data (ip_address, country, country_code, city, latitude, longitude, isp)
                VALUES 
                    ('192.168.1.100', 'United States', 'US', 'New York', 40.7128, -74.0060, 'Example ISP'),
                    ('10.0.0.50', 'China', 'CN', 'Beijing', 39.9042, 116.4074, 'China Telecom'),
                    ('172.16.0.25', 'Russia', 'RU', 'Moscow', 55.7558, 37.6176, 'Rostelecom')
                ON CONFLICT (ip_address) DO NOTHING;
                
                -- Insert sample attacker profiles
                INSERT INTO attacker_profiles (source_ip, threat_level, skill_level, reputation_score, total_attacks)
                VALUES 
                    ('192.168.1.100', 'HIGH', 'ADVANCED', 75, 50),
                    ('10.0.0.50', 'CRITICAL', 'EXPERT', 95, 150),
                    ('172.16.0.25', 'MEDIUM', 'INTERMEDIATE', 45, 25)
                ON CONFLICT (source_ip) DO NOTHING;
                
                -- Insert sample attacks
                INSERT INTO attacks (attack_id, source_ip, target_port, attack_type, severity, confidence, payload)
                VALUES 
                    ('attack_001', '192.168.1.100', 22, 'BRUTE_FORCE', 'HIGH', 0.9, 'ssh login attempts'),
                    ('attack_002', '10.0.0.50', 80, 'SQL_INJECTION', 'CRITICAL', 0.95, 'UNION SELECT * FROM users'),
                    ('attack_003', '172.16.0.25', 443, 'XSS', 'MEDIUM', 0.7, '<script>alert("xss")</script>')
                ON CONFLICT (attack_id) DO NOTHING;
                """
                
                logger.info("Inserting sample data...")
                cursor.execute(sample_data_sql)
                logger.info("Sample data inserted successfully")
            
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Failed to insert sample data: {e}")
            return False
    
    def run_full_migration(self):
        """Run complete database migration"""
        logger.info("Starting SecureHoney PostgreSQL migration...")
        
        try:
            # Step 1: Create database
            self.create_database_if_not_exists()
            
            # Step 2: Apply custom types
            if not self.apply_custom_types():
                return False
            
            # Step 3: Create tables
            if not self.create_tables_with_types():
                return False
            
            # Step 4: Create indexes
            if not self.create_indexes():
                return False
            
            # Step 5: Insert sample data
            if not self.insert_sample_data():
                logger.warning("Sample data insertion failed, but migration continues")
            
            logger.info("✅ SecureHoney PostgreSQL migration completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False
    
    def verify_migration(self):
        """Verify migration was successful"""
        try:
            conn = self.connect()
            
            with conn.cursor() as cursor:
                # Check if custom types exist
                cursor.execute("""
                    SELECT typname FROM pg_type 
                    WHERE typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'securehoney')
                    ORDER BY typname
                """)
                types = [row[0] for row in cursor.fetchall()]
                
                # Check if tables exist
                cursor.execute("""
                    SELECT tablename FROM pg_tables 
                    WHERE schemaname = 'public' 
                    AND tablename IN ('attacks', 'attacker_profiles', 'geolocation_data')
                    ORDER BY tablename
                """)
                tables = [row[0] for row in cursor.fetchall()]
                
                # Check if functions exist
                cursor.execute("""
                    SELECT proname FROM pg_proc 
                    WHERE pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'securehoney')
                    ORDER BY proname
                """)
                functions = [row[0] for row in cursor.fetchall()]
                
                logger.info(f"Custom types created: {len(types)}")
                logger.info(f"Tables created: {len(tables)}")
                logger.info(f"Functions created: {len(functions)}")
                
                # Test a query with custom types
                cursor.execute("""
                    SELECT COUNT(*) FROM attacks 
                    WHERE severity = 'HIGH'::securehoney.attack_severity
                """)
                high_severity_count = cursor.fetchone()[0]
                logger.info(f"High severity attacks: {high_severity_count}")
            
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Migration verification failed: {e}")
            return False

def main():
    """Main migration function"""
    migrator = PostgreSQLMigrator()
    
    if migrator.run_full_migration():
        migrator.verify_migration()
        print("\n🎉 SecureHoney PostgreSQL setup complete!")
        print("Database is ready with custom types and enhanced schema.")
    else:
        print("\n❌ Migration failed. Check logs for details.")

if __name__ == "__main__":
    main()
