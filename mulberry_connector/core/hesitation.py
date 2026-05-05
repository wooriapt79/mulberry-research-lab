# mulberry_connector/core/hesitation.py
"""
Hesitation Engine — Scruple-Time (류원 + 장승배기 원칙 1)

"멈춤이 지혜다" — 불확실성 >= 0.3 시 숙고 모드 자동 진입.
망설임은 나약함이 아니라 윤리적 숙고다.
"""

import re
from dataclasses import dataclass
from enum import Enum


class HesitationLevel(Enum):
    CLEAR = "clear"          # 확신 — 바로 실행
    PAUSE = "pause"          # 잠깐 확인 권장
    REVIEW = "review"        # 사람 검토 필요


@dataclass
class HesitationResult:
    level: HesitationLevel
    uncertainty: float       # 0.0 ~ 1.0
    triggers: list[str]
    message: str


# 불확실성 트리거 키워드
UNCERTAINTY_SIGNALS = [
    (r"\b(아마|아마도|혹시|모르겠|불확실|확실하지)\b", 0.20),
    (r"\b(실험적|테스트|미검증|초안|draft)\b", 0.15),
    (r"\b(삭제|제거|초기화|reset|drop)\b", 0.25),
    (r"\b(전체|모든|all|전부)\b", 0.10),
    (r"\b(배포|deploy|production|운영)\b", 0.15),
]


class HesitationEngine:
    """Scruple-Time 엔진 — 불확실성 감지 및 숙고 모드 진입"""

    def __init__(self, threshold: float = 0.30):
        self.threshold = threshold

    def evaluate(self, content: str, intent: str = "") -> HesitationResult:
        uncertainty = 0.0
        triggers = []

        text = f"{content} {intent}".lower()

        for pattern, weight in UNCERTAINTY_SIGNALS:
            if re.search(pattern, text, re.IGNORECASE):
                uncertainty = min(1.0, uncertainty + weight)
                triggers.append(pattern)

        uncertainty = round(uncertainty, 2)

        if uncertainty >= 0.5:
            level = HesitationLevel.REVIEW
            message = "불확실성이 높습니다. 사람의 검토가 필요합니다."
        elif uncertainty >= self.threshold:
            level = HesitationLevel.PAUSE
            message = "잠깐 — 이 작업을 실행해도 괜찮은지 확인해 주세요."
        else:
            level = HesitationLevel.CLEAR
            message = "실행 준비 완료."

        return HesitationResult(
            level=level,
            uncertainty=uncertainty,
            triggers=triggers,
            message=message,
        )
