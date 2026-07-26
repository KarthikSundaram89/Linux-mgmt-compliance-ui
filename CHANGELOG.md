# Changelog

All notable changes to the Linux Inventory Manager are documented here.

This project follows [Semantic Versioning](https://semver.org/).

---

## [1.0.0] - 2026-07-25

### Initial Release

Production-ready Enterprise Linux Inventory & Compliance Platform.

### Architecture
- **Deployment**: Single EC2 instance (Amazon Linux 2023)
- **Database**: SQLite with ORM abstraction (PostgreSQL-ready)
- **Secrets**: AWS Secrets Manager (SSH private keys)
- **Web Server**: Nginx (frontend) + Uvicorn (backend API)
- **Process Manager**: systemd services

### AWS Services
- EC2 (application host)
- AWS Secrets Manager (SSH key storage)

### Backend (Python 3.12 / FastAPI)
- 12 independent SSH-based Linux inventory collectors
- Plugin-based collector architecture (add new collectors without code changes)
- Command allowlist security (no arbitrary command execution)
- APScheduler with daily collection + hourly retry for failed servers
- 20 concurrent SSH sessions (configurable)
- Compressed JSON snapshots with SHA-256 checksums
- Change detection engine with severity classification
- Report generation (CSV, Excel, PDF)
- JWT authentication with refresh tokens
- RBAC (Administrator, Operator, Read Only)
- Structured logging with secret masking
- Rate limiting, CSRF protection, input validation
- Audit trail for all significant actions
- Enterprise password policy enforcement

### Collectors
1. Operating System (hostname, kernel, uptime, virtualization)
2. Users (non-system accounts, password aging, SSH keys)
3. Groups (local groups, members, admin groups)
4. Sudo (privileged users, sudoers rules, NOPASSWD)
5. Password Policy (login.defs, PAM, lockout, compliance)
6. Filesystem (mounts, NFS/SMB, capacity, usage)
7. Packages (rpm/dpkg, version tracking)
8. Services (systemd, enabled/running, failed highlight)
9. Chrony (NTP sync status, sources, health warnings)
10. Network (DNS, gateway, interfaces, IPv4/IPv6)
11. SSH Configuration (security audit, PermitRootLogin)
12. Cron & Systemd Timers (scheduled tasks)

### Frontend (React 18 / TypeScript / Material UI)
- Executive dashboard with Chart.js charts
- Server inventory DataGrid with bulk actions
- Server detail page (14 tabs for all collectors)
- Change history with severity filtering
- Snapshot comparison (color-coded diffs)
- Global search with autocomplete
- Advanced filters (OS, kernel, status, environment)
- Report generation and download
- User management (admin)
- System status monitoring
- Dark/light theme toggle
- Responsive design

### Security (OWASP Top 10 Compliant)
- Command injection: impossible (frozen allowlist)
- SQL injection: impossible (SQLAlchemy ORM only)
- XSS: prevented (CSP + input sanitization + React)
- CSRF: double-submit cookie pattern
- Broken auth: account lockout + password policy + JWT
- Broken access control: RBAC on every endpoint
- Security misconfiguration: hardened defaults
- Sensitive data exposure: secrets never on disk
- Insufficient logging: structured audit trail

### Deployment & Operations
- Automated installation script (`scripts/install.sh`)
- Upgrade script with auto-rollback (`scripts/upgrade.sh`)
- Backup/restore scripts (`scripts/backup.sh`, `scripts/restore.sh`)
- Health check script (`scripts/health-check.sh`)
- Log rotation configuration
- GitHub Actions CI pipeline (tests, security scan, build)
- Pre-commit hooks (ruff, mypy, bandit, gitleaks)

### Documentation
- README with architecture diagram
- Installation guide
- Deployment guide
- Security guide (OWASP coverage matrix)
- Operational runbook
- Creating new collectors (developer guide)
- Sample snapshot and change report

### Supported Linux Distributions
- Red Hat Enterprise Linux (RHEL)
- Amazon Linux
- Ubuntu
- Debian
- Rocky Linux
- Oracle Linux
- Kali Linux
- CentOS
- SUSE (future-ready)

### Scaling
- Default: 300 servers with 20 concurrent SSH sessions
- Tested design: 2,000+ servers (increase concurrency setting)
- Database: SQLite → PostgreSQL migration via config change only

---

## Development History

| Phase | Description | Lines |
|-------|-------------|-------|
| Phase 1 | Architecture & Foundation | 8,787 |
| Phase 2 | Collection Engine (12 collectors) | 4,573 |
| Phase 3 | Enterprise Web UI & APIs | 2,301 |
| Phase 4 | Security, DevSecOps & Production | 2,758 |
| **Total** | | **~18,400** |
