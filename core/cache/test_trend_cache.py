# -*- coding: utf-8 -*-
"""Tests for TrendCache - verifies 5-minute TTL caching avoids repeated API calls."""

import time
from unittest.mock import patch

import pytest

from core.cache.trend_cache import TrendCache


@pytest.fixture
def cache(tmp_path):
    return TrendCache(cache_dir=str(tmp_path / "trend_cache"), ttl_seconds=300)


def test_first_request_calls_api(cache):
    with patch.object(TrendCache, "_fetch_from_api", return_value=["a", "b"]) as mock_api:
        result = cache.get_trends("korea food")

    mock_api.assert_called_once()
    assert result["trends"] == ["a", "b"]
    assert cache.cache_hit_ratio() == 0.0


def test_repeated_requests_hit_cache(cache):
    with patch.object(TrendCache, "_fetch_from_api", return_value=["a", "b"]) as mock_api:
        cache.get_trends("korea food")
        for _ in range(4):
            cache.get_trends("korea food")

    mock_api.assert_called_once()
    assert cache.cache_hit_ratio() == 0.8


def test_expired_entry_refetches(cache):
    with patch.object(TrendCache, "_fetch_from_api", return_value=["a"]) as mock_api:
        cache.get_trends("korea food")

    cache.ttl_seconds = 0
    time.sleep(0.01)

    with patch.object(TrendCache, "_fetch_from_api", return_value=["a", "b"]) as mock_api:
        result = cache.get_trends("korea food")

    mock_api.assert_called_once()
    assert result["trends"] == ["a", "b"]


def test_ttl_remaining_decreases(cache):
    with patch.object(TrendCache, "_fetch_from_api", return_value=["a"]):
        first = cache.get_trends("korea food")

    assert first["ttl_remaining"] == 300

    with patch.object(TrendCache, "_fetch_from_api", return_value=["a"]):
        second = cache.get_trends("korea food")

    assert second["ttl_remaining"] <= 300


def test_different_queries_use_separate_cache_entries(cache):
    with patch.object(TrendCache, "_fetch_from_api", return_value=["food"]) as mock_api:
        cache.get_trends("korea food")
        cache.get_trends("japan food")

    assert mock_api.call_count == 2
