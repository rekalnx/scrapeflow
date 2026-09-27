"""Core data models for ScrapeFlow."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
import time


@dataclass
class Request:
    """Represents an HTTP request task."""
    url: str
    method: str = "GET"
    headers: Dict[str, str] = field(default_factory=dict)
    data: Optional[bytes] = None
    params: Dict[str, Any] = field(default_factory=dict)
    meta: Dict[str, Any] = field(default_factory=dict)
    retries: int = 3
    timeout: float = 15.0
    priority: int = 0


@dataclass
class Response:
    """Represents an HTTP response result."""
    url: str
    status_code: int
    headers: Dict[str, str]
    body: bytes
    request: Request
    elapsed: float = 0.0
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)

    @property
    def text(self) -> str:
        """Decode body text with fallback."""
        try:
            return self.body.decode("utf-8")
        except UnicodeDecodeError:
            return self.body.decode("latin-1", errors="replace")

    @property
    def is_success(self) -> bool:
        """Check if HTTP status indicates success (2xx)."""
        return 200 <= self.status_code < 300
