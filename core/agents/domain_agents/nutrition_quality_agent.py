# -*- coding: utf-8 -*-
"""
도메인 에이전트 09 — 영양·품질 분석

공동구매 품목의 영양소·품질 등급·원산지 신뢰도를 분석.
어르신 건강 관점에서 최적 품목 선정을 돕는다.

spirit_score = 0.91 (어르신 건강·안전, 매슬로우 1~2단계 직접 기여)
CTO Koda · DAY5 · 2026-06-17
"""
from __future__ import annotations

from core.agents.domain_agent_base import AgentResult, DomainAgentBase

_NUTRITION: dict[str, dict] = {
    "배추": {
        "grade": "A", "vitamin_c_mg": 45, "fiber_g": 1.2, "calories_kcal": 15,
        "health_benefit": "면역력 강화, 소화 촉진",
        "elderly_fit": "매우 적합 — 저칼로리·고섬유",
    },
    "감자": {
        "grade": "A", "vitamin_c_mg": 20, "fiber_g": 2.1, "calories_kcal": 77,
        "health_benefit": "칼륨 풍부, 혈압 조절",
        "elderly_fit": "적합 — 포만감·에너지 공급",
    },
    "사과": {
        "grade": "A+", "vitamin_c_mg": 5, "fiber_g": 2.4, "calories_kcal": 52,
        "health_benefit": "폴리페놀 항산화, 장 건강",
        "elderly_fit": "매우 적합 — 간편 섭취·소화 용이",
    },
    "쌀": {
        "grade": "A", "vitamin_c_mg": 0, "fiber_g": 0.4, "calories_kcal": 130,
        "health_benefit": "주요 에너지원, 소화 부담 적음",
        "elderly_fit": "필수 — 주식 안정 공급",
    },
    "고구마": {
        "grade": "A+", "vitamin_c_mg": 25, "fiber_g": 3.0, "calories_kcal": 86,
        "health_benefit": "베타카로틴·식이섬유 풍부, 변비 예방",
        "elderly_fit": "매우 적합 — 달고 부드러워 섭취 편의",
    },
}
_DEFAULT_NUTRITION = {
    "grade": "B", "vitamin_c_mg": 10, "fiber_g": 1.0, "calories_kcal": 60,
    "health_benefit": "일반적 영양 공급",
    "elderly_fit": "적합",
}


def _extract_commodity(query: str) -> tuple[str, dict]:
    for name, data in _NUTRITION.items():
        if name in query:
            return name, data
    return "일반 상품", _DEFAULT_NUTRITION


class NutritionQualityAgent(DomainAgentBase):
    domain: str = "nutrition_quality"
    spirit_score: float = 0.91

    async def process(self, query: str) -> AgentResult:
        commodity, data = _extract_commodity(query)
        insight = (
            f"{commodity} 품질등급 {data['grade']}: {data['health_benefit']}. "
            f"어르신 적합도: {data['elderly_fit']}."
        )
        return AgentResult(
            domain=self.domain,
            spirit_score=self.spirit_score,
            data={**data, "commodity": commodity, "insight": insight},
            source="NutritionResearchDB",
        )
