-- SecureHoney PostgreSQL Custom Data Types
-- Advanced data types for honeypot attack analysis and monitoring

-- Create custom schema for SecureHoney types
CREATE SCHEMA IF NOT EXISTS securehoney;

-- Enum for attack severity levels
CREATE TYPE securehoney.attack_severity AS ENUM (
    'LOW',
    'MEDIUM', 
    'HIGH',
    'CRITICAL'
);

-- Enum for threat levels
CREATE TYPE securehoney.threat_level AS ENUM (
    'UNKNOWN',
    'LOW',
    'MEDIUM',
    'HIGH',
    'CRITICAL'
);

-- Enum for attack types
CREATE TYPE securehoney.attack_type AS ENUM (
    'PORT_SCAN',
    'BRUTE_FORCE',
    'SQL_INJECTION',
    'XSS',
    'MALWARE_UPLOAD',
    'CREDENTIAL_THEFT',
    'COMMAND_INJECTION',
    'DIRECTORY_TRAVERSAL',
    'DDOS',
    'RECONNAISSANCE',
    'EXPLOITATION',
    'PERSISTENCE',
    'PRIVILEGE_ESCALATION',
    'LATERAL_MOVEMENT',
    'EXFILTRATION',
    'UNKNOWN'
);

-- Enum for honeypot service types
CREATE TYPE securehoney.service_type AS ENUM (
    'SSH',
    'HTTP',
    'HTTPS',
    'FTP',
    'TELNET',
    'SMTP',
    'POP3',
    'IMAP',
    'DNS',
    'MYSQL',
    'POSTGRESQL',
    'REDIS',
    'MONGODB',
    'ELASTICSEARCH',
    'CUSTOM'
);

-- Enum for interaction types
CREATE TYPE securehoney.interaction_type AS ENUM (
    'CONNECTION',
    'LOGIN_ATTEMPT',
    'COMMAND_EXECUTION',
    'FILE_UPLOAD',
    'FILE_DOWNLOAD',
    'DATA_EXTRACTION',
    'MALWARE_DEPLOYMENT',
    'CONFIGURATION_CHANGE',
    'PRIVILEGE_ESCALATION',
    'LATERAL_MOVEMENT'
);

-- Enum for skill levels
CREATE TYPE securehoney.skill_level AS ENUM (
    'SCRIPT_KIDDIE',
    'INTERMEDIATE',
    'ADVANCED',
    'EXPERT',
    'NATION_STATE'
);

-- Enum for malware analysis status
CREATE TYPE securehoney.analysis_status AS ENUM (
    'PENDING',
    'IN_PROGRESS',
    'COMPLETED',
    'FAILED',
    'QUARANTINED'
);

-- Enum for system metric types
CREATE TYPE securehoney.metric_type AS ENUM (
    'ATTACK_RATE',
    'CPU_USAGE',
    'MEMORY_USAGE',
    'DISK_USAGE',
    'NETWORK_TRAFFIC',
    'CONNECTION_COUNT',
    'RESPONSE_TIME',
    'ERROR_RATE',
    'THREAT_SCORE'
);

-- Composite type for IP geolocation
CREATE TYPE securehoney.geolocation AS (
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
    is_proxy BOOLEAN,
    is_tor BOOLEAN,
    is_vpn BOOLEAN
);

-- Composite type for attack metadata
CREATE TYPE securehoney.attack_metadata AS (
    user_agent TEXT,
    referer TEXT,
    payload_hash VARCHAR(64),
    signature_match TEXT[],
    vulnerability_cve TEXT[],
    attack_vector VARCHAR(100),
    exploit_kit VARCHAR(100)
);

-- Composite type for behavioral patterns
CREATE TYPE securehoney.behavioral_pattern AS (
    timing_patterns JSONB,
    frequency_patterns JSONB,
    target_patterns JSONB,
    technique_patterns JSONB,
    persistence_indicators JSONB
);

