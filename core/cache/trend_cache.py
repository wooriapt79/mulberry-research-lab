# -*- coding: utf-8 -*-
"""
TrendCache - 5-minute TTL cache for Google Trends API calls.

Purpose: prevent HTTP 429 (rate limit) errors observed in Issue #98
by serving repeated queries from a local JSON cache within the TTL window.
"""

import json
import time
from pathlib import Path
from typing import Any, Dict


class TrendCache:
    """File-backed cache with an in-memory TTL layer for trend queries."""

    def __init__(self, cache_dir: str = "./trend_cache", ttl_seconds: int = 300):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds = ttl_seconds
        self._hits = 0
        self._misses = 0

    def _cache_path(self, query: str) -> Path:
        safe_name = "".join(c if c.isalnum() else "_" for c in query.lower())
        return self.cache_dir / f"{safe_name}.json"

    def get_trends(self, query: str) -> Dict[str, Any]:
        """
        Return cached trends if fresh, otherwise call the API and cache the result.

        Returns:
            {"trends": [...], "cached_at": <timestamp>, "ttl_remaining": <seconds>}
        """
        path = self._cache_path(query)

        if path.exists():
            with path.open("r", encoding="utf-8") as f:
                entry = json.load(f)

            age = time.time() - entry["cached_at"]
            if age < self.ttl_seconds:
                self._hits += 1
                entry["ttl_remaining"] = max(0, int(self.ttl_seconds - age))
                return entry

        self._misses += 1
        trends = self._fetch_from_api(query)
        entry = {
            "trends": trends,
            "cached_at": time.time(),
            "ttl_remaining": self.ttl_seconds,
        }
        with path.open("w", encoding="utf-8") as f:
            json.dump(entry, f, ensure_ascii=False)

        return entry

    def _fetch_from_api(self, query: str) -> list:
        """Fetch trend data from the upstream API. Override or mock in tests."""
        import requests

        response = requests.get(
            "https://trends.google.com/trends/api/dailytrends",
            params={"geo": "KR", "q": query},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    def cache_hit_ratio(self) -> float:
        """Return hits / (hits + misses), or 0.0 if no requests yet."""
        total = self._hits + self._misses
        if total == 0:
            return 0.0
        return self._hits / total
