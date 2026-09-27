"""Tests for export pipelines."""

import csv
import json
import os
import shutil
import sqlite3
import tempfile
import unittest
from scrapeflow.pipeline import CsvPipeline, JsonLinesPipeline, SqlitePipeline


class TestPipelines(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_jsonlines_pipeline(self):
        out_path = os.path.join(self.test_dir, "data.jsonl")
        pipe = JsonLinesPipeline(out_path)
        pipe.open()
        pipe.process_item({"name": "Item A", "price": 10.5})
        pipe.process_item({"name": "Item B", "price": 20.0})
        pipe.close()

        with open(out_path, "r", encoding="utf-8") as f:
            lines = [json.loads(line) for line in f]

        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0]["name"], "Item A")
        self.assertEqual(lines[1]["price"], 20.0)

    def test_csv_pipeline(self):
        out_path = os.path.join(self.test_dir, "data.csv")
        pipe = CsvPipeline(out_path, fieldnames=["title", "score"])
        pipe.open()
        pipe.process_item({"title": "Post 1", "score": 99})
        pipe.process_item({"title": "Post 2", "score": 42})
        pipe.close()

        with open(out_path, "r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))

        self.assertEqual(len(reader), 2)
        self.assertEqual(reader[0]["title"], "Post 1")
        self.assertEqual(reader[1]["score"], "42")

    def test_sqlite_pipeline(self):
        db_path = os.path.join(self.test_dir, "test.db")
        pipe = SqlitePipeline(db_path, table_name="products")
        pipe.open()
        pipe.process_item({"sku": "PROD-1", "stock": 15})
        pipe.process_item({"sku": "PROD-2", "stock": 0})
        pipe.close()

        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT sku, stock FROM products ORDER BY id ASC")
        rows = cur.fetchall()
        conn.close()

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0], ("PROD-1", 15))
        self.assertEqual(rows[1], ("PROD-2", 0))


if __name__ == "__main__":
    unittest.main()
