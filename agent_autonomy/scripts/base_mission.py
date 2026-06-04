#!/usr/bin/env python3
"""
agent_autonomy/scripts/base_mission.py
공통 베이스 클래스 — 모든 에이전트 미션의 기반

설계 원칙:
  - 새 미션이 생겨도 base_mission.py는 수정하지 않는다
  - 각 에이전트 스크립트({agent}_mission.py)만 수정한다
  - 미션 유형이 늘어나도 개별 스크립트에 추가하면 된다

Koda CTO · Option B 구현 · 2026-06-05
"""

import sys, os, json, yaml, urllib.request
from pathlib import Path
from datetime import datetime, timezone
from abc import ABC, abstractmethod

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE = Path(__file__).parent.parent.parent

# .env.local 자동 로드
_env = BASE / ".env.local"
if _env.exists():
    for line in _env.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

GH_TOKEN   = os.getenv("GITHUB_TOKEN", "")
ANTHROPIC  = os.getenv("ANTHROPIC_API_KEY", "")
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")
REPO       = os.getenv("REPO_FULL", "wooriapt79/mulberry-research-lab")
TIMESTAMP  = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
TODAY      = datetime.now().strftime("%Y-%m-%d")


class BaseMission(ABC):
    """
    모든 에이전트 미션의 공통 베이스.
    새 미션 추가 시 이 클래스는 수정하지 않는다.
    """

    def __init__(self):
        self.issue_number = os.getenv("ISSUE_NUMBER", "")
        self.issue_title  = os.getenv("ISSUE_TITLE", "")
        self.issue_body   = (os.getenv("ISSUE_BODY", "") or "")[:800]
        self.issue_label  = os.getenv("ISSUE_LABEL", "")
        self.passport     = self._load_passport()

    # ── 추상 메서드 (각 에이전트가 구현) ─────────────────────────
    @property
    @abstractmethod
    def agent_id(self) -> str: ...

    @property
    @abstractmethod
    def emoji(self) -> str: ...

    @property
    @abstractmethod
    def brand(self) -> str: ...  # claude / gemini

    @property
    @abstractmethod
    def system_prompt(self) -> str: ...

    @abstractmethod
    def get_mission_prompt(self) -> str:
        """미션별 프롬프트 — 라벨에 따라 다른 작업 수행"""
        ...

    # ── 공통 유틸 (수정 불필요) ───────────────────────────────────
    def _load_passport(self) -> dict:
        passport_dir = BASE / "agentpassport" / "agents"
        for f in passport_dir.glob("*_passport.yaml"):
            try:
                data = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
                if data.get("metadata", {}).get("agent_id", "").startswith(
                    self.agent_id.split("_")[0]
                ):
                    return data
            except Exception:
                continue
        return {}

    def check_permission(self, action: str = "github_issue_comment") -> bool:
        matrix    = self.passport.get("tool_governance_matrix", {})
        allowed   = matrix.get("autonomous_processing_zone", {}).get("allowed_tools", [])
        prohibited = matrix.get("prohibited_tools", [])
        if action in prohibited:
            return False
        return len(allowed) > 0

    def call_llm(self, prompt: str) -> str:
        if self.brand == "gemini" and GEMINI_KEY:
            url     = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
            payload = json.dumps({
                "contents": [{"parts": [{"text": self.system_prompt + "\n\n" + prompt}]}],
                "generationConfig": {"temperature": 0.7, "maxOutputTokens": 600},
            }).encode("utf-8")
            req = urllib.request.Request(url, data=payload,
                                         headers={"Content-Type": "application/json"},
                                         method="POST")
        elif ANTHROPIC:
            payload = json.dumps({
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 600,
                "system": self.system_prompt,
                "messages": [{"role": "user", "content": prompt}],
            }).encode("utf-8")
            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages", data=payload,
                headers={"x-api-key": ANTHROPIC,
                         "anthropic-version": "2023-06-01",
                         "content-type": "application/json"},
                method="POST"
            )
        else:
            return f"[{self.agent_id}] API 키 없음"

        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                result = json.loads(r.read())
                if self.brand == "gemini":
                    return result["candidates"][0]["content"]["parts"][0]["text"]
                return result["content"][0]["text"]
        except Exception as e:
            return f"[{self.agent_id}] 오류: {e}"

    def post_comment(self, body: str) -> bool:
        if not GH_TOKEN or not self.issue_number:
            return False
        payload = json.dumps({"body": body}).encode("utf-8")
        req = urllib.request.Request(
            f"https://api.github.com/repos/{REPO}/issues/{self.issue_number}/comments",
            data=payload,
            headers={"Authorization": f"token {GH_TOKEN}",
                     "Content-Type": "application/json"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                return r.status == 201
        except Exception:
            return False

    def log_training(self, result: str):
        log_dir  = BASE / "training_logs"
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / f"{self.agent_id}_actions_{TODAY}.jsonl"
        entry    = {
            "timestamp": TIMESTAMP, "agent_id": self.agent_id,
            "issue_number": self.issue_number, "issue_title": self.issue_title,
            "label": self.issue_label, "action": "direct_mission",
            "result_len": len(result), "passport_ok": bool(self.passport),
        }
        with log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def run(self):
        """공통 실행 흐름 — 수정 불필요"""
        print(f"\n{'='*50}")
        print(f"  {self.emoji} {self.agent_id} 미션 실행")
        print(f"  Issue #{self.issue_number} | 라벨: {self.issue_label}")
        print(f"{'='*50}")

        if not self.check_permission():
            print("  ❌ Passport 권한 없음")
            return

        print("  🔍 미션 수행 중...")
        prompt   = self.get_mission_prompt()
        response = self.call_llm(prompt)
        print(f"  ✅ 응답 생성 ({len(response)}자)")

        comment = (
            f"### {self.emoji} {self.agent_id.split('_')[0].capitalize()} — 직접 참여\n\n"
            f"{response}\n\n"
            f"---\n*라벨: `{self.issue_label}` · Passport 인증 · {TIMESTAMP}*"
        )
        ok = self.post_comment(comment)
        print(f"  {'✅ 댓글 게시' if ok else '❌ 게시 실패'}")

        self.log_training(response)
        print(f"  📝 training_logs 기록\n")
