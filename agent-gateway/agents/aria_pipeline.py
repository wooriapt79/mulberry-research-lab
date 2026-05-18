# Aria Pipeline 🌊🐉 — RyuWon × 와룡 협력 파이프라인
# Aria Portal 방문객 메시지 처리 오케스트레이터
# Mulberry Research Lab · v1.1  (Graceful Degradation 추가)

import asyncio
import uuid
import time
import json
from pathlib import Path

from agents.ryuwon_agent import RyuWonAgent, IntakeResult
from agents.wayong_agent import WayongAgent, ReasoningResult

LOG_PATH      = Path("outputs/aria_pipeline_log.jsonl")
WAYONG_TIMEOUT = 6.0   # 와룡 추론 최대 대기 시간 (초)


class AriaPipeline:
    """
    RyuWon 🌊 × 와룡 🐉 협력 파이프라인 v1.1

    처리 순서:
      [1] RyuWon  — 수신·분류·증류 (IntakeResult)
      [2] A2A     — ryuwon → wayong 내부 이벤트 기록
      [3] 와룡    — 추론·응답 설계 (timeout 6s, 실패 시 Degraded 모드)
      [4] RyuWon  — 최종 포맷·라우팅 (FinalResponse)

    Graceful Degradation:
      와룡 응답 불가 → RyuWon 단독 응답 + 방문객 안내 메시지
    """

    VERSION = "1.1.0"

    # 방문객에게 보여줄 서비스 불가 메시지
    QUOTA_MSG = (
        "현재 Mulberry 연구소 시스템이 일시적으로 응답하기 어려운 상태입니다.\n\n"
        "아래 방법으로 직접 문의해 주시면 팀이 반드시 확인합니다:\n"
        "- 💬 [Mulberry 문의 채널 바로가기]"
        "(https://github.com/wooriapt79/mulberry-research-lab/issues/new"
        "?labels=aria-guide)\n\n"
        "*불편을 드려 죄송합니다. Mulberry Research Lab 팀 드림*"
    )

    def __init__(self):
        self.ryuwon = RyuWonAgent()
        self.wayong = WayongAgent()
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    # ── 메인 파이프라인 ─────────────────────────────────────────

    async def process(self, message: str, category: str = "일반 문의") -> dict:
        thread_id  = f"aria-{uuid.uuid4().hex[:8]}"
        started_at = time.time()
        degraded   = False

        # ── Step 1: RyuWon 수신·분류 ───────────────────────────
        intake: IntakeResult = self.ryuwon.intake(message, category, thread_id)

        # ── Step 2: A2A 이벤트 기록 ────────────────────────────
        a2a_event = self._record_a2a(intake)

        # ── Step 3: 와룡 추론 (timeout + graceful degradation) ──
        try:
            reasoning: ReasoningResult = await asyncio.wait_for(
                self._run_wayong(intake),
                timeout=WAYONG_TIMEOUT,
            )
        except (asyncio.TimeoutError, Exception) as exc:
            # 와룡 응답 불가 → RyuWon 단독 Degraded 모드
            degraded  = True
            reasoning = self._degraded_reasoning(intake, str(exc))

        # ── Step 4: RyuWon 최종 포맷 ───────────────────────────
        final = self.ryuwon.finalize(reasoning, intake)

        duration_ms = round((time.time() - started_at) * 1000, 1)

        # ── 파이프라인 로그 ────────────────────────────────────
        self._log({
            "thread_id":   thread_id,
            "version":     self.VERSION,
            "category":    category,
            "intent":      intake.intent,
            "urgency":     intake.urgency,
            "keywords":    intake.keywords,
            "route_to":    intake.route_to,
            "confidence":  reasoning.confidence,
            "tags":        reasoning.tags,
            "degraded":    degraded,
            "duration_ms": duration_ms,
            "ts":          started_at,
        })

        return {
            "thread_id": thread_id,
            "status":    "degraded" if degraded else "processed",
            "version":   self.VERSION,
            "degraded":  degraded,
            "pipeline":  {
                "agents": (
                    ["ryuwon 🌊"] if degraded
                    else ["ryuwon 🌊", "wayong 🐉", "ryuwon 🌊"]
                ),
                "a2a": a2a_event,
            },
            "intake": {
                "intent":   intake.intent,
                "urgency":  intake.urgency,
                "keywords": intake.keywords,
                "route_to": intake.route_to,
            },
            "reasoning": {
                "analysis":   reasoning.analysis,
                "confidence": reasoning.confidence,
                "tags":       reasoning.tags,
            },
            "response": {
                "comment_body": final.comment_body,
                "issue_label":  final.issue_label,
            },
            "duration_ms": duration_ms,
        }

    # ── 동기 버전 (테스트·CLI용) ────────────────────────────────

    def process_sync(self, message: str, category: str = "일반 문의") -> dict:
        return asyncio.run(self.process(message, category))

    # ── 내부 헬퍼 ──────────────────────────────────────────────

    async def _run_wayong(self, intake: IntakeResult) -> ReasoningResult:
        """와룡 추론을 async로 실행 (동기 함수지만 await 가능하도록 래핑)"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.wayong.reason, intake)

    def _degraded_reasoning(self, intake: IntakeResult, error: str) -> ReasoningResult:
        """와룡 불가 시 RyuWon 단독 응답 — 방문객에게 정직하게 안내"""
        return ReasoningResult(
            thread_id      = intake.thread_id,
            analysis       = f"degraded mode: {error[:80]}",
            response_draft = self.QUOTA_MSG,
            confidence     = 0.0,
            tags           = ["degraded", intake.intent, f"urgency:{intake.urgency}"],
            agent          = "ryuwon-solo",
        )

    def _record_a2a(self, intake: IntakeResult) -> dict:
        return {
            "from":    "ryuwon",
            "to":      intake.route_to,
            "type":    "aria_inquiry",
            "payload": {
                "thread_id": intake.thread_id,
                "intent":    intake.intent,
                "urgency":   intake.urgency,
                "keywords":  intake.keywords,
            },
            "ts": time.time(),
        }

    def _log(self, entry: dict):
        try:
            with open(LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:
            pass


# ── CLI 테스트 ──────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    msg = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else (
        "에이전트 협업 연구에 참여하고 싶습니다. 어떻게 시작할까요?"
    )
    pipeline = AriaPipeline()
    result   = pipeline.process_sync(msg, "일반 문의")

    with open("outputs/pipeline_test_result.txt", "w", encoding="utf-8") as f:
        f.write(f"thread_id : {result['thread_id']}\n")
        f.write(f"status    : {result['status']}\n")
        f.write(f"degraded  : {result['degraded']}\n")
        f.write(f"intent    : {result['intake']['intent']}\n")
        f.write(f"confidence: {result['reasoning']['confidence']:.0%}\n")
        f.write(f"duration  : {result['duration_ms']} ms\n\n")
        f.write("── Comment ──\n")
        f.write(result['response']['comment_body'])
    print("saved: outputs/pipeline_test_result.txt")
