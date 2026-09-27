"""Example: Scraping product pages into JSONL and SQLite simultaneously."""

import asyncio
from scrapeflow import Crawler, Request, Response, Selector, JsonLinesPipeline, SqlitePipeline


def parse_page(resp: Response, crawler: Crawler):
    if not resp.is_success:
        print(f"Skipping failed page: {resp.url} ({resp.status_code})")
        return

    sel = Selector(resp.text)
    title = sel.extract_first_regex(r"<title>(.*?)</title>", default="Unknown")

    item = {
        "url": resp.url,
        "title": title,
        "status": resp.status_code,
        "latency_sec": round(resp.elapsed, 3),
    }

    # Automatically stream to all pipelines
    crawler.process_item(item)
    print(f"[EXTRACTED] {title} ({resp.url})")


async def main():
    crawler = Crawler(
        concurrency=3,
        default_delay=0.2,
        pipelines=[
            JsonLinesPipeline("demo_output.jsonl"),
            SqlitePipeline("demo_output.db", table_name="crawled_pages"),
        ],
    )

    urls = [
        "https://httpbin.org/html",
        "https://httpbin.org/links/5/0",
        "https://httpbin.org/links/5/1",
    ]
    requests = [Request(url=u) for u in urls]

    print("Starting pipeline...")
    await crawler.crawl(requests, parse_page)
    print("Crawling finished. Stats:", crawler.stats)


if __name__ == "__main__":
    asyncio.run(main())
