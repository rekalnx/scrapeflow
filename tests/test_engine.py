"""Tests for Crawler engine with mock HTTP server."""

import asyncio
import http.server
import threading
import unittest
from scrapeflow.engine import Crawler
from scrapeflow.models import Request, Response
from scrapeflow.pipeline import BasePipeline


class MockHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == "/ok":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><title>Success Page</title><body>OK</body></html>")
        elif self.path == "/retry-then-ok":
            if not hasattr(self.server, "attempts"):
                self.server.attempts = 0
            self.server.attempts += 1
            if self.server.attempts < 2:
                self.send_response(503)
                self.end_headers()
                self.wfile.write(b"Service Unavailable")
            else:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"Recovered")
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")


class ListSink(BasePipeline):
    def __init__(self):
        self.items = []

    def process_item(self, item):
        self.items.append(item)


class TestCrawlerEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = http.server.HTTPServer(("127.0.0.1", 0), MockHandler)
        cls.port = cls.server.server_port
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_crawl_basic(self):
        sink = ListSink()
        crawler = Crawler(concurrency=2, default_delay=0.01, pipelines=[sink])
        reqs = [
            Request(url=f"http://127.0.0.1:{self.port}/ok"),
            Request(url=f"http://127.0.0.1:{self.port}/404"),
        ]

        def parse(resp: Response, c: Crawler):
            if resp.is_success:
                c.process_item({"url": resp.url, "body": resp.text})

        asyncio.run(crawler.crawl(reqs, parse))
        self.assertEqual(len(sink.items), 1)
        self.assertIn("Success Page", sink.items[0]["body"])
        stats = crawler.stats
        self.assertEqual(stats["requests_total"], 2)
        self.assertEqual(stats["requests_success"], 1)

    def test_crawl_retry(self):
        crawler = Crawler(concurrency=1, default_delay=0.01)
        req = Request(url=f"http://127.0.0.1:{self.port}/retry-then-ok", retries=2)

        async def run():
            resp = await crawler.fetch(req)
            return resp

        resp = asyncio.run(run())
        self.assertTrue(resp.is_success)
        self.assertEqual(resp.text, "Recovered")


if __name__ == "__main__":
    unittest.main()
