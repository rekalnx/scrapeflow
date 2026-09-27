"""Tests for rate limiting logic."""

import asyncio
import time
import unittest
from scrapeflow.limiter import DomainRateLimiter


class TestLimiter(unittest.TestCase):
    def test_extract_domain(self):
        limiter = DomainRateLimiter()
        self.assertEqual(limiter.extract_domain("https://api.github.com/repos"), "api.github.com")
        self.assertEqual(limiter.extract_domain("http://example.org:8080/path"), "example.org:8080")
        self.assertEqual(limiter.extract_domain("invalid-url"), "localhost")

    def test_acquire_rate(self):
        async def run():
            limiter = DomainRateLimiter(default_delay=0.1)
            t0 = time.monotonic()
            await limiter.acquire("https://example.com/1")
            await limiter.acquire("https://example.com/2")
            t1 = time.monotonic()
            self.assertGreaterEqual(t1 - t0, 0.09)

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
