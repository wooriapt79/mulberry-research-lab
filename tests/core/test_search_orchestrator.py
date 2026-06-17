# -*- coding: utf-8 -*-
"""
tests/core/test_search_orchestrator.py

MulberrySearchOrchestrator + 도메인 에이전트 테스트 (pytest-asyncio)

테스트 항목:
  1. 정상 검색: 두 에이전트 모두 결과 반환
  2. Spirit Gate 필터: 낮은 spirit_score 에이전트 제외
  3. 에이전트 에러 처리: 한 에이전트가 예외를 던져도 나머지 정상
  4. 빈 에이전트 목록
  5. AgriculturalPriceAgent 개별 동작
  6. LocalSupplyAgent 개별 동작 + 지역 추출
  7. MockBaekyaDataGateway 헬스체크
"""
from __future__ import annotations

import asyncio
import pytest

from core.agents.domain_agent_base import AgentResult, DomainAgentBase
from core.agents.domain_agents.agricultural_price_agent import AgriculturalPriceAgent
from core.agents.domain_agents.local_supply_agent import LocalSupplyAgent
from core.gateway.baekya_data_gateway import MockBaekyaDataGateway
from core.orchestrator.mulberry_search_orchestrator import (
    SPIRIT_FILTER_THRESHOLD,
    MulberrySearchOrchestrator,
    SearchResult,
)


# --------------------------------------------------------------------------
# 헬퍼
# --------------------------------------------------------------------------

class _AlwaysPassAgent(DomainAgentBase):
    domain = "always_pass"
    spirit_score = 0.95

    async def process(self, query: str) -> AgentResult:
        return AgentResult(domain=self.domain, spirit_score=self.spirit_score, data={"ok": True})


class _LowSpiritAgent(DomainAgentBase):
    domain = "low_spirit"
    spirit_score = 0.50  # < 0.70 → Spirit Gate에서 걸림

    async def process(self, query: str) -> AgentResult:
        return AgentResult(domain=self.domain, spirit_score=self.spirit_score, data={"ok": True})


class _ErrorAgent(DomainAgentBase):
    domain = "error_agent"
    spirit_score = 0.99

    async def process(self, query: str) -> AgentResult:
        raise RuntimeError("의도적 에러 — 테스트용")


# --------------------------------------------------------------------------
# 테스트
# --------------------------------------------------------------------------

@pytest.mark.anyio
async def test_normal_search_returns_two_results():
    orch = MulberrySearchOrchestrator(agents=[_AlwaysPassAgent(), _AlwaysPassAgent()])
    result = await orch.search("사과 시세")
    assert isinstance(result, SearchResult)
    assert result.passed_agents == 2
    assert result.total_agents == 2
    assert result.errors == []


@pytest.mark.anyio
async def test_spirit_gate_filters_low_score():
    orch = MulberrySearchOrchestrator(agents=[_AlwaysPassAgent(), _LowSpiritAgent()])
    result = await orch.search("쌀 수급")
    assert result.passed_agents == 1
    assert len(result.filtered_out) == 1
    assert result.filtered_out[0].domain == "low_spirit"


@pytest.mark.anyio
async def test_error_agent_does_not_crash_orchestrator():
    orch = MulberrySearchOrchestrator(agents=[_AlwaysPassAgent(), _ErrorAgent()])
    result = await orch.search("배추 시세")
    assert result.passed_agents == 1
    assert len(result.errors) == 1
    assert "error_agent" in result.errors[0]


@pytest.mark.anyio
async def test_empty_agent_list_returns_graceful_message():
    orch = MulberrySearchOrchestrator(agents=[])
    result = await orch.search("아무 쿼리")
    assert result.passed_agents == 0
    assert "에이전트" in result.answer


@pytest.mark.anyio
async def test_agricultural_price_agent_returns_valid_result():
    agent = AgriculturalPriceAgent(gateway=MockBaekyaDataGateway())
    result = await agent.safe_process("사과 시세 알려줘")
    assert result.ok
    assert result.domain == "agricultural_price"
    assert result.spirit_score >= SPIRIT_FILTER_THRESHOLD
    assert "prices" in result.data
    assert "insight" in result.data


@pytest.mark.anyio
async def test_local_supply_agent_extracts_region():
    agent = LocalSupplyAgent(gateway=MockBaekyaDataGateway())
    result = await agent.safe_process("경기 지역 배추 수급 상황")
    assert result.ok
    assert result.domain == "local_supply"
    assert result.data.get("region") == "경기"


@pytest.mark.anyio
async def test_mock_gateway_is_healthy():
    gw = MockBaekyaDataGateway()
    assert await gw.is_healthy()


@pytest.mark.anyio
async def test_default_orchestrator_search_end_to_end():
    """기본 에이전트 2개 포함 실 경로 통합 테스트."""
    orch = MulberrySearchOrchestrator()
    result = await orch.search("부산 지역 감자 시세와 수급 현황")
    assert result.total_agents == 2
    assert result.passed_agents == 2
    assert len(result.answer) > 0
