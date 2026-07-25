#!/usr/bin/env bash
# ==============================================================================
# Linux Inventory Manager - Installation Script
# ==============================================================================
# Target: Amazon Linux 2023 / RHEL 8+ / Ubuntu 22.04+
# Usage:  sudo bash scripts/install.sh
# ==============================================================================

set -euo pipefail

APP_NAME="linux-inventory-manager"
APP_USER="linuxinventory"
APP_GROUP="linuxinventory"
INSTALL_DIR="/opt/${APP_NAME}"
VENV_DIR="${INSTALL_DIR}/venv"
LOG_DIR="${INSTALL_DIR}/logs"
STORAGE_DIR="${INSTALL_DIR}/storage"
CONFIG_DIR="${INSTALL_DIR}/config"
PYTHON_VERSION="3.12"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ─── Pre-flight Checks ────────────────────────────────────────────────────────

if [[ $EUID -ne 0 ]]; then
    log_error "This script must be run as root (sudo)"
    exit 1
fi

log_info "Starting ${APP_NAME} installation..."

# ─── Create Application User ──────────────────────────────────────────────────

if ! id "${APP_USER}" &>/dev/null; then
    log_info "Creating application user: ${APP_USER}"
    useradd -r -m -d "${INSTALL_DIR}" -s /bin/bash "${APP_USER}"
else
    log_info "User ${APP_USER} already exists"
fi

# ─── Create Directory Structure ───────────────────────────────────────────────

log_info "Creating directory structure..."
mkdir -p "${INSTALL_DIR}"/{storage/{snapshots,reports,exports,backups},logs,config}
mkdir -p "${INSTALL_DIR}"/frontend/dist

# ─── Install System Dependencies ──────────────────────────────────────────────

log_info "Installing system dependencies..."

if command -v dnf &>/dev/null; then
    # Amazon Linux 2023 / RHEL 9 / Rocky 9
    dnf install -y python3.12 python3.12-pip python3.12-devel \
        gcc libffi-devel openssl-devel nginx git
elif command -v yum &>/dev/null; then
    # RHEL 8 / CentOS 8
    yum install -y python3 python3-pip python3-devel \
        gcc libffi-devel openssl-devel nginx git
elif command -v apt-get &>/dev/null; then
    # Ubuntu / Debian
    apt-get update
    apt-get install -y python3.12 python3.12-venv python3.12-dev \
        python3-pip gcc libffi-dev libssl-dev nginx git
fi

# ─── Create Virtual Environment ───────────────────────────────────────────────

log_info "Creating Python virtual environment..."
if command -v python3.12 &>/dev/null; then
    python3.12 -m venv "${VENV_DIR}"
else
    python3 -m venv "${VENV_DIR}"
fi

# ─── Install Python Dependencies ──────────────────────────────────────────────

log_info "Installing Python dependencies..."
"${VENV_DIR}/bin/pip" install --upgrade pip setuptools wheel
"${VENV_DIR}/bin/pip" install -r "${INSTALL_DIR}/requirements.txt"

# ─── Configuration ────────────────────────────────────────────────────────────

if [[ ! -f "${INSTALL_DIR}/.env" ]]; then
    log_info "Creating default configuration..."
    cp "${CONFIG_DIR}/.env.example" "${INSTALL_DIR}/.env"

    # Generate a strong secret key
    SECRET_KEY=$("${VENV_DIR}/bin/python" -c "import secrets; print(secrets.token_urlsafe(64))")
    sed -i "s|CHANGE-ME-USE-STRONG-RANDOM-VALUE|${SECRET_KEY}|g" "${INSTALL_DIR}/.env"

    log_warn "IMPORTANT: Edit ${INSTALL_DIR}/.env with your production settings"
else
    log_info "Configuration file already exists, skipping..."
fi

# ─── Initialize Database ──────────────────────────────────────────────────────

log_info "Initializing database..."
cd "${INSTALL_DIR}"
"${VENV_DIR}/bin/python" -c "
import asyncio
from backend.database.session import init_db
asyncio.run(init_db())
print('Database initialized successfully')
"

# ─── Build Frontend ───────────────────────────────────────────────────────────

if command -v npm &>/dev/null; then
    log_info "Building frontend..."
    cd "${INSTALL_DIR}/frontend"
    npm ci --production=false
    npm run build
else
    log_warn "npm not found. Install Node.js 20+ to build the frontend."
    log_warn "Run: cd ${INSTALL_DIR}/frontend && npm ci && npm run build"
fi

# ─── Install Systemd Services ─────────────────────────────────────────────────

log_info "Installing systemd services..."
cp "${CONFIG_DIR}/linux-inventory-backend.service" /etc/systemd/system/
cp "${CONFIG_DIR}/linux-inventory-frontend.service" /etc/systemd/system/

# ─── Install Nginx Configuration ──────────────────────────────────────────────

log_info "Installing Nginx configuration..."
cp "${CONFIG_DIR}/nginx.conf" "${CONFIG_DIR}/nginx-production.conf"

# ─── Install Logrotate ────────────────────────────────────────────────────────

log_info "Installing log rotation..."
cp "${CONFIG_DIR}/logrotate.conf" /etc/logrotate.d/${APP_NAME}

# ─── Set Permissions ──────────────────────────────────────────────────────────

log_info "Setting file permissions..."
chown -R "${APP_USER}:${APP_GROUP}" "${INSTALL_DIR}"
chmod 600 "${INSTALL_DIR}/.env"
chmod 700 "${STORAGE_DIR}"
chmod 700 "${LOG_DIR}"

# ─── Enable and Start Services ────────────────────────────────────────────────

log_info "Enabling services..."
systemctl daemon-reload
systemctl enable linux-inventory-backend
systemctl enable linux-inventory-frontend

log_info "Starting backend service..."
systemctl start linux-inventory-backend

# Wait for backend to be ready
sleep 3
if systemctl is-active --quiet linux-inventory-backend; then
    log_info "Backend service started successfully"
else
    log_error "Backend service failed to start. Check: journalctl -u linux-inventory-backend"
    exit 1
fi

# ─── Install Backup Cron ──────────────────────────────────────────────────────

log_info "Installing backup cron job..."
cat > /etc/cron.d/${APP_NAME}-backup << 'EOF'
# Daily database backup at 1:00 AM
0 1 * * * linuxinventory /opt/linux-inventory-manager/scripts/backup.sh >> /opt/linux-inventory-manager/logs/backup.log 2>&1
EOF
chmod 644 /etc/cron.d/${APP_NAME}-backup

# ─── Final Summary ────────────────────────────────────────────────────────────

echo ""
log_info "============================================"
log_info " Installation Complete!"
log_info "============================================"
echo ""
log_info "Application: ${INSTALL_DIR}"
log_info "Config:      ${INSTALL_DIR}/.env"
log_info "Logs:        ${LOG_DIR}"
log_info "Storage:     ${STORAGE_DIR}"
echo ""
log_info "Services:"
log_info "  Backend:  systemctl status linux-inventory-backend"
log_info "  Frontend: systemctl status linux-inventory-frontend"
echo ""
log_info "Health Check:"
log_info "  curl http://localhost:8000/api/v1/health"
echo ""
log_warn "NEXT STEPS:"
log_warn "  1. Edit ${INSTALL_DIR}/.env with production settings"
log_warn "  2. Configure AWS Secrets Manager credentials"
log_warn "  3. Create admin user (see docs/installation.md)"
log_warn "  4. Configure SSL/TLS (ALB or Let's Encrypt)"
log_warn "  5. Restart: systemctl restart linux-inventory-backend"
echo ""
