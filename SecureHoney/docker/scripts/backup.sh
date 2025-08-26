#!/bin/bash
set -e

# Database backup script for SecureHoney
BACKUP_DIR="/backups"
DB_HOST="database"
DB_NAME="${POSTGRES_DB:-securehoney}"
DB_USER="${POSTGRES_USER:-securehoney}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/securehoney_backup_${TIMESTAMP}.sql"

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}"

echo "Starting database backup at $(date)"

# Create database dump
pg_dump -h "${DB_HOST}" -U "${DB_USER}" -d "${DB_NAME}" \
    --verbose --clean --no-owner --no-privileges \
    --format=custom > "${BACKUP_FILE}"

# Compress the backup
gzip "${BACKUP_FILE}"
BACKUP_FILE="${BACKUP_FILE}.gz"

echo "Backup completed: ${BACKUP_FILE}"

# Keep only last 7 days of backups
find "${BACKUP_DIR}" -name "securehoney_backup_*.sql.gz" -mtime +7 -delete

echo "Old backups cleaned up"
echo "Backup process completed at $(date)"
