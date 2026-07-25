#!/usr/bin/env bash
# ==============================================================================
# Linux Inventory Manager - Health Check Script
# ==============================================================================
# Comprehensive health verification for monitoring and alerting.
# Usage: bash scripts/health-check.sh
# Exit codes: 0 = healthy, 1 = degraded, 2 = critical
# ==============================================================================

set -uo pipefail

APP_DIR="/opt/linux-inventory-manager"
API_URL="http://localhost:8000/api/v1"
EXIT_CODE=0

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

check_pass() { echo -e "  ${GREEN}[PASS]${NC} $1"; }
check_warn() { echo -e "  ${YELLOW}[WARN]${NC} $1"; EXIT_CODE=1; }
check_fail() { echo -e "  ${RED}[FAIL]${NC} $1"; EXIT_CODE=2; }

echo "=== Linux Inventory Manager Health Check ==="
echo "  Time: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo ""

# ─── Service Status ───────────────────────────────────────────────────────────

echo "Services:"
if systemctl is-active --quiet linux-inventory-backend 2>/dev/null; then
    check_pass "Backend service: active"
else
    check_fail "Backend service: inactive"
fi

if systemctl is-active --quiet linux-inventory-frontend 2>/dev/null; then
    check_pass "Frontend service: active"
else
    check_warn "Frontend service: inactive"
fi

# ─── API Health ───────────────────────────────────────────────────────────────

echo ""
echo "API Endpoints:"
HEALTH=$(curl -sf --max-time 5 "${API_URL}/health" 2>/dev/null)
if [[ $? -eq 0 ]]; then
    check_pass "Health endpoint: responding"
else
    check_fail "Health endpoint: not responding"
fi

READY=$(curl -sf --max-time 5 "${API_URL}/health/ready" 2>/dev/null)
if [[ $? -eq 0 ]]; then
    check_pass "Readiness endpoint: ready"
else
    check_warn "Readiness endpoint: not ready"
fi

# ─── Database ─────────────────────────────────────────────────────────────────

echo ""
echo "Database:"
DB_FILE="${APP_DIR}/storage/inventory.db"
if [[ -f "${DB_FILE}" ]]; then
    DB_SIZE=$(du -h "${DB_FILE}" | cut -f1)
    check_pass "Database file exists (${DB_SIZE})"
    # Check if writable
    if [[ -w "${DB_FILE}" ]]; then
        check_pass "Database is writable"
    else
        check_fail "Database is NOT writable"
    fi
else
    check_fail "Database file not found"
fi

# ─── Storage ──────────────────────────────────────────────────────────────────

echo ""
echo "Storage:"
DISK_USAGE=$(df "${APP_DIR}/storage" 2>/dev/null | tail -1 | awk '{print $5}' | tr -d '%')
if [[ -n "${DISK_USAGE}" ]]; then
    if [[ ${DISK_USAGE} -lt 80 ]]; then
        check_pass "Disk usage: ${DISK_USAGE}%"
    elif [[ ${DISK_USAGE} -lt 90 ]]; then
        check_warn "Disk usage: ${DISK_USAGE}% (high)"
    else
        check_fail "Disk usage: ${DISK_USAGE}% (critical)"
    fi
fi

SNAP_DIR="${APP_DIR}/storage/snapshots"
if [[ -d "${SNAP_DIR}" ]]; then
    SNAP_COUNT=$(find "${SNAP_DIR}" -name "*.json.gz" -type f | wc -l)
    check_pass "Snapshots: ${SNAP_COUNT} files"
else
    check_warn "Snapshots directory missing"
fi

# ─── Logs ─────────────────────────────────────────────────────────────────────

echo ""
echo "Logs:"
LOG_DIR="${APP_DIR}/logs"
if [[ -d "${LOG_DIR}" ]]; then
    LOG_SIZE=$(du -sh "${LOG_DIR}" 2>/dev/null | cut -f1)
    check_pass "Log directory: ${LOG_SIZE}"
    # Check for recent errors
    RECENT_ERRORS=$(grep -c "ERROR" "${LOG_DIR}/app.log" 2>/dev/null | tail -1 || echo "0")
    if [[ ${RECENT_ERRORS} -gt 100 ]]; then
        check_warn "Recent errors in app.log: ${RECENT_ERRORS}"
    else
        check_pass "Error count acceptable: ${RECENT_ERRORS}"
    fi
else
    check_warn "Log directory missing"
fi

# ─── Configuration ────────────────────────────────────────────────────────────

echo ""
echo "Configuration:"
if [[ -f "${APP_DIR}/.env" ]]; then
    ENV_PERMS=$(stat -c %a "${APP_DIR}/.env" 2>/dev/null || stat -f %Lp "${APP_DIR}/.env" 2>/dev/null)
    if [[ "${ENV_PERMS}" == "600" ]]; then
        check_pass ".env permissions: 600 (secure)"
    else
        check_warn ".env permissions: ${ENV_PERMS} (should be 600)"
    fi
else
    check_fail ".env file missing"
fi

# ─── Summary ──────────────────────────────────────────────────────────────────

echo ""
echo "=== Summary ==="
case ${EXIT_CODE} in
    0) echo -e "  Status: ${GREEN}HEALTHY${NC}" ;;
    1) echo -e "  Status: ${YELLOW}DEGRADED${NC}" ;;
    2) echo -e "  Status: ${RED}CRITICAL${NC}" ;;
esac
echo ""

exit ${EXIT_CODE}
