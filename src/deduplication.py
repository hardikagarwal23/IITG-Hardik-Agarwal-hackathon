import hashlib
import re
import time
from typing import Dict, Optional
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


class DeduplicationIndex:
    """Exact and canonical deduplication using URL cleaning and SHA-256 text hashing."""

    def __init__(self, ttl_seconds: int = 7200):
        self.ttl = ttl_seconds
        # hash -> {"timestamp": float, "url": str, "title": str, "seen_count": int}
        self.registry: Dict[str, dict] = {}

    @staticmethod
    def canonicalize_url(url: Optional[str]) -> str:
        """Strip tracking query parameters (utm_*, ref, etc.) and fragments."""
        if not url:
            return ""
        parsed = urlparse(url.strip())
        tracking_params = {
            "utm_source",
            "utm_medium",
            "utm_campaign",
            "utm_term",
            "utm_content",
            "fbclid",
            "gclid",
            "ref",
        }
        filtered_query = [
            (k, v)
            for k, v in parse_qsl(parsed.query, keep_blank_values=True)
            if k.lower() not in tracking_params
        ]
        clean_query = urlencode(filtered_query)
        clean_path = re.sub(r"/+", "/", parsed.path).rstrip("/")
        return urlunparse(
            (
                parsed.scheme.lower(),
                parsed.netloc.lower(),
                clean_path,
                "",
                clean_query,
                "",
            )
        )

    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize punctuation, casing, and whitespace."""
        text = text.lower()
        text = re.sub(r"[^\w\s]", "", text)
        return " ".join(text.split())

    def compute_hash(self, text: str, url: Optional[str] = None) -> str:
        canonical_url = self.canonicalize_url(url)
        normalized_content = self.normalize_text(text)
        composite = f"{canonical_url}|{normalized_content}"
        return hashlib.sha256(composite.encode("utf-8")).hexdigest()

    def _prune(self):
        now = time.time()
        expired = [
            k
            for k, v in self.registry.items()
            if now - v["timestamp"] > self.ttl
        ]
        for k in expired:
            del self.registry[k]

    def is_duplicate(self, text: str, url: Optional[str] = None) -> bool:
        self._prune()
        event_hash = self.compute_hash(text, url)
        return event_hash in self.registry

    def register(self, text: str, url: Optional[str] = None) -> str:
        self._prune()
        event_hash = self.compute_hash(text, url)
        now = time.time()
        if event_hash in self.registry:
            self.registry[event_hash]["seen_count"] += 1
            self.registry[event_hash]["timestamp"] = now
        else:
            self.registry[event_hash] = {
                "timestamp": now,
                "url": self.canonicalize_url(url),
                "title": text.strip(),
                "seen_count": 1,
            }
        return event_hash