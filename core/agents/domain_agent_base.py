# -*- coding: utf-8 -*-
"""
도메인 전문가 에이전트 베이스 클래스

MulberrySearchOrchestrator가 asyncio.gather로 병렬 호출하는
각 도메인 에이전트의 공통 인터페이스를 정의한다.

CTO Koda · DAY4 · 2026-06-17
"""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentResult:
    """도메인 에이전트 처리 결과"""
    domain: str
    spirit_score: float        # 0.0 ~ 1.0 (장승배기 정신 정합도)
    data: dict[str, Any]       # 도메인별 실질 데이터
    source: str = ""           # 데이터 출처 설명
    latency_ms: float = 0.0
    error: str | None = None   # None이면 정상

    @property
    def ok(self) -> bool:
        return self.error is None


class DomainAgentBase(ABC):
    """
    도메인 전문가 에이전트 베이스

    서브클래스는 domain, spirit_score를 선언하고
    process()를 구현한다.

    spirit_score는 에이전트가 장승배기 정신(어르신·지역·공익)에
    얼마나 부합하는 데이터를 제공하는지를 나타낸다.
    MulberrySearchOrchestrator는 spirit_score >= SPIRIT_FILTER_THRESHOLD인
    결과만 최종 답변에 포함시킨다.
    """

    domain: str = ""
    spirit_score: float = 1.0

    @abstractmethod
    async def process(self, query: str) -> AgentResult:
        """쿼리를 처리하고 AgentResult를 반환한다."""

    async def safe_process(self, query: str) -> AgentResult:
        """예외를 AgentResult.error로 변환하는 래퍼."""
        t0 = time.monotonic()
        try:
            result = await self.process(query)
            result.latency_ms = (time.monotonic() - t0) * 1000
            return result
        except Exception as exc:  # noqa: BLE001
            return AgentResult(
                domain=self.domain,
                spirit_score=self.spirit_score,
                data={},
                error=str(exc),
                latency_ms=(time.monotonic() - t0) * 1000,
            )
