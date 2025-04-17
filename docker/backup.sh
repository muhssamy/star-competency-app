#!/bin/bash

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="/app/backups"
DB_BACKUP_FILE="${BACKUP_DIR}/${DB_NAME}_${TIMESTAMP}.dump"
UPLOADS_BACKUP_FILE="${BACKUP_DIR}/uploads_${TIMESTAMP}.tar.gz"
KEEP_DAYS=30

# Create backup directory
mkdir -p "${BACKUP_DIR}"

# Database backup
echo "Starting database backup at $(date)"
PGPASSWORD="${DB_PASSWORD}" pg_dump -h "${DB_HOST}" -U "${DB_USER}" -Fc "${DB_NAME}" > "${DB_BACKUP_FILE}"

# Verify database backup
if pg_restore --list "${DB_BACKUP_FILE}" >/dev/null 2>&1; then
    echo "Database backup verified successfully"
else
    echo "Database backup verification failed!"
    rm -f "${DB_BACKUP_FILE}"
    exit 1
fi

# Uploads backup
echo "Starting uploads backup at $(date)"
if [ -d "${UPLOADS_DIR}" ]; then
    tar -czf "${UPLOADS_BACKUP_FILE}" -C "$(dirname "${UPLOADS_DIR}")" "$(basename "${UPLOADS_DIR}")"
else
    echo "Uploads directory not found at ${UPLOADS_DIR}, skipping..."
fi

# Cleanup old backups
echo "Cleaning up backups older than ${KEEP_DAYS} days"
find "${BACKUP_DIR}" -name "*.dump" -o -name "*.tar.gz" -type f -mtime +${KEEP_DAYS} -delete

echo "Backup process completed at $(date)"