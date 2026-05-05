# mulberry_connector/core/handoff.py
"""
Handoff Gate — 인계 준비도 검증 (류원)

코드가 아닌 메시지/콘텐츠 인계 시
다음 에이전트에게 충분한 맥락이 전달되는지 확인.
"""

from dataclasses import dataclass


MIN_LENGTH = 50       # 최소 글자 수
MIN_SECTIONS = 1      # 최소 섹션 수 (## 헤더)


@dataclass
class HandoffResult:
    ready: bool
    score: int
    feedback: list[str]
    note: str


class HandoffGate:
    """콘텐츠 인계 준비도 검증"""

    def check(self, content: str, agent_id: str = "unknown") -> HandoffResult:
        score = 100
        feedback = []

        if len(content.strip()) < MIN_LENGTH:
            score -= 30
            feedback.append(f"콘텐츠가 너무 짧습니다 ({len(content)}자 < {MIN_LENGTH}자)")

        if content.count("##") < MIN_SECTIONS:
            score -= 20
            feedback.append("구조화된 섹션(##)이 없습니다. 다음 에이전트가 파악하기 어렵습니다.")

        if not any(kw in content for kw in ["결론", "요약", "Summary", "Next", "다음"]):
            score -= 10
            feedback.append("다음 단계 또는 결론이 명시되지 않았습니다.")

        score = max(0, score)
        ready = score >= 70

        if not feedback:
            feedback.append("인계 준비 완료 — 다음 에이전트에게 전달합니다.")

        note = (
            f"[{agent_id}] 인계 준비 완료 ({score}/100)"
            if ready
            else f"[{agent_id}] 인계 보류 ({score}/100) — 보완 필요"
        )

        return HandoffResult(score=score, ready=ready, feedback=feedback, note=note)
