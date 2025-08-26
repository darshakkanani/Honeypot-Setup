"""
Configuration management for SecureHoney backend
"""

import os
import secrets
from typing import List, Optional

class Config:
    """Application configuration"""
    
    # Application
    APP_NAME: str = "SecureHoney Admin API"
    VERSION: str = "3.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "5001"))
    
    # Database
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_NAME: str = os.getenv("DB_NAME", "securehoney")
    DB_USER: str = os.getenv("DB_USER", "securehoney")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "securehoney123")
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "20"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "0"))
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    # Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD") or None
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    
    # Security
    JWT_SECRET: str = os.getenv("JWT_SECRET", secrets.token_urlsafe(32))
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_HOURS: int = int(os.getenv("JWT_EXPIRY_HOURS", "24"))
    
    # Password policy
    MIN_PASSWORD_LENGTH: int = 8
    REQUIRE_UPPERCASE: bool = True
    REQUIRE_LOWERCASE: bool = True
    REQUIRE_NUMBERS: bool = True
    REQUIRE_SPECIAL_CHARS: bool = True
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: str = os.getenv("RATE_LIMIT_REQUESTS", "100/minute")
    LOGIN_RATE_LIMIT: str = os.getenv("LOGIN_RATE_LIMIT", "5/minute")
    
    # CORS
    CORS_ORIGINS: List[str] = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    CORS_ALLOW_CREDENTIALS: bool = True
    
    # Email
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_TLS: bool = os.getenv("SMTP_TLS", "true").lower() == "true"
    FROM_EMAIL: str = os.getenv("FROM_EMAIL", "noreply@securehoney.local")
    
    # Frontend
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # Registration
    REGISTRATION_ENABLED: bool = os.getenv("REGISTRATION_ENABLED", "false").lower() == "true"
    INVITE_CODE: str = os.getenv("INVITE_CODE", "securehoney2024")
    
    # Monitoring
    SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    METRICS_ENABLED: bool = os.getenv("METRICS_ENABLED", "true").lower() == "true"
    
    # File uploads
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "/tmp/uploads")
    
    # Webhook
    WEBHOOK_URL: Optional[str] = os.getenv("WEBHOOK_URL")
    WEBHOOK_SECRET: Optional[str] = os.getenv("WEBHOOK_SECRET")
    
    # Honeypot integration
    HONEYPOT_API_URL: str = os.getenv("HONEYPOT_API_URL", "http://localhost:8000")
    HONEYPOT_API_KEY: str = os.getenv("HONEYPOT_API_KEY", "")
    
    # Blockchain
    BLOCKCHAIN_ENABLED: bool = os.getenv("BLOCKCHAIN_ENABLED", "true").lower() == "true"
    BLOCKCHAIN_NODE_URL: str = os.getenv("BLOCKCHAIN_NODE_URL", "http://localhost:8545")
    
    # AI Analysis
    AI_ENABLED: bool = os.getenv("AI_ENABLED", "true").lower() == "true"
    AI_MODEL_PATH: str = os.getenv("AI_MODEL_PATH", "/app/models")
    
    # Backup
    BACKUP_ENABLED: bool = os.getenv("BACKUP_ENABLED", "true").lower() == "true"
    BACKUP_INTERVAL_HOURS: int = int(os.getenv("BACKUP_INTERVAL_HOURS", "24"))
    BACKUP_RETENTION_DAYS: int = int(os.getenv("BACKUP_RETENTION_DAYS", "7"))
    
    # Performance
    WORKER_PROCESSES: int = int(os.getenv("WORKER_PROCESSES", "1"))
    WORKER_CONNECTIONS: int = int(os.getenv("WORKER_CONNECTIONS", "1000"))
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        if not self.JWT_SECRET or len(self.JWT_SECRET) < 32:
            errors.append("JWT_SECRET must be at least 32 characters long")
        
        if not self.DB_PASSWORD:
            errors.append("DB_PASSWORD is required")
        
        if self.SMTP_HOST and not self.SMTP_USER:
            errors.append("SMTP_USER is required when SMTP_HOST is set")
        
        return errors

# Global config instance
config = Config()

# Validate configuration on import
validation_errors = config.validate()
if validation_errors:
    raise ValueError(f"Configuration errors: {', '.join(validation_errors)}")
