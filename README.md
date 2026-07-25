# Linux Inventory Manager

Enterprise Linux Inventory & Compliance Platform

## Overview

A production-ready web application that inventories approximately 300+ Linux servers distributed across multiple AWS accounts via SSH. Collects operating system information, tracks changes over time, and provides compliance reporting.

**Supported Linux Distributions:**
- Red Hat Enterprise Linux (RHEL)
- Amazon Linux
- Ubuntu
- Kali Linux
- Debian
- Rocky Linux
- Oracle Linux

> **Note:** This application is Linux-focused only. AWS infrastructure inventory is maintained elsewhere. This platform connects to servers over SSH to collect OS-level information.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                React Frontend                        │
│  (Material UI, TypeScript, Chart.js)                │
└─────────────────────┬───────────────────────────────┘
                      │ REST API (JSON)
┌─────────────────────┴───────────────────────────────┐
│              FastAPI Backend                          │
│  ┌─────────┐ ┌──────────┐ ┌────────────────────┐   │
│  │  Auth   │ │Scheduler │ │  Collection Engine  │   │
│  │  RBAC   │ │APScheduler│ │  20 concurrent SSH │   │
│  └─────────┘ └──────────┘ └────────────────────┘   │
│  ┌─────────────────────────────────────────────┐    │
│  │           Service Layer                      │    │
│  │  Collection │ ChangeDetection │ Reports      │    │
│  └─────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────┐    │
│  │         Repository Layer (Data Access)       │    │
│  └─────────────────────────────────────────────┘    │
└─────────────────────┬───────────────────────────────┘
           ┌──────────┴──────────┐
     ┌─────┴─────┐        ┌─────┴─────┐
     │  SQLite   │        │   Disk    │
     │ (metadata)│        │(snapshots)│
     └───────────┘        └───────────┘
```

## Key Features

| Feature | Description |
|---------|-------------|
| **Inventory Collection** | Automated daily SSH-based collection with 20 concurrent sessions |
| **Change Detection** | Automatic comparison between consecutive snapshots |
| **Compliance Dashboard** | Real-time server status, collection metrics, and alerts |
| **Hybrid Storage** | SQLite for metadata, compressed JSON for full snapshots |
| **RBAC** | Role-based access control (admin, operator, viewer, auditor) |
| **Reporting** | Export to CSV, Excel, PDF |
| **Scheduler** | APScheduler with retry logic, pause/resume, manual triggers |
| **Secrets Management** | AWS Secrets Manager integration (keys never on disk) |
| **Audit Trail** | Immutable audit log for all significant actions |

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12+, FastAPI, SQLAlchemy, APScheduler, Paramiko |
| Frontend | React 18, TypeScript, Material UI, Chart.js |
| Database | SQLite (PostgreSQL-ready) |
| Auth | JWT (local), future: Azure AD, LDAP, AWS SSO |
| Deployment | Systemd services on EC2, Docker for CI |

## Project Structure

```
├── backend/
│   ├── api/v1/endpoints/    # REST API controllers
│   ├── authentication/      # JWT, login, providers
│   ├── authorization/       # RBAC framework
│   ├── collectors/          # SSH data collectors (Phase 2)
│   ├── database/            # Engine, sessions, migrations
│   ├── logging/             # Structured logging
│   ├── models/              # SQLAlchemy ORM models
│   ├── notifications/       # Alert system
│   ├── parser/              # Raw data parsers
│   ├── reports/             # Report generation
│   ├── repositories/        # Data access layer
│   ├── scheduler/           # APScheduler management
│   ├── security/            # Secrets, middleware
│   ├── services/            # Business logic
│   ├── settings/            # Configuration
│   └── ssh/                 # Connection management
├── frontend/
│   └── src/
│       ├── components/      # Reusable UI components
│       ├── contexts/        # React contexts
│       ├── hooks/           # Custom hooks
│       ├── layouts/         # Page layouts
│       ├── pages/           # Route pages
│       ├── services/        # API client services
│       ├── themes/          # Material UI theme
│       └── types/           # TypeScript type definitions
├── config/                  # Configuration files
├── storage/                 # Runtime data (gitignored)
│   ├── snapshots/           # Compressed inventory JSON
│   ├── reports/             # Generated reports
│   └── exports/             # Data exports
└── logs/                    # Application logs (gitignored)
```

## Quick Start

See [docs/installation.md](docs/installation.md) for full instructions.

```bash
# Clone repository
git clone https://github.com/KarthikSundaram89/Linux-mgmt-compliance-ui.git
cd Linux-mgmt-compliance-ui

# Backend setup
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp config/.env.example .env
# Edit .env with your settings

# Initialize database
python -c "import asyncio; from backend.database.session import init_db; asyncio.run(init_db())"

# Start backend
uvicorn backend.main:app --reload --port 8000

# Frontend setup (separate terminal)
cd frontend
npm install
npm run dev
```

## API Documentation

Once running, access:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc
- OpenAPI JSON: http://localhost:8000/api/openapi.json

## Design Principles

- **SOLID** - Single responsibility, open/closed, Liskov substitution, interface segregation, dependency inversion
- **Repository Pattern** - All database access through repositories
- **Service Layer** - Business logic isolated from controllers and data access
- **Dependency Injection** - FastAPI Depends() for all cross-cutting concerns
- **Clean Architecture** - No business logic in API controllers
- **DRY / KISS** - No duplication, simple implementations

## License

Proprietary - Internal Use Only
