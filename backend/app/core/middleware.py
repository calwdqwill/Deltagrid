"""FastAPI middleware: request ID tracing, global exception handling.

Phase 6: Operational observability foundation.
"""

import uuid
import logging
from typing import Optional

from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    DeltaGridException,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ConflictError,
    ValidationError,
)

logger = logging.getLogger(__name__)


class RequestIDMiddleware:
    """ASGI middleware that adds X-Request-ID to every request."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            request_id = request.headers.get("X-Request-ID") or f"req_{uuid.uuid4().hex[:12]}"
            scope["request_id"] = request_id

            # Inject request_id into response headers
            async def send_with_request_id(message):
                if message["type"] == "http.response.start":
                    headers = list(message.get("headers", []))
                    headers.append((b"X-Request-ID", request_id.encode()))
                    message["headers"] = headers
                await send(message)

            await self.app(scope, receive, send_with_request_id)
        else:
            await self.app(scope, receive, send)


def add_exception_handlers(app):
    """Register global exception handlers on FastAPI app."""

    @app.exception_handler(DeltaGridException)
    async def deltagrid_exception_handler(request: Request, exc: DeltaGridException):
        request_id = getattr(request.state, "request_id", None) or request.scope.get("request_id", "unknown")

        status_map = {
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            AuthorizationError: status.HTTP_403_FORBIDDEN,
            NotFoundError: status.HTTP_404_NOT_FOUND,
            ConflictError: status.HTTP_409_CONFLICT,
            ValidationError: status.HTTP_422_UNPROCESSABLE_ENTITY,
        }

        code = type(exc).__name__.replace("Error", "").upper()
        status_code = status_map.get(type(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)

        logger.warning(f"[{request_id}] {code}: {exc}")

        return JSONResponse(
            status_code=status_code,
            content={
                "error": {
                    "code": code,
                    "message": str(exc),
                    "request_id": request_id,
                }
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", None) or request.scope.get("request_id", "unknown")
        logger.exception(f"[{request_id}] Unhandled exception")

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                    "request_id": request_id,
                }
            },
        )
