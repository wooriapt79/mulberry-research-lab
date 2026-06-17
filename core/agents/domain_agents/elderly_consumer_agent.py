# -*- coding: utf-8 -*-
"""
도메인 에이전트 04 — 어르신 소비 패턴 & 니즈

매슬로우 욕구 단계 기반으로 어르신의 구매 행동·선호도를 분석.
공동구매 품목 선정과 커뮤니케이션 전략에 활용한다.

spirit_score = 0.90 (어르신 복지·존중, 매슬로우 1~3단계 직접 기여)
CTO Koda · DAY5 · 2026-06-17
"""
from __future__ import annotations

from core.agents.domain_agent_base import AgentResult, DomainAgentBase

_COMMODITY_PREFS: dict[str, dict] = {
    "배추": {"preference_score": 0.92, "repeat_purchase_rate": 0.88, "group_buy_fit": "매우 높음"},
    "감자": {"preference_score": 0.90, "repeat_purchase_rate": 0.85, "group_buy_fit": "매우 높음"},
    "사과": {"preference_score": 0.87, "repeat_purchase_rate": 0.80, "group_buy_fit": "높음"},
    "쌀":   {"preference_score": 0.95, "repeat_purchase_rate": 0.95, "group_buy_fit": "매우 높음"},
    "고구마": {"preference_score": 0.88, "repeat_purchase_rate": 0.82, "group_buy_fit": "높음"},
}
_DEFAULT_PREF = {"preference_score": 0.75, "repeat_purchase_rate": 0.70, "group_buy_fit": "보통"}


def _extract_commodity(query: str) -> tuple[str, dict]:
    for name, pref in _COMMODITY_PREFS.items():
        if name in query:
            return name, pref
    return "일반 상품", _DEFAULT_PREF


class ElderlyConsumerAgent(DomainAgentBase):
    domain: str = "elderly_consumer"
    spirit_score: float = 0.90

    async def process(self, query: str) -> AgentResult:
        commodity, pref = _extract_commodity(query)
        fit = pref["group_buy_fit"]
        repeat = int(pref["repeat_purchase_rate"] * 100)
        insight = (
            f"어르신 {commodity} 선호도 높음 (재구매율 {repeat}%). "
            f"공동구매 적합도: {fit}. "
            f"소량·자주 구매 패턴 — 월 2회 이하 배송 권장."
        )
        return AgentResult(
            domain=self.domain,
            spirit_score=self.spirit_score,
            data={**pref, "commodity": commodity, "maslow_level": "1~3단계", "insight": insight},
            source="ElderlyConsumerResearch",
        )
