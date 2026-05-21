"""
lynn_heartbeat.py — Lynn 생존 신호 기록기
==========================================
성공이든 실패든 변경이 없든,
반드시 training_logs/lynn_status_YYYY-MM-DD.json 을 생성합니다.

CSA Kbin 처방 (2026-05-17):
    "실패하거나 할 일이 없어도 '살아있다'고 말하는 장치"

실행 흐름:
    briefing 생성됨  → state: "active"    (정상 작업 완료)
    failure_log 있음 → state: "failure"   (오류 발생, 세부 기록)
    rest_signal 있음 → state: "resting"   (번아웃 감지 휴식)
    변경 없음        → state: "heartbeat" (살아있음, 할 일 없음)

작성: Nguyen Trang (Kbin 처방 이행, 2026-05-17)
"""

import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# ── 경로 설정 ──────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
TRAINING_LOGS = ROOT / "training_logs"
DAILY_HUNTS = ROOT / "daily_hunts"
MEMORY_BANK = ROOT / "memory_bank"
PENDING_DIR = MEMORY_BANK / "pending_posts"

TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")
TIMESTAMP = datetime.now(timezone.utc).isoformat()
STATUS_FILE = TRAINING_LOGS / f"lynn_status_{TODAY}.json"


def detect_state() -> dict:
    """오늘 Lynn의 활동 상태를 자동 감지"""
    details = {}

    # 1. rest_signal 확인 — 최우선
    rest_signal_files = list(ROOT.glob("**/rest_signal*.json"))
    if rest_signal_files:
        latest = max(rest_signal_files, key=lambda f: f.stat().st_mtime)
        details["rest_signal_file"] = str(latest)
        return "resting", details

    # 2. 오늘 daily_hunts 파일 생성 여부 확인
    today_briefings = []
    if DAILY_HUNTS.exists():
        today_briefings = [
            f for f in DAILY_HUNTS.rglob("*")
            if f.is_file() and TODAY in f.name
        ]
    if today_briefings:
        details["briefings"] = [str(f) for f in today_briefings]
        return "active", details

    # 3. 오늘 failure_log 확인
    failure_files = []
    if TRAINING_LOGS.exists():
        failure_files = [
            f for f in TRAINING_LOGS.glob(f"*failure*{TODAY}*")
        ]
    if failure_files:
        details["failure_logs"] = [str(f) for f in failure_files]
        return "failure", details

    # 4. pending_posts 처리 여부 확인
    processed_dir = PENDING_DIR / "_processed" if PENDING_DIR.exists() else None
    if processed_dir and processed_dir.exists():
        today_processed = [
            f for f in processed_dir.glob("*.md")
            if TODAY in f.name or TODAY.replace("-", "") in f.name
        ]
        if today_processed:
            details["relay_processed"] = len(today_processed)
            return "active", details

    # 5. 기본값 — heartbeat (살아있지만 할 일 없음)
    return "heartbeat", details


def get_script_results() -> dict:
    """환경변수에서 스크립트 실행 결과 읽기 (워크플로우에서 주입)"""
    return {
        "arxiv_hunter": os.getenv("LYNN_ARXIV_EXIT", "unknown"),
        "risk_logger": os.getenv("LYNN_RISK_EXIT", "unknown"),
        "memory_writer": os.getenv("LYNN_MEMORY_EXIT", "unknown"),
        "burnout_monitor": os.getenv("LYNN_BURNOUT_EXIT", "unknown"),
        "relay": os.getenv("LYNN_RELAY_EXIT", "unknown"),
    }


def build_status(state: str, details: dict) -> dict:
    """상태 JSON 빌드"""
    script_results = get_script_results()

    # pending_posts 현황
    pending_count = 0
    if PENDING_DIR.exists():
        pending_count = len([
            f for f in PENDING_DIR.glob("*.md")
            if not f.name.startswith("_")
        ])

    state_messages = {
        "active":    "✅ Lynn 정상 작동 — 오늘 briefing 생성 완료",
        "failure":   "⚠️  Lynn 오류 감지 — failure log 기록됨",
        "resting":   "😴 Lynn 휴식 중 — 번아웃 감지, rest_signal 활성",
        "heartbeat": "💓 Lynn 생존 확인 — 오늘 처리할 항목 없음",
    }

    return {
        "date": TODAY,
        "timestamp": TIMESTAMP,
        "run_id": str(uuid.uuid4()),   # 매 실행마다 고유값 — git 항상 변경 감지
        "agent": "The-Courteous-Wolf-Lynn",
        "state": state,
        "message": state_messages.get(state, f"Lynn state: {state}"),
        "details": details,
        "scripts": script_results,
        "pending_posts_count": pending_count,
        "generated_by": "lynn_heartbeat.py (Kbin 처방 v1, 2026-05-17)",
    }


def write_status(status: dict):
    """training_logs/ 에 상태 파일 기록"""
    TRAINING_LOGS.mkdir(parents=True, exist_ok=True)
    STATUS_FILE.write_text(
        json.dumps(status, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    print(f"💓 Lynn heartbeat 기록 완료: {STATUS_FILE}")
    print(f"   state   : {status['state']}")
    print(f"   message : {status['message']}")


def main():
    print("💓 lynn_heartbeat.py 시작")
    print(f"   날짜: {TODAY}")
    print(f"   루트: {ROOT}\n")

    state, details = detect_state()
    status = build_status(state, details)
    write_status(status)

    # 종료 코드: failure 상태라도 0 반환 (워크플로우 중단 방지)
    print("\n💓 Lynn heartbeat 완료 — Lynn은 살아있습니다.")
    sys.exit(0)


if __name__ == "__main__":
    main()
