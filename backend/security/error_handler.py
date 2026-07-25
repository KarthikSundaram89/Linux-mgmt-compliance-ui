"""
Secure Error Handling
=====================

Never expose stack traces, DB errors, or filesystem paths.
Log detailed errors server-side; return generic messages.
"""

import logging
import traceback
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("security")


def register_error_handlers(app: FastAPI) -> None:
    """Register all secure error handlers on the app."""

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        """Handle HTTP exceptions with safe messages."""
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(
        request: Request, exc: ValueError
    ) -> JSONResponse:
        """Handle validation errors."""
        logger.warning(
            f"Validation error: {exc}",
            extra={"path": request.url.path},
        )
        return JSONResponse(
            status_code=422,
            content={"detail": str(exc)},
        )

    @app.exception_handler(PermissionError)
    async def permission_error_handler(
        request: Request, exc: PermissionError
    ) -> JSONResponse:
        """Handle permission errors."""
        logger.warning(
            f"Permission denied: {exc}",
            extra={"path": request.url.path},
        )
        return JSONResponse(
            status_code=403,
            content={"detail": "Access denied"},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """
        Catch-all handler for unhandled exceptions.

        SECURITY: Never expose internal details to client.
        Log the full traceback server-side for debugging.
        """
        logger.error(
            "Unhandled exception",
            extra={
                "path": request.url.path,
                "method": request.method,
                "error_type": type(exc).__name__,
                "traceback": traceback.format_exc(),
            },
        )
        return JSONResponse(
            status_code=500,
            content={
                "detail": "An internal error occurred. "
                "Please contact the administrator."
            },
        )
