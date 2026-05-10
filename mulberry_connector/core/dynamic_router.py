"""
Dynamic Constraint Scoring Router (Kbin CTO 설계 / Koda 구현)

Issue #24 — Kbin 권고사항:
  "Static fallback ❌ → Adaptive execution governance ⭕"

라우팅 공식:
  route_score = (trust * weight)
              - latency_penalty
              - quota_penalty
              - ethical_risk
              + context_match

Tool Capability Levels:
  L0: read-only       → Hesitation 없음
  L1: draft           → 경미한 Hesitation
  L2: external_post   → Hesitation 필수
  L3: code_modify     → Human Review 권장
  L4: deploy_financial→ Human Review 필수

Shared Execution Audit Log:
  모든 라우팅 결정을 audit_log에 기록 → Tool Reputation 누적
"""

import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from core.tool_registry import ToolRegistry, Tool

AUDIT_LOG_PATH = Path(__file__).parent.parent.parent / "training_logs" / "execution_audit.jsonl"

# Capability Level 정의
CAPABILITY_LEVELS = {
    "L0": {"label": "read-only",        "hesitation": "none",   "human_review": False},
    "L1": {"label": "draft",            "hesitation": "low",    "human_review": False},
    "L2": {"label": "external_post",    "hesitation": "medium", "human_review": False},
    "L3": {"label": "code_modify",      "hesitation": "high",   "human_review": True},
    "L4": {"label": "deploy_financial", "hesitation": "block",  "human_review": True},
}

# 에이전트 컨디션 — 실제 운영 시 헬스체크 API로 교체
# 현재: 기본값 기반 (향후 동적 수집)
DEFAULT_AGENT_CONDITIONS: dict[str, dict] = {
    "koda":   {"latency": 0.3, "quota": 0.9, "bio_state": "active"},
    "kbin":   {"latency": 0.4, "quota": 0.8, "bio_state": "active"},
    "malu":   {"latency": 0.5, "quota": 0.7, "bio_state": "active"},
    "wayong": {"latency": 0.6, "quota": 0.6, "bio_state": "active"},
    "ryuwon": {"latency": 0.4, "quota": 0.8, "bio_state": "active"},
    "lynn":   {"latency": 0.3, "quota": 1.0, "bio_state": "active"},
    "jr":     {"latency": 0.8, "quota": 0.5, "bio_state": "active"},
    "trang":  {"latency": 0.2, "quota": 1.0, "bio_state": "active"},
}

BIO_PENALTY = {"active": 0.0, "charging": 0.3, "rest": 0.5, "travel": 0.4}


@dataclass
class RouteScore:
    agent: str
    score: float
    trust: float
    latency_penalty: float
    quota_penalty: float
    ethical_risk: float
    context_match: float
    bio_penalty: float


@dataclass
class DynamicRouteResult:
    selected_agent: str
    capability_level: str
    human_review_required: bool
    hesitation_level: str
    scores: list[RouteScore]
    reason: str
    audit_id: str = field(default_factory=lambda: f"rt_{int(time.time()*1000)%100000}")


