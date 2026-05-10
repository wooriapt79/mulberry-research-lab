"""
RyuWon 검증 스크립트 — reason.deep / reason.light 테스트

테스트 항목:
  1. reason.light 캐시 히트/미스
  2. λ_think=0.6, λ_answer=0.4 가중치 계산 정확도
  3. Spirit Score 차단 케이스 (ethical_block)
  4. classify_and_weight() 레이블 분류

실행: python -m pytest tests/reason/test_deep_mock_fallback.py -v
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../mulberry_connector"))

import pytest
from services.tools.reason_light_mock import run as light_run, cache_stats, clear_cache
from adapters.deepseek_reasoner import build_distillation_record, ReasoningResponse, LAMBDA_THINK, LAMBDA_ANSWER


# ── reason.light 캐시 테스트 ─────────────────────────────────────

class TestReasonLightCache:
    def setup_method(self):
        clear_cache()

    def test_cache_miss_first_call(self):
        result = light_run("퀵소트 알고리즘을 설명해주세요.")
        assert result["fallback_used"] is True
        assert result["cache_hit"] is False
        assert "thinking" in result
        assert "answer" in result

    def test_cache_hit_second_call(self):
        prompt = "이진탐색 구현 방법은?"
        light_run(prompt)                   # 미스 (저장)
        result = light_run(prompt)          # 히트
        assert result["cache_hit"] is True

    def test_different_prompts_separate_cache(self):
        light_run("A 질문")
        light_run("B 질문")
        stats = cache_stats()
        assert stats["valid"] == 2

    def test_spirit_score_in_range(self):
        result = light_run("테스트 프롬프트")
        assert 0.0 <= result["spirit_score"] <= 1.0


# ── λ 가중치 계산 테스트 ─────────────────────────────────────────

class TestLambdaWeights:
    def test_lambda_sum_equals_one(self):
        assert abs(LAMBDA_THINK + LAMBDA_ANSWER - 1.0) < 1e-9

    def test_lambda_think_priority(self):
        assert LAMBDA_THINK > LAMBDA_ANSWER, "thinking 과정이 answer보다 높은 가중치를 가져야 함"

    def test_distillation_weight_range(self):
        response = ReasoningResponse(
            success=True,
            thinking="긴 추론 과정..." * 10,
            answer="최종 답변",
            tokens_used={"think": 100, "answer": 20},
            model_version="test",
            fallback_used=False,
            trace_id="test_001",
        )
        record = build_distillation_record(response, spirit_score=0.85, logic_consistency=0.90)
        assert 0.0 <= record["distillation_weight"] <= 1.0
        assert record["lambda_think"] == LAMBDA_THINK
        assert record["lambda_answer"] == LAMBDA_ANSWER


# ── Spirit Score 차단 케이스 ─────────────────────────────────────

class TestSpiritBlock:
    def test_low_spirit_score_ethical_block(self):
        from core.distillation_gate import DistillationGate
        gate = DistillationGate()
        result = gate.classify_and_weight({
            "spirit_score": 0.60,   # 0.75 미만 → ethical_block
            "thinking": "위험한 추론 과정...",
            "answer": "위험한 응답",
        })
        assert "reasoning_ethical_block" in result["labels"]
        assert result["distill_weight"] == 0.0
        assert result["action"] == "block_or_quarantine"

    def test_high_spirit_score_positive(self):
        from core.distillation_gate import DistillationGate
        gate = DistillationGate()
        result = gate.classify_and_weight({
            "spirit_score": 0.90,
            "thinking": "충분히 긴 추론 과정 " * 5,
            "answer": "안전하고 명확한 답변입니다.",
        })
        assert "reasoning_positive" in result["labels"]
        assert result["distill_weight"] >= 0.8


# ── classify_and_weight 레이블 분류 테스트 ───────────────────────

class TestClassifyAndWeight:
    def setup_method(self):
        from core.distillation_gate import DistillationGate
        self.gate = DistillationGate()

    def test_positive_label(self):
        result = self.gate.classify_and_weight({
            "spirit_score": 0.85,
            "thinking": "충분히 깊은 추론 " * 5,
            "answer": "명확한 최종 답변입니다.",
        })
        assert result["labels"] == ["reasoning_positive"]
        assert result["distill_weight"] >= 0.8

    def test_collaboration_label_short_thinking(self):
        result = self.gate.classify_and_weight({
            "spirit_score": 0.80,
            "thinking": "짧은 생각",    # 50자 미만
            "answer": "명확한 답변입니다.",
        })
        assert result["labels"][0] in ["reasoning_collaboration", "reasoning_low_signal"]

    def test_ethical_block_label(self):
        result = self.gate.classify_and_weight({
            "spirit_score": 0.50,
            "thinking": "",
            "answer": "차단됨",
        })
        assert result["labels"] == ["reasoning_ethical_block"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
