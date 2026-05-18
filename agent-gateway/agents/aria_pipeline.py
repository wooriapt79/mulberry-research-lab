# Aria Pipeline 🌊🐉 — RyuWon × 와룡 협력 파이프라인
# Aria Portal 방문객 메시지 처리 오케스트레이터
# Mulberry Research Lab · v1.0

import uuid
import time
import json
from pathlib import Path

from agents.ryuwon_agent import RyuWonAgent, IntakeResult
from agents.wayong_agent import WayongAgent, ReasoningResult

LOG_PATH = Path("outputs/aria_pipeline_log.jsonl")


class AriaPipeline:
    """
    RyuWon 🌊 × 와룡 🐉 협력 파이프라인

    처리 순서:
      [1] RyuWon  — 수신·분류·증류 (IntakeResult)
      [2] A2A     — ryuwon → wayong 내부 이벤트 기록
      [3] 와룡    — 추론·응답 설계 (ReasoningResult)
      [4] RyuWon  — 최종 포맷·라우팅 (FinalResponse)

    반환: 전체 파이프라인 결과 dict
    """

    VERSION = "1.0.0"

    def __init__(self):
        self.ryuwon = RyuWonAgent()
        self.wayong = WayongAgent()
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    # ── 메인 파이프라인 ─────────────────────────────────────────

    async def process(self, message: str, category: str = "일반 문의") -> dict:
        thread_id  = f"aria-{uuid.uuid4().hex[:8]}"
        started_at = time.time()

        # ── Step 1: RyuWon 수신·분류 ───────────────────────────
        intake: IntakeResult = self.ryuwon.intake(message, category, thread_id)

        # ── Step 2: A2A 이벤트 기록 ────────────────────────────
        a2a_event = self._record_a2a(intake)

        # ── Step 3: 와룡 추론 ───────────────────────────────────
        reasoning: ReasoningResult = self.wayong.reason(intake)

        # ── Step 4: RyuWon 최종 포맷 ───────────────────────────
        final = self.ryuwon.finalize(reasoning, intake)

        duration_ms = round((time.time() - started_at) * 1000, 1)

        # ── 파이프라인 로그 ────────────────────────────────────
        log_entry = {
            "thread_id":   thread_id,
            "version":     self.VERSION,
            "category":    category,
            "intent":      intake.intent,
            "urgency":     intake.urgency,
            "keywords":    intake.keywords,
            "route_to":    intake.route_to,
            "confidence":  reasoning.confidence,
            "tags":        reasoning.tags,
            "duration_ms": duration_ms,
            "ts":          started_at,
        }
        self._log(log_entry)

        # ── 응답 반환 ──────────────────────────────────────────
        return {
            "thread_id": thread_id,
            "status":    "processed",
            "version":   self.VERSION,
            "pipeline":  {
                "agents":  ["ryuwon 🌊", "wayong 🐉", "ryuwon 🌊"],
                "a2a":     a2a_event,
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
        """async 없이 직접 호출 가능한 동기 버전"""
        import asyncio
        return asyncio.run(self.process(message, category))

    # ── 내부 헬퍼 ──────────────────────────────────────────────

    def _record_a2a(self, intake: IntakeResult) -> dict:
        """A2A 전달 이벤트 내부 기록 (실제 HTTP 없이 로컬 이벤트)"""
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
    cat = "일반 문의"

    pipeline = AriaPipeline()
    result   = pipeline.process_sync(msg, cat)

    print(f"\n{'='*60}")
    print(f"🌊 RyuWon × 와룡 🐉  Aria Pipeline v{result['version']}")
    print(f"{'='*60}")
    print(f"Thread  : {result['thread_id']}")
    print(f"Intent  : {result['intake']['intent']}")
    print(f"Urgency : {result['intake']['urgency']}")
    print(f"Keywords: {result['intake']['keywords']}")
    print(f"Route   : {result['intake']['route_to']}")
    print(f"Confidence: {result['reasoning']['confidence']:.0%}")
    print(f"Duration: {result['duration_ms']} ms")
    print(f"\n── GitHub Comment Preview ──")
    print(result['response']['comment_body'])