-- Composite type for threat intelligence
CREATE TYPE securehoney.threat_intel AS (
    reputation_score INTEGER,
    malware_families TEXT[],
    campaign_tags TEXT[],
    attribution VARCHAR(200),
    first_seen_global TIMESTAMP,
    last_seen_global TIMESTAMP,
    confidence_score DECIMAL(3, 2)
);

-- Domain type for IP addresses with validation
CREATE DOMAIN securehoney.ip_address AS INET
    CHECK (VALUE IS NOT NULL);

-- Domain type for port numbers
CREATE DOMAIN securehoney.port_number AS INTEGER
    CHECK (VALUE >= 1 AND VALUE <= 65535);

-- Domain type for hash values (SHA256)
CREATE DOMAIN securehoney.hash_sha256 AS CHAR(64)
    CHECK (VALUE ~ '^[a-fA-F0-9]{64}$');

-- Domain type for hash values (MD5)
CREATE DOMAIN securehoney.hash_md5 AS CHAR(32)
    CHECK (VALUE ~ '^[a-fA-F0-9]{32}$');

-- Domain type for confidence scores (0.0 to 1.0)
CREATE DOMAIN securehoney.confidence_score AS DECIMAL(3, 2)
    CHECK (VALUE >= 0.00 AND VALUE <= 1.00);

-- Domain type for reputation scores (0 to 100)
CREATE DOMAIN securehoney.reputation_score AS INTEGER
    CHECK (VALUE >= 0 AND VALUE <= 100);

-- Function to validate JSON schema for attack patterns
CREATE OR REPLACE FUNCTION securehoney.validate_attack_pattern(pattern JSONB)
RETURNS BOOLEAN AS $$
BEGIN
    -- Basic validation for required fields in attack patterns
    RETURN (
        pattern ? 'types' AND
        pattern ? 'frequency' AND
        pattern ? 'timing' AND
        jsonb_typeof(pattern->'types') = 'array' AND
        jsonb_typeof(pattern->'frequency') = 'object' AND
        jsonb_typeof(pattern->'timing') = 'object'
    );
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to calculate threat score based on multiple factors
CREATE OR REPLACE FUNCTION securehoney.calculate_threat_score(
    attack_count INTEGER,
    severity_avg DECIMAL,
    unique_techniques INTEGER,
    time_span_hours INTEGER
) RETURNS INTEGER AS $$
DECLARE
    base_score INTEGER := 0;
    frequency_multiplier DECIMAL := 1.0;
    severity_multiplier DECIMAL := 1.0;
    technique_multiplier DECIMAL := 1.0;
    persistence_multiplier DECIMAL := 1.0;
BEGIN
    -- Base score from attack count
    base_score := LEAST(attack_count * 2, 40);
    
    -- Frequency multiplier (attacks per hour)
    IF time_span_hours > 0 THEN
        frequency_multiplier := LEAST((attack_count::DECIMAL / time_span_hours) * 0.5, 2.0);
    END IF;
    
    -- Severity multiplier
    severity_multiplier := CASE 
        WHEN severity_avg >= 4.0 THEN 2.0
        WHEN severity_avg >= 3.0 THEN 1.5
        WHEN severity_avg >= 2.0 THEN 1.2
        ELSE 1.0
    END;
    
    -- Technique diversity multiplier
    technique_multiplier := CASE
        WHEN unique_techniques >= 10 THEN 1.8
        WHEN unique_techniques >= 5 THEN 1.4
        WHEN unique_techniques >= 3 THEN 1.2
        ELSE 1.0
    END;
    
    -- Persistence multiplier (longer campaigns are more threatening)
    persistence_multiplier := CASE
        WHEN time_span_hours >= 168 THEN 1.5  -- 1 week
        WHEN time_span_hours >= 24 THEN 1.3   -- 1 day
        WHEN time_span_hours >= 1 THEN 1.1    -- 1 hour
        ELSE 1.0
    END;
    
    -- Calculate final score (max 100)
    RETURN LEAST(
        (base_score * frequency_multiplier * severity_multiplier * 
         technique_multiplier * persistence_multiplier)::INTEGER,
        100
    );
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to extract attack signatures from payload
CREATE OR REPLACE FUNCTION securehoney.extract_attack_signatures(payload TEXT)
RETURNS TEXT[] AS $$
DECLARE
    signatures TEXT[] := '{}';
