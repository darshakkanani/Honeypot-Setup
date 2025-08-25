-- SecureHoney Admin Panel Database Schema
-- Complete database schema for honeypot attack monitoring and analysis

-- Create main database schema
CREATE SCHEMA IF NOT EXISTS securehoney;

-- Import custom types from shared utils
\i '../shared-utils/database/postgresql_types.sql';

-- Main tables for attack tracking
CREATE TABLE IF NOT EXISTS securehoney.attack_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(64) UNIQUE NOT NULL,
    source_ip securehoney.ip_address NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    total_attacks INTEGER DEFAULT 0,
    unique_ports INTEGER DEFAULT 0,
    attack_intensity securehoney.threat_level DEFAULT 'UNKNOWN',
    session_type securehoney.attack_type DEFAULT 'UNKNOWN',
    geolocation securehoney.geolocation,
    user_agent TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    threat_score INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS securehoney.attacks (
    id SERIAL PRIMARY KEY,
    attack_id VARCHAR(64) UNIQUE NOT NULL,
    session_id VARCHAR(64) REFERENCES securehoney.attack_sessions(session_id),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    source_ip securehoney.ip_address NOT NULL,
    source_port securehoney.port_number,
    target_port securehoney.port_number NOT NULL,
    protocol VARCHAR(10) DEFAULT 'TCP',
    attack_type securehoney.attack_type NOT NULL,
    attack_vector VARCHAR(50) DEFAULT 'NETWORK',
    severity securehoney.attack_severity NOT NULL,
    confidence securehoney.confidence_score DEFAULT 0.5,
    payload TEXT,
    payload_size INTEGER DEFAULT 0,
    payload_hash securehoney.hash_sha256,
    response_sent TEXT,
    connection_duration DECIMAL(10,3),
    bytes_received INTEGER DEFAULT 0,
    bytes_sent INTEGER DEFAULT 0,
    honeypot_response VARCHAR(50) DEFAULT 'ENGAGED',
    metadata securehoney.attack_metadata,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS securehoney.attacker_profiles (
    id SERIAL PRIMARY KEY,
    source_ip securehoney.ip_address UNIQUE NOT NULL,
    first_seen TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    total_attacks INTEGER DEFAULT 0,
    total_sessions INTEGER DEFAULT 0,
    attack_frequency DECIMAL(10,2) DEFAULT 0.0,
    primary_attack_type securehoney.attack_type,
    skill_level securehoney.skill_level DEFAULT 'SCRIPT_KIDDIE',
    persistence_score DECIMAL(3,2) DEFAULT 0.0,
    stealth_score DECIMAL(3,2) DEFAULT 0.0,
    success_rate DECIMAL(3,2) DEFAULT 0.0,
    preferred_ports INTEGER[],
    attack_patterns securehoney.behavioral_pattern,
    tools_used TEXT[],
    geolocation_history JSONB,
    user_agents TEXT[],
    is_bot BOOLEAN DEFAULT FALSE,
    is_tor BOOLEAN DEFAULT FALSE,
    is_vpn BOOLEAN DEFAULT FALSE,
    threat_level securehoney.threat_level DEFAULT 'UNKNOWN',
    reputation_score securehoney.reputation_score DEFAULT 50,
    threat_intel securehoney.threat_intel,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS securehoney.attack_patterns (
    id SERIAL PRIMARY KEY,
    attack_id VARCHAR(64) REFERENCES securehoney.attacks(attack_id),
    pattern_type VARCHAR(50) NOT NULL,
    pattern_name VARCHAR(100) NOT NULL,
    pattern_description TEXT,
    confidence securehoney.confidence_score DEFAULT 0.5,
    severity securehoney.attack_severity NOT NULL,
    indicators JSONB,
    mitre_technique VARCHAR(20),
    signature_match TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS securehoney.honeypot_interactions (
    id SERIAL PRIMARY KEY,
    attack_id VARCHAR(64) REFERENCES securehoney.attacks(attack_id),
    service_type securehoney.service_type NOT NULL,
    interaction_type securehoney.interaction_type NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    username_attempted VARCHAR(255),
    password_attempted VARCHAR(255),
    command_executed TEXT,
    file_uploaded VARCHAR(500),
    file_hash securehoney.hash_sha256,
    http_method VARCHAR(10),
    http_path VARCHAR(500),
    http_headers JSONB,
    response_code INTEGER,
    interaction_success BOOLEAN DEFAULT FALSE,
    data_extracted JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS securehoney.threat_intelligence (
    id SERIAL PRIMARY KEY,
    ip_address securehoney.ip_address,
    domain VARCHAR(255),
    hash_value securehoney.hash_sha256,
    threat_type VARCHAR(50) NOT NULL,
    threat_source VARCHAR(100) NOT NULL,
    confidence securehoney.confidence_score DEFAULT 0.5,
    first_reported TIMESTAMP WITH TIME ZONE,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    additional_info JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS securehoney.attack_campaigns (
    id SERIAL PRIMARY KEY,
    campaign_id VARCHAR(64) UNIQUE NOT NULL,
    campaign_name VARCHAR(200),
    start_date TIMESTAMP WITH TIME ZONE,
    end_date TIMESTAMP WITH TIME ZONE,
    total_attackers INTEGER DEFAULT 0,
    total_attacks INTEGER DEFAULT 0,
    primary_targets JSONB,
    attack_methods JSONB,
    geographic_distribution JSONB,
    campaign_type VARCHAR(50) DEFAULT 'UNKNOWN',
    threat_actor VARCHAR(200),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS securehoney.system_metrics (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metric_type securehoney.metric_type NOT NULL,
    metric_value DECIMAL(15,6) NOT NULL,
    metric_unit VARCHAR(20),
    component VARCHAR(50) NOT NULL,
    additional_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS securehoney.malware_analysis (
    id SERIAL PRIMARY KEY,
    file_hash securehoney.hash_sha256 UNIQUE NOT NULL,
    file_name VARCHAR(500),
    file_size INTEGER,
    file_type VARCHAR(50),
    upload_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    source_ip securehoney.ip_address,
    attack_id VARCHAR(64) REFERENCES securehoney.attacks(attack_id),
    malware_family VARCHAR(100),
    threat_level securehoney.threat_level DEFAULT 'UNKNOWN',
    analysis_status securehoney.analysis_status DEFAULT 'PENDING',
    static_analysis JSONB,
    dynamic_analysis JSONB,
    iocs JSONB,
    yara_matches JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS securehoney.geolocation_data (
    id SERIAL PRIMARY KEY,
    ip_address securehoney.ip_address UNIQUE NOT NULL,
    country VARCHAR(100),
    country_code CHAR(2),
    region VARCHAR(100),
    city VARCHAR(100),
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    timezone VARCHAR(50),
    isp VARCHAR(200),
    organization VARCHAR(200),
    asn VARCHAR(50),
    is_proxy BOOLEAN DEFAULT FALSE,
    is_tor BOOLEAN DEFAULT FALSE,
    is_vpn BOOLEAN DEFAULT FALSE,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Admin panel specific tables
CREATE TABLE IF NOT EXISTS securehoney.admin_users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    salt VARCHAR(32) NOT NULL,
    role VARCHAR(20) DEFAULT 'analyst',
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP WITH TIME ZONE,
    failed_login_attempts INTEGER DEFAULT 0,
    account_locked_until TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS securehoney.admin_sessions (
    id SERIAL PRIMARY KEY,
    session_token VARCHAR(128) UNIQUE NOT NULL,
    user_id INTEGER REFERENCES securehoney.admin_users(id),
    ip_address INET NOT NULL,
    user_agent TEXT,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS securehoney.admin_audit_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES securehoney.admin_users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(64),
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS securehoney.system_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value JSONB NOT NULL,
    config_type VARCHAR(20) DEFAULT 'string',
    description TEXT,
    is_sensitive BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS securehoney.alerts (
    id SERIAL PRIMARY KEY,
    alert_id VARCHAR(64) UNIQUE NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    severity securehoney.attack_severity NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    source_ip securehoney.ip_address,
    attack_id VARCHAR(64) REFERENCES securehoney.attacks(attack_id),
    campaign_id VARCHAR(64) REFERENCES securehoney.attack_campaigns(campaign_id),
    is_acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by INTEGER REFERENCES securehoney.admin_users(id),
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_by INTEGER REFERENCES securehoney.admin_users(id),
    resolved_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_attacks_source_ip ON securehoney.attacks(source_ip);
CREATE INDEX IF NOT EXISTS idx_attacks_timestamp ON securehoney.attacks(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_attacks_type_severity ON securehoney.attacks(attack_type, severity);
CREATE INDEX IF NOT EXISTS idx_attacks_target_port ON securehoney.attacks(target_port);
CREATE INDEX IF NOT EXISTS idx_attack_sessions_source_ip ON securehoney.attack_sessions(source_ip);
CREATE INDEX IF NOT EXISTS idx_attack_sessions_active ON securehoney.attack_sessions(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_attacker_profiles_threat_level ON securehoney.attacker_profiles(threat_level);
CREATE INDEX IF NOT EXISTS idx_attacker_profiles_last_seen ON securehoney.attacker_profiles(last_seen DESC);
CREATE INDEX IF NOT EXISTS idx_geolocation_country ON securehoney.geolocation_data(country_code, country);
CREATE INDEX IF NOT EXISTS idx_system_metrics_timestamp ON securehoney.system_metrics(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_admin_sessions_token ON securehoney.admin_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_admin_sessions_active ON securehoney.admin_sessions(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_alerts_unresolved ON securehoney.alerts(is_resolved) WHERE is_resolved = FALSE;

-- Create triggers for automatic updates
CREATE OR REPLACE FUNCTION securehoney.update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply update triggers to relevant tables
CREATE TRIGGER update_attack_sessions_timestamp
    BEFORE UPDATE ON securehoney.attack_sessions
    FOR EACH ROW EXECUTE FUNCTION securehoney.update_timestamp();

CREATE TRIGGER update_attacker_profiles_timestamp
    BEFORE UPDATE ON securehoney.attacker_profiles
    FOR EACH ROW EXECUTE FUNCTION securehoney.update_timestamp();

CREATE TRIGGER update_attack_campaigns_timestamp
    BEFORE UPDATE ON securehoney.attack_campaigns
    FOR EACH ROW EXECUTE FUNCTION securehoney.update_timestamp();

CREATE TRIGGER update_malware_analysis_timestamp
    BEFORE UPDATE ON securehoney.malware_analysis
    FOR EACH ROW EXECUTE FUNCTION securehoney.update_timestamp();

CREATE TRIGGER update_admin_users_timestamp
    BEFORE UPDATE ON securehoney.admin_users
    FOR EACH ROW EXECUTE FUNCTION securehoney.update_timestamp();

CREATE TRIGGER update_system_config_timestamp
    BEFORE UPDATE ON securehoney.system_config
    FOR EACH ROW EXECUTE FUNCTION securehoney.update_timestamp();

-- Create trigger for automatic threat score updates
CREATE TRIGGER update_attacker_threat_score
    AFTER INSERT ON securehoney.attacks
    FOR EACH ROW EXECUTE FUNCTION securehoney.update_threat_score_trigger();

-- Create materialized views for dashboard performance
CREATE MATERIALIZED VIEW IF NOT EXISTS securehoney.dashboard_stats AS
SELECT 
    COUNT(*) as total_attacks,
    COUNT(DISTINCT source_ip) as unique_attackers,
    COUNT(DISTINCT target_port) as unique_ports_targeted,
    COUNT(*) FILTER (WHERE timestamp >= CURRENT_DATE) as attacks_today,
    COUNT(*) FILTER (WHERE severity = 'CRITICAL') as critical_attacks,
    COUNT(*) FILTER (WHERE severity = 'HIGH') as high_attacks,
    array_agg(DISTINCT attack_type) as attack_types_seen,
    MAX(timestamp) as last_attack_time
FROM securehoney.attacks;

CREATE MATERIALIZED VIEW IF NOT EXISTS securehoney.geographic_stats AS
SELECT 
    g.country,
    g.country_code,
    COUNT(a.*) as attack_count,
    COUNT(DISTINCT a.source_ip) as unique_attackers,
    AVG(CASE a.severity
        WHEN 'LOW' THEN 1
        WHEN 'MEDIUM' THEN 2
        WHEN 'HIGH' THEN 3
        WHEN 'CRITICAL' THEN 4
    END) as avg_severity,
    g.latitude,
    g.longitude
FROM securehoney.attacks a
JOIN securehoney.geolocation_data g ON a.source_ip = g.ip_address
GROUP BY g.country, g.country_code, g.latitude, g.longitude;

-- Function to refresh materialized views
CREATE OR REPLACE FUNCTION securehoney.refresh_dashboard_views()
RETURNS VOID AS $$
BEGIN
    REFRESH MATERIALIZED VIEW securehoney.dashboard_stats;
    REFRESH MATERIALIZED VIEW securehoney.geographic_stats;
    REFRESH MATERIALIZED VIEW securehoney.daily_attack_stats;
END;
$$ LANGUAGE plpgsql;

-- Insert default system configuration
INSERT INTO securehoney.system_config (config_key, config_value, config_type, description) VALUES
('honeypot.enabled', 'true', 'boolean', 'Enable/disable honeypot system'),
('honeypot.ports', '[22, 80, 443, 21, 23, 25, 53, 110, 143, 993, 995, 3306, 5432, 6379, 9200]', 'array', 'Ports to monitor'),
('alerts.email_enabled', 'false', 'boolean', 'Enable email alerts'),
('alerts.email_recipients', '[]', 'array', 'Email recipients for alerts'),
('alerts.threshold_critical', '10', 'integer', 'Critical alert threshold (attacks per hour)'),
('alerts.threshold_high', '5', 'integer', 'High alert threshold (attacks per hour)'),
('geo.api_enabled', 'true', 'boolean', 'Enable geolocation API'),
('geo.cache_duration', '86400', 'integer', 'Geolocation cache duration in seconds'),
('analysis.auto_block_enabled', 'false', 'boolean', 'Enable automatic IP blocking'),
('analysis.auto_block_threshold', '20', 'integer', 'Auto-block threshold (attacks per IP)'),
('dashboard.refresh_interval', '30', 'integer', 'Dashboard refresh interval in seconds'),
('retention.attack_data_days', '90', 'integer', 'Days to retain attack data'),
('retention.log_data_days', '30', 'integer', 'Days to retain log data')
ON CONFLICT (config_key) DO NOTHING;

-- Create default admin user (password: admin123 - should be changed immediately)
INSERT INTO securehoney.admin_users (username, email, password_hash, salt, role) VALUES
('admin', 'admin@securehoney.local', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/A5/jF3kkS', 'randomsalt123', 'admin')
ON CONFLICT (username) DO NOTHING;

-- Comments for documentation
COMMENT ON SCHEMA securehoney IS 'SecureHoney honeypot system database schema';
COMMENT ON TABLE securehoney.attacks IS 'Individual attack events captured by honeypots';
COMMENT ON TABLE securehoney.attacker_profiles IS 'Comprehensive profiles of attacking entities';
COMMENT ON TABLE securehoney.admin_users IS 'Administrative users for the honeypot system';
COMMENT ON MATERIALIZED VIEW securehoney.dashboard_stats IS 'Pre-computed statistics for dashboard performance';
