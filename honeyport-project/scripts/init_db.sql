-- HoneyPort Database Initialization Script

-- Create database extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS honeyport;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS ai_models;

-- Set search path
SET search_path TO honeyport, public;

-- Create tables for attack logs
CREATE TABLE IF NOT EXISTS attack_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source_ip INET NOT NULL,
    source_port INTEGER,
    destination_port INTEGER NOT NULL,
    protocol VARCHAR(10) NOT NULL,
    attack_type VARCHAR(50),
    payload TEXT,
    user_agent TEXT,
    http_method VARCHAR(10),
    url_path TEXT,
    headers JSONB,
    session_id VARCHAR(255),
    geolocation JSONB,
    threat_level DECIMAL(3,2) DEFAULT 0.5,
    blockchain_hash VARCHAR(66),
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_attack_logs_timestamp ON attack_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_attack_logs_source_ip ON attack_logs(source_ip);
CREATE INDEX IF NOT EXISTS idx_attack_logs_attack_type ON attack_logs(attack_type);
CREATE INDEX IF NOT EXISTS idx_attack_logs_threat_level ON attack_logs(threat_level);
CREATE INDEX IF NOT EXISTS idx_attack_logs_session_id ON attack_logs(session_id);
CREATE INDEX IF NOT EXISTS idx_attack_logs_processed ON attack_logs(processed);

-- Create sessions table
CREATE TABLE IF NOT EXISTS attack_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) UNIQUE NOT NULL,
    source_ip INET NOT NULL,
    start_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    end_time TIMESTAMPTZ,
    duration_seconds INTEGER,
    request_count INTEGER DEFAULT 0,
    unique_urls INTEGER DEFAULT 0,
    attack_types TEXT[],
    user_agents TEXT[],
    geolocation JSONB,
    sophistication_score DECIMAL(3,2) DEFAULT 0.5,
    automation_level DECIMAL(3,2) DEFAULT 0.5,
    persistence_score DECIMAL(3,2) DEFAULT 0.5,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sessions_source_ip ON attack_sessions(source_ip);
CREATE INDEX IF NOT EXISTS idx_sessions_start_time ON attack_sessions(start_time);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON attack_sessions(status);