BEGIN
    -- SQL Injection patterns
    IF payload ~* '(union|select|insert|update|delete|drop|create|alter)\s' THEN
        signatures := array_append(signatures, 'SQL_INJECTION');
    END IF;
    
    -- XSS patterns
    IF payload ~* '<script|javascript:|onload=|onerror=' THEN
        signatures := array_append(signatures, 'XSS');
    END IF;
    
    -- Command injection patterns
    IF payload ~* '(\||;|`|&&|\$\(|\${)' THEN
        signatures := array_append(signatures, 'COMMAND_INJECTION');
    END IF;
    
    -- Directory traversal patterns
    IF payload ~* '\.\./|\.\.\\|%2e%2e%2f|%2e%2e%5c' THEN
        signatures := array_append(signatures, 'DIRECTORY_TRAVERSAL');
    END IF;
    
    -- LDAP injection patterns
    IF payload ~* '(\*|\(|\)|&|\||!|=|<|>|~|%)' AND payload ~* 'cn=|ou=|dc=' THEN
        signatures := array_append(signatures, 'LDAP_INJECTION');
    END IF;
    
    -- Buffer overflow patterns
    IF length(payload) > 1000 AND payload ~ '[A-Za-z0-9]{100,}' THEN
        signatures := array_append(signatures, 'BUFFER_OVERFLOW');
    END IF;
    
    RETURN signatures;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to determine attack sophistication level
CREATE OR REPLACE FUNCTION securehoney.assess_attack_sophistication(
    payload TEXT,
    techniques TEXT[],
    duration_minutes INTEGER,
    unique_ports INTEGER
) RETURNS securehoney.skill_level AS $$
BEGIN
    -- Nation state indicators
    IF array_length(techniques, 1) >= 8 AND 
       duration_minutes >= 1440 AND  -- 24 hours
       unique_ports >= 10 THEN
        RETURN 'NATION_STATE';
    END IF;
    
    -- Expert indicators
    IF array_length(techniques, 1) >= 5 AND 
       duration_minutes >= 360 AND   -- 6 hours
       unique_ports >= 5 THEN
        RETURN 'EXPERT';
    END IF;
    
    -- Advanced indicators
    IF array_length(techniques, 1) >= 3 AND 
       duration_minutes >= 60 AND    -- 1 hour
       unique_ports >= 3 THEN
        RETURN 'ADVANCED';
    END IF;
    
    -- Intermediate indicators
    IF array_length(techniques, 1) >= 2 OR 
       duration_minutes >= 30 OR     -- 30 minutes
       unique_ports >= 2 THEN
        RETURN 'INTERMEDIATE';
    END IF;
    
    -- Default to script kiddie
    RETURN 'SCRIPT_KIDDIE';
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to generate attack fingerprint
CREATE OR REPLACE FUNCTION securehoney.generate_attack_fingerprint(
    source_ip INET,
    user_agent TEXT,
    attack_patterns TEXT[],
    timing_signature TEXT
) RETURNS VARCHAR(64) AS $$
BEGIN
    RETURN encode(
        digest(
            COALESCE(source_ip::TEXT, '') || '|' ||
            COALESCE(user_agent, '') || '|' ||
            COALESCE(array_to_string(attack_patterns, ','), '') || '|' ||
            COALESCE(timing_signature, ''),
            'sha256'
        ),
        'hex'
    );
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Trigger function to auto-update threat scores
CREATE OR REPLACE FUNCTION securehoney.update_threat_score_trigger()
RETURNS TRIGGER AS $$
BEGIN
    -- Update attacker profile threat score when new attack is added
    UPDATE attacker_profiles 
    SET reputation_score = securehoney.calculate_threat_score(
        (SELECT COUNT(*) FROM attacks WHERE source_ip = NEW.source_ip),
        (SELECT AVG(
            CASE severity
                WHEN 'LOW' THEN 1
                WHEN 'MEDIUM' THEN 2  
                WHEN 'HIGH' THEN 3
                WHEN 'CRITICAL' THEN 4
            END
        ) FROM attacks WHERE source_ip = NEW.source_ip),
        (SELECT COUNT(DISTINCT attack_type) FROM attacks WHERE source_ip = NEW.source_ip),
        (SELECT EXTRACT(EPOCH FROM (MAX(timestamp) - MIN(timestamp)))/3600 
         FROM attacks WHERE source_ip = NEW.source_ip)::INTEGER
    ),
    last_seen = NEW.timestamp
    WHERE source_ip = NEW.source_ip;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- View for attack summary with enhanced analytics