class DynamicConstraintRouter:
    """
    Kbin CTO 설계 — 에이전트 컨디션 기반 동적 라우팅.

    route_score = (trust * weight) - latency_penalty - quota_penalty
                - ethical_risk + context_match - bio_penalty
    """

    def __init__(self, registry: ToolRegistry = None):
        self.registry = registry or ToolRegistry()
        AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    def route(
        self,
        tool_id: str,
        requesting_agent: str,
        context: str = "",
        candidate_agents: list[str] = None,
    ) -> DynamicRouteResult:
        """
        tool_id를 실행할 최적 에이전트를 동적으로 선택.

        candidate_agents: 후보 에이전트 목록 (None이면 borrowable_by 전체)
        """
        tool = self.registry.get(tool_id)
        if not tool:
            return self._fail(tool_id, "등록되지 않은 도구")

        # 후보 에이전트 결정
        if candidate_agents is None:
            if tool.is_public():
                candidate_agents = list(DEFAULT_AGENT_CONDITIONS.keys())
            else:
                candidate_agents = [tool.owner] + [
                    a for a in tool.borrowable_by if a != "*"
                ]

        # 요청 에이전트 우선 포함
        if requesting_agent not in candidate_agents:
            candidate_agents = [requesting_agent] + candidate_agents

        # 각 후보 점수 계산
        scores = [
            self._score(agent, tool, context)
            for agent in candidate_agents
            if agent in DEFAULT_AGENT_CONDITIONS
        ]
        scores.sort(key=lambda s: s.score, reverse=True)

        if not scores:
            return self._fail(tool_id, "실행 가능한 에이전트 없음")

        best = scores[0]
        cap_level = getattr(tool, "capability_level", "L2")
        cap_info = CAPABILITY_LEVELS.get(cap_level, CAPABILITY_LEVELS["L2"])

        result = DynamicRouteResult(
            selected_agent=best.agent,
            capability_level=cap_level,
            human_review_required=cap_info["human_review"],
            hesitation_level=cap_info["hesitation"],
            scores=scores,
            reason=(
                f"동적 라우팅: {best.agent} (score={best.score:.3f}) | "
                f"Level={cap_level} | hesitation={cap_info['hesitation']}"
            ),
        )

        # Audit Log 기록
        self._audit(tool_id, requesting_agent, result)
        return result

    def _score(self, agent: str, tool: Tool, context: str) -> RouteScore:
        cond = DEFAULT_AGENT_CONDITIONS.get(agent, {})

        trust = getattr(tool, "trust_score", 0.8)
        latency = cond.get("latency", 0.5)
        quota = cond.get("quota", 0.5)
        bio = cond.get("bio_state", "active")

        latency_penalty = latency * 0.2
        quota_penalty   = (1.0 - quota) * 0.3
        bio_penalty_val = BIO_PENALTY.get(bio, 0.0)

        # 윤리 리스크: capability level 기반
        cap = getattr(tool, "capability_level", "L2")
        ethical_risk = {"L0": 0.0, "L1": 0.05, "L2": 0.1, "L3": 0.2, "L4": 0.4}.get(cap, 0.1)

        # 컨텍스트 매칭: 소유자 에이전트에 가산점
        context_match = 0.15 if agent == tool.owner else 0.0

        score = (
            trust * 0.4
            - latency_penalty
            - quota_penalty
            - ethical_risk
            + context_match
            - bio_penalty_val
        )

        return RouteScore(
            agent=agent, score=round(score, 4),
            trust=trust, latency_penalty=round(latency_penalty, 3),
            quota_penalty=round(quota_penalty, 3),
            ethical_risk=ethical_risk, context_match=context_match,
            bio_penalty=bio_penalty_val,
        )

    def _fail(self, tool_id: str, reason: str) -> DynamicRouteResult:
        return DynamicRouteResult(
            selected_agent="", capability_level="L0",
            human_review_required=False, hesitation_level="none",
            scores=[], reason=f"FAIL: {reason}",
        )

    def _audit(self, tool_id: str, requester: str, result: DynamicRouteResult):
        """Shared Execution Audit Log — Tool Reputation 누적 기반."""
        entry = {
            "audit_id": result.audit_id,
            "timestamp": datetime.utcnow().isoformat(),
            "tool_id": tool_id,
            "requester": requester,
            "selected": result.selected_agent,
            "capability_level": result.capability_level,
            "human_review": result.human_review_required,
            "top_score": result.scores[0].score if result.scores else 0,
            "candidates": len(result.scores),
        }
        with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def tool_reputation(self, tool_id: str) -> dict:
        """Audit Log에서 Tool Reputation 집계."""
        if not AUDIT_LOG_PATH.exists():
            return {"tool_id": tool_id, "calls": 0}
        calls, agents = 0, {}
        with open(AUDIT_LOG_PATH, encoding="utf-8") as f:
            for line in f:
                entry = json.loads(line)
                if entry.get("tool_id") == tool_id:
                    calls += 1
                    a = entry.get("selected", "unknown")
                    agents[a] = agents.get(a, 0) + 1
        return {"tool_id": tool_id, "calls": calls, "executors": agents}
