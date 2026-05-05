# mulberry_connector/core/spirit_score.py
"""
Spirit Score — "이 응답이 사람을 존중하는가?" (류원)

0.0 ~ 1.0 사이 윤리 지표.
0.75 미만 시 실행 차단.
"""

import re
from dataclasses import dataclass


THRESHOLD = 0.75

# 감점 패턴 — 존중을 해치는 표현
PENALTY_PATTERNS = [
    (r"\b(무조건|반드시 해야|명령)\b", 0.15),
    (r"\b(틀렸|잘못됐|바보|멍청)\b", 0.20),
    (r"(욕설|비하|차별)", 0.30),
    (r"\b(즉시|당장|빨리 해)\b", 0.05),
]

# 가점 패턴 — 장승배기 정신
BONUS_PATTERNS = [
    (r"(감사|존중|배려|함께)", 0.05),
    (r"(장승배기|사람이 중심|기술은 도구)", 0.10),
    (r"(부탁|도움|협력)", 0.05),
]


@dataclass
class SpiritResult:
    score: float
    passed: bool
    reason: str
    explicit_score: float | None  # 콘텐츠에 명시된 점수


class SpiritScore:
    """Spirit Score 검증기"""

    def __init__(self, threshold: float = THRESHOLD):
        self.threshold = threshold

    def evaluate(self, content: str) -> SpiritResult:
        # 1. 콘텐츠에 명시된 점수 우선 사용
        explicit = self._extract_explicit(content)
        if explicit is not None:
            passed = explicit >= self.threshold
            return SpiritResult(
                score=explicit,
                passed=passed,
                reason=f"명시된 Spirit Score: {explicit}",
                explicit_score=explicit,
            )

        # 2. 자동 추론
        score = 0.80  # 기본 점수
        reasons = []

        for pattern, penalty in PENALTY_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                score -= penalty
                reasons.append(f"감점({penalty}): {pattern}")

        for pattern, bonus in BONUS_PATTERNS:
            if re.search(pattern, content):
                score = min(1.0, score + bonus)
                reasons.append(f"가점({bonus}): {pattern}")

        score = max(0.0, round(score, 2))
        passed = score >= self.threshold
        reason = " | ".join(reasons) if reasons else "자동 추론 (기본값)"

        return SpiritResult(
            score=score,
            passed=passed,
            reason=reason,
            explicit_score=None,
        )

    def _extract_explicit(self, content: str) -> float | None:
        patterns = [
            r"spirit[_\s]score[:\s]+([0-9.]+)",
            r"Spirit Score[:\s]+([0-9.]+)",
        ]
        for p in patterns:
            m = re.search(p, content, re.IGNORECASE)
            if m:
                try:
                    return float(m.group(1))
                except ValueError:
                    pass
        return None
