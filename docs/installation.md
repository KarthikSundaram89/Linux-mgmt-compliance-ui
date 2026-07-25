# Installation Guide

## Prerequisites

| Requirement | Version |
|-------------|---------|
| Python | 3.12+ |
| Node.js | 20+ |
| npm | 10+ |
| AWS CLI | 2.x (for Secrets Manager) |

## Backend Installation

### 1. Create Application User

```bash
sudo useradd -r -m -d /opt/linux-inventory-manager -s /bin/bash linuxinventory
sudo mkdir -p /opt/linux-inventory-manager
sudo chown linuxinventory:linuxinventory /opt/linux-inventory-manager
```

### 2. Clone Repository

```bash
sudo -u linuxinventory git clone \
  https://github.com/KarthikSundaram89/Linux-mgmt-compliance-ui.git \
  /opt/linux-inventory-manager
```

### 3. Create Virtual Environment

```bash
cd /opt/linux-inventory-manager
sudo -u linuxinventory python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp config/.env.example .env
# Edit .env with production values
# IMPORTANT: Generate a strong SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

### 5. Initialize Database

```bash
python -c "import asyncio; from backend.database.session import init_db; asyncio.run(init_db())"
```

### 6. Create Initial Admin User

```bash
python -c "
import asyncio
from backend.database.session import async_session_factory
from backend.authentication.service import AuthenticationService

async def create_admin():
    async with async_session_factory() as session:
        user = await AuthenticationService.create_user(
            session=session,
            username='admin',
            email='admin@company.com',
            full_name='System Administrator',
            password='ChangeThisPassword!',
        )
        await session.commit()
        print(f'Admin user created: {user.username}')

asyncio.run(create_admin())
"
```

### 7. Create Storage Directories

```bash
mkdir -p storage/{snapshots,reports,exports} logs
chown -R linuxinventory:linuxinventory storage logs
```

## Frontend Installation

### 1. Build Frontend

```bash
cd /opt/linux-inventory-manager/frontend
npm ci
npm run build
```

### 2. Install Nginx

```bash
sudo apt install nginx  # Debian/Ubuntu
sudo yum install nginx  # RHEL/Amazon Linux
```

## Systemd Service Setup

### 1. Install Service Files

```bash
sudo cp config/linux-inventory-backend.service /etc/systemd/system/
sudo cp config/linux-inventory-frontend.service /etc/systemd/system/
sudo systemctl daemon-reload
```

### 2. Enable and Start Services

```bash
sudo systemctl enable linux-inventory-backend
sudo systemctl enable linux-inventory-frontend
sudo systemctl start linux-inventory-backend
sudo systemctl start linux-inventory-frontend
```

### 3. Verify

```bash
sudo systemctl status linux-inventory-backend
curl http://localhost:8000/api/v1/health
```

## AWS Secrets Manager Setup

### 1. Create SSH Key Secrets

```bash
aws secretsmanager create-secret \
  --name "linux-inventory/ssh/production" \
  --description "SSH private key for production Linux servers" \
  --secret-string file://path-to-private-key.pem
```

### 2. IAM Permissions

The EC2 instance role needs:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:*:*:secret:linux-inventory/*"
    }
  ]
}
```

## SSH Known Hosts

Populate the known hosts file for all managed servers:

```bash
ssh-keyscan -t ed25519,rsa server1.example.com >> /opt/linux-inventory-manager/.ssh/known_hosts
```

## Firewall Configuration

The application server needs:
- Outbound SSH (port 22) to all managed servers
- Outbound HTTPS (443) to AWS Secrets Manager
- Inbound HTTP/HTTPS for web UI access
