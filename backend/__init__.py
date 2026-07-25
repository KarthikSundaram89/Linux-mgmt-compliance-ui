"""
Enterprise Linux Inventory & Compliance Platform
================================================

A production-ready web application for inventorying and monitoring
Linux servers across multiple AWS accounts via SSH.

Modules:
    api             - REST API controllers (FastAPI routers)
    authentication  - Authentication providers and token management
    authorization   - Role-based access control (RBAC)
    collectors      - Linux inventory data collectors
    scheduler       - APScheduler-based collection scheduling
    ssh             - SSH connection management and pooling
    parser          - Raw data parsing and normalization
    database        - Database engine, sessions, and migrations
    services        - Business logic service layer
    models          - SQLAlchemy ORM models
    repositories    - Data access layer (Repository Pattern)
    notifications   - Alert and notification system
    reports         - Report generation (CSV, Excel, PDF)
    settings        - Application configuration
    logging         - Structured logging framework
    security        - Security utilities and middleware
"""

__version__ = "1.0.0"
__application__ = "Linux Inventory Manager"
