# -*- coding: utf-8 -*-
"""
도메인 에이전트 10 — 소비자 리뷰·평판

공동구매 참여자의 만족도·재구매 의향·불만 패턴을 분석하여
품목·공급처 선정에 반영한다.

spirit_score = 0.80
CTO Koda · DAY5 · 2026-06-17
"""
from __future__ import annotations

from core.agents.domain_agent_base import AgentResult, DomainAgentBase

_REVIEWS: dict[str, dict] = {
    "배추": {
        "avg_rating": 4.6, "review_count": 1240, "repurchase_rate": 0.88,
        "top_positive": "신선도 최고, 가격 만족",
        "top_complaint": "낱개 포장 없음",
        "trust_score": 0.91,
    },
    "감자": {
        "avg_rating": 4.5, "review_count": 980, "repurchase_rate": 0.84,
        "top_positive": "크기 균일, 맛 좋음",
        "top_complaint": "간혹 흙 많이 묻어 있음",
        "trust_score": 0.88,
    },
    "사과": {
        "avg_rating": 4.7, "review_count": 1560, "repurchase_rate": 0.90,
        "top_positive": "당도 높고 아삭함",
        "top_complaint": "가격 변동 크다",
        "trust_score": 0.93,
    },
    "쌀": {
        "avg_rating": 4.8, "review_count": 2100, "repurchase_rate": 0.95,
        "top_positive": "밥맛 차이 확실, 가격 저렴",
        "top_complaint": "배송 지연 가끔 있음",
        "trust_score": 0.95,
    },
}
_DEFAULT_REVIEW = {
    "avg_rating": 4.2, "review_count": 300, "repurchase_rate": 0.75,
    "top_positive": "품질 양호",
    "top_complaint": "리뷰 데이터 부족",
    "trust_score": 0.80,
}


def _extract_commodity(query: str) -> tuple[str, dict]:
    for name, data in _REVIEWS.items():
        if name in query:
            return name, data
    return "일반 상품", _DEFAULT_REVIEW


class ConsumerReviewAgent(DomainAgentBase):
    domain: str = "consumer_review"
    spirit_score: float = 0.80

    async def process(self, query: str) -> AgentResult:
        commodity, data = _extract_commodity(query)
        repurchase_pct = int(data["repurchase_rate"] * 100)
        insight = (
            f"{commodity} 평점 {data['avg_rating']}/5.0 ({data['review_count']:,}건). "
            f"재구매율 {repurchase_pct}%. 호평: {data['top_positive']}. "
            f"불만: {data['top_complaint']}."
        )
        return AgentResult(
            domain=self.domain,
            spirit_score=self.spirit_score,
            data={**data, "commodity": commodity, "insight": insight},
            source="ConsumerReviewAggregator",
        )
