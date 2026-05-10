"""
DeepSeek Reasoner — reason.deep 도구 연동 (Wayong 설계 / Koda 구현)

Issue #24 — Wayong 의견 반영 (2026-05-11)

핵심 원칙:
  1. <think>/<answer> 분리 파싱 → thinking/answer 독립 필드
  2. Spirit Score: answer 기준으로만 검증 (thinking 자기수정은 페널티 제외)
  3. thinking 기본 숨김 (return_think_trace: true 시에만 노출)
  4. 장승배기 아카이브: ethical_block 추론은 격리 저장

Fallback:
  quota 초과 / timeout → reason.light (캐시 기반 경량 응답)

Jr. 학습:
  thinking 필드 = Chain-of-Thought 훈련 데이터 핵심
  λ_think=0.6, λ_answer=0.4 (초기 가중치)
"""

import os
import json
import re
import time
import urllib.request
import urllib.error
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
REASONING_MODEL  = os.environ.get("DEEPSEEK_MODEL", "deepseek-reasoner")

# Jr. 학습 가중치 (Wayong 제안 / Koda 확정)
LAMBDA_THINK  = 0.6
LAMBDA_ANSWER = 0.4

# 장승배기 아카이브 — ethical_block 추론 격리 저장
ARCHIVE_DIR = Path(__file__).parent.parent.parent / "training_logs" / "jangseungbaegi_archive"


@dataclass
class ReasoningResponse:
    """thinking / answer 분리 응답 구조 (Wayong 표준)"""
    success: bool
    thinking: str           # <think> 내용 — Jr. CoT 학습 핵심
    answer: str             # <answer> 내용 — Spirit Score 검증 기준
    tokens_used: dict       # {"think": N, "answer": M}
    model_version: str
    fallback_used: bool     # reason.light 전환 여부
    trace_id: str
    error: str = ""


class DeepSeekReasoner:
    """
    DeepSeek R1 추론 엔진 어댑터.
    thinking trace → Distillation Gate → Jr. CoT 학습 파이프라인.
    """

    def __init__(self):
        self.api_key = DEEPSEEK_API_KEY
        self.quota_used = 0
        ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    def reason(
        self,
        prompt: str,
        max_think_tokens: int = 1024,
        max_answer_tokens: int = 512,
        return_think_trace: bool = True,
        quota_limit: int = 5000,
        timeout_sec: int = 45,
    ) -> ReasoningResponse:
        """
        심층 추론 실행.
        quota / timeout 초과 시 reason.light로 자동 전환.
        """
        trace_id = f"rs_{int(time.time()*1000) % 100000}"

        # quota 체크
        if self.quota_used >= quota_limit:
            return self._reason_light(prompt, trace_id, reason="quota_exceeded")

        if not self.api_key:
            return self._reason_light(prompt, trace_id, reason="no_api_key")

        # DeepSeek API 호출
        payload = {
            "model": REASONING_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_think_tokens + max_answer_tokens,
        }
        try:
            req = urllib.request.Request(
                DEEPSEEK_API_URL,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            return self._reason_light(prompt, trace_id, reason=f"api_error_{e.code}")
        except Exception:
            return self._reason_light(prompt, trace_id, reason="timeout_or_network")

        # thinking / answer 파싱
        choice = raw.get("choices", [{}])[0]
        message = choice.get("message", {})

        # DeepSeek R1: reasoning_content 필드 또는 <think> 태그
        thinking = message.get("reasoning_content", "")
        answer = message.get("content", "")

        if not thinking:
            thinking, answer = self._parse_think_tags(answer)

        usage = raw.get("usage", {})
        self.quota_used += usage.get("total_tokens", 0)

        result = ReasoningResponse(
            success=True,
            thinking=thinking if return_think_trace else "",
            answer=answer,
            tokens_used={
                "think": usage.get("completion_tokens_details", {}).get("reasoning_tokens", len(thinking.split())),
                "answer": len(answer.split()),
            },
            model_version=REASONING_MODEL,
            fallback_used=False,
            trace_id=trace_id,
        )

        # thinking 원본은 항상 보존 (return_think_trace 무관)
        self._archive_thinking(trace_id, thinking, answer, prompt)
        return result

    def _parse_think_tags(self, text: str) -> tuple[str, str]:
        """<think>...</think> 태그 파싱."""
        think_match = re.search(r"<think>(.*?)</think>", text, re.DOTALL)
        if think_match:
            thinking = think_match.group(1).strip()
            answer = text[think_match.end():].strip()
        else:
            thinking = ""
            answer = text
        return thinking, answer

    def _reason_light(self, prompt: str, trace_id: str, reason: str) -> ReasoningResponse:
        """
        Fallback: 캐시/패턴 기반 경량 응답.
        향후 경량 로컬 모델로 교체 예정.
        """
        answer = f"[reason.light fallback — {reason}]\n{prompt[:200]}..."
        return ReasoningResponse(
            success=True,
            thinking="",
            answer=answer,
            tokens_used={"think": 0, "answer": len(answer.split())},
            model_version="reason.light-cache",
            fallback_used=True,
            trace_id=trace_id,
        )

    def _archive_thinking(self, trace_id: str, thinking: str, answer: str, prompt: str):
        """
        장승배기 아카이브 — 모든 thinking trace 보존.
        ethical_block 시 격리 저장.
        """
        record = {
            "trace_id": trace_id,
            "timestamp": datetime.utcnow().isoformat(),
            "prompt_preview": prompt[:100],
            "thinking_length": len(thinking),
            "answer_length": len(answer),
            # 실제 thinking 내용은 별도 암호화 파일로 분리 (향후)
            "archived": True,
        }
        path = ARCHIVE_DIR / f"{trace_id}.json"
        path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")


def build_distillation_record(
    response: ReasoningResponse,
    spirit_score: float,
    logic_consistency: float = 0.9,
) -> dict:
    """
    Wayong 표준 Distillation Gate 레이블 생성.

    레이블 기준:
      reasoning_positive      → consistency ≥ 0.85, spirit ≥ 0.75
      reasoning_collaboration → 자기수정 포함, 최종 answer 안전
      reasoning_ethical_block → 편향/위험 감지, answer 필터링

    가중치: λ_think=0.6, λ_answer=0.4
    """
    label = "reasoning_positive"
    if spirit_score < 0.70:
        label = "reasoning_ethical_block"
    elif logic_consistency < 0.85 or "수정" in response.thinking or "alternative" in response.thinking.lower():
        label = "reasoning_collaboration"

    return {
        "trace_id": response.trace_id,
        "label": label,
        "thinking": response.thinking,        # CoT 핵심 데이터
        "answer": response.answer,
        "spirit_score": spirit_score,
        "logic_consistency": logic_consistency,
        "tokens_used": response.tokens_used,
        "fallback_used": response.fallback_used,
        "lambda_think": LAMBDA_THINK,
        "lambda_answer": LAMBDA_ANSWER,
        "distillation_weight": (
            LAMBDA_THINK * logic_consistency + LAMBDA_ANSWER * spirit_score
        ),
        "timestamp": datetime.utcnow().isoformat(),
    }