CREATE OR REPLACE VIEW securehoney.attack_analytics AS
SELECT 
    a.source_ip,
    COUNT(*) as total_attacks,
    COUNT(DISTINCT a.attack_type) as unique_attack_types,
    COUNT(DISTINCT a.target_port) as unique_target_ports,
    AVG(CASE a.severity
        WHEN 'LOW' THEN 1
        WHEN 'MEDIUM' THEN 2
        WHEN 'HIGH' THEN 3  
        WHEN 'CRITICAL' THEN 4
    END) as avg_severity,
    MIN(a.timestamp) as first_attack,
    MAX(a.timestamp) as last_attack,
    EXTRACT(EPOCH FROM (MAX(a.timestamp) - MIN(a.timestamp)))/3600 as campaign_duration_hours,
    g.country,
    g.country_code,
    ap.threat_level,
    ap.skill_level,
    ap.reputation_score
FROM attacks a
LEFT JOIN geolocation_data g ON a.source_ip = g.ip_address
LEFT JOIN attacker_profiles ap ON a.source_ip = ap.source_ip
GROUP BY a.source_ip, g.country, g.country_code, ap.threat_level, ap.skill_level, ap.reputation_score;

-- Materialized view for performance on large datasets
CREATE MATERIALIZED VIEW securehoney.daily_attack_stats AS
SELECT 
    DATE(timestamp) as attack_date,
    COUNT(*) as total_attacks,
    COUNT(DISTINCT source_ip) as unique_attackers,
    COUNT(DISTINCT target_port) as unique_ports_targeted,
    COUNT(*) FILTER (WHERE severity = 'CRITICAL') as critical_attacks,
    COUNT(*) FILTER (WHERE severity = 'HIGH') as high_attacks,
    COUNT(*) FILTER (WHERE severity = 'MEDIUM') as medium_attacks,
    COUNT(*) FILTER (WHERE severity = 'LOW') as low_attacks,
    array_agg(DISTINCT attack_type) as attack_types_seen
FROM attacks
GROUP BY DATE(timestamp)
ORDER BY attack_date DESC;

-- Index for performance optimization
CREATE INDEX IF NOT EXISTS idx_attacks_source_ip_timestamp ON attacks(source_ip, timestamp);
CREATE INDEX IF NOT EXISTS idx_attacks_type_severity ON attacks(attack_type, severity);
CREATE INDEX IF NOT EXISTS idx_attacks_timestamp_desc ON attacks(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_geolocation_country ON geolocation_data(country_code, country);

-- Refresh materialized view function
CREATE OR REPLACE FUNCTION securehoney.refresh_daily_stats()
RETURNS VOID AS $$
BEGIN
    REFRESH MATERIALIZED VIEW securehoney.daily_attack_stats;
END;
$$ LANGUAGE plpgsql;

-- Comments for documentation
COMMENT ON SCHEMA securehoney IS 'SecureHoney honeypot system custom data types and functions';
COMMENT ON TYPE securehoney.attack_severity IS 'Enumeration of attack severity levels';
COMMENT ON TYPE securehoney.threat_level IS 'Enumeration of threat assessment levels';
COMMENT ON TYPE securehoney.geolocation IS 'Composite type for IP geolocation data';
COMMENT ON FUNCTION securehoney.calculate_threat_score IS 'Calculates threat score based on attack patterns and behavior';
COMMENT ON VIEW securehoney.attack_analytics IS 'Comprehensive attack analytics with geolocation and threat assessment';
