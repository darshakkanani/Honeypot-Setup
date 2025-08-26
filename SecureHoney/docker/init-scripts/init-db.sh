#!/bin/bash
set -e

# Wait for PostgreSQL to be ready
until pg_isready -h localhost -p 5432 -U "$POSTGRES_USER"; do
  echo "Waiting for PostgreSQL to be ready..."
  sleep 2
done

echo "PostgreSQL is ready. Initializing SecureHoney database..."

# Create the schema and initial data
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Set search path
    SET search_path TO securehoney, public;
    
    -- Insert default admin user if not exists
    INSERT INTO securehoney.admin_users (username, email, password_hash, salt, role)
    SELECT 'admin', 'admin@securehoney.local', 
           '\$2b\$12\$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/A5/jF3kkS', 
           'randomsalt123', 'admin'
    WHERE NOT EXISTS (
        SELECT 1 FROM securehoney.admin_users WHERE username = 'admin'
    );
    
    -- Insert default system configuration
    INSERT INTO securehoney.system_config (config_key, config_value, config_type, description)
    VALUES 
        ('honeypot.enabled', 'true', 'boolean', 'Enable/disable honeypot system'),
        ('honeypot.ports', '[22, 80, 443, 21, 23, 25, 53, 110, 143, 993, 995, 3306, 5432, 6379, 9200]', 'array', 'Ports to monitor'),
        ('alerts.email_enabled', 'false', 'boolean', 'Enable email alerts'),
        ('dashboard.refresh_interval', '30', 'integer', 'Dashboard refresh interval in seconds')
    ON CONFLICT (config_key) DO NOTHING;
    
    -- Refresh materialized views
    REFRESH MATERIALIZED VIEW IF EXISTS securehoney.dashboard_stats;
    REFRESH MATERIALIZED VIEW IF EXISTS securehoney.geographic_stats;
    
    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA securehoney TO securehoney;
    GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA securehoney TO securehoney;
EOSQL

echo "SecureHoney database initialization completed!"
