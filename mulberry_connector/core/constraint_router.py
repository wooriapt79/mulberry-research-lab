"""
Constraint-Aware Router — 제약 인식 라우터 (Issue #24 Phase 2)

Kbin 설계 개념:
  Gateway = 실행 통제 시스템
  → 도구 요청이 들어오면 제약 조건을 전부 확인하고
    실행 가능한 에이전트로 라우팅하거나 Fallback 처리.

판단 순서:
  1. 도구 존재 확인
  2. 에이전트 권한 확인 (ToolRegistry)
  3. Spirit Score 검증
  4. 파라미터 유효성 검사
  5. 실행 or Fallback 결정
  6. 결과 반환 + Checkpoint 저장
"""

import time
import json
import subprocess
from pathlib import Path
from dataclasses import dataclass

from core.tool_registry import ToolRegistry
from core.policy import PolicyEngine
from core.distillation_gate import DistillationGate
from mulberry_tools.schema import (
    MulberryToolCall,
    MulberryToolResult,
    ToolCallStatus,
    validate_params,
)


# ── Kbin 가이드 반영: 동적 라우팅 기반 구조 ──────────────────────
# 현재: 하드코딩 우선순위 (v1)
# 다음: 에이전트 컨디션(CPU/Mem/응답속도) 기반 가중치 라우팅 (v2 예정)
# v2 설계: agent_condition_score[agent] = f(cpu, mem, latency, spirit_avg)
#          → 가장 높은 score의 에이전트로 동적 라우팅

# Fallback 우선순위: 요청 에이전트가 실행 불가일 때 대신할 에이전트 목록
FALLBACK_PRIORITY: dict[str, list[str]] = {
    "terminal.exec":  ["koda"],
    "file.read":      ["koda"],
    "file.write":     ["koda"],
    "github.comment": ["koda"],
    "github.pr":      ["koda"],
    "code.exec":      ["koda", "kbin"],
    "web.search":     ["kbin"],
    "vision.analyze": ["malu"],
    "reason.deep":    ["wayong", "ryuwon"],
    "code.generate":  ["wayong", "koda"],
    "lang.multilingual": ["ryuwon"],
    "memory.read":    ["lynn"],
    "memory.write":   ["lynn"],
    "edge.infer":     ["jr"],
}

CHECKPOINT_DIR = Path(__file__).parent.parent.parent / "training_logs" / "tool_checkpoints"


@dataclass
class RouteDecision:
    execute: bool
    executor: str          # 실제 실행 에이전트
    fallback: bool
    reason: str
    spirit_score: float
    spirit_threshold: float


