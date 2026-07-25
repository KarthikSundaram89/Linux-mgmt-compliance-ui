# Deployment Guide

## Production Deployment on EC2

### Recommended Instance

| Spec | Recommendation |
|------|---------------|
| Instance Type | t3.medium (2 vCPU, 4 GB RAM) |
| OS | Amazon Linux 2023 or Ubuntu 22.04 |
| Storage | 100 GB gp3 (for snapshots) |
| Security Group | SSH from admin IPs, HTTP/HTTPS from internal |

### Architecture

```
[Users] → [ALB/Nginx :443] → [EC2 Instance]
                                  ├── Nginx (frontend static files)
                                  ├── Uvicorn (backend API :8000)
                                  └── SSH → [300+ Linux Servers]
```

### Deployment Steps

1. **Provision EC2 instance** with appropriate IAM role
2. **Follow installation guide** in `docs/installation.md`
3. **Configure SSL/TLS** via ALB or Let's Encrypt
4. **Set up monitoring** (CloudWatch, Prometheus)
5. **Configure backups** for SQLite database

### Environment-Specific Configuration

| Setting | Development | Production |
|---------|------------|------------|
| ENVIRONMENT | development | production |
| DEBUG | true | false |
| WORKERS | 1 | 4 |
| LOG_FORMAT | text | json |
| LOG_LEVEL | DEBUG | INFO |
| SECRETS_PROVIDER | local | aws_secrets_manager |
| SCHEDULER_ENABLED | false | true |

### Database Backup

```bash
# Daily SQLite backup (add to cron)
0 1 * * * cp /opt/linux-inventory-manager/storage/inventory.db \
  /opt/linux-inventory-manager/storage/backups/inventory-$(date +\%Y\%m\%d).db

# Retain 30 days of backups
find /opt/linux-inventory-manager/storage/backups -name "*.db" -mtime +30 -delete
```

### Log Rotation

Application logs are rotated automatically by the logging framework.
Nginx logs should be rotated via logrotate:

```
/opt/linux-inventory-manager/logs/nginx-*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    postrotate
        systemctl reload linux-inventory-frontend
    endscript
}
```

### Health Monitoring

```bash
# Backend health check
curl -s http://localhost:8000/api/v1/health | jq .

# Readiness check
curl -s http://localhost:8000/api/v1/health/ready | jq .
```

### Scaling Considerations

| Scale | Servers | Recommendation |
|-------|---------|---------------|
| Current | 300 | Single EC2 t3.medium, SQLite |
| Medium | 1000 | t3.large, increase concurrent SSH to 40 |
| Large | 2000+ | Migrate to PostgreSQL, consider worker queue |

### Security Hardening

- [ ] Disable root SSH access on the application server
- [ ] Use IAM instance role (no access keys on disk)
- [ ] Enable VPC flow logs
- [ ] Restrict SSH outbound to managed server IPs only
- [ ] Enable CloudTrail for Secrets Manager access
- [ ] Set up WAF rules if exposed to the internet
- [ ] Rotate JWT secret key periodically
- [ ] Enable MFA for admin accounts (future)

### Updating the Application

```bash
# Pull latest code
cd /opt/linux-inventory-manager
sudo -u linuxinventory git pull origin main

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt

# Rebuild frontend
cd frontend && npm ci && npm run build && cd ..

# Restart services
sudo systemctl restart linux-inventory-backend
sudo systemctl restart linux-inventory-frontend
```

### Rollback

```bash
# Revert to previous commit
cd /opt/linux-inventory-manager
sudo -u linuxinventory git checkout <previous-commit-hash>

# Reinstall dependencies and restart
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart linux-inventory-backend
```

## Docker Deployment (Optional)

For CI/CD testing or containerized environments:

```bash
docker compose up -d
```

The Docker deployment is provided for development and testing.
Production deployment on EC2 uses systemd services directly.

## Future: PostgreSQL Migration

When scaling beyond 1000 servers:

1. Install PostgreSQL and create database
2. Update `DATABASE_URL` in `.env`:
   ```
   DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/linuxinventory
   ```
3. Uncomment `asyncpg` in `requirements.txt`
4. Run Alembic migrations
5. No application code changes required
