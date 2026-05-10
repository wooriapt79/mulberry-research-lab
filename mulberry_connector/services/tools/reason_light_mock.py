"""
reason.light 캐시 기반 모킹 (RyuWon 설계)

핵심 구조: 추후 경량모델 로드 시 이 파일만 교체 (핫스왑).
TTL 기반 캐시로 동일 프롬프트 반복 요청 비용 절감.
"""

import hashlib
import time
from typing import Dict

CACHE: Dict[str, Dict] = {}
CACHE_TTL_SEC = 3600  # 1시간


def run(
    prompt: str,
    max_think_tokens: int = 512,
    max_answer_tokens: int = 256,
) -> Dict:
    """
    캐시 기반 경량 추론 (추후 경량모델로 핫스왑 가능).

    캐시 히트 → 즉시 반환
    캐시 미스 → 패턴 기반 정형 응답 생성 후 캐시 저장
    """
    key = hashlib.sha256(prompt.encode("utf-8")).hexdigest()

    # 캐시 히트
    if key in CACHE:
        entry = CACHE[key]
        if time.time() - entry["cached_at"] < CACHE_TTL_SEC:
            result = entry["response"].copy()
            result["cache_hit"] = True
            return result

    # 캐시 미스 — 정형 응답
    response = {
        "thinking": "캐시 기반 유사 케이스 참조 중... (reason.light 모킹)",
        "answer": f"[reason.light] 유사 문맥 기반 정형 응답.\n입력 요약: {prompt[:80]}...",
        "tokens_used": {"think": 48, "answer": 24},
        "spirit_score": 0.82,
        "labels": ["reasoning_collaboration"],
        "distill_weight": 0.5,
        "fallback_used": True,
        "cache_hit": False,
    }

    CACHE[key] = {"response": response, "cached_at": time.time()}
    return response


def cache_stats() -> Dict:
    """캐시 상태 조회."""
    now = time.time()
    valid = sum(1 for e in CACHE.values() if now - e["cached_at"] < CACHE_TTL_SEC)
    return {"total": len(CACHE), "valid": valid, "ttl_sec": CACHE_TTL_SEC}


def clear_cache():
    """캐시 초기화."""
    CACHE.clear()
