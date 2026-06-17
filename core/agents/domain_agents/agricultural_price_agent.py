# -*- coding: utf-8 -*-
"""
도메인 에이전트 01 — 글로벌 농산물 시세

어르신·지역 거점이 공동구매 품목의 적정 가격을 판단하도록
글로벌·국내 농산물 시세 정보를 제공한다.

spirit_score = 0.92
→ 식품 접근성(매슬로우 1단계)과 경제적 공정성에 직접 기여.

CTO Koda · DAY4 · 2026-06-17
"""
from __future__ import annotations

from typing import Any

from core.agents.domain_agent_base import AgentResult, DomainAgentBase
from core.gateway.baekya_data_gateway import BaekyaDataGateway, MockBaekyaDataGateway

# 시세 조회 대상 품목 키워드 매핑
_COMMODITY_KEYWORDS: dict[str, str] = {
    "사과": "apple",
    "배": "pear",
    "포도": "grape",
    "쌀": "rice",
    "감자": "potato",
    "고구마": "sweet_potato",
    "양파": "onion",
    "마늘": "garlic",
    "배추": "cabbage",
    "무": "radish",
}


def _extract_commodity(query: str) -> str:
    """쿼리에서 품목을 추출한다. 매칭 없으면 'general'."""
    for kor, eng in _COMMODITY_KEYWORDS.items():
        if kor in query:
            return eng
    return "general"


class AgriculturalPriceAgent(DomainAgentBase):
    """글로벌 농산물 시세 도메인 에이전트"""

    domain: str = "agricultural_price"
    spirit_score: float = 0.92

    def __init__(self, gateway: BaekyaDataGateway | None = None) -> None:
        self._gateway = gateway or MockBaekyaDataGateway()

    async def process(self, query: str) -> AgentResult:
        commodity = _extract_commodity(query)
        prices = await self._gateway.fetch_agricultural_prices(commodity)

        insight = _build_insight(prices)

        return AgentResult(
            domain=self.domain,
            spirit_score=self.spirit_score,
            data={
                "commodity": prices.get("commodity"),
                "prices": prices.get("prices", {}),
                "trend": prices.get("trend"),
                "unit": prices.get("unit"),
                "insight": insight,
            },
            source=prices.get("source", "BaekyaDataGateway"),
        )


def _build_insight(prices: dict[str, Any]) -> str:
    trend = prices.get("trend", "stable")
    spot = prices.get("prices", {}).get("spot")
    if spot is None:
        return "시세 정보를 가져올 수 없습니다."
    if trend == "rising":
        return f"현재 시세 {spot:,}원/kg — 상승 중. 조기 구매가 유리합니다."
    if trend == "falling":
        return f"현재 시세 {spot:,}원/kg — 하락 중. 관망 또는 소량 구매를 권장합니다."
    return f"현재 시세 {spot:,}원/kg — 안정적입니다."
