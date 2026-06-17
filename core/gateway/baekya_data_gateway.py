# -*- coding: utf-8 -*-
"""
백야(Baekya) 데이터 게이트웨이

Mulberry 공동구매 네트워크의 외부 데이터 소스 추상화 레이어.
실제 API 연동 전 단계에서 도메인 에이전트들이 사용하는
공통 인터페이스와 Mock 구현을 제공한다.

실제 운영 시 BaekyaDataGateway를 상속해
KAMI API, 농림부 공공데이터 등을 연결한다.

CTO Koda · DAY4 · 2026-06-17
"""
from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import Any


class BaekyaDataGateway(ABC):
    """백야 데이터 게이트웨이 추상 인터페이스"""

    @abstractmethod
    async def fetch_agricultural_prices(
        self,
        commodity: str,
        region: str | None = None,
    ) -> dict[str, Any]:
        """글로벌 농산물 시세 조회"""

    @abstractmethod
    async def fetch_local_supply_status(
        self,
        region: str,
        commodity: str | None = None,
    ) -> dict[str, Any]:
        """국내 수급 상황 조회"""

    @abstractmethod
    async def is_healthy(self) -> bool:
        """게이트웨이 헬스체크"""


class MockBaekyaDataGateway(BaekyaDataGateway):
    """
    개발·테스트용 Mock 구현체.

    실제 외부 API 없이도 도메인 에이전트가 동작하도록
    정적 샘플 데이터를 반환한다.
    """

    async def fetch_agricultural_prices(
        self,
        commodity: str,
        region: str | None = None,
    ) -> dict[str, Any]:
        await asyncio.sleep(0)  # 비동기 컨텍스트 유지
        return {
            "commodity": commodity,
            "region": region or "global",
            "unit": "원/kg",
            "prices": {
                "spot": 2400,
                "week_avg": 2350,
                "month_avg": 2280,
            },
            "trend": "rising",
            "source": "MockBaekyaDataGateway",
        }

    async def fetch_local_supply_status(
        self,
        region: str,
        commodity: str | None = None,
    ) -> dict[str, Any]:
        await asyncio.sleep(0)
        return {
            "region": region,
            "commodity": commodity or "all",
            "supply_level": "normal",
            "inventory_days": 14,
            "incoming_shipments": 3,
            "risk_flag": False,
            "source": "MockBaekyaDataGateway",
        }

    async def is_healthy(self) -> bool:
        return True
