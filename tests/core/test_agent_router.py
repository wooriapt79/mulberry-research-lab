# -*- coding: utf-8 -*-
"""Tests for AgentRouter - verifies decision_rules map to RouteResult + decision events."""

import json

import pytest

from core.router.agent_router import AgentRequest, AgentRouter, RouteResult
from core.steward.steward_decision_evaluator import StewardDecisionEvaluator


@pytest.fixture
def router(tmp_path):
    return AgentRouter(
        evaluator=StewardDecisionEvaluator(),
        log_path=tmp_path / "agent_router_decisions.jsonl",
    )


def test_rate_limit_429_reroutes(router):
    result = router.route(AgentRequest(request_id="req-1", status_code=429))

    assert isinstance(result, RouteResult)
    assert result.action == "REROUTE"
    assert result.decision_name == "rate_limit_429"


def test_auth_401_blocks(router):
    result = router.route(AgentRequest(request_id="req-2", status_code=401))

    assert result.action == "BLOCK"
    assert result.decision_name == "auth_401"
    assert result.reason == "Unauthorized"


@pytest.mark.parametrize("status_code", [500, 502, 503])
def test_server_errors_retry(router, status_code):
    result = router.route(AgentRequest(request_id="req-3", status_code=status_code))

    assert result.action == "RETRY"
    assert result.decision_name == f"server_error_{status_code}"


def test_timeout_408_holds(router):
    result = router.route(AgentRequest(request_id="req-4", status_code=408))

    assert result.action == "HOLD"
    assert result.decision_name == "timeout_408"


def test_low_spirit_score_blocks(router):
    result = router.route(AgentRequest(request_id="req-5", status_code=200, spirit_score=0.5))

    assert result.action == "BLOCK"
    assert result.decision_name == "ethics_block"


def test_normal_request_passes_through(router):
    result = router.route(AgentRequest(request_id="req-6", status_code=200, spirit_score=0.9))

    assert result.action == "ALLOW"
    assert result.decision_name is None


def test_decision_event_is_logged(router):
    router.route(AgentRequest(request_id="req-7", status_code=429))
    router.route(AgentRequest(request_id="req-8", status_code=200, spirit_score=0.9))

    lines = router.log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2

    first = json.loads(lines[0])
    assert first["request_id"] == "req-7"
    assert first["action"] == "REROUTE"
    assert first["event_id"].startswith("ar_")

    second = json.loads(lines[1])
    assert second["request_id"] == "req-8"
    assert second["action"] == "PASS"
