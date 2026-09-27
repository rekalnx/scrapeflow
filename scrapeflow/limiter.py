"""Asynchronous rate limiter and backoff mechanisms."""

import asyncio
import time
from urllib.parse import urlparse
from typing import Dict, Optional


class DomainRateLimiter:
    """Thread-safe and async-safe domain-level rate limiter."""

    def __init__(self, default_delay: float = 0.5):
        self.default_delay = default_delay
        self._last_access: Dict[str, float] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self._global_lock: Optional[asyncio.Lock] = None

    async def _get_lock(self, domain: str) -> asyncio.Lock:
        if self._global_lock is None:
            self._global_lock = asyncio.Lock()
        async with self._global_lock:
            if domain not in self._locks:
                self._locks[domain] = asyncio.Lock()
            return self._locks[domain]

    @staticmethod
    def extract_domain(url: str) -> str:
        """Extract network location from URL."""
        parsed = urlparse(url)
        return parsed.netloc.lower() or "localhost"

    async def acquire(self, url: str, delay: float = None):
        """Wait until the domain rate limit window allows another request."""
        domain = self.extract_domain(url)
        rate_delay = delay if delay is not None else self.default_delay
        if rate_delay <= 0:
            return

        lock = await self._get_lock(domain)
        async with lock:
            now = time.monotonic()
            last = self._last_access.get(domain, 0.0)
            elapsed = now - last
            wait_time = rate_delay - elapsed
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            self._last_access[domain] = time.monotonic()
