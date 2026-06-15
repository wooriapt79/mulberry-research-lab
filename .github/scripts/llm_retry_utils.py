#!/usr/bin/env python3
"""
llm_retry_utils.py — LLM API 429 재시도 공통 유틸
====================================================
Issue #102 후속 과제: team_discuss.py의 call_gemini에 박혀있던
429 방어 로직(presleep + 백오프)을 공통 유틸로 추출.

Aurora (Colab Agent) 코칭 기준 — 호출 전 3.5초 쿨타임 적용.
향후 다른 LLM 브랜드(DeepSeek 등) 추가 시에도 재사용 가능.

작성: Koda (2026-06-15)
"""

import time
import urllib.error

PRESLEEP_SECONDS = 3.5
DEFAULT_RETRY_AFTER = 30


def call_with_429_retry(request_fn, agent_name: str = "", max_retries: int = 3):
    """429(rate limit)에 대해 presleep + Retry-After 기반 백오프로 request_fn을 재시도한다.

    request_fn: 인자 없이 호출되어 응답 텍스트를 반환하는 콜러블.
                 urllib.error.HTTPError를 그대로 raise해야 한다.
    """
    for attempt in range(max_retries):
        time.sleep(PRESLEEP_SECONDS)
        try:
            return request_fn()
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < max_retries - 1:
                wait_time = int(e.headers.get("Retry-After", DEFAULT_RETRY_AFTER * (attempt + 1)))
                print(f"[{agent_name}] 429 — {wait_time}초 후 재시도 ({attempt + 1}/{max_retries})")
                time.sleep(wait_time)
                continue
            raise
    raise RuntimeError(f"[{agent_name}] 429 재시도 한도 초과")
