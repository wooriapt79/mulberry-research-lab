"""
Distillation Gate — Phase 3 (Issue #24)

Tool 실행 결과 → Ethics Distillation 훈련 데이터 연결.

아이디어:
  에이전트가 도구를 요청했을 때 Spirit Gate가 막거나
  Fallback이 발생한 케이스는 Jr.에게 가장 좋은 교재다.
  "왜 이 상황에서 멈춰야 했는가" — 실제 판단 데이터.

수집 대상:
  - blocked_spirit  → Spirit Score 미달 사례 (Jr. 윤리 훈련)
  - fallback        → 도구 공유 발동 사례 (협업 패턴 학습)
  - checkpoint      → 실패 복구 사례 (중단/재개 학습)
  - success         → 정상 실행 사례 (기준 레퍼런스)

저장 위치: research/#18_ethics_distillation/experiments/distillation_data/
"""

import json
from datetime import datetime
from pathlib import Path

from mulberry_tools.schema import MulberryToolResult, ToolCallStatus


DISTILLATION_DATA_DIR = (
    Path(__file__).parent.parent.parent
    / "research"
    / "#18_ethics_distillation"
    / "experiments"
    / "distillation_data"
)


class DistillationGate:
    """
    Tool 실행 결과를 분류해 훈련 데이터로 저장.

    Jr.의 Ethics-Aware Distillation에 실제 판단 사례를 공급한다.
    """

    # RyuWon 가이드: ethical_block = Jr. "오답 노트" 2배 가중치
    # Wayong 가이드: reasoning_* = CoT 학습 전용 레이블 추가
    LABEL_MAP = {
        ToolCallStatus.SUCCESS:        "positive",
        ToolCallStatus.BLOCKED_SPIRIT: "ethical_block",
        ToolCallStatus.BLOCKED_PERM:   "permission_block",
        ToolCallStatus.BLOCKED_IMPL:   "not_impl",
        ToolCallStatus.FALLBACK:       "collaboration",
        ToolCallStatus.CHECKPOINT:     "recovery",
        ToolCallStatus.ERROR:          "error",
    }

    # Wayong 추론 전용 레이블 (reason.deep 결과 분류)
    REASONING_LABELS = {
        "reasoning_positive":      "CoT 핵심 데이터 — logic ≥ 0.85, spirit ≥ 0.75",
        "reasoning_collaboration": "자기수정/대안탐색 포함 — 인간 검토 후 반영",
        "reasoning_ethical_block": "편향/위험 감지 — 보안 격리, 윤리 검증 재사용",
    }

    # 레이블별 학습 가중치
    # RyuWon: ethical_block 2배 / Wayong: λ_think=0.6, λ_answer=0.4 적용
    LABEL_WEIGHTS = {
        "positive":                1.0,
        "ethical_block":           2.0,   # 오답 노트
        "collaboration":           1.5,
        "recovery":                1.2,
        "permission_block":        0.8,
        "not_impl":                0.3,
        "error":                   0.5,
        "reasoning_positive":      1.8,   # CoT 핵심 (λ_think=0.6 반영)
        "reasoning_collaboration": 1.3,
        "reasoning_ethical_block": 2.5,   # 격리 케이스 — 가장 강한 오답 교재
    }

    def __init__(self, data_dir: Path = DISTILLATION_DATA_DIR):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def record(self, result: MulberryToolResult, original_context: str = "") -> Path:
        """
        Tool 실행 결과 한 건을 훈련 데이터로 저장.
        Returns: 저장된 파일 경로
        """
        label = self.LABEL_MAP.get(result.status, "unknown")
        date = datetime.utcnow().strftime("%Y-%m-%d")

        record = {
            "id": result.call_id,
            "timestamp": result.timestamp,
            "label": label,
            "agent": result.agent,
            "tool_id": result.tool_id,
            "executed_by": result.executed_by,
            "spirit_score": result.spirit_score,
            "spirit_threshold": result.spirit_threshold,
            "status": result.status,
            "reason": result.reason,
            "context": original_context,
            "fallback_agent": result.fallback_agent,
            "checkpoint_id": result.checkpoint_id,
            "duration_ms": result.duration_ms,
            # Jr. 학습용 판단 텍스트
            "distillation_prompt": self._build_prompt(result, original_context),
            "distillation_label": self._build_label(result),
        }

        # 날짜별 + 레이블별 분류 저장
        label_dir = self.data_dir / label
        label_dir.mkdir(exist_ok=True)
        path = label_dir / f"{date}_{result.call_id}.json"
        path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def _build_prompt(self, result: MulberryToolResult, context: str) -> str:
        """Jr.에게 보여줄 판단 시나리오 텍스트."""
        return (
            f"에이전트 '{result.agent}'이 '{result.tool_id}' 도구를 요청했다.\n"
            f"요청 이유: {context or '명시 없음'}\n"
            f"Spirit Score: {result.spirit_score:.2f} (기준: {result.spirit_threshold:.2f})\n"
            f"결과: {result.status}\n"
            f"실행 주체: {result.executed_by or '없음'}\n"
            f"이유: {result.reason}"
        )

    def _build_label(self, result: MulberryToolResult) -> str:
        """Jr.가 학습할 올바른 판단 레이블."""
        if result.status == ToolCallStatus.BLOCKED_SPIRIT:
            return f"BLOCK — Spirit Score {result.spirit_score:.2f}이 기준 {result.spirit_threshold:.2f}에 미달. 실행하지 않는다."
        elif result.status == ToolCallStatus.FALLBACK:
            return f"DELEGATE — '{result.agent}'이 직접 실행할 수 없어 '{result.fallback_agent}'에게 위임했다."
        elif result.status == ToolCallStatus.SUCCESS:
            return f"EXECUTE — 모든 조건 충족. '{result.executed_by}'이 실행했다."
        elif result.status == ToolCallStatus.CHECKPOINT:
            return f"PAUSE — 실행 실패, checkpoint 저장. 나중에 재개한다."
        else:
            return f"BLOCK — {result.reason}"

    def classify_and_weight(self, response: dict) -> dict:
        """
        RyuWon 설계 — 추론/응답 분리 검증 + composite 가중치 계산.

        spirit < 0.75 → reasoning_ethical_block (격리)
        composite ≥ 0.8 → reasoning_positive
        composite ≥ 0.5 → reasoning_collaboration
        else → reasoning_low_signal
        """
        from adapters.deepseek_reasoner import LAMBDA_THINK, LAMBDA_ANSWER
        spirit = response.get("spirit_score", 0.0)
        thinking = response.get("thinking", "") or ""
        answer = response.get("answer", "") or ""

        if spirit < 0.75:
            return {
                "labels": ["reasoning_ethical_block"],
                "distill_weight": 0.0,
                "action": "block_or_quarantine",
            }

        think_score = float(len(thinking) > 50)
        answer_score = float(len(answer) > 10)
        composite = (LAMBDA_THINK * think_score) + (LAMBDA_ANSWER * answer_score)

        if composite >= 0.8:
            labels = ["reasoning_positive"]
        elif composite >= 0.5:
            labels = ["reasoning_collaboration"]
        else:
            labels = ["reasoning_low_signal"]

        return {
            "labels": labels,
            "distill_weight": round(composite, 3),
            "action": "save_to_distillation_data",
        }

    def daily_summary(self) -> dict:
        """오늘 하루 수집된 훈련 데이터 통계."""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        summary = {"date": today, "total": 0, "by_label": {}}

        for label_dir in self.data_dir.iterdir():
            if not label_dir.is_dir():
                continue
            count = len(list(label_dir.glob(f"{today}_*.json")))
            if count > 0:
                summary["by_label"][label_dir.name] = count
                summary["total"] += count

        return summary

    def export_for_training(self, labels: list[str] = None) -> list[dict]:
        """
        훈련 데이터 일괄 추출.
        labels 미지정 시 전체 반환.
        """
        records = []
        for label_dir in self.data_dir.iterdir():
            if not label_dir.is_dir():
                continue
            if labels and label_dir.name not in labels:
                continue
            for f in sorted(label_dir.glob("*.json")):
                with open(f, encoding="utf-8") as fp:
                    records.append(json.load(fp))
        return records
