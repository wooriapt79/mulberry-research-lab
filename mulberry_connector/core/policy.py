# mulberry_connector/core/policy.py
"""
Policy Engine — Decision Codes (CSA Kbin 설계)

Ethics(Spirit Score) + Execution(Hesitation) 두 레이어를 분리하여
최종 실행 결정을 내린다.

Decision Codes:
  EXECUTE      - 즉시 실행
  CONFIRM      - 사용자 확인 후 실행
  HUMAN_REVIEW - 사람 검토 필수
  BLOCK        - 실행 차단
"""

from dataclasses import dataclass
from enum import Enum

from .spirit_score import SpiritScore, SpiritResult
from .hesitation import HesitationEngine, HesitationResult, HesitationLevel


class Decision(Enum):
    EXECUTE      = "EXECUTE"
    CONFIRM      = "CONFIRM"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    BLOCK        = "BLOCK"


@dataclass
class PolicyResult:
    decision: Decision
    spirit: SpiritResult
    hesitation: HesitationResult
    reason: str
    safe_to_proceed: bool


class PolicyEngine:
    """
    통합 정책 엔진 — 모든 에이전트 공용.
    Spirit Score(윤리) + Hesitation(불확실성) -> Decision Code
    """

    def __init__(
        self,
        spirit_threshold: float = 0.75,
        hesitation_threshold: float = 0.30,
    ):
        self.spirit = SpiritScore(threshold=spirit_threshold)
        self.hesitation = HesitationEngine(threshold=hesitation_threshold)

    def evaluate(self, content: str, intent: str = "", bypass: bool = False) -> PolicyResult:
        spirit_result = self.spirit.evaluate(content)
        hesitation_result = self.hesitation.evaluate(content, intent)

        # 1. Spirit 실패 -> 즉시 BLOCK
        if not spirit_result.passed and not bypass:
            return PolicyResult(
                decision=Decision.BLOCK,
                spirit=spirit_result,
                hesitation=hesitation_result,
                reason=f"Spirit Score {spirit_result.score} < {self.spirit.threshold} — 실행 차단",
                safe_to_proceed=False,
            )

        # 2. 높은 불확실성 -> HUMAN_REVIEW
        if hesitation_result.level == HesitationLevel.REVIEW:
            return PolicyResult(
                decision=Decision.HUMAN_REVIEW,
                spirit=spirit_result,
                hesitation=hesitation_result,
                reason=f"불확실성 {hesitation_result.uncertainty} — 사람 검토 필요",
                safe_to_proceed=False,
            )

        # 3. 중간 불확실성 -> CONFIRM
        if hesitation_result.level == HesitationLevel.PAUSE:
            return PolicyResult(
                decision=Decision.CONFIRM,
                spirit=spirit_result,
                hesitation=hesitation_result,
                reason=f"불확실성 {hesitation_result.uncertainty} — 확인 후 실행",
                safe_to_proceed=False,
            )

        # 4. 통과 -> EXECUTE
        return PolicyResult(
            decision=Decision.EXECUTE,
            spirit=spirit_result,
            hesitation=hesitation_result,
            reason="Spirit + Hesitation 검증 통과",
            safe_to_proceed=True,
        )
