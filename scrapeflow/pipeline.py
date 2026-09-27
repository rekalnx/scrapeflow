"""Data export pipelines: JSON Lines, CSV, and SQLite."""

import csv
import json
import sqlite3
from typing import Any, Dict, List, Optional
import os


class BasePipeline:
    """Base class for data sinks."""
    def open(self):
        pass

    def process_item(self, item: Dict[str, Any]):
        raise NotImplementedError

    def close(self):
        pass


class JsonLinesPipeline(BasePipeline):
    """Streams items as newline-delimited JSON."""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self._file = None

    def open(self):
        os.makedirs(os.path.dirname(os.path.abspath(self.filepath)), exist_ok=True)
        self._file = open(self.filepath, "a", encoding="utf-8")

    def process_item(self, item: Dict[str, Any]):
        if not self._file:
            self.open()
        line = json.dumps(item, ensure_ascii=False)
        self._file.write(line + "\n")
        self._file.flush()

    def close(self):
        if self._file:
            self._file.close()
            self._file = None


class CsvPipeline(BasePipeline):
    """Streams tabular items to CSV with dynamic header management."""

    def __init__(self, filepath: str, fieldnames: Optional[List[str]] = None):
        self.filepath = filepath
        self.fieldnames = fieldnames
        self._file = None
        self._writer = None
        self._headers_written = False

    def open(self):
        os.makedirs(os.path.dirname(os.path.abspath(self.filepath)), exist_ok=True)
        file_exists = os.path.exists(self.filepath) and os.path.getsize(self.filepath) > 0
        self._file = open(self.filepath, "a", newline="", encoding="utf-8")
        if file_exists:
            self._headers_written = True

    def process_item(self, item: Dict[str, Any]):
        if not self._file:
            self.open()

        if not self.fieldnames:
            self.fieldnames = list(item.keys())

        if not self._writer:
            self._writer = csv.DictWriter(
                self._file, fieldnames=self.fieldnames, extrasaction="ignore"
            )

        if not self._headers_written:
            self._writer.writeheader()
            self._headers_written = True

        self._writer.writerow(item)
        self._file.flush()

    def close(self):
        if self._file:
            self._file.close()
            self._file = None


class SqlitePipeline(BasePipeline):
    """Persists structured items directly to SQLite database."""

    def __init__(self, db_path: str, table_name: str = "scraped_data"):
        self.db_path = db_path
        self.table_name = table_name
        self._conn = None
        self._schema_initialized = False

    def open(self):
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        self._conn = sqlite3.connect(self.db_path)

    def _ensure_schema(self, item: Dict[str, Any]):
        if not self._schema_initialized:
            cursor = self._conn.cursor()
            cols = ["id INTEGER PRIMARY KEY AUTOINCREMENT"]
            for k, v in item.items():
                safe_key = "".join(c for c in k if c.isalnum() or c == "_")
                if isinstance(v, int):
                    col_type = "INTEGER"
                elif isinstance(v, float):
                    col_type = "REAL"
                else:
                    col_type = "TEXT"
                cols.append(f'"{safe_key}" {col_type}')
            query = f'CREATE TABLE IF NOT EXISTS "{self.table_name}" ({", ".join(cols)})'
            cursor.execute(query)
            self._conn.commit()
            self._schema_initialized = True

    def process_item(self, item: Dict[str, Any]):
        if not self._conn:
            self.open()

        keys = list(item.keys())
        self._ensure_schema(item)

        sanitized_keys = ["".join(c for c in k if c.isalnum() or c == "_") for k in keys]
        col_names = ", ".join(f'"{k}"' for k in sanitized_keys)
        placeholders = ", ".join("?" for _ in keys)
        values = [v if isinstance(v, (int, float, str, bytes)) or v is None else json.dumps(v) for v in item.values()]

        cursor = self._conn.cursor()
        query = f'INSERT INTO "{self.table_name}" ({col_names}) VALUES ({placeholders})'
        cursor.execute(query, values)
        self._conn.commit()

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None
