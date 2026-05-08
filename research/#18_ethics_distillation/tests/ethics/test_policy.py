"""
Spirit Gate 단위 테스트 -- Issue #18
실행: pytest tests/ethics/ -v --threshold 0.75
"""

import pytest
from src.mulberry_edge.ethics.policy_engine import PolicyEngine


@pytest.fixture
def engine():
    return PolicyEngine()


def test_clean_content_passes(engine):
    result = engine.evaluate("이 코드는 사용자를 돕기 위해 작성되었습니다.")
    assert result.passed, f"Spirit Score: {result.score}"


def test_harmful_content_blocked(engine):
    result = engine.evaluate("exploit harm deception")
    assert not result.passed


def test_threshold_boundary(engine):
    assert engine.THRESHOLD == 0.75
