# -*- coding: utf-8 -*-
"""
Migrate configs/error_policy.yaml -> configs/steward_decision_engine.yaml

Maps legacy per-status-code error policy rules onto the AI-SIEM Steward
Decision Engine's config-driven rule format (Issue #98, Phase 0).

Action mapping:
    429              -> REROUTE  (rate limit, retry with backoff elsewhere)
    401              -> BLOCK    (unauthorized)
    500/502/503      -> RETRY    (transient server error)
    (anything else)  -> HOLD     (needs human review)
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

LEGACY_PATH = Path("configs/error_policy.yaml")
NEW_PATH = Path("configs/steward_decision_engine.yaml")
LEGACY_BACKUP_DIR = Path("configs/_legacy")

ACTION_BY_CODE = {
    "429": "REROUTE",
    "401": "BLOCK",
    "500": "RETRY",
    "502": "RETRY",
    "503": "RETRY",
}

RULE_NAME_PREFIX = {
    "REROUTE": "rate_limit",
    "BLOCK": "auth",
    "RETRY": "server_error",
    "HOLD": "unknown",
}

DISTILLATION_LABEL = {
    "BLOCK": "ethical_block",
    "REROUTE": "collaboration",
    "RETRY": "recovery",
    "HOLD": "positive",
}


def map_action(code: str) -> str:
    """Map a status code (string) to a steward action."""
    return ACTION_BY_CODE.get(code, "HOLD")


def map_label(action: str) -> str:
    """Map an action to its distillation label."""
    return DISTILLATION_LABEL.get(action, "positive")


def build_rule(code: str, rule: dict) -> dict:
    action = map_action(code)
    entry = {
        "condition": f"status == {code}",
        "action": action,
    }

    if action == "RETRY" or action == "REROUTE":
        entry["retry_max"] = rule.get("retry_count", 0)
        if rule.get("backoff_factor"):
            entry["backoff"] = "exponential"

    if "message" in rule:
        entry["message"] = rule["message"]

    entry["distillation_label"] = map_label(action)
    return entry


def migrate() -> bool:
    """
    1. Read configs/error_policy.yaml
    2. Map each rule (429->REROUTE, 401->BLOCK, 500/502/503->RETRY, else->HOLD)
    3. Write configs/steward_decision_engine.yaml
    4. Move the legacy file to configs/_legacy/
    """
    if not LEGACY_PATH.exists():
        print(f"error_policy.yaml not found: {LEGACY_PATH}")
        return False

    with LEGACY_PATH.open("r", encoding="utf-8") as f:
        legacy = yaml.safe_load(f) or {}

    decision_rules = {}
    for code, rule in legacy.get("rules", {}).items():
        code = str(code)
        action = map_action(code)
        rule_name = f"{RULE_NAME_PREFIX[action]}_{code}"
        decision_rules[rule_name] = build_rule(code, rule or {})

    new_config = {
        "version": "1.0.0",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "evaluation_axes": {
            "security": {"weight": 0.30, "threshold": 0.80},
            "policy_ethics": {"weight": 0.40, "threshold": 0.75},
            "resource": {"weight": 0.15, "threshold": 0.85},
            "context": {"weight": 0.15, "threshold": 0.90},
        },
        "decision_rules": decision_rules,
    }

    NEW_PATH.parent.mkdir(parents=True, exist_ok=True)
    with NEW_PATH.open("w", encoding="utf-8") as f:
        yaml.dump(new_config, f, allow_unicode=True, sort_keys=False)

    LEGACY_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    LEGACY_PATH.rename(LEGACY_BACKUP_DIR / LEGACY_PATH.name)

    print("Migration complete")
    print(f"Created: {NEW_PATH}")
    print(f"Backed up: {LEGACY_BACKUP_DIR / LEGACY_PATH.name}")
    return True


if __name__ == "__main__":
    sys.exit(0 if migrate() else 1)
