from __future__ import annotations

from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from .logging import bind_correlation_id, clear_correlation_id


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Ensure each request has a correlation id for logging."""

    header_name = "X-Correlation-ID"

    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:  # type: ignore[override]
        correlation_id = bind_correlation_id(request.headers.get(self.header_name))
        response = await call_next(request)
        response.headers[self.header_name] = correlation_id
        clear_correlation_id()
        return response
