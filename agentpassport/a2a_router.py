#!/usr/bin/env python3
"""
agentpassport/a2a_router.py — Mulberry A2A 위임 실행 엔진
=========================================================
역할:
  에이전트가 자신의 passport 권한 밖 요청을 받았을 때
  tool_registry에서 담당 에이전트를 찾아 자동 위임한다.

흐름:
  요청 수신
      ↓
  passport.yaml — 권한 확인
      ↓ 권한 없음
  tool_registry.yaml — master_agent 탐색
      ↓ 발견
  A2A 위임 → 담당 에이전트 실행
      ↓ 없음
  exception_handling_protocol — 에스컬레이션

설계: Malu · 구현: Koda CTO · 2026-06-01
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

BASE = Path(__file__).parent
AGENTS_DIR = BASE / "agents"
REGISTRY_PATH = BASE / "tool_registry.yaml"
PROTOCOL_PATH = BASE / "exception_handling_protocol.yaml"
LOG_PATH = BASE / "logs" / "exceptions.jsonl"


@dataclass
class RoutingResult:
    success: bool
    delegated_to: Optional[str] = None
    tool_id: Optional[str] = None
    escalation_level: Optional[int] = None
    message: str = ""


class A2ARouter:
    """
    Mulberry A2A 위임 라우터.
    passport 권한 → tool_registry → exception_handling 순으로 처리.
    """

    def __init__(self):
        self.registry  = self._load_yaml(REGISTRY_PATH)
        self.protocol  = self._load_yaml(PROTOCOL_PATH)
        self.passports = self._load_all_passports()

    @staticmethod
    def _load_yaml(path: Path) -> dict:
        if not path.exists():
            return {}
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    def _load_all_passports(self) -> dict:
        passports = {}
        if not AGENTS_DIR.exists():
            return passports
        for f in AGENTS_DIR.glob("*_passport.yaml"):
            data = self._load_yaml(f)
            agent_id = data.get("metadata", {}).get("agent_id")
            if agent_id:
                passports[agent_id] = data
        return passports

    def check_permission(self, agent_id: str, tool_id: str) -> str:
        """
        ALLOWED / HUMAN_REQUIRED / PROHIBITED 반환
        """
        passport = self.passports.get(agent_id, {})
        matrix = passport.get("tool_governance_matrix", {})

        allowed = matrix.get("autonomous_processing_zone", {}).get("allowed_tools", [])
        human   = matrix.get("human_required_interventions", {}).get("tools", [])
        prohibited = matrix.get("prohibited_tools", [])

        if tool_id in prohibited:
            return "PROHIBITED"
        if tool_id in human:
            return "HUMAN_REQUIRED"
        if tool_id in allowed:
            return "ALLOWED"
        return "UNKNOWN"

    def find_master_agent(self, tool_id: str) -> Optional[str]:
        """tool_registry에서 tool_id의 master_agent(owner) 탐색"""
        tools = self.registry.get("tools", [])
        for tool in tools:
            if tool.get("id") == tool_id:
                return tool.get("owner")
        return None

    def route(self, requesting_agent: str, tool_id: str, payload: dict = None) -> RoutingResult:
        """
        메인 라우팅 로직.
        1. 권한 확인
        2. 가능하면 자율 실행
        3. 위임 필요하면 A2A 위임
        4. 불가능하면 에스컬레이션
        """
        print(f"\n[A2ARouter] {requesting_agent} → {tool_id}")
        permission = self.check_permission(requesting_agent, tool_id)
        print(f"  권한 상태: {permission}")

        if permission == "ALLOWED":
            return RoutingResult(
                success=True, tool_id=tool_id,
                message=f"✅ {requesting_agent} 자율 실행 가능"
            )

        if permission == "PROHIBITED":
            self._log_exception(requesting_agent, tool_id, "unauthorized_tool_access", 3)
            return RoutingResult(
                success=False, escalation_level=3,
                message=f"🚫 PROHIBITED — CEO re.eul 승인 필요"
            )

        if permission in ("HUMAN_REQUIRED", "UNKNOWN"):
            # tool_registry에서 담당자 탐색
            master = self.find_master_agent(tool_id)
            if master and master != requesting_agent:
                print(f"  A2A 위임 → {master}")
                self._log_exception(requesting_agent, tool_id, "delegated", 1)
                return RoutingResult(
                    success=True,
                    delegated_to=master,
                    tool_id=tool_id,
                    escalation_level=1,
                    message=f"🔀 A2A 위임: {requesting_agent} → {master}"
                )

            # 담당자 없음 → 팀 토론 이슈
            self._log_exception(requesting_agent, tool_id, "unknown_tool_request", 2)
            return RoutingResult(
                success=False, escalation_level=2,
                message=f"⚠️ 담당 에이전트 없음 — 팀 토론 이슈 생성 필요"
            )

    def _log_exception(self, agent: str, tool: str, exc_type: str, level: int):
        from datetime import datetime, timezone
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "requesting_agent": agent,
            "requested_tool": tool,
            "exception_type": exc_type,
            "escalation_level": level,
        }
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ── 실행 ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Mulberry A2A Router 테스트")
    parser.add_argument("--agent", default="kbin_csa",  help="요청 에이전트 ID")
    parser.add_argument("--tool",  default="deploy_production", help="요청 도구 ID")
    args = parser.parse_args()

    router = A2ARouter()
    result = router.route(args.agent, args.tool)
    print(f"\n결과: {result.message}")
    if result.delegated_to:
        print(f"위임 대상: {result.delegated_to}")
    if result.escalation_level:
        print(f"에스컬레이션 레벨: {result.escalation_level}")
