from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.logging.logger import get_logger

logger = get_logger("request-context")


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Log every incoming request with method, path and status code."""

    async def dispatch(self, request: Request, call_next) -> Response:
        logger.info(f"--> {request.method} {request.url.path}")
        response = await call_next(request)
        request_id = getattr(request.state, "request_id", "-")
        logger.info(
            f"<-- {request.method} {request.url.path} "
            f"status={response.status_code} request_id={request_id}"
        )
        return response
