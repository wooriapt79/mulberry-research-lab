# -*- coding: utf-8 -*-
"""
tests/core/test_domain_agents_day5.py

DAY5 도메인 에이전트 03~10 유닛 테스트 +
10개 에이전트 통합 병렬 테스트 (pytest-anyio)
"""
from __future__ import annotations

import pytest

from core.agents.domain_agents.regional_characteristic_agent import RegionalCharacteristicAgent
from core.agents.domain_agents.elderly_consumer_agent import ElderlyConsumerAgent
from core.agents.domain_agents.group_buy_timing_agent import GroupBuyTimingAgent
from core.agents.domain_agents.competitor_alternative_agent import CompetitorAlternativeAgent
from core.agents.domain_agents.logistics_delivery_agent import LogisticsDeliveryAgent
from core.agents.domain_agents.weather_seasonal_agent import WeatherSeasonalAgent
from core.agents.domain_agents.nutrition_quality_agent import NutritionQualityAgent
from core.agents.domain_agents.consumer_review_agent import ConsumerReviewAgent
from core.orchestrator.mulberry_search_orchestrator import (
    MulberrySearchOrchestrator,
    SPIRIT_FILTER_THRESHOLD,
)

INJE_QUERY = "인제군 어르신 배추 공동구매 최적 시기는?"


# --------------------------------------------------------------------------
# 에이전트 03: 지역 특성
# --------------------------------------------------------------------------

@pytest.mark.anyio
async def test_regional_characteristic_inje():
    agent = RegionalCharacteristicAgent()
    result = await agent.safe_process(INJE_QUERY)
    assert result.ok
    assert result.domain == "regional_characteristic"
    assert result.spirit_score >= SPIRIT_FILTER_THRESHOLD
    assert result.data["region"] == "인제"
    assert "insight" in result.data


# --------------------------------------------------------------------------
# 에이전트 04: 어르신 소비 패턴
# --------------------------------------------------------------------------

@pytest.mark.anyio
async def test_elderly_consumer_cabbage():
    agent = ElderlyConsumerAgent()
    result = await agent.safe_process("배추 공동구매")
    assert result.ok
    assert result.domain == "elderly_consumer"
    assert result.spirit_score >= SPIRIT_FILTER_THRESHOLD
    assert result.data["commodity"] == "배추"
    assert result.data["group_buy_fit"] in ["높음", "매우 높음"]


# --------------------------------------------------------------------------
# 에이전트 05: 공동구매 타이밍
# --------------------------------------------------------------------------

@pytest.mark.anyio
async def test_group_buy_timing_returns_recommendation():
    agent = GroupBuyTimingAgent()
    result = await agent.safe_process("배추 공동구매 언제가 좋아요")
    assert result.ok
    assert result.domain == "group_buy_timing"
    assert result.spirit_score >= SPIRIT_FILTER_THRESHOLD
    assert "recommendation" in result.data
    assert result.data["best_month"] in range(1, 13)


# --------------------------------------------------------------------------
# 에이전트 06: 경쟁 플랫폼
# --------------------------------------------------------------------------

@pytest.mark.anyio
async def test_competitor_alternative_price_lower():
    agent = CompetitorAlternativeAgent()
    result = await agent.safe_process("배추 가격 비교")
    assert result.ok
    assert result.domain == "competitor_alternative"
    assert result.data["mulberry_est"] < result.data["coupang_price"]


# --------------------------------------------------------------------------
# 에이전트 07: 물류·배송
# --------------------------------------------------------------------------

@pytest.mark.anyio
async def test_logistics_delivery_inje():
    agent = LogisticsDeliveryAgent()
    result = await agent.safe_process("인제 배송 조건")
    assert result.ok
    assert result.domain == "logistics_delivery"
    assert result.data["region"] == "인제"
    assert result.data["delivery_days"] > 0


# --------------------------------------------------------------------------
# 에이전트 08: 계절·날씨
# --------------------------------------------------------------------------

@pytest.mark.anyio
async def test_weather_seasonal_returns_season():
    agent = WeatherSeasonalAgent()
    result = await agent.safe_process("배추 지금 사도 돼요?")
    assert result.ok
    assert result.domain == "weather_seasonal"
    assert result.spirit_score >= SPIRIT_FILTER_THRESHOLD
    assert result.data["season"] in ["봄", "여름", "가을", "겨울"]
    assert "storage_risk" in result.data


# --------------------------------------------------------------------------
# 에이전트 09: 영양·품질
# --------------------------------------------------------------------------

@pytest.mark.anyio
async def test_nutrition_quality_cabbage_grade():
    agent = NutritionQualityAgent()
    result = await agent.safe_process("배추 영양 정보")
    assert result.ok
    assert result.domain == "nutrition_quality"
    assert result.spirit_score >= SPIRIT_FILTER_THRESHOLD
    assert result.data["grade"] in ["A", "A+", "B"]
    assert "elderly_fit" in result.data


# --------------------------------------------------------------------------
# 에이전트 10: 소비자 리뷰
# --------------------------------------------------------------------------

@pytest.mark.anyio
async def test_consumer_review_rating_range():
    agent = ConsumerReviewAgent()
    result = await agent.safe_process("배추 리뷰")
    assert result.ok
    assert result.domain == "consumer_review"
    assert 1.0 <= result.data["avg_rating"] <= 5.0
    assert result.data["review_count"] > 0


# --------------------------------------------------------------------------
# 10개 통합 테스트 — 인제군 데모 쿼리
# --------------------------------------------------------------------------

@pytest.mark.anyio
async def test_full_10_agents_parallel_inje_demo():
    """인제군청 미팅 데모 쿼리: 10개 에이전트 병렬 실행."""
    orch = MulberrySearchOrchestrator()
    result = await orch.search(INJE_QUERY)

    assert result.total_agents == 10
    assert result.passed_agents == 10, (
        f"Spirit Gate 필터링 예상치 못한 제외: {[r.domain for r in result.filtered_out]}"
    )
    assert result.errors == [], f"에이전트 에러 발생: {result.errors}"
    assert len(result.answer) > 100
    # 핵심 도메인 모두 포함 확인
    domains = {r.domain for r in result.domain_results}
    assert "agricultural_price" in domains
    assert "elderly_consumer" in domains
    assert "group_buy_timing" in domains
    assert "nutrition_quality" in domains


@pytest.mark.anyio
async def test_all_agents_spirit_score_above_threshold():
    """모든 에이전트의 spirit_score가 SPIRIT_FILTER_THRESHOLD(0.70) 이상."""
    orch = MulberrySearchOrchestrator()
    result = await orch.search("배추")
    for r in result.domain_results:
        assert r.spirit_score >= SPIRIT_FILTER_THRESHOLD, (
            f"{r.domain}: spirit_score={r.spirit_score} < {SPIRIT_FILTER_THRESHOLD}"
        )
