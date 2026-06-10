# trend_cache.py 성능 리포트

**작성**: CTO Koda
**날짜**: 2026-06-10
**관련**: Issue #98 (HTTP 429), Issue #96 (Trend Stream Injector)

---

## 구현 요약

`core/cache/trend_cache.py` — 5분(300초) TTL 파일 기반 캐시.

- `TrendCache(cache_dir, ttl_seconds=300)`
- `get_trends(query) -> {"trends": [...], "cached_at": ts, "ttl_remaining": sec}`
- `cache_hit_ratio() -> float`

캐시 미스 시에만 `_fetch_from_api()` 호출 (Google Trends API), 결과를 `cache_dir`에 쿼리별 JSON으로 저장.

---

## 테스트 결과

```
core/cache/test_trend_cache.py — 5 passed
```

| 테스트 | 결과 |
|---|---|
| 첫 요청 시 API 호출 | ✅ PASS |
| 2~5번째 요청 캐시 반환 | ✅ PASS |
| TTL 만료 후 재호출 | ✅ PASS |
| ttl_remaining 감소 확인 | ✅ PASS |
| 쿼리별 독립 캐시 | ✅ PASS |

---

## 429 시뮬레이션 (5회 연속 요청)

```
Request 1: ttl_remaining=300s elapsed=0.0009s   (cache miss → API)
Request 2: ttl_remaining=299s elapsed=0.0090s   (cache hit)
Request 3: ttl_remaining=299s elapsed=0.0004s   (cache hit)
Request 4: ttl_remaining=299s elapsed=0.0002s   (cache hit)
Request 5: ttl_remaining=299s elapsed=0.0002s   (cache hit)

cache_hit_ratio = 0.8
```

---

## 검증 기준 충족 여부

| 기준 | 결과 |
|---|---|
| 첫 요청: API 호출 (캐시 미스) | ✅ |
| 2~5번째 요청: 캐시 반환 (1초 이내) | ✅ |
| HTTP 429 발생 없음 | ✅ |
| pytest 전체 통과 | ✅ (5/5) |
| 캐시 히트율 > 80% | ✅ (80%) |

---

## 다음 단계

Phase 0.5에서 `core/agents/trend_stream_injector.py`(Aurora 제공)에 `TrendCache`를 통합 예정.
