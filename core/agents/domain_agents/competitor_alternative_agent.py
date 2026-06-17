# -*- coding: utf-8 -*-
"""
도메인 에이전트 06 — 경쟁 플랫폼 & 대안 상품

쿠팡·마켓컬리 등 경쟁 플랫폼 가격 동향과
대안 상품을 분석하여 Mulberry 공동구매의 차별점을 도출한다.

spirit_score = 0.82
CTO Koda · DAY5 · 2026-06-17
"""
from __future__ import annotations

from core.agents.domain_agent_base import AgentResult, DomainAgentBase

_COMPETITOR_DATA: dict[str, dict] = {
    "배추": {
        "coupang_price": 4500, "kurly_price": 5200, "mulberry_est": 3200,
        "mulberry_advantage": "32% 저렴 (공동구매 직거래)",
        "alternatives": ["얼갈이배추", "양배추"],
    },
    "감자": {
        "coupang_price": 6800, "kurly_price": 7500, "mulberry_est": 4900,
        "mulberry_advantage": "28% 저렴",
        "alternatives": ["고구마", "토란"],
    },
    "사과": {
        "coupang_price": 18000, "kurly_price": 22000, "mulberry_est": 14000,
        "mulberry_advantage": "22% 저렴",
        "alternatives": ["배", "감"],
    },
}
_DEFAULT_DATA = {
    "coupang_price": 10000, "kurly_price": 12000, "mulberry_est": 8000,
    "mulberry_advantage": "약 20% 저렴 (추정)",
    "alternatives": [],
}


def _extract_commodity(query: str) -> tuple[str, dict]:
    for name, data in _COMPETITOR_DATA.items():
        if name in query:
            return name, data
    return "일반 상품", _DEFAULT_DATA


class CompetitorAlternativeAgent(DomainAgentBase):
    domain: str = "competitor_alternative"
    spirit_score: float = 0.82

    async def process(self, query: str) -> AgentResult:
        commodity, data = _extract_commodity(query)
        alt_str = ", ".join(data["alternatives"]) if data["alternatives"] else "없음"
        insight = (
            f"Mulberry 공동구매 예상가 {data['mulberry_est']:,}원/kg — "
            f"{data['mulberry_advantage']}. 대안 상품: {alt_str}."
        )
        return AgentResult(
            domain=self.domain,
            spirit_score=self.spirit_score,
            data={**data, "commodity": commodity, "insight": insight},
            source="CompetitorPriceMonitor",
        )
