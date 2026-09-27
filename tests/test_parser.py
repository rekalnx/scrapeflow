"""Tests for Selector and parser."""

import unittest
from scrapeflow.parser import Selector


class TestParser(unittest.TestCase):
    def setUp(self):
        self.html = """
        <html>
            <head><title>Test Store</title></head>
            <body>
                <h1>Welcome to Store</h1>
                <a href="/product/1">Item 1</a>
                <a href="/product/2">Item 2</a>
                <span class="price">$49.99</span>
            </body>
        </html>
        """

    def test_extract_links(self):
        sel = Selector(self.html)
        links = sel.extract_links()
        self.assertIn("/product/1", links)
        self.assertIn("/product/2", links)

    def test_extract_regex(self):
        sel = Selector(self.html)
        price = sel.extract_first_regex(r"\$([0-9]+\.[0-9]+)")
        self.assertEqual(price, "49.99")
        title = sel.extract_first_regex(r"<title>(.*?)</title>")
        self.assertEqual(title, "Test Store")

    def test_extract_text(self):
        sel = Selector(self.html)
        text = sel.extract_text()
        self.assertIn("Welcome to Store", text)
        self.assertIn("Item 1", text)


if __name__ == "__main__":
    unittest.main()
