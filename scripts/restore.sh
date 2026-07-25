#!/usr/bin/env bash
# ==============================================================================
# Linux Inventory Manager - Restore Script
# ==============================================================================
# Restores from a backup archive created by backup.sh.
# Usage: sudo bash scripts/restore.sh <backup_file.tar.gz>
# ==============================================================================

set -euo pipefail

APP_DIR="/opt/linux-inventory-manager"
APP_USER="linuxinventory"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'
log_info()  { echo -e "${GREEN}[RESTORE]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[RESTORE]${NC} $1"; }
log_error() { echo -e "${RED}[RESTORE]${NC} $1"; }

if [[ $EUID -ne 0 ]]; then
    log_error "This script must be run as root"
    exit 1
fi

BACKUP_FILE="${1:-}"
if [[ -z "${BACKUP_FILE}" || ! -f "${BACKUP_FILE}" ]]; then
    log_error "Usage: $0 <backup_file.tar.gz>"
    log_info "Available backups:"
    ls -lh "${APP_DIR}/storage/backups/backup_"*.tar.gz 2>/dev/null || echo "  None found"
    exit 1
fi

log_info "Restoring from: ${BACKUP_FILE}"

# ─── Verify Backup ───────────────────────────────────────────────────────────

log_info "Verifying backup integrity..."
if ! tar -tzf "${BACKUP_FILE}" &>/dev/null; then
    log_error "Backup file is corrupted"
    exit 1
fi
log_info "Backup verified"

# ─── Stop Services ───────────────────────────────────────────────────────────

log_info "Stopping services..."
systemctl stop linux-inventory-backend 2>/dev/null || true

# ─── Extract Backup ──────────────────────────────────────────────────────────

TEMP_DIR=$(mktemp -d)
log_info "Extracting to ${TEMP_DIR}..."
tar -xzf "${BACKUP_FILE}" -C "${TEMP_DIR}"
RESTORE_DIR=$(find "${TEMP_DIR}" -mindepth 1 -maxdepth 1 -type d | head -1)

# ─── Restore Database ────────────────────────────────────────────────────────

if [[ -f "${RESTORE_DIR}/inventory.db.gz" ]]; then
    log_info "Restoring database..."
    # Backup current DB first
    cp "${APP_DIR}/storage/inventory.db" "${APP_DIR}/storage/inventory.db.pre-restore" 2>/dev/null || true
    gunzip -c "${RESTORE_DIR}/inventory.db.gz" > "${APP_DIR}/storage/inventory.db"
    chown "${APP_USER}:${APP_USER}" "${APP_DIR}/storage/inventory.db"
    log_info "Database restored"
else
    log_warn "No database in backup, skipping..."
fi

# ─── Restore Configuration ───────────────────────────────────────────────────

if [[ -d "${RESTORE_DIR}/config" ]]; then
    log_info "Restoring configuration..."
    # Don't overwrite .env (may have secrets)
    log_warn "Configuration files available in backup but NOT auto-restored"
    log_warn "Review: ${RESTORE_DIR}/config/"
fi

# ─── Cleanup ─────────────────────────────────────────────────────────────────

rm -rf "${TEMP_DIR}"

# ─── Restart Services ────────────────────────────────────────────────────────

log_info "Starting services..."
systemctl start linux-inventory-backend

sleep 3
if systemctl is-active --quiet linux-inventory-backend; then
    log_info "Backend started successfully after restore"
else
    log_error "Backend failed to start! Check logs."
    exit 1
fi

log_info "============================================"
log_info " Restore Complete!"
log_info "============================================"
