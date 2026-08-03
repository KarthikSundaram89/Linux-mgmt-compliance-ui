"""
Application Entry Point
=======================

FastAPI application factory with middleware, exception handlers,
and router registration.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from backend.api.v1.router import api_router
from backend.database.session import engine, init_db
from backend.logging.setup import setup_logging
from backend.scheduler.manager import SchedulerManager
from backend.settings.config import get_settings
from backend.security.middleware import SecurityHeadersMiddleware
from backend.security.rate_limiter import RateLimitMiddleware
from backend.security.input_validation import RequestSizeLimitMiddleware
from backend.security.error_handler import register_error_handlers


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.
    
    Handles startup and shutdown events including:
    - Database initialization
    - Scheduler startup
    - Logging configuration
    - Graceful shutdown of all services
    """
    settings = get_settings()
    
    # Initialize logging
    setup_logging(settings)
    
    # Initialize database
    await init_db()
    
    # Start scheduler
    scheduler_manager = SchedulerManager(settings)
    await scheduler_manager.start()
    app.state.scheduler = scheduler_manager
    
    yield
    
    # Shutdown
    await scheduler_manager.shutdown()
    await engine.dispose()


def create_application() -> FastAPI:
    """
    Application factory.
    
    Creates and configures the FastAPI application with all
    middleware, exception handlers, and routers.
    
    Returns:
        FastAPI: Configured application instance.
    """
    settings = get_settings()
    
    app = FastAPI(
        title="Linux Inventory Manager",
        description=(
            "Enterprise Linux Inventory & Compliance Platform. "
            "Inventories Linux servers via SSH, tracks changes, "
            "and provides compliance reporting."
        ),
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Trusted host middleware
    if settings.allowed_hosts:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.allowed_hosts,
        )
    
    # Security headers middleware
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Rate limiting middleware
    app.add_middleware(RateLimitMiddleware)
    
    # Request body size limit (10 MB)
    app.add_middleware(RequestSizeLimitMiddleware)
    
    # Register secure error handlers (never expose internals)
    register_error_handlers(app)
    
    # Register API routers
    app.include_router(api_router, prefix="/api/v1")
    
    return app


# Application instance
app = create_application()
