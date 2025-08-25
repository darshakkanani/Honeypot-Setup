# SecureHoney PostgreSQL Custom Data Types

This directory contains PostgreSQL-specific enhancements for the SecureHoney honeypot database system, including custom data types, functions, and optimized schemas.

## Features

### Custom Data Types

#### Enums
- `securehoney.attack_severity` - Attack severity levels (LOW, MEDIUM, HIGH, CRITICAL)
- `securehoney.threat_level` - Threat assessment levels (UNKNOWN, LOW, MEDIUM, HIGH, CRITICAL)
- `securehoney.attack_type` - Comprehensive attack type classification
- `securehoney.service_type` - Honeypot service types (SSH, HTTP, FTP, etc.)
- `securehoney.interaction_type` - Interaction classification
- `securehoney.skill_level` - Attacker skill assessment
- `securehoney.analysis_status` - Malware analysis status
- `securehoney.metric_type` - System metric types

#### Composite Types
- `securehoney.geolocation` - IP geolocation data structure
- `securehoney.attack_metadata` - Attack metadata composite
- `securehoney.behavioral_pattern` - Behavioral analysis patterns
- `securehoney.threat_intel` - Threat intelligence data

#### Domain Types
- `securehoney.ip_address` - Validated IP addresses
- `securehoney.port_number` - Valid port numbers (1-65535)
- `securehoney.hash_sha256` - SHA256 hash validation
- `securehoney.hash_md5` - MD5 hash validation
- `securehoney.confidence_score` - Confidence scores (0.0-1.0)
- `securehoney.reputation_score` - Reputation scores (0-100)

### Custom Functions

#### Analysis Functions
- `calculate_threat_score()` - Multi-factor threat scoring
- `extract_attack_signatures()` - Automatic signature extraction
- `assess_attack_sophistication()` - Skill level assessment
- `generate_attack_fingerprint()` - Attack fingerprinting
- `validate_attack_pattern()` - JSON schema validation

#### Utility Functions
- `update_threat_score_trigger()` - Automatic threat score updates
- `refresh_daily_stats()` - Materialized view refresh

### Views and Analytics

#### Views
- `securehoney.attack_analytics` - Comprehensive attack analysis
- `securehoney.daily_attack_stats` - Daily statistics (materialized)

#### Indexes
- Performance-optimized indexes for all major queries
- GIN indexes for JSONB columns
- Composite indexes for common query patterns

## Setup Instructions

### 1. Prerequisites
```bash
# Install PostgreSQL (Ubuntu/Debian)
sudo apt-get install postgresql postgresql-contrib

# Install Python dependencies
pip install psycopg2-binary sqlalchemy
```

### 2. Environment Variables
```bash
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=securehoney
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=securehoney
```

### 3. Run Migration
```bash
# Run the migration script
python postgresql_migration.py

# Or run individual steps
python -c "
from postgresql_migration import PostgreSQLMigrator
migrator = PostgreSQLMigrator()
migrator.run_full_migration()
"
```

### 4. Verify Installation
```sql
-- Check custom types
SELECT typname FROM pg_type 
WHERE typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'securehoney')
ORDER BY typname;

-- Test custom functions
SELECT securehoney.calculate_threat_score(50, 3.5, 8, 72);

-- Query with custom types
SELECT * FROM attacks 
WHERE severity = 'HIGH'::securehoney.attack_severity
AND attack_type = 'SQL_INJECTION'::securehoney.attack_type;
```

## Usage Examples

### Insert Attack with Custom Types
```python
from models_postgresql import postgresql_db

attack_data = {
    'attack_id': 'attack_12345',
    'source_ip': '192.168.1.100',
    'target_port': 22,
    'attack_type': 'BRUTE_FORCE',
    'severity': 'HIGH',
    'confidence': 0.95,
    'payload': 'ssh brute force attempt',
    'signatures': ['BRUTE_FORCE', 'SSH_ATTACK']
}

attack_id = postgresql_db.insert_attack_with_types(attack_data)
```

### Query with Enums
```python
# Get high severity attacks
high_severity_attacks = postgresql_db.get_attacks_by_severity('HIGH')

# Get critical threat actors
critical_threats = postgresql_db.get_threat_actors_by_level('CRITICAL')
```

