# -*- coding: utf-8 -*-
"""
Agent Router (Issue #98, Phase 1)

Connects `StewardDecisionEvaluator` to actual request routing. An
`AgentRequest` is evaluated against `configs/steward_decision_engine.yaml`
and the resulting `decision_rules` action (BLOCK/REROUTE/RETRY/HOLD/ALLOW)
is translated into a `RouteResult` that callers act on.

Every routing decision is appended to `training_logs/agent_router_decisions.jsonl`
so the Mission Control "Decision" panel can replay/stream them
(see `routes/decision-events.js` in mulberry-mission-control for the
consuming side - same JSON shape).
"""

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from core.steward.steward_decision_evaluator import StewardDecisionEvaluator

DECISION_LOG_PATH = (
    Path(__file__).parent.parent.parent / "training_logs" / "agent_router_decisions.jsonl"
)

# decision_rules `action` -> Decision UI color mapping (Mission Control Decision menu)
_ACTION_TO_EVENT = {
    "BLOCK": "BLOCK",
    "REROUTE": "REROUTE",
    "RETRY": "RETRY",
    "HOLD": "HOLD",
    "ALLOW": "PASS",
}


@dataclass
class AgentRequest:
    """A request entering the router."""

    request_id: str
    status_code: int
    spirit_score: Optional[float] = None
    meta: dict = field(default_factory=dict)


@dataclass
class RouteResult:
    """Outcome of `AgentRouter.route()`."""

    action: str
    request_id: str
    decision_name: Optional[str] = None
    reason: Optional[str] = None
    target: Optional[str] = None
    delay: Optional[str] = None
    queue: Optional[str] = None

    @classmethod
    def blocked(cls, request_id: str, decision_name: Optional[str], reason: Optional[str]) -> "RouteResult":
        return cls(action="BLOCK", request_id=request_id, decision_name=decision_name, reason=reason)

    @classmethod
    def reroute(cls, request_id: str, decision_name: Optional[str], target: Optional[str]) -> "RouteResult":
        return cls(action="REROUTE", request_id=request_id, decision_name=decision_name, target=target)

    @classmethod
    def retry(cls, request_id: str, decision_name: Optional[str], delay: Optional[str]) -> "RouteResult":
        return cls(action="RETRY", request_id=request_id, decision_name=decision_name, delay=delay)

    @classmethod
    def hold(cls, request_id: str, decision_name: Optional[str], queue: Optional[str]) -> "RouteResult":
        return cls(action="HOLD", request_id=request_id, decision_name=decision_name, queue=queue)

    @classmethod
    def pass_through(cls, request_id: str, decision_name: Optional[str] = None) -> "RouteResult":
        return cls(action="ALLOW", request_id=request_id, decision_name=decision_name)


class AgentRouter:
    """Routes `AgentRequest`s through `StewardDecisionEvaluator`."""

    def __init__(self, evaluator: Optional[StewardDecisionEvaluator] = None, log_path: Path = DECISION_LOG_PATH):
        self.evaluator = evaluator or StewardDecisionEvaluator()
        self.log_path = Path(log_path)

    def route(self, request: AgentRequest) -> RouteResult:
        context = {}
        if request.spirit_score is not None:
            context["spirit_score"] = request.spirit_score

        decision = self.evaluator.evaluate(request.status_code, context)
        result = self._to_route_result(request, decision)
        self._emit_decision_event(request, decision, result)
        return result

    @staticmethod
    def _to_route_result(request: AgentRequest, decision: dict) -> RouteResult:
        action = decision.get("action", "ALLOW")
        name = decision.get("name")

        if action == "BLOCK":
            return RouteResult.blocked(request.request_id, name, decision.get("message"))
        if action == "REROUTE":
            return RouteResult.reroute(request.request_id, name, decision.get("target"))
        if action == "RETRY":
            return RouteResult.retry(request.request_id, name, decision.get("backoff"))
        if action == "HOLD":
            return RouteResult.hold(request.request_id, name, decision.get("queue"))
        return RouteResult.pass_through(request.request_id, name)

    def _emit_decision_event(self, request: AgentRequest, decision: dict, result: RouteResult) -> None:
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_id": f"ar_{uuid.uuid4().hex[:12]}",
            "request_id": request.request_id,
            "action": _ACTION_TO_EVENT.get(decision.get("action", "ALLOW"), "PASS"),
            "decision_name": decision.get("name"),
            "status_code": request.status_code,
            "spirit_score": request.spirit_score,
            "message": decision.get("message"),
        }

        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
