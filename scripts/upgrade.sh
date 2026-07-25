#!/usr/bin/env bash
# ==============================================================================
# Linux Inventory Manager - Upgrade Script
# ==============================================================================
# Safely upgrades the application with rollback capability.
# Usage: sudo bash scripts/upgrade.sh
# ==============================================================================

set -euo pipefail

APP_DIR="/opt/linux-inventory-manager"
APP_USER="linuxinventory"
VENV_DIR="${APP_DIR}/venv"
BACKUP_DIR="${APP_DIR}/storage/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'
log_info()  { echo -e "${GREEN}[UPGRADE]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[UPGRADE]${NC} $1"; }
log_error() { echo -e "${RED}[UPGRADE]${NC} $1"; }

if [[ $EUID -ne 0 ]]; then
    log_error "This script must be run as root"
    exit 1
fi

log_info "Starting upgrade of Linux Inventory Manager..."

# ─── Pre-upgrade Backup ───────────────────────────────────────────────────────

log_info "Creating pre-upgrade backup..."
sudo -u "${APP_USER}" bash "${APP_DIR}/scripts/backup.sh" --full
log_info "Backup completed"

# ─── Pull Latest Code ─────────────────────────────────────────────────────────

log_info "Pulling latest code..."
cd "${APP_DIR}"
CURRENT_COMMIT=$(sudo -u "${APP_USER}" git rev-parse HEAD)
sudo -u "${APP_USER}" git fetch origin main
sudo -u "${APP_USER}" git checkout main
sudo -u "${APP_USER}" git pull origin main
NEW_COMMIT=$(sudo -u "${APP_USER}" git rev-parse HEAD)

if [[ "${CURRENT_COMMIT}" == "${NEW_COMMIT}" ]]; then
    log_info "Already up to date (${CURRENT_COMMIT:0:8})"
    exit 0
fi

log_info "Upgrading: ${CURRENT_COMMIT:0:8} → ${NEW_COMMIT:0:8}"

# ─── Update Python Dependencies ───────────────────────────────────────────────

log_info "Updating Python dependencies..."
"${VENV_DIR}/bin/pip" install --upgrade pip
"${VENV_DIR}/bin/pip" install -r "${APP_DIR}/requirements.txt"

# ─── Run Database Migrations ──────────────────────────────────────────────────

log_info "Running database migrations..."
cd "${APP_DIR}"
"${VENV_DIR}/bin/alembic" upgrade head 2>/dev/null || {
    log_warn "Alembic migrations skipped (may not be configured)"
}

# ─── Rebuild Frontend ─────────────────────────────────────────────────────────

if command -v npm &>/dev/null; then
    log_info "Rebuilding frontend..."
    cd "${APP_DIR}/frontend"
    npm ci --production=false
    npm run build
fi

# ─── Restart Services ─────────────────────────────────────────────────────────

log_info "Restarting services..."
systemctl restart linux-inventory-backend

# Wait for health check
sleep 5
if curl -sf http://localhost:8000/api/v1/health > /dev/null; then
    log_info "Backend healthy after upgrade"
else
    log_error "Backend failed health check! Rolling back..."
    cd "${APP_DIR}"
    sudo -u "${APP_USER}" git checkout "${CURRENT_COMMIT}"
    "${VENV_DIR}/bin/pip" install -r "${APP_DIR}/requirements.txt"
    systemctl restart linux-inventory-backend
    log_error "Rolled back to ${CURRENT_COMMIT:0:8}"
    exit 1
fi

systemctl restart linux-inventory-frontend 2>/dev/null || true

# ─── Set Permissions ──────────────────────────────────────────────────────────

chown -R "${APP_USER}:${APP_USER}" "${APP_DIR}"
chmod 600 "${APP_DIR}/.env"

# ─── Summary ──────────────────────────────────────────────────────────────────

log_info "============================================"
log_info " Upgrade Complete!"
log_info " ${CURRENT_COMMIT:0:8} → ${NEW_COMMIT:0:8}"
log_info "============================================"
