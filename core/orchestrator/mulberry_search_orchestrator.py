# -*- coding: utf-8 -*-
"""
Mulberry 멀티에이전트 검색 오케스트레이터

장승배기 정신: 어르신이 신선한 식품에 접근하는 것을 돕기 위해
도메인 전문가 에이전트들을 병렬로 실행하고,
Spirit Gate(spirit_score >= 0.70)를 통과한 결과만 종합한다.

작업 흐름:
  1. 쿼리 분석 → 관련 도메인 에이전트 선택
  2. asyncio.gather로 병렬 실행
  3. Spirit Gate 필터링 (spirit_score >= SPIRIT_FILTER_THRESHOLD)
  4. 결과 종합 → SearchResult 반환

CTO Koda · DAY4 · 2026-06-17
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

from core.agents.domain_agent_base import AgentResult, DomainAgentBase
from core.agents.domain_agents.agricultural_price_agent import AgriculturalPriceAgent
from core.agents.domain_agents.local_supply_agent import LocalSupplyAgent

logger = logging.getLogger(__name__)

SPIRIT_FILTER_THRESHOLD: float = 0.70


@dataclass
class SearchResult:
    """오케스트레이터 최종 검색 결과"""
    query: str
    answer: str
    domain_results: list[AgentResult] = field(default_factory=list)
    filtered_out: list[AgentResult] = field(default_factory=list)
    total_agents: int = 0
    passed_agents: int = 0
    errors: list[str] = field(default_factory=list)


class MulberrySearchOrchestrator:
    """
    멀티에이전트 검색 오케스트레이터

    Usage:
        orchestrator = MulberrySearchOrchestrator()
        result = await orchestrator.search("경기 지역 사과 시세 알려줘")
    """

    def __init__(
        self,
        agents: list[DomainAgentBase] | None = None,
        spirit_threshold: float = SPIRIT_FILTER_THRESHOLD,
    ) -> None:
        self._agents: list[DomainAgentBase] = _default_agents() if agents is None else agents
        self._spirit_threshold = spirit_threshold

    async def search(self, query: str) -> SearchResult:
        """
        쿼리를 처리하고 SearchResult를 반환한다.

        1. 관련 에이전트 선택
        2. 병렬 실행 (safe_process — 개별 에러가 전체를 막지 않음)
        3. Spirit Gate 필터링
        4. 결과 종합
        """
        selected = self._select_agents(query)
        if not selected:
            return SearchResult(
                query=query,
                answer="관련 도메인 에이전트를 찾을 수 없습니다.",
                total_agents=0,
            )

        raw_results: list[AgentResult] = await asyncio.gather(
            *[agent.safe_process(query) for agent in selected]
        )

        passed, filtered_out, errors = self._apply_spirit_gate(raw_results)

        answer = self._aggregate(query, passed)

        return SearchResult(
            query=query,
            answer=answer,
            domain_results=passed,
            filtered_out=filtered_out,
            total_agents=len(selected),
            passed_agents=len(passed),
            errors=errors,
        )

    # ------------------------------------------------------------------
    # 내부 메서드
    # ------------------------------------------------------------------

    def _select_agents(self, query: str) -> list[DomainAgentBase]:
        """쿼리와 관련된 에이전트를 선택한다. 현재는 전체 에이전트 반환."""
        return list(self._agents)

    def _apply_spirit_gate(
        self, results: list[AgentResult]
    ) -> tuple[list[AgentResult], list[AgentResult], list[str]]:
        """spirit_score 기준 필터링 + 에러 분리."""
        passed: list[AgentResult] = []
        filtered_out: list[AgentResult] = []
        errors: list[str] = []

        for r in results:
            if r.error:
                errors.append(f"[{r.domain}] {r.error}")
                logger.warning("Agent error domain=%s error=%s", r.domain, r.error)
                continue
            if r.spirit_score >= self._spirit_threshold:
                passed.append(r)
            else:
                filtered_out.append(r)
                logger.info(
                    "Spirit Gate filtered domain=%s score=%.2f threshold=%.2f",
                    r.domain,
                    r.spirit_score,
                    self._spirit_threshold,
                )

        return passed, filtered_out, errors

    def _aggregate(self, query: str, results: list[AgentResult]) -> str:
        """통과된 에이전트 결과를 종합하여 최종 답변을 생성한다."""
        if not results:
            return "Spirit Gate를 통과한 결과가 없습니다. 다른 쿼리를 시도해 주세요."

        lines: list[str] = [f"'{query}'에 대한 Mulberry 검색 결과:\n"]
        for r in results:
            lines.append(f"[{r.domain}]")
            for key, val in r.data.items():
                if isinstance(val, dict):
                    for k, v in val.items():
                        lines.append(f"  {k}: {v}")
                else:
                    lines.append(f"  {key}: {val}")
            lines.append("")

        return "\n".join(lines).strip()


def _default_agents() -> list[DomainAgentBase]:
    """기본 도메인 에이전트 목록 (DAY4 기준: 2개)."""
    return [
        AgriculturalPriceAgent(),
        LocalSupplyAgent(),
    ]
