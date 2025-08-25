# SecureHoney Admin Panel Database

Complete database implementation for the SecureHoney honeypot system admin panel.

## Overview

This database system provides comprehensive data storage and management for:
- Attack event tracking and analysis
- Attacker profiling and behavioral analysis
- System configuration and user management
- Real-time alerting and monitoring
- Audit logging and compliance

## Components

### 1. Database Schema (`schema.sql`)
Complete PostgreSQL schema with:
- **Core Tables**: attacks, attacker_profiles, attack_sessions
- **Admin Tables**: admin_users, admin_sessions, system_config
- **Intelligence Tables**: threat_intelligence, geolocation_data
- **Analysis Tables**: attack_patterns, malware_analysis
- **Monitoring Tables**: system_metrics, alerts

### 2. Configuration (`config.py`)
Database connection and configuration management:
- Environment-based configuration
- SSL/TLS support
- Connection pooling
- Health monitoring
- Async connection support

### 3. Models (`models_admin.py`)
SQLAlchemy ORM models for admin panel:
- `AdminUser`: User authentication and authorization
- `AdminSession`: Session management
- `SystemConfig`: Configuration storage
- `Alert`: System alerting
- `AdminAuditLog`: Audit trail

### 4. Initialization (`init_db.py`)
Database setup and initialization:
- Schema creation
- Initial data population
- Health verification
- Reset capabilities

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Database
Set environment variables:
```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=securehoney
export DB_USER=securehoney
export DB_PASSWORD=your_password
export DB_SCHEMA=securehoney
```

### 3. Initialize Database
```bash
python init_db.py
```

### 4. Verify Installation
```bash
python init_db.py --verify-only
```

## Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_HOST` | localhost | Database host |
| `DB_PORT` | 5432 | Database port |
| `DB_NAME` | securehoney | Database name |
| `DB_USER` | securehoney | Database user |
| `DB_PASSWORD` | - | Database password |
| `DB_SCHEMA` | securehoney | Schema name |
| `DB_POOL_SIZE` | 10 | Connection pool size |
| `DB_SSL_MODE` | prefer | SSL mode |

### Configuration File
Alternatively, create `database_config.json`:
```json
{
  "host": "localhost",
  "port": 5432,
  "database": "securehoney",
  "username": "securehoney",
  "password": "your_password",
  "schema": "securehoney",
  "pool_size": 10,
  "ssl_mode": "require"
}
```

## Usage Examples

### Basic Database Operations
```python
from database.models_admin import admin_db

# Create user
user = admin_db.create_user("admin", "admin@example.com", "password123")

# Authenticate
session = admin_db.authenticate_user("admin", "password123", "127.0.0.1")

# Get dashboard data
stats = admin_db.get_dashboard_summary()
```

### Configuration Management
```python
# Set configuration
admin_db.set_config("honeypot.enabled", True, user_id=1, config_type="boolean")

# Get configuration
enabled = admin_db.get_config("honeypot.enabled")
```

### Alert Management
```python
# Create alert
alert = admin_db.create_alert(
    "HIGH_THREAT", "HIGH", 
    "Multiple attacks detected",
    source_ip="192.168.1.100"
)

# Get unresolved alerts
alerts = admin_db.get_unresolved_alerts()
```

## Database Schema Details

### Core Attack Tables
- **attacks**: Individual attack events with full metadata
- **attack_sessions**: Grouped attacks from same source
- **attacker_profiles**: Comprehensive attacker analysis
- **attack_patterns**: Detected attack signatures

### Admin Panel Tables
- **admin_users**: System administrators and analysts
- **admin_sessions**: Authentication sessions
- **admin_audit_log**: Complete audit trail
- **system_config**: System configuration settings

### Intelligence Tables
- **threat_intelligence**: External threat data
- **geolocation_data**: IP geolocation information
- **malware_analysis**: Malware sample analysis

## Security Features

### Authentication
- Secure password hashing with bcrypt
- Account lockout protection
- Session management with expiration
- Role-based access control

### Audit Logging
- Complete action audit trail
- IP address and user agent tracking
- Resource-level change tracking
- Compliance reporting support

### Data Protection
- Sensitive configuration masking
- SQL injection prevention
- Connection encryption support
- Input validation and sanitization

## Performance Optimization

### Indexing Strategy
- Source IP indexing for fast lookups
- Timestamp indexing for time-based queries
- Composite indexes for common query patterns
- Partial indexes for active records

### Materialized Views
- Pre-computed dashboard statistics
- Geographic attack distribution
- Daily attack summaries
- Automatic refresh functions

### Connection Pooling
- Configurable pool sizes
- Connection recycling
- Timeout management
- Health monitoring

## Monitoring and Maintenance

### Health Checks
```python
from database.config import get_health_status

health = get_health_status()
print(f"Database status: {health['status']}")
```

### Data Retention
- Configurable retention policies
- Automatic cleanup of old data
- Archive functionality
- Performance impact monitoring

### Backup Recommendations
- Regular PostgreSQL dumps
- Point-in-time recovery setup
- Configuration backup
- Disaster recovery planning

## Troubleshooting

### Common Issues

1. **Connection Failures**
   - Check database credentials
   - Verify network connectivity
   - Review SSL configuration
   - Check firewall settings

2. **Performance Issues**
   - Monitor connection pool usage
   - Review query execution plans
   - Check index utilization
   - Analyze slow query logs

3. **Schema Issues**
   - Verify schema permissions
   - Check custom type installation
   - Review migration status
   - Validate table structures

### Diagnostic Commands
```bash
# Test connection
python -c "from database.config import test_connection; print(test_connection())"

# Check health
python init_db.py --verify-only

# Reset database (WARNING: destroys data)
python init_db.py --reset
```

## Integration

### With Honeypot Engine
```python
from database.database_integration import log_attack

# Log attack from honeypot
attack_data = {
    'source_ip': '192.168.1.100',
    'target_port': 22,
    'attack_type': 'BRUTE_FORCE',
    'severity': 'HIGH',
    'payload': 'ssh login attempt'
}
log_attack(attack_data)
```

### With Admin Panel API
```python
from database.models_admin import admin_db

# Authenticate API request
user = admin_db.validate_session(session_token)
if user:
    # Process authenticated request
    pass
```

## Development

### Running Tests
```bash
pytest tests/
```

### Code Quality
```bash
black database/
flake8 database/
mypy database/
```

### Database Migrations
```bash
alembic init alembic
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review database logs
3. Verify configuration settings
4. Test with minimal setup

## License

Part of the SecureHoney honeypot system.