### Use Custom Functions
```python
# Calculate threat score
threat_score = postgresql_db.execute_custom_function(
    'calculate_threat_score', 
    attack_count=50, 
    severity_avg=3.2, 
    unique_techniques=8, 
    time_span_hours=72
)

# Extract attack signatures
signatures = postgresql_db.execute_custom_function(
    'extract_attack_signatures', 
    "SELECT * FROM users WHERE 1=1"
)
```

### Advanced Queries
```sql
-- Get attack analytics with geolocation
SELECT 
    source_ip,
    total_attacks,
    avg_severity,
    country,
    threat_level,
    skill_level
FROM securehoney.attack_analytics
WHERE threat_level IN ('HIGH', 'CRITICAL')
ORDER BY reputation_score DESC;

-- Daily attack trends
SELECT 
    attack_date,
    total_attacks,
    unique_attackers,
    critical_attacks,
    attack_types_seen
FROM securehoney.daily_attack_stats
WHERE attack_date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY attack_date DESC;

-- Sophisticated attackers
SELECT 
    source_ip,
    skill_level,
    total_attacks,
    unique_attack_types,
    campaign_duration_hours
FROM securehoney.attack_analytics
WHERE skill_level IN ('EXPERT', 'NATION_STATE')
ORDER BY campaign_duration_hours DESC;
```

## Performance Optimizations

### Indexes Created
- `idx_attacks_source_ip_time` - Source IP and timestamp
- `idx_attacks_type_severity` - Attack type and severity
- `idx_attacks_payload_hash` - Payload hash lookup
- `idx_attacker_profiles_threat` - Threat level and reputation
- `idx_geolocation_country` - Country-based queries
- GIN indexes for all JSONB columns

### Materialized Views
- `securehoney.daily_attack_stats` - Pre-computed daily statistics
- Automatic refresh function available

### Query Optimization Tips
1. Use enum values directly in queries for better performance
2. Leverage composite indexes for multi-column filters
3. Use materialized views for complex analytics
4. Refresh materialized views during low-traffic periods

## Maintenance

### Regular Tasks
```sql
-- Refresh materialized views
SELECT securehoney.refresh_daily_stats();

-- Update table statistics
ANALYZE attacks;
ANALYZE attacker_profiles;

-- Check index usage
SELECT schemaname, tablename, indexname, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_tup_read DESC;
```

### Backup and Recovery
```bash
# Backup with custom types
pg_dump -h localhost -U postgres -d securehoney -f securehoney_backup.sql

# Restore
psql -h localhost -U postgres -d securehoney -f securehoney_backup.sql
```

## Integration with SecureHoney

The PostgreSQL custom types integrate seamlessly with the existing SecureHoney components:

1. **Honeypot Engine** - Uses typed models for attack logging
2. **Admin Panel** - Enhanced queries with type safety
3. **Analytics** - Advanced analysis with custom functions
4. **Geolocation** - Composite type for location data
5. **Threat Intelligence** - Structured threat data storage

## Benefits

1. **Type Safety** - Enum constraints prevent invalid data
2. **Performance** - Optimized indexes and materialized views
3. **Data Integrity** - Domain constraints and validation
4. **Advanced Analytics** - Custom functions for complex analysis
5. **Scalability** - PostgreSQL-specific optimizations
6. **Maintainability** - Clear schema with documented types

## Troubleshooting

### Common Issues

1. **Enum Value Errors**
   ```sql
   -- Check valid enum values
   SELECT enumlabel FROM pg_enum 
   WHERE enumtypid = 'securehoney.attack_severity'::regtype;
   ```

2. **Function Not Found**
   ```sql
   -- Check if functions exist
   SELECT proname FROM pg_proc 
   WHERE pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'securehoney');
   ```

3. **Permission Issues**
   ```sql
   -- Grant schema usage
   GRANT USAGE ON SCHEMA securehoney TO your_user;
   GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA securehoney TO your_user;
   ```

For additional support, check the migration logs and verify all custom types and functions are properly created.