-- Create AI insights table
CREATE TABLE IF NOT EXISTS ai_insights (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    attack_log_id UUID REFERENCES attack_logs(id),
    session_id VARCHAR(255),
    insight_type VARCHAR(50) NOT NULL,
    confidence_score DECIMAL(3,2),
    prediction JSONB,
    model_version VARCHAR(50),
    processing_time_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ai_insights_attack_log_id ON ai_insights(attack_log_id);
CREATE INDEX IF NOT EXISTS idx_ai_insights_insight_type ON ai_insights(insight_type);
CREATE INDEX IF NOT EXISTS idx_ai_insights_confidence ON ai_insights(confidence_score);

-- Create blockchain logs table
CREATE TABLE IF NOT EXISTS blockchain_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    block_hash VARCHAR(66) NOT NULL,
    transaction_hash VARCHAR(66),
    block_number BIGINT,
    log_hash VARCHAR(66) NOT NULL,
    attack_log_id UUID REFERENCES attack_logs(id),
    verified BOOLEAN DEFAULT FALSE,
    verification_timestamp TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_blockchain_logs_block_hash ON blockchain_logs(block_hash);
CREATE INDEX IF NOT EXISTS idx_blockchain_logs_attack_log_id ON blockchain_logs(attack_log_id);

-- Create alerts table
CREATE TABLE IF NOT EXISTS security_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    source_ip INET,
    attack_log_id UUID REFERENCES attack_logs(id),
    session_id VARCHAR(255),
    metadata JSONB,
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by VARCHAR(100),
    acknowledged_at TIMESTAMPTZ,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_by VARCHAR(100),
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_alerts_alert_type ON security_alerts(alert_type);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON security_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_alerts_acknowledged ON security_alerts(acknowledged);
CREATE INDEX IF NOT EXISTS idx_alerts_resolved ON security_alerts(resolved);

-- Create honeypot configuration table
CREATE TABLE IF NOT EXISTS honeypot_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value JSONB,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert default configuration
INSERT INTO honeypot_config (config_key, config_value, description) VALUES
('behavior_mode', '"realistic"', 'Current honeypot behavior mode'),
('ai_enabled', 'true', 'Whether AI analysis is enabled'),
('blockchain_enabled', 'true', 'Whether blockchain logging is enabled'),
('alert_threshold', '0.7', 'Threat level threshold for alerts'),
('adaptation_threshold', '0.8', 'Confidence threshold for behavior adaptation')
ON CONFLICT (config_key) DO NOTHING;

-- Create analytics schema tables
SET search_path TO analytics, public;

-- Daily attack statistics
CREATE TABLE IF NOT EXISTS daily_stats (
    date DATE PRIMARY KEY,
    total_attacks INTEGER DEFAULT 0,
    unique_ips INTEGER DEFAULT 0,
    unique_sessions INTEGER DEFAULT 0,
    top_attack_types JSONB,
    top_source_countries JSONB,
    avg_threat_level DECIMAL(3,2),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Attacker profiles
CREATE TABLE IF NOT EXISTS attacker_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_ip INET UNIQUE NOT NULL,
    first_seen TIMESTAMPTZ NOT NULL,
    last_seen TIMESTAMPTZ NOT NULL,
    total_attacks INTEGER DEFAULT 0,
    total_sessions INTEGER DEFAULT 0,
    attack_types TEXT[],
    user_agents TEXT[],
    geolocation JSONB,
    sophistication_score DECIMAL(3,2) DEFAULT 0.5,
    automation_level DECIMAL(3,2) DEFAULT 0.5,
    persistence_score DECIMAL(3,2) DEFAULT 0.5,
    threat_category VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_attacker_profiles_source_ip ON attacker_profiles(source_ip);
CREATE INDEX IF NOT EXISTS idx_attacker_profiles_threat_category ON attacker_profiles(threat_category);

-- AI models metadata
SET search_path TO ai_models, public;

CREATE TABLE IF NOT EXISTS model_metadata (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_name VARCHAR(100) NOT NULL,
    model_type VARCHAR(50) NOT NULL,
    version VARCHAR(20) NOT NULL,
    file_path TEXT,
    accuracy DECIMAL(5,4),
    precision_score DECIMAL(5,4),
    recall DECIMAL(5,4),
    f1_score DECIMAL(5,4),
    training_samples INTEGER,
    training_date TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT FALSE,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_model_metadata_name ON model_metadata(model_name);
CREATE INDEX IF NOT EXISTS idx_model_metadata_active ON model_metadata(is_active);

-- Training history
CREATE TABLE IF NOT EXISTS training_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_name VARCHAR(100) NOT NULL,
    training_start TIMESTAMPTZ NOT NULL,
    training_end TIMESTAMPTZ,
    samples_count INTEGER,
    validation_accuracy DECIMAL(5,4),
    loss DECIMAL(10,6),
    epochs INTEGER,
    hyperparameters JSONB,
    status VARCHAR(20) DEFAULT 'running',
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create functions for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_attack_logs_updated_at BEFORE UPDATE ON honeyport.attack_logs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_sessions_updated_at BEFORE UPDATE ON honeyport.attack_sessions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_config_updated_at BEFORE UPDATE ON honeyport.honeypot_config FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_daily_stats_updated_at BEFORE UPDATE ON analytics.daily_stats FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_attacker_profiles_updated_at BEFORE UPDATE ON analytics.attacker_profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create views for common queries
SET search_path TO honeyport, public;

-- Recent attacks view
CREATE OR REPLACE VIEW recent_attacks AS
SELECT 
    al.*,
    ai.confidence_score,
    ai.prediction as ai_prediction
FROM attack_logs al
LEFT JOIN ai_insights ai ON al.id = ai.attack_log_id AND ai.insight_type = 'threat_assessment'
ORDER BY al.timestamp DESC;

-- Active sessions view
CREATE OR REPLACE VIEW active_sessions AS
SELECT * FROM attack_sessions 
WHERE status = 'active' 
ORDER BY start_time DESC;

-- High threat attacks view
CREATE OR REPLACE VIEW high_threat_attacks AS
SELECT * FROM attack_logs 
WHERE threat_level >= 0.7 
ORDER BY timestamp DESC;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA honeyport TO honeyport;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA analytics TO honeyport;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA ai_models TO honeyport;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA honeyport TO honeyport;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA analytics TO honeyport;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA ai_models TO honeyport;
