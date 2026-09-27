"""Lightweight HTML and text extraction utilities using stdlib."""

import re
from html.parser import HTMLParser
from typing import Dict, List, Optional


class SimpleHTMLParser(HTMLParser):
    """Zero-dependency HTML tree and text collector."""

    def __init__(self):
        super().__init__()
        self.text_chunks: List[str] = []
        self.links: List[str] = []
        self.images: List[str] = []

    def handle_data(self, data: str):
        cleaned = data.strip()
        if cleaned:
            self.text_chunks.append(cleaned)

    def handle_starttag(self, tag: str, attrs: List[tuple]):
        attr_dict = dict(attrs)
        if tag == "a" and "href" in attr_dict:
            self.links.append(attr_dict["href"])
        elif tag == "img" and "src" in attr_dict:
            self.images.append(attr_dict["src"])


class Selector:
    """Convenient text, regex, and element extraction wrapper."""

    def __init__(self, html: str):
        self.html = html

    def xpath_regex(self, pattern: str) -> List[str]:
        """Find all regex matches in source."""
        return re.findall(pattern, self.html, flags=re.DOTALL | re.IGNORECASE)

    def extract_first_regex(self, pattern: str, default: Optional[str] = None) -> Optional[str]:
        """Extract first regex match or group."""
        match = re.search(pattern, self.html, flags=re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1) if match.groups() else match.group(0)
        return default

    def extract_links(self) -> List[str]:
        """Extract all href targets."""
        parser = SimpleHTMLParser()
        parser.feed(self.html)
        return parser.links

    def extract_text(self) -> str:
        """Extract all visible text joined by spaces."""
        parser = SimpleHTMLParser()
        parser.feed(self.html)
        return " ".join(parser.text_chunks)
