# -*- coding: utf-8 -*-
"""
도메인 에이전트 05 — 공동구매 타이밍 최적화

수확 주기·명절 수요·시장 사이클을 종합하여
최적 공동구매 실시 시점을 제안한다.

spirit_score = 0.87
CTO Koda · DAY5 · 2026-06-17
"""
from __future__ import annotations

import datetime

from core.agents.domain_agent_base import AgentResult, DomainAgentBase

# 월별 품목 최적 구매 시즌 (1=최적, 0=비추천)
_SEASONAL_SCORE: dict[str, list[float]] = {
    "배추":  [0.3, 0.3, 0.4, 0.5, 0.5, 0.6, 0.5, 0.6, 0.8, 1.0, 0.9, 0.5],
    "감자":  [0.4, 0.4, 0.5, 0.7, 1.0, 0.9, 0.7, 0.5, 0.4, 0.4, 0.4, 0.4],
    "사과":  [0.3, 0.3, 0.3, 0.4, 0.5, 0.5, 0.6, 0.8, 1.0, 1.0, 0.9, 0.5],
    "고구마":[0.4, 0.4, 0.4, 0.5, 0.5, 0.5, 0.5, 0.7, 1.0, 0.9, 0.7, 0.5],
    "쌀":    [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.6, 0.8, 1.0, 1.0, 0.8, 0.6],
}
_COMMODITIES = list(_SEASONAL_SCORE.keys())


def _extract_commodity(query: str) -> str:
    for c in _COMMODITIES:
        if c in query:
            return c
    return "배추"


class GroupBuyTimingAgent(DomainAgentBase):
    domain: str = "group_buy_timing"
    spirit_score: float = 0.87

    async def process(self, query: str) -> AgentResult:
        commodity = _extract_commodity(query)
        month = datetime.date.today().month
        scores = _SEASONAL_SCORE.get(commodity, [0.5] * 12)
        current_score = scores[month - 1]
        best_month = scores.index(max(scores)) + 1

        if current_score >= 0.8:
            timing = "지금이 최적 시점"
        elif current_score >= 0.6:
            timing = "적정 시점 (구매 가능)"
        else:
            timing = f"비추천 — {best_month}월 구매 권장"

        return AgentResult(
            domain=self.domain,
            spirit_score=self.spirit_score,
            data={
                "commodity": commodity,
                "current_month": month,
                "seasonal_score": current_score,
                "best_month": best_month,
                "recommendation": timing,
            },
            source="SeasonalCalendar",
        )
