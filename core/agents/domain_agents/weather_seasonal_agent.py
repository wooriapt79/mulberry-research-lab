# -*- coding: utf-8 -*-
"""
도메인 에이전트 08 — 계절·날씨 데이터

현재 계절 및 기상 조건이 농산물 품질·보관·수요에
미치는 영향을 분석한다.

spirit_score = 0.88
CTO Koda · DAY5 · 2026-06-17
"""
from __future__ import annotations

import datetime

from core.agents.domain_agent_base import AgentResult, DomainAgentBase

_SEASON_MAP = {
    (3, 4, 5): ("spring", "봄", "서늘하고 건조. 엽채류 품질 우수."),
    (6, 7, 8): ("summer", "여름", "고온다습. 냉장 보관 필수. 배송 속도 중요."),
    (9, 10, 11): ("autumn", "가을", "수확 최성기. 대부분 품목 최적 품질."),
    (12, 1, 2): ("winter", "겨울", "냉해 위험. 뿌리채소·저장 작물 적합."),
}

_STORAGE_RISK: dict[str, dict] = {
    "summer": {"배추": "HIGH", "감자": "MED", "쌀": "LOW", "사과": "HIGH"},
    "winter": {"배추": "LOW",  "감자": "LOW", "쌀": "LOW", "사과": "LOW"},
    "spring": {"배추": "LOW",  "감자": "MED", "쌀": "LOW", "사과": "MED"},
    "autumn": {"배추": "LOW",  "감자": "LOW", "쌀": "LOW", "사과": "LOW"},
}


def _get_season(month: int) -> tuple[str, str, str]:
    for months, info in _SEASON_MAP.items():
        if month in months:
            return info
    return ("autumn", "가을", "수확 최성기.")


def _extract_commodity(query: str) -> str:
    for c in ["배추", "감자", "쌀", "사과", "고구마"]:
        if c in query:
            return c
    return "배추"


class WeatherSeasonalAgent(DomainAgentBase):
    domain: str = "weather_seasonal"
    spirit_score: float = 0.88

    async def process(self, query: str) -> AgentResult:
        month = datetime.date.today().month
        season_en, season_kr, season_desc = _get_season(month)
        commodity = _extract_commodity(query)
        risk = _STORAGE_RISK.get(season_en, {}).get(commodity, "MED")
        risk_kr = {"HIGH": "높음 — 냉장 필수", "MED": "보통", "LOW": "낮음"}.get(risk, "보통")

        insight = f"{season_kr} ({month}월): {season_desc} {commodity} 보관 위험도: {risk_kr}."
        return AgentResult(
            domain=self.domain,
            spirit_score=self.spirit_score,
            data={
                "month": month, "season": season_kr,
                "season_description": season_desc,
                "commodity": commodity,
                "storage_risk": risk_kr,
                "insight": insight,
            },
            source="WeatherSeasonalDB",
        )
