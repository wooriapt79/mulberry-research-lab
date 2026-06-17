# -*- coding: utf-8 -*-
"""
도메인 에이전트 03 — 지역 특성 분석

인제군 등 농촌 지역의 인구 구조·소득 수준·접근성을 분석하여
공동구매 전략 수립을 지원한다.

spirit_score = 0.85 (지역 공동체 강화, 소외 지역 접근성 개선)
CTO Koda · DAY5 · 2026-06-17
"""
from __future__ import annotations

from core.agents.domain_agent_base import AgentResult, DomainAgentBase

_REGION_PROFILES: dict[str, dict] = {
    "인제": {"population": 31000, "elderly_ratio": 0.38, "access_score": 0.42, "avg_income": 2800},
    "양구": {"population": 22000, "elderly_ratio": 0.35, "access_score": 0.38, "avg_income": 2600},
    "고성": {"population": 27000, "elderly_ratio": 0.40, "access_score": 0.45, "avg_income": 2700},
    "화천": {"population": 25000, "elderly_ratio": 0.37, "access_score": 0.41, "avg_income": 2650},
}
_DEFAULT_PROFILE = {"population": 50000, "elderly_ratio": 0.25, "access_score": 0.70, "avg_income": 3500}


def _extract_region(query: str) -> tuple[str, dict]:
    for name, profile in _REGION_PROFILES.items():
        if name in query:
            return name, profile
    return "일반 지역", _DEFAULT_PROFILE


class RegionalCharacteristicAgent(DomainAgentBase):
    domain: str = "regional_characteristic"
    spirit_score: float = 0.85

    async def process(self, query: str) -> AgentResult:
        region, profile = _extract_region(query)
        elderly_pct = int(profile["elderly_ratio"] * 100)
        access = "낮음" if profile["access_score"] < 0.5 else "보통"
        insight = (
            f"{region}: 고령 인구 {elderly_pct}%, 상품 접근성 {access}. "
            f"공동구매 거점 운영 시 배송 비용 절감 효과 높음."
        )
        return AgentResult(
            domain=self.domain,
            spirit_score=self.spirit_score,
            data={**profile, "region": region, "insight": insight},
            source="RegionalProfileDB",
        )
