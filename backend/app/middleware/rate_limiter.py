"""Rate limiter middleware using in-memory sliding window."""

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import settings

logger = logging.getLogger("social_media.rate_limiter")


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """Sliding window rate limiter middleware."""

    def __init__(self, app, requests_per_window: int = None, window_seconds: int = None):
        super().__init__(app)
        self.max_requests = requests_per_window or settings.RATE_LIMIT_REQUESTS
        self.window = window_seconds or settings.RATE_LIMIT_WINDOW_SECONDS
        self._store: dict[str, list[float]] = {}

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path in ("/", "/health"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        key = f"rate:{client_ip}"
        now = time.time()
        window_start = now - self.window

        if key not in self._store:
            self._store[key] = []

        # Remove expired entries
        self._store[key] = [t for t in self._store[key] if t > window_start]

        if len(self._store[key]) >= self.max_requests:
            retry_after = int(self.window - (now - self._store[key][0]))
            logger.warning(f"Rate limit exceeded for {client_ip}")
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
                headers={"Retry-After": str(max(retry_after, 1))},
            )

        self._store[key].append(now)

        response = await call_next(request)
        remaining = self.max_requests - len(self._store[key])
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(max(remaining, 0))
        return response
