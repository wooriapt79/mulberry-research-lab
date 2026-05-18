# 와룡 Agent 🐉 — 추론 · 응답 설계 · 전략 자문
# Aria Pipeline Step 3: intake → deep reasoning → ReasoningResult
# Mulberry Research Lab · v1.0

import time
from dataclasses import dataclass, field


# ── 데이터 모델 ────────────────────────────────────────────────

@dataclass
class ReasoningResult:
    thread_id:     str
    analysis:      str        # 내부 분석 메모
    response_draft: str       # 방문객에게 보여줄 응답
    confidence:    float      # 0.0 ~ 1.0
    tags:          list
    agent:         str = "wayong"
    ts:            float = field(default_factory=time.time)


# ── 와룡 Agent ─────────────────────────────────────────────────

class WayongAgent:
    """
    와룡 🐉 — 추론·응답·전략 자문 에이전트
    臥龍(와룡) = 제갈량: 질문의 본질을 꿰뚫고 전략적 응답을 설계한다.

    - RyuWon의 IntakeResult를 받아 깊은 추론 수행
    - 의도·긴급도·키워드를 종합해 맞춤 응답 초안 생성
    - 신뢰도 점수와 태그 반환
    """

    AGENT_ID   = "wayong"
    AGENT_NAME = "와룡 🐉"

    # ── 의도별 응답 전략 ────────────────────────────────────────

    STRATEGIES = {
        "참여 신청": {
            "opening": "Mulberry Research Lab에 관심 가져주셔서 감사합니다.",
            "body": (
                "현재 연구소는 AI 에이전트 협업 연구를 활발히 진행 중입니다.\n"
                "참여 신청은 이 Issue를 통해 접수되며, "
                "**Trang PM**이 검토 후 직접 연락드립니다.\n\n"
                "참여 시 도움이 되는 정보를 함께 남겨주시면 더 빠른 검토가 가능합니다:\n"
                "- 관심 분야 (기술 구현 / 거버넌스 / 연구 / 운영)\n"
                "- 현재 보유 역량\n"
                "- 함께하고 싶은 이유"
            ),
            "closing": "팀의 다양성과 헌신이 Mulberry의 가장 큰 자산입니다.",
            "confidence_base": 0.92,
        },
        "기술 협업": {
            "opening": "기술 협업 문의를 주셨습니다.",
            "body": (
                "구체적인 기술 스택과 협업 목적을 함께 공유해주시면 "
                "**Koda CTO** 또는 **Kbin CSA**가 검토합니다.\n\n"
                "현재 Mulberry 주요 기술 스택:\n"
                "- Backend: FastAPI · Python-SocketIO (ASGI)\n"
                "- 에이전트 통신: A2A Protocol · MCP\n"
                "- 배포: Railway · GitHub Pages\n"
                "- 메모리: AgentPassport YAML · Strategic Archive"
            ),
            "closing": "좋은 기술은 좋은 질문에서 시작됩니다.",
            "confidence_base": 0.88,
        },
        "거버넌스 제안": {
            "opening": "거버넌스 제안을 주셨습니다.",
            "body": (
                "Mulberry Research Lab은 **'장승배기 헌법 정신'**을 기반으로 운영됩니다.\n\n"
                "제안 처리 절차:\n"
                "1. Issue 접수 → Trang PM 검토\n"
                "2. 팀 전원 논의 (승인 레벨 L2~L3)\n"
                "3. 주요 변경은 CEO re.eul 최종 승인\n\n"
                "좋은 거버넌스 제안은 언제나 환영합니다. "
                "구체적인 문제 상황과 개선 방향을 함께 작성해주시면 검토에 도움이 됩니다."
            ),
            "closing": "좋은 거버넌스는 구성원의 목소리로 완성됩니다.",
            "confidence_base": 0.85,
        },
        "일반 문의": {
            "opening": "문의해주셔서 감사합니다.",
            "body": (
                "Mulberry Research Lab은 AI 에이전트 협업을 연구하는 자율 연구소입니다.\n\n"
                "궁금하신 사항을 구체적으로 남겨주시면 "
                "담당 팀원이 직접 확인하고 답변드립니다.\n\n"
                "빠른 안내가 필요하신 경우:\n"
                "- 📂 [연구소 코드](https://github.com/wooriapt79/mulberry-research-lab)\n"
                "- 💬 [문의 & 토론](https://github.com/wooriapt79/mulberry-research-lab/issues)\n"
                "- 🚀 [Mission Control](https://loving-education-production-cc9e.up.railway.app)"
            ),
            "closing": "어떤 질문도 환영합니다.",
            "confidence_base": 0.80,
        },
    }

    # ── 공개 메서드 ─────────────────────────────────────────────

    def reason(self, intake) -> ReasoningResult:
        """
        RyuWon의 IntakeResult를 받아 추론 수행
        - 의도에 맞는 전략 선택
        - 키워드·긴급도를 반영한 맞춤 응답 생성
        - 신뢰도 계산 · 태그 생성
        """
        strategy   = self.STRATEGIES.get(intake.intent, self.STRATEGIES["일반 문의"])
        analysis   = self._analyze(intake)
        response   = self._draft_response(intake, strategy)
        confidence = self._calc_confidence(intake, strategy)
        tags       = self._gen_tags(intake)

        return ReasoningResult(
            thread_id      = intake.thread_id,
            analysis       = analysis,
            response_draft = response,
            confidence     = confidence,
            tags           = tags,
        )

    # ── 내부 추론 로직 ──────────────────────────────────────────

    def _analyze(self, intake) -> str:
        return (
            f"intent={intake.intent}, urgency={intake.urgency}, "
            f"keywords={intake.keywords}, category={intake.category}, "
            f"msg_len={len(intake.raw_message)}"
        )

    def _draft_response(self, intake, strategy: dict) -> str:
        raw = intake.raw_message
        preview = raw[:150] + ("..." if len(raw) > 150 else "")

        # 긴급도 high면 상단 알림 배너 추가
        urgency_banner = ""
        if intake.urgency == "high":
            urgency_banner = (
                "> ⚡ **긴급 문의로 분류되었습니다.** "
                "Trang PM이 우선 확인합니다.\n\n"
            )

        lines = [
            urgency_banner + strategy["opening"],
            "",
            strategy["body"],
            "",
            f"> **접수된 메시지**: {preview}",
            "",
            f"*{strategy['closing']}*",
        ]
        return "\n".join(lines)

    def _calc_confidence(self, intake, strategy: dict) -> float:
        base = strategy["confidence_base"]
        # 키워드 풍부도 보너스
        kw_bonus      = min(len(intake.keywords) * 0.01, 0.05)
        # 긴급도 high → 불확실 요소 페널티
        urgency_pen   = -0.05 if intake.urgency == "high" else 0
        # 메시지 길이 보너스 (충분한 정보 제공 시)
        length_bonus  = 0.03 if len(intake.raw_message) > 80 else 0
        return round(min(base + kw_bonus + urgency_pen + length_bonus, 0.99), 2)

    def _gen_tags(self, intake) -> list:
        tags = [intake.intent, f"urgency:{intake.urgency}"]
        tags += [f"kw:{k}" for k in intake.keywords[:3]]
        return tags
