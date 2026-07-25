# Operational Runbook

## Daily Operations

### Health Check
```bash
bash /opt/linux-inventory-manager/scripts/health-check.sh
curl -s http://localhost:8000/api/v1/health | jq .
```

### View Collection Status
```bash
curl -s http://localhost:8000/api/v1/scheduler/status | jq .
```

### View Recent Logs
```bash
tail -100 /opt/linux-inventory-manager/logs/app.log
tail -50 /opt/linux-inventory-manager/logs/collector.log
tail -50 /opt/linux-inventory-manager/logs/security.log
```

## Common Tasks

### Manual Collection Trigger
```bash
curl -X POST http://localhost:8000/api/v1/collections/trigger-all \
  -H "Authorization: Bearer $TOKEN"
```

### Pause Scheduler
```bash
curl -X POST http://localhost:8000/api/v1/scheduler/pause \
  -H "Authorization: Bearer $TOKEN"
```

### Resume Scheduler
```bash
curl -X POST http://localhost:8000/api/v1/scheduler/resume \
  -H "Authorization: Bearer $TOKEN"
```

### Create Admin User
```bash
cd /opt/linux-inventory-manager
source venv/bin/activate
python -c "
import asyncio
from backend.database.session import async_session_factory
from backend.authentication.service import AuthenticationService
async def create():
    async with async_session_factory() as session:
        user = await AuthenticationService.create_user(
            session, 'admin', 'admin@company.com',
            'Admin User', 'TempPassword!123')
        await session.commit()
        print(f'Created: {user.username}')
asyncio.run(create())
"
```

### Unlock User Account
```bash
curl -X POST http://localhost:8000/api/v1/users/{user_id}/unlock \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

## Troubleshooting

### Backend Won't Start
```bash
# Check logs
journalctl -u linux-inventory-backend -n 50 --no-pager
# Check config
cat /opt/linux-inventory-manager/.env | grep -v SECRET
# Check permissions
ls -la /opt/linux-inventory-manager/storage/
# Test manually
cd /opt/linux-inventory-manager
source venv/bin/activate
python -c "from backend.settings.config import get_settings; print(get_settings())"
```

### Collection Failures
```bash
# Recent collection errors
grep "ERROR" /opt/linux-inventory-manager/logs/collector.log | tail -20
# SSH connectivity test
ssh -i /path/to/key -o ConnectTimeout=10 user@server hostname
```

### High Disk Usage
```bash
# Check snapshot storage
du -sh /opt/linux-inventory-manager/storage/snapshots/
# Run cleanup
source /opt/linux-inventory-manager/venv/bin/activate
python -c "
import asyncio
from backend.services.snapshot_service import SnapshotStorageService
s = SnapshotStorageService()
asyncio.run(s.cleanup_old_snapshots())
"
```

### Database Issues
```bash
# Check integrity
sqlite3 /opt/linux-inventory-manager/storage/inventory.db "PRAGMA integrity_check;"
# Check size
ls -lh /opt/linux-inventory-manager/storage/inventory.db
# Vacuum (reclaim space)
sqlite3 /opt/linux-inventory-manager/storage/inventory.db "VACUUM;"
```

## Backup & Restore

### Manual Backup
```bash
sudo -u linuxinventory bash /opt/linux-inventory-manager/scripts/backup.sh --full
```

### Restore from Backup
```bash
sudo bash /opt/linux-inventory-manager/scripts/restore.sh /path/to/backup.tar.gz
```

## Upgrade Procedure

```bash
sudo bash /opt/linux-inventory-manager/scripts/upgrade.sh
```

The upgrade script automatically:
1. Creates a pre-upgrade backup
2. Pulls latest code
3. Updates dependencies
4. Runs migrations
5. Rebuilds frontend
6. Restarts services
7. Verifies health (auto-rollback on failure)

## Emergency Procedures

### Emergency Stop
```bash
systemctl stop linux-inventory-backend
systemctl stop linux-inventory-frontend
```

### Rollback to Previous Version
```bash
cd /opt/linux-inventory-manager
sudo -u linuxinventory git log --oneline -5  # Find target commit
sudo -u linuxinventory git checkout <commit_hash>
source venv/bin/activate
pip install -r requirements.txt
systemctl restart linux-inventory-backend
```

## Monitoring Endpoints

| Endpoint | Purpose | Auth Required |
|----------|---------|---------------|
| `/api/v1/health` | Basic liveness | No |
| `/api/v1/health/ready` | Readiness probe | No |
| `/api/v1/health/live` | Liveness probe | No |
| `/api/v1/health/metrics` | Prometheus metrics | No |
| `/api/v1/system/status` | Detailed status | Yes (admin) |
