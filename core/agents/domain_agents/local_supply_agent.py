# -*- coding: utf-8 -*-
"""
도메인 에이전트 02 — 국내 수급 상황

특정 지역의 공동구매 품목 수급 현황을 파악하여
재고 부족·과잉 리스크를 조기에 감지한다.

spirit_score = 0.88
→ 지역 공동체(소속감, 매슬로우 3단계)와 안전한 식품 공급(2단계)에 기여.

CTO Koda · DAY4 · 2026-06-17
"""
from __future__ import annotations

from core.agents.domain_agent_base import AgentResult, DomainAgentBase
from core.gateway.baekya_data_gateway import BaekyaDataGateway, MockBaekyaDataGateway

# 지역 키워드 매핑 (간략화)
_REGION_KEYWORDS: list[str] = [
    "서울", "부산", "대구", "인천", "광주", "대전", "울산",
    "경기", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주",
]


def _extract_region(query: str) -> str:
    for region in _REGION_KEYWORDS:
        if region in query:
            return region
    return "전국"


class LocalSupplyAgent(DomainAgentBase):
    """국내 수급 상황 도메인 에이전트"""

    domain: str = "local_supply"
    spirit_score: float = 0.88

    def __init__(self, gateway: BaekyaDataGateway | None = None) -> None:
        self._gateway = gateway or MockBaekyaDataGateway()

    async def process(self, query: str) -> AgentResult:
        region = _extract_region(query)
        status = await self._gateway.fetch_local_supply_status(region)

        alert = _build_alert(status)

        return AgentResult(
            domain=self.domain,
            spirit_score=self.spirit_score,
            data={
                "region": status.get("region"),
                "supply_level": status.get("supply_level"),
                "inventory_days": status.get("inventory_days"),
                "incoming_shipments": status.get("incoming_shipments"),
                "risk_flag": status.get("risk_flag", False),
                "alert": alert,
            },
            source=status.get("source", "BaekyaDataGateway"),
        )


def _build_alert(status: dict) -> str:
    if status.get("risk_flag"):
        days = status.get("inventory_days", 0)
        return f"⚠️ {status.get('region')} 수급 위험 — 재고 {days}일치 남음. 긴급 발주 필요."
    level = status.get("supply_level", "normal")
    days = status.get("inventory_days", 0)
    incoming = status.get("incoming_shipments", 0)
    return f"{status.get('region')} 수급 {level} — 재고 {days}일치, 입고 예정 {incoming}건."
