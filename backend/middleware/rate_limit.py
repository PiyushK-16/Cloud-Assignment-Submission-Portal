"""Tiny in-memory sliding-window rate limiter (brute-force protection for /login and /register).
For multiple server instances use an API Gateway / Redis-backed limiter instead."""
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

from backend.config import settings


class RateLimiter:
    def __init__(self, limit_getter, window_seconds: int = 60):
        self.limit_getter = limit_getter
        self.window = window_seconds
        self.hits: dict[str, deque] = defaultdict(deque)

    def __call__(self, request: Request) -> None:
        key = request.client.host if request.client else "unknown"
        now = time.time()
        q = self.hits[key]
        while q and now - q[0] > self.window:
            q.popleft()
        if len(q) >= self.limit_getter():
            raise HTTPException(429, "Too many attempts. Please wait a minute and try again.")
        q.append(now)


auth_limiter = RateLimiter(lambda: settings.rate_limit_login_per_min)