class ConstraintAwareRouter:
    """
    도구 요청의 모든 제약 조건을 확인하고
    실행 에이전트를 결정하는 라우터.
    """

    def __init__(self):
        self.registry = ToolRegistry()
        self.policy = PolicyEngine()
        self.distillation_gate = DistillationGate()

    def route(self, call: MulberryToolCall) -> RouteDecision:
        """제약 조건 확인 후 실행 결정."""

        # 1. 도구 존재 확인
        tool = self.registry.get(call.tool_id)
        if not tool:
            return RouteDecision(
                execute=False, executor="", fallback=False,
                reason=f"등록되지 않은 도구: {call.tool_id}",
                spirit_score=0.0, spirit_threshold=0.0,
            )

        # 2. 구현 여부 확인
        if not tool.implemented:
            return RouteDecision(
                execute=False, executor="", fallback=False,
                reason=f"'{call.tool_id}' 미구현 (소유자: {tool.owner}, 향후 연동 예정)",
                spirit_score=0.0, spirit_threshold=0.0,
            )

        # 3. 권한 확인
        can = self.registry.can_borrow(call.agent, call.tool_id)
        executor = call.agent
        fallback = False

        if not can:
            # Fallback: 실행 가능한 다른 에이전트로 라우팅
            fallback_agents = FALLBACK_PRIORITY.get(call.tool_id, [tool.owner])
            if fallback_agents:
                executor = fallback_agents[0]
                fallback = True
            else:
                return RouteDecision(
                    execute=False, executor="", fallback=False,
                    reason=f"'{call.agent}'은 '{call.tool_id}' 사용 권한 없음, fallback 없음",
                    spirit_score=0.0, spirit_threshold=0.0,
                )

        # 4. Spirit Score 검증
        threshold = self.registry.spirit_required(call.tool_id)
        spirit_result = self.policy.evaluate(
            call.context or call.tool_id,
            call.tool_id,
            bypass=call.bypass_spirit,
        )
        score = spirit_result.spirit.score

        if score < threshold and not call.bypass_spirit:
            return RouteDecision(
                execute=False, executor=executor, fallback=fallback,
                reason=f"Spirit Score 부족: {score:.2f} < {threshold} (도구: {call.tool_id})",
                spirit_score=score, spirit_threshold=threshold,
            )

        return RouteDecision(
            execute=True, executor=executor, fallback=fallback,
            reason="OK" if not fallback else f"Fallback: {call.agent} → {executor}",
            spirit_score=score, spirit_threshold=threshold,
        )

    def execute(self, call: MulberryToolCall) -> MulberryToolResult:
        """라우팅 후 실행까지 처리하는 통합 메서드."""
        t0 = time.monotonic()

        # 파라미터 유효성 검사
        valid, err = validate_params(call.tool_id, call.params)
        if not valid:
            return MulberryToolResult(
                call_id=call.call_id, agent=call.agent, tool_id=call.tool_id,
                status=ToolCallStatus.ERROR, reason=f"파라미터 오류: {err}",
            )

        # 라우팅 결정
        decision = self.route(call)

        if not decision.execute:
            status = (
                ToolCallStatus.BLOCKED_SPIRIT if "Spirit" in decision.reason
                else ToolCallStatus.BLOCKED_PERM if "권한" in decision.reason
                else ToolCallStatus.BLOCKED_IMPL if "미구현" in decision.reason
                else ToolCallStatus.ERROR
            )
            blocked_result = MulberryToolResult(
                call_id=call.call_id, agent=call.agent, tool_id=call.tool_id,
                status=status, reason=decision.reason,
                spirit_score=decision.spirit_score,
                spirit_threshold=decision.spirit_threshold,
                executed_by=decision.executor,
            )
            # Phase 3: 차단된 케이스도 Distillation Gate에 기록 (Jr. 윤리 훈련 핵심 데이터)
            self.distillation_gate.record(blocked_result, original_context=call.context)
            return blocked_result

        # 실행
        result_data, error = self._dispatch(call)
        duration = (time.monotonic() - t0) * 1000

        if error:
            # Checkpoint 저장 (재개 가능)
            ckpt_id = self._save_checkpoint(call, decision)
            return MulberryToolResult(
                call_id=call.call_id, agent=call.agent, tool_id=call.tool_id,
                status=ToolCallStatus.CHECKPOINT,
                reason=f"실행 실패 → checkpoint 저장: {error}",
                checkpoint_id=ckpt_id,
                executed_by=decision.executor,
                spirit_score=decision.spirit_score,
                spirit_threshold=decision.spirit_threshold,
                duration_ms=duration,
            )

        status = ToolCallStatus.FALLBACK if decision.fallback else ToolCallStatus.SUCCESS
        final_result = MulberryToolResult(
            call_id=call.call_id, agent=call.agent, tool_id=call.tool_id,
            status=status, result=result_data,
            executed_by=decision.executor,
            fallback_agent=decision.executor if decision.fallback else None,
            spirit_score=decision.spirit_score,
            spirit_threshold=decision.spirit_threshold,
            reason=decision.reason,
            duration_ms=duration,
        )
        # Phase 3: 모든 실행 결과를 Distillation Gate에 기록
        self.distillation_gate.record(final_result, original_context=call.context)
        return final_result

    def _dispatch(self, call: MulberryToolCall) -> tuple[any, str]:
        """도구 ID에 따라 실제 실행 핸들러 호출."""
        try:
            if call.tool_id == "terminal.exec":
                return self._exec_terminal(call.params), ""
            elif call.tool_id == "file.read":
                return self._exec_file_read(call.params), ""
            elif call.tool_id == "file.write":
                return self._exec_file_write(call.params), ""
            elif call.tool_id == "code.exec":
                return self._exec_code(call.params), ""
            else:
                # github.comment / github.pr 는 기존 어댑터가 처리
                return {"routed": True, "tool_id": call.tool_id}, ""
        except Exception as e:
            return None, str(e)

    def _exec_terminal(self, params: dict) -> dict:
        cmd = params.get("command", "")
        cwd = params.get("cwd", ".")
        timeout = params.get("timeout_sec", 30)
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            cwd=cwd, timeout=timeout
        )
        return {
            "stdout": result.stdout[:2000],
            "stderr": result.stderr[:500],
            "returncode": result.returncode,
        }

    def _exec_file_read(self, params: dict) -> dict:
        path = Path(params.get("path", ""))
        encoding = params.get("encoding", "utf-8")
        content = path.read_text(encoding=encoding)
        return {"path": str(path), "content": content[:5000], "size": len(content)}

    def _exec_file_write(self, params: dict) -> dict:
        path = Path(params.get("path", ""))
        content = params.get("content", "")
        encoding = params.get("encoding", "utf-8")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding=encoding)
        return {"path": str(path), "bytes_written": len(content.encode())}

    def _exec_code(self, params: dict) -> dict:
        code = params.get("code", "")
        timeout = params.get("timeout_sec", 30)
        result = subprocess.run(
            ["python3", "-c", code],
            capture_output=True, text=True, timeout=timeout
        )
        return {
            "stdout": result.stdout[:2000],
            "stderr": result.stderr[:500],
            "returncode": result.returncode,
        }

    def _save_checkpoint(self, call: MulberryToolCall, decision: RouteDecision) -> str:
        """실패한 작업을 checkpoint로 저장 — 재개 가능."""
        CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
        ckpt = {
            "call_id": call.call_id,
            "agent": call.agent,
            "tool_id": call.tool_id,
            "params": call.params,
            "context": call.context,
            "executor": decision.executor,
            "saved_at": MulberryToolCall.__fields__["timestamp"].default_factory(),
            "resolved": False,
        }
        path = CHECKPOINT_DIR / f"{call.call_id}.json"
        path.write_text(json.dumps(ckpt, ensure_ascii=False, indent=2), encoding="utf-8")
        return call.call_id
