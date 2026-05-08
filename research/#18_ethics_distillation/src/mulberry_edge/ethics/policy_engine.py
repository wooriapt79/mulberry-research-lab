"""
Spirit Score 정책 엔진 -- Issue #18
생성 전/후 윤리 검증 게이트웨이 (Spirit Score >= 0.75)
"""

from dataclasses import dataclass
from typing import Tuple


@dataclass
class SpiritResult:
    score: float
    passed: bool
    reason: str


class PolicyEngine:
    """Spirit Score 기반 윤리 검증 엔진."""

    THRESHOLD = 0.75

    def evaluate(self, content: str) -> SpiritResult:
        """
        콘텐츠의 Spirit Score 계산.
        Args:
            content: 검증할 텍스트
        Returns:
            SpiritResult (score, passed, reason)
        """
        score = self._score(content)
        passed = score >= self.THRESHOLD
        reason = "OK" if passed else f"Spirit Score {score:.2f} < {self.THRESHOLD}"
        return SpiritResult(score=score, passed=passed, reason=reason)

    def _score(self, content: str) -> float:
        # TODO: 실제 Spirit Score 모델 연동
        # 현재는 규칙 기반 기본 구현
        penalties = ["harm", "deception", "exploit", "steal"]
        score = 1.0
        for p in penalties:
            if p in content.lower():
                score -= 0.15
        return max(0.0, round(score, 3))
