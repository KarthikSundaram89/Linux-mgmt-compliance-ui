# ECS Fargate Deployment Guide

## Architecture

```
                    ┌─────────────────────┐
                    │   Internal ALB      │
                    │   (HTTPS :443)      │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                                  │
    ┌─────────┴──────────┐         ┌────────────┴───────────┐
    │  ECS Service: API   │         │ ECS Service: Collector  │
    │  (2 tasks, HA)      │         │ (1-5 tasks, auto-scale) │
    │                     │         │                         │
    │  FastAPI + Frontend │         │  SQS Consumer           │
    │  Scheduler triggers │───SQS──▶│  SSH Collectors         │
    │  REST APIs          │         │  Snapshot Storage       │
    │  Auth / RBAC        │         │  Change Detection       │
    └─────────┬───────────┘         └────────────┬────────────┘
              │                                   │
              │         ┌──────────────┐          │
              ├────────▶│  PostgreSQL   │◀─────────┤
              │         │  (RDS)       │          │
              │         └──────────────┘          │
              │         ┌──────────────┐          │
              └────────▶│  EFS         │◀─────────┘
                        │  (Snapshots) │
                        └──────────────┘
```

## Prerequisites

- Existing ECS Fargate cluster
- VPC with private subnets (NAT gateway for outbound)
- AWS CLI configured
- Terraform >= 1.5
- Docker for building images

## Deployment Steps

### 1. Build and Push Container Images

```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com

# Build API image
docker build -f infra/ecs/Dockerfile.api -t linux-inventory:api-latest .
docker tag linux-inventory:api-latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/linux-inventory:api-latest
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/linux-inventory:api-latest

# Build Collector image
docker build -f infra/ecs/Dockerfile.collector -t linux-inventory:collector-latest .
docker tag linux-inventory:collector-latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/linux-inventory:collector-latest
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/linux-inventory:collector-latest
```

### 2. Create Secrets in AWS Secrets Manager

```bash
# Application secret key
aws secretsmanager create-secret \
  --name "linux-inventory/secret-key" \
  --secret-string "$(python3 -c 'import secrets; print(secrets.token_urlsafe(64))')"

# Database URL (after RDS is created)
aws secretsmanager create-secret \
  --name "linux-inventory/database-url" \
  --secret-string "postgresql+asyncpg://linuxinv:PASSWORD@RDS_ENDPOINT:5432/linuxinventory"

# SSH keys for managed servers
aws secretsmanager create-secret \
  --name "linux-inventory/ssh/production" \
  --secret-string file://path-to-private-key.pem
```

### 3. Deploy Infrastructure with Terraform

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values

terraform init
terraform plan
terraform apply
```

### 4. Initialize Database

```bash
# Run one-off ECS task for DB initialization
aws ecs run-task \
  --cluster your-cluster \
  --task-definition linux-inventory-api \
  --launch-type FARGATE \
  --overrides '{
    "containerOverrides": [{
      "name": "api",
      "command": ["python", "-c", "import asyncio; from backend.database.session import init_db; asyncio.run(init_db())"]
    }]
  }' \
  --network-configuration '{
    "awsvpcConfiguration": {
      "subnets": ["subnet-xxx"],
      "securityGroups": ["sg-xxx"]
    }
  }'
```

### 5. Create Initial Admin User

```bash
aws ecs run-task \
  --cluster your-cluster \
  --task-definition linux-inventory-api \
  --launch-type FARGATE \
  --overrides '{
    "containerOverrides": [{
      "name": "api",
      "command": ["python", "-c", "import asyncio; from backend.database.session import async_session_factory; from backend.authentication.service import AuthenticationService; asyncio.run((lambda: AuthenticationService.create_user(...))())"]
    }]
  }'
```

## Scaling

| Scale | Servers | API Tasks | Collector Tasks | Notes |
|-------|---------|-----------|-----------------|-------|
| Small | 300 | 2 | 1 | Default config |
| Medium | 1000 | 2 | 2-3 | Auto-scales |
| Large | 2000+ | 3 | 3-5 | Increase RDS |

Auto-scaling triggers when SQS queue depth exceeds 10 messages per task.

## Container Communication

- **API → Collector**: Via SQS (async, decoupled)
- **Both → PostgreSQL**: Direct connection via security groups
- **Both → EFS**: Mounted filesystem (snapshots, reports)
- **Both → Secrets Manager**: IAM role-based access
- **Collector → Linux Servers**: SSH outbound (port 22)

## Local Development

Simulate the full ECS architecture locally:

```bash
docker compose -f infra/docker-compose.ecs-local.yml up
```

This starts: PostgreSQL, LocalStack (SQS), API, Collector, Frontend.

## Monitoring

- **CloudWatch Logs**: `/ecs/linux-inventory/api`, `/ecs/linux-inventory/collector`
- **Health Checks**: API `:8000/api/v1/health`, Collector `:8001/health`
- **SQS Metrics**: Queue depth, age of oldest message
- **ECS Metrics**: CPU, memory, running task count

## Cost Estimate (us-east-1)

| Resource | Spec | Monthly Est. |
|----------|------|-------------|
| ECS API (2 tasks) | 1 vCPU / 2 GB | ~$60 |
| ECS Collector (1 task avg) | 2 vCPU / 4 GB | ~$60 |
| RDS PostgreSQL | db.t4g.small | ~$30 |
| EFS | ~10 GB | ~$3 |
| ALB | Internal | ~$20 |
| SQS | Low volume | ~$1 |
| **Total** | | **~$175/mo** |
