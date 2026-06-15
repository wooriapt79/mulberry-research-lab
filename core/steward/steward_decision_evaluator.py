# -*- coding: utf-8 -*-
"""
Steward Decision Evaluator (Issue #98, Phase 0)

Loads `configs/steward_decision_engine.yaml` and evaluates a request
(HTTP status code + optional context, e.g. spirit_score) against the
configured `decision_rules`, returning the action a Steward Agent should
take.

Replaces the previous hardcoded per-status-code branches scattered across
`error_policy.yaml` consumers with a single config-driven evaluator -
"문서 수정 -> YAML 갱신 -> 평가기가 그대로 반영" workflow.
"""

import operator
import re
from pathlib import Path
from typing import Any, Optional

import yaml

DEFAULT_CONFIG_PATH = Path("configs/steward_decision_engine.yaml")

_OPERATORS = {
    "==": operator.eq,
    "!=": operator.ne,
    ">=": operator.ge,
    "<=": operator.le,
    ">": operator.gt,
    "<": operator.lt,
}

# e.g. "status == 429" or "spirit_score < 0.70"
_CONDITION_RE = re.compile(r"^(\w+)\s*(==|!=|>=|<=|>|<)\s*([\w.]+)$")


def _coerce(value: str) -> Any:
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return value


class StewardDecisionEvaluator:
    """Evaluates requests against `configs/steward_decision_engine.yaml`."""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
        self.config = self._load_config()
        self.decision_rules = self.config.get("decision_rules", {})
        self.evaluation_axes = self.config.get("evaluation_axes", {})

    def _load_config(self) -> dict:
        if not self.config_path.exists():
            raise FileNotFoundError(f"steward decision config not found: {self.config_path}")
        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    @staticmethod
    def _rule_matches(condition: str, facts: dict) -> bool:
        match = _CONDITION_RE.match(condition.strip())
        if not match:
            return False
        field, op_str, raw_value = match.groups()
        if field not in facts or facts[field] is None:
            return False
        return _OPERATORS[op_str](facts[field], _coerce(raw_value))

    def evaluate(self, status: int, context: Optional[dict] = None) -> dict:
        """Evaluate a request and return the matching decision.

        `facts` combines the HTTP `status` with any extra `context`
        (e.g. `spirit_score`) and is checked against every rule's
        `condition`. The first matching rule wins, in config order;
        unmatched requests fall back to `action: ALLOW`.
        """
        facts = {"status": status, **(context or {})}

        for name, rule in self.decision_rules.items():
            condition = str(rule.get("condition", ""))
            if self._rule_matches(condition, facts):
                decision = dict(rule)
                decision["name"] = name
                decision["status"] = status
                return decision

        return {"action": "ALLOW", "name": None, "status": status}
