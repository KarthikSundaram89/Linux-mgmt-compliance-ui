#!/usr/bin/env bash
# ==============================================================================
# Linux Inventory Manager - Backup Script
# ==============================================================================
# Creates timestamped backups of database, configuration, and snapshots.
# Usage: bash scripts/backup.sh [--full|--db-only|--config-only]
# ==============================================================================

set -euo pipefail

APP_DIR="/opt/linux-inventory-manager"
BACKUP_DIR="${APP_DIR}/storage/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'
log_info() { echo -e "${GREEN}[BACKUP]${NC} $(date +%H:%M:%S) $1"; }
log_warn() { echo -e "${YELLOW}[BACKUP]${NC} $(date +%H:%M:%S) $1"; }

BACKUP_TYPE="${1:-full}"
BACKUP_PATH="${BACKUP_DIR}/${TIMESTAMP}"

mkdir -p "${BACKUP_PATH}"

log_info "Starting ${BACKUP_TYPE} backup → ${BACKUP_PATH}"

# ─── Database Backup ──────────────────────────────────────────────────────────

backup_database() {
    log_info "Backing up database..."
    DB_FILE="${APP_DIR}/storage/inventory.db"
    if [[ -f "${DB_FILE}" ]]; then
        # Use SQLite .backup for consistent copy
        sqlite3 "${DB_FILE}" ".backup '${BACKUP_PATH}/inventory.db'"
        gzip "${BACKUP_PATH}/inventory.db"
        log_info "Database backup: $(du -h "${BACKUP_PATH}/inventory.db.gz" | cut -f1)"
    else
        log_warn "Database file not found: ${DB_FILE}"
    fi
}

# ─── Configuration Backup ─────────────────────────────────────────────────────

backup_config() {
    log_info "Backing up configuration..."
    mkdir -p "${BACKUP_PATH}/config"
    # Copy config (excluding secrets)
    cp "${APP_DIR}/.env" "${BACKUP_PATH}/config/.env" 2>/dev/null || true
    cp -r "${APP_DIR}/config/"*.conf "${BACKUP_PATH}/config/" 2>/dev/null || true
    cp "${APP_DIR}/config/"*.service "${BACKUP_PATH}/config/" 2>/dev/null || true
    # Remove actual secrets from backup
    sed -i 's/SECRET_KEY=.*/SECRET_KEY=REDACTED/g' "${BACKUP_PATH}/config/.env" 2>/dev/null || true
    log_info "Configuration backed up"
}

# ─── Snapshot Metadata Backup ─────────────────────────────────────────────────

backup_snapshots() {
    log_info "Backing up snapshot metadata..."
    SNAP_DIR="${APP_DIR}/storage/snapshots"
    if [[ -d "${SNAP_DIR}" ]]; then
        # Only backup file listing (actual snapshots are large)
        find "${SNAP_DIR}" -name "*.json.gz" -type f > "${BACKUP_PATH}/snapshot_inventory.txt"
        SNAP_COUNT=$(wc -l < "${BACKUP_PATH}/snapshot_inventory.txt")
        log_info "Snapshot inventory: ${SNAP_COUNT} files indexed"
    fi
}

# ─── Execute Backup ───────────────────────────────────────────────────────────

case "${BACKUP_TYPE}" in
    full)
        backup_database
        backup_config
        backup_snapshots
        ;;
    db-only|--db-only)
        backup_database
        ;;
    config-only|--config-only)
        backup_config
        ;;
    *)
        backup_database
        backup_config
        backup_snapshots
        ;;
esac

# ─── Create Archive ───────────────────────────────────────────────────────────

log_info "Creating archive..."
ARCHIVE="${BACKUP_DIR}/backup_${TIMESTAMP}.tar.gz"
tar -czf "${ARCHIVE}" -C "${BACKUP_DIR}" "${TIMESTAMP}"
rm -rf "${BACKUP_PATH}"

ARCHIVE_SIZE=$(du -h "${ARCHIVE}" | cut -f1)
log_info "Archive created: ${ARCHIVE} (${ARCHIVE_SIZE})"

# ─── Verify Backup ───────────────────────────────────────────────────────────

log_info "Verifying backup integrity..."
if tar -tzf "${ARCHIVE}" &>/dev/null; then
    log_info "Backup verification: PASSED"
else
    log_warn "Backup verification: FAILED"
    exit 1
fi

# ─── Cleanup Old Backups ──────────────────────────────────────────────────────

log_info "Cleaning up backups older than ${RETENTION_DAYS} days..."
DELETED=$(find "${BACKUP_DIR}" -name "backup_*.tar.gz" -mtime +${RETENTION_DAYS} -delete -print | wc -l)
if [[ ${DELETED} -gt 0 ]]; then
    log_info "Removed ${DELETED} old backup(s)"
fi

# ─── Summary ──────────────────────────────────────────────────────────────────

log_info "Backup complete: ${ARCHIVE} (${ARCHIVE_SIZE})"
