# RyuWon Agent 🌊 — 수신 · 증류 · 흐름
# Aria Pipeline Step 1 & 4: intake → classify → finalize
# Mulberry Research Lab · v1.0

import re
import time
from dataclasses import dataclass, field


# ── 데이터 모델 ────────────────────────────────────────────────

@dataclass
class IntakeResult:
    thread_id: str
    category: str       # Aria Portal 선택 카테고리
    intent: str         # 분류된 의도
    keywords: list      # 추출 키워드
    urgency: str        # low / medium / high
    route_to: str       # wayong / trang / direct
    raw_message: str
    ts: float = field(default_factory=time.time)


@dataclass
class FinalResponse:
    thread_id: str
    comment_body: str   # GitHub Issue 댓글 본문
    issue_label: str    # GitHub 라벨
    log_entry: dict


# ── RyuWon Agent ───────────────────────────────────────────────

class RyuWonAgent:
    """
    RyuWon 🌊 — 수신·증류·흐름 에이전트
    - Aria Portal 메시지를 받아 분류·정제
    - 와룡에게 A2A로 전달할 IntakeResult 생성
    - 와룡의 추론 결과를 받아 최종 응답 포맷
    """

    AGENT_ID   = "ryuwon"
    AGENT_NAME = "RyuWon 🌊"

    # 의도 분류 키워드 맵
    INTENT_MAP = {
        "참여 신청":   ["참여", "합류", "지원", "신청", "함께", "팀", "join", "apply"],
        "기술 협업":   ["API", "api", "코드", "구현", "기술", "개발", "서버",
                        "에러", "버그", "error", "bug", "deploy", "배포"],
        "거버넌스 제안": ["거버넌스", "정책", "규칙", "제안", "헌법", "원칙",
                          "governance", "policy"],
        "일반 문의":   [],  # fallback
    }

    # 긴급도 키워드 맵
    URGENCY_MAP = {
        "high":   ["긴급", "urgent", "critical", "장애", "에러", "error",
                   "즉시", "emergency", "down", "중단"],
        "medium": ["질문", "문의", "확인", "알고싶", "궁금", "어떻게"],
    }

    # 라벨 맵
    LABEL_MAP = {
        "참여 신청":    "aria-join",
        "기술 협업":    "aria-tech",
        "거버넌스 제안": "aria-governance",
        "일반 문의":    "aria-guide",
    }

    # ── 공개 메서드 ─────────────────────────────────────────────

    def intake(self, message: str, category: str, thread_id: str) -> IntakeResult:
        """Step 1: 메시지 수신·분류·증류"""
        keywords = self._extract_keywords(message)
        intent   = self._classify_intent(message, category)
        urgency  = self._assess_urgency(message)
        route_to = self._decide_route(urgency)

        return IntakeResult(
            thread_id   = thread_id,
            category    = category,
            intent      = intent,
            keywords    = keywords,
            urgency     = urgency,
            route_to    = route_to,
            raw_message = message,
        )

    def finalize(self, reasoning, intake: IntakeResult) -> FinalResponse:
        """Step 4: 와룡 추론 결과 → GitHub 댓글 포맷"""
        comment = self._format_comment(reasoning, intake)
        label   = self.LABEL_MAP.get(intake.intent, "aria-guide")
        log     = {
            "thread_id":  intake.thread_id,
            "agent":      self.AGENT_ID,
            "action":     "finalize",
            "intent":     intake.intent,
            "urgency":    intake.urgency,
            "confidence": reasoning.confidence,
            "ts":         time.time(),
        }
        return FinalResponse(
            thread_id    = intake.thread_id,
            comment_body = comment,
            issue_label  = label,
            log_entry    = log,
        )

    # ── 내부 분류 로직 ──────────────────────────────────────────

    def _extract_keywords(self, message: str) -> list:
        stopwords = {
            "을", "를", "이", "가", "은", "는", "에", "의",
            "와", "과", "하고", "그리고", "하지만", "그런데",
            "합니다", "입니다", "있습니다", "없습니다",
        }
        words = re.findall(r'[가-힣A-Za-z0-9]+', message)
        return [w for w in words if len(w) >= 2 and w not in stopwords][:8]

    def _classify_intent(self, message: str, category: str) -> str:
        for intent, kws in self.INTENT_MAP.items():
            if any(k in message for k in kws):
                return intent
        # 카테고리 버튼 선택값을 fallback으로
        return category if category in self.INTENT_MAP else "일반 문의"

    def _assess_urgency(self, message: str) -> str:
        msg_lower = message.lower()
        for level, kws in self.URGENCY_MAP.items():
            if any(k in msg_lower for k in kws):
                return level
        return "low"

    def _decide_route(self, urgency: str) -> str:
        if urgency == "high":
            return "trang"   # 긴급 → Trang PM 직행
        return "wayong"      # 기본 → 와룡 추론

    # ── 응답 포맷 ───────────────────────────────────────────────

    def _format_comment(self, reasoning, intake: IntakeResult) -> str:
        kw_str = ", ".join(f"`{k}`" for k in intake.keywords[:5]) or "—"
        lines = [
            "## 🌊 RyuWon · 흐름 처리 리포트",
            "",
            f"| 항목 | 값 |",
            f"|------|-----|",
            f"| 카테고리 | {intake.category} |",
            f"| 분류 의도 | {intake.intent} |",
            f"| 긴급도 | {intake.urgency} |",
            f"| 키워드 | {kw_str} |",
            f"| 스레드 | `{intake.thread_id}` |",
            "",
            "---",
            "",
            "## 🐉 와룡 · 추론 응답",
            "",
            reasoning.response_draft,
            "",
            "---",
            "",
            f"*신뢰도: **{reasoning.confidence:.0%}** | "
            f"태그: {', '.join(f'`{t}`' for t in reasoning.tags[:4])}*",
            f"*Mulberry Research Lab · Aria Pipeline v1.0 · "
            f"[RyuWon 🌊 → 와룡 🐉]*",
        ]
        return "\n".join(lines)
