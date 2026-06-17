# -*- coding: utf-8 -*-
"""
도메인 에이전트 07 — 물류·배송 조건

지역별 배송 소요 시간·비용·냉장 가능 여부를 분석.
농촌 거점 배송 최적화를 지원한다.

spirit_score = 0.83
CTO Koda · DAY5 · 2026-06-17
"""
from __future__ import annotations

from core.agents.domain_agent_base import AgentResult, DomainAgentBase

_LOGISTICS: dict[str, dict] = {
    "인제": {"delivery_days": 2, "cost_per_kg": 850, "cold_chain": True,  "hub": "춘천물류센터"},
    "양구": {"delivery_days": 3, "cost_per_kg": 950, "cold_chain": True,  "hub": "춘천물류센터"},
    "고성": {"delivery_days": 2, "cost_per_kg": 900, "cold_chain": False, "hub": "속초물류센터"},
    "화천": {"delivery_days": 2, "cost_per_kg": 820, "cold_chain": True,  "hub": "춘천물류센터"},
}
_DEFAULT_LOGISTICS = {"delivery_days": 1, "cost_per_kg": 500, "cold_chain": True, "hub": "수도권물류센터"}

_REGIONS = list(_LOGISTICS.keys())


def _extract_region(query: str) -> tuple[str, dict]:
    for r in _REGIONS:
        if r in query:
            return r, _LOGISTICS[r]
    return "일반 지역", _DEFAULT_LOGISTICS


class LogisticsDeliveryAgent(DomainAgentBase):
    domain: str = "logistics_delivery"
    spirit_score: float = 0.83

    async def process(self, query: str) -> AgentResult:
        region, info = _extract_region(query)
        cold = "냉장 가능" if info["cold_chain"] else "냉장 불가 (상온만)"
        insight = (
            f"{region} 배송: {info['delivery_days']}일 소요, "
            f"kg당 {info['cost_per_kg']:,}원, {cold}. "
            f"거점 허브: {info['hub']}."
        )
        return AgentResult(
            domain=self.domain,
            spirit_score=self.spirit_score,
            data={**info, "region": region, "insight": insight},
            source="LogisticsDB",
        )
