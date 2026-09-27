# ScrapeFlow ⚡

> Resilient, high-concurrency web scraping and automated data ingestion engine.  
> **Pure Python. Zero external dependencies.**

[![Tests](https://github.com/rekalnx/scrapeflow/actions/workflows/ci.yml/badge.svg)](https://github.com/rekalnx/scrapeflow/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-brightgreen.svg)](https://www.python.org/)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-0-success.svg)](#)

---

## Why ScrapeFlow?

Most Python scraping setups are either too heavy (Scrapy with twisted architectures) or too brittle (basic `requests` loops that collapse on rate limits and 429s).

**ScrapeFlow** hits the sweet spot:
- 🚀 **Asynchronous Concurrency**: Built on `asyncio` worker pools with non-blocking network I/O.
- 🛡️ **Intelligent Domain Limiter**: Automatically throttles requests per domain host so you don't burn proxies or get IP banned.
- 🔁 **Exponential Backoff Retries**: Automatically recovers from intermittent network drops, HTTP 429 (Too Many Requests), and 5xx server errors.
- 💾 **Multi-Sink Pipelines**: Stream extracted items simultaneously into JSON Lines (`.jsonl`), CSV, or SQLite with zero boilerplate.
- 📦 **Zero External Dependencies**: Runs on standard Python libraries. No C extensions, no heavy driver setups.

---

## Quickstart (30 Seconds)

### 1. Programmatic Crawl

```python
import asyncio
from scrapeflow import Crawler, Request, Response, Selector, JsonLinesPipeline

def parse(resp: Response, crawler: Crawler):
    if not resp.is_success:
        return
    
    sel = Selector(resp.text)
    title = sel.extract_first_regex(r"<title>(.*?)</title>", default="No title")
    
    crawler.process_item({
        "url": resp.url,
        "title": title,
        "status": resp.status_code
    })

async def main():
    crawler = Crawler(
        concurrency=5,
        default_delay=0.2,
        pipelines=[JsonLinesPipeline("results.jsonl")]
    )
    
    targets = [
        Request("https://news.ycombinator.com"),
        Request("https://python.org"),
    ]
    
    await crawler.crawl(targets, parse)
    print("Execution stats:", crawler.stats)

if __name__ == "__main__":
    asyncio.run(main())
```

---

### 2. Command Line Interface (CLI)

Run ad-hoc extractions directly from your terminal:

```bash
# Export titles and links to JSONL
python3 -m scrapeflow https://example.com https://python.org --extract-title --extract-links -o pages.jsonl

# Export structured data directly to SQLite database
python3 -m scrapeflow https://example.com -f sqlite -o output.db
```

---

## Core Architecture

```
            [ URLs / Request Queue ]
                       │
                       ▼
        [ Domain Rate Limiter (Token Bucket) ]
                       │
                       ▼
         [ Concurrency Worker Pool (5-50x) ]
                       │
                 ( HTTP Fetch )
                       │
             ┌─────────┴─────────┐
         [ Success ]         [ 429 / 5xx ]
             │                   │
             ▼                   ▼
      [ HTML / Regex ]     [ Exponential ]
        [ Selectors ]        [ Backoff ]
             │                   │
             ▼                   └─► ( Retry Queue )
      [ Multi-Sink Pipelines ]
      ├── JSON Lines (.jsonl)
      ├── Comma-Separated (.csv)
      └── SQLite DB (.sqlite)
```

---

## Features

| Feature | ScrapeFlow | Traditional Loops | Scrapy |
| :--- | :---: | :---: | :---: |
| **External Dependencies** | **0 (Zero)** | 1-3 | 20+ |
| **Async / Non-blocking** | ✅ Yes | ❌ No | ✅ Yes |
| **Domain-aware Throttling**| ✅ Built-in | ❌ Manual | ✅ Complex config |
| **Dynamic SQLite Export** | ✅ Automatic | ❌ Manual SQL | ❌ Manual Pipeline |
| **Memory Footprint** | `< 15 MB` | `~ 25 MB` | `~ 90 MB` |

---

## Running Tests

ScrapeFlow includes a complete test suite with mock servers:

```bash
python3 -m unittest discover tests
```

---

## License

MIT License. Designed and maintained by [Reihan Valentino](https://github.com/rekalnx).
