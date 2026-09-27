"""CLI entrypoint for ScrapeFlow."""

import argparse
import asyncio
import sys
from .engine import Crawler
from .models import Request, Response
from .parser import Selector
from .pipeline import CsvPipeline, JsonLinesPipeline, SqlitePipeline


def main():
    parser = argparse.ArgumentParser(description="ScrapeFlow - Asynchronous Web Scraping Pipeline")
    parser.add_argument("urls", nargs="+", help="Target URL(s) to fetch")
    parser.add_argument("-c", "--concurrency", type=int, default=5, help="Concurrent workers (default: 5)")
    parser.add_argument("-d", "--delay", type=float, default=0.2, help="Domain rate limit delay (seconds)")
    parser.add_argument("-f", "--format", choices=["jsonl", "csv", "sqlite"], default="jsonl", help="Export format")
    parser.add_argument("-o", "--output", default="output.jsonl", help="Output file path")
    parser.add_argument("--extract-title", action="store_true", help="Extract page title automatically")
    parser.add_argument("--extract-links", action="store_true", help="Extract links automatically")

    args = parser.parse_args()

    pipeline = None
    if args.format == "jsonl":
        pipeline = JsonLinesPipeline(args.output)
    elif args.format == "csv":
        pipeline = CsvPipeline(args.output)
    elif args.format == "sqlite":
        pipeline = SqlitePipeline(args.output)

    crawler = Crawler(
        concurrency=args.concurrency,
        default_delay=args.delay,
        pipelines=[pipeline],
    )

    requests = [Request(url=u) for u in args.urls]

    def parse(resp: Response, c: Crawler):
        sel = Selector(resp.text)
        item = {
            "url": resp.url,
            "status": resp.status_code,
            "elapsed_seconds": round(resp.elapsed, 3),
        }
        if args.extract_title:
            item["title"] = sel.extract_first_regex(r"<title>(.*?)</title>", default="")
        if args.extract_links:
            item["links"] = sel.extract_links()

        c.process_item(item)
        print(f"[{resp.status_code}] {resp.url} ({round(resp.elapsed, 2)}s)")

    print(f"ScrapeFlow starting: {len(requests)} URLs with concurrency {args.concurrency}")
    asyncio.run(crawler.crawl(requests, parse))
    print(f"Done. Stats: {crawler.stats}")
    print(f"Output saved to: {args.output}")


if __name__ == "__main__":
    main()
