"""Asynchronous crawling and extraction engine."""

import asyncio
import inspect
import logging
import random
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request as URLRequest, urlopen
from typing import Any, Callable, Dict, List, Optional

from .limiter import DomainRateLimiter
from .models import Request, Response
from .pipeline import BasePipeline

logger = logging.getLogger("scrapeflow")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
]


class Crawler:
    """High-performance resilient async crawler."""

    def __init__(
        self,
        concurrency: int = 5,
        default_delay: float = 0.5,
        default_timeout: float = 15.0,
        pipelines: Optional[List[BasePipeline]] = None,
        rotate_ua: bool = True,
    ):
        self.concurrency = concurrency
        self.default_timeout = default_timeout
        self.rotate_ua = rotate_ua
        self.limiter = DomainRateLimiter(default_delay=default_delay)
        self.pipelines = pipelines or []
        self._semaphore = None
        self._stats = {
            "requests_total": 0,
            "requests_success": 0,
            "requests_failed": 0,
            "items_processed": 0,
            "start_time": 0.0,
            "elapsed_time": 0.0,
        }

    @property
    def stats(self) -> Dict[str, Any]:
        return dict(self._stats)

    def _fetch_sync(self, req: Request) -> Response:
        """Synchronous HTTP fetch executed in thread executor."""
        url = req.url
        if req.params:
            delim = "&" if "?" in url else "?"
            url = f"{url}{delim}{urlencode(req.params)}"

        headers = dict(req.headers)
        if self.rotate_ua and "User-Agent" not in headers:
            headers["User-Agent"] = random.choice(USER_AGENTS)

        py_req = URLRequest(url=url, data=req.data, headers=headers, method=req.method)
        start_time = time.monotonic()

        try:
            with urlopen(py_req, timeout=req.timeout) as resp:
                body = resp.read()
                resp_headers = dict(resp.headers.items())
                elapsed = time.monotonic() - start_time
                return Response(
                    url=url,
                    status_code=resp.status,
                    headers=resp_headers,
                    body=body,
                    request=req,
                    elapsed=elapsed,
                )
        except HTTPError as e:
            elapsed = time.monotonic() - start_time
            body = e.read() if hasattr(e, "read") else b""
            resp_headers = dict(e.headers.items()) if hasattr(e, "headers") and e.headers else {}
            return Response(
                url=url,
                status_code=e.code,
                headers=resp_headers,
                body=body,
                request=req,
                elapsed=elapsed,
                error=str(e),
            )
        except Exception as e:
            elapsed = time.monotonic() - start_time
            return Response(
                url=url,
                status_code=0,
                headers={},
                body=b"",
                request=req,
                elapsed=elapsed,
                error=str(e),
            )

    async def fetch(self, request: Request) -> Response:
        """Fetch request with domain rate limit and automatic retries."""
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self.concurrency)

        loop = asyncio.get_running_loop()
        retries_left = request.retries

        while True:
            await self._semaphore.acquire()
            try:
                await self.limiter.acquire(request.url)
                self._stats["requests_total"] += 1

                resp = await loop.run_in_executor(None, self._fetch_sync, request)

                if resp.is_success:
                    self._stats["requests_success"] += 1
                    return resp

                # Handle retriable errors (status 429, 5xx, or network failure)
                should_retry = (
                    retries_left > 0
                    and (resp.status_code == 0 or resp.status_code == 429 or resp.status_code >= 500)
                )

                if not should_retry:
                    self._stats["requests_failed"] += 1
                    return resp

                retries_left -= 1
                backoff = (2 ** (request.retries - retries_left)) + random.uniform(0.1, 0.5)
                logger.warning(
                    "Retrying %s in %.2fs (status=%s, err=%s, left=%d)",
                    request.url,
                    backoff,
                    resp.status_code,
                    resp.error,
                    retries_left,
                )
                await asyncio.sleep(backoff)
            finally:
                self._semaphore.release()

    def process_item(self, item: Dict[str, Any]):
        """Push an extracted item to all configured pipelines."""
        self._stats["items_processed"] += 1
        for pipe in self.pipelines:
            pipe.process_item(item)

    async def crawl(
        self,
        requests: List[Request],
        parse_func: Callable[[Response, "Crawler"], Any],
    ) -> List[Any]:
        """Crawl a batch of requests concurrently and process with parse_func."""
        self._stats["start_time"] = time.monotonic()

        for pipe in self.pipelines:
            pipe.open()

        try:
            tasks = []
            for req in requests:
                async def _worker(r: Request):
                    resp = await self.fetch(r)
                    if inspect.iscoroutinefunction(parse_func):
                        return await parse_func(resp, self)
                    return parse_func(resp, self)

                tasks.append(_worker(req))

            results = await asyncio.gather(*tasks, return_exceptions=True)
            return results
        finally:
            self._stats["elapsed_time"] = time.monotonic() - self._stats["start_time"]
            for pipe in self.pipelines:
                pipe.close()
