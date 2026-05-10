"""
MulberryToolCall — 도구 호출 표준 스키마 (Kbin 설계 / Koda 구현)

Issue #24: [RFC] 도구 공유 레이어: MCP를 넘어선 실행 민주화 인프라

모든 에이전트가 도구를 요청할 때 이 스키마 하나를 사용한다.
MCP가 연결만 한다면, MulberryToolCall은 실행 전 판단까지 담는다.

  실행판단 → 제약관리 → 윤리검증 → 상태유지 → 중단/재개 → 공유실행
"""

import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


# ── 요청 ─────────────────────────────────────────────────────────

class MulberryToolCall(BaseModel):
    """도구 호출 표준 요청 스키마."""

    call_id: str = Field(
        default_factory=lambda: str(uuid.uuid4())[:8],
        description="호출 고유 ID (자동 생성)"
    )
    agent: str = Field(
        description="요청 에이전트 ID (koda / malu / ryuwon / ...)"
    )
    tool_id: str = Field(
        description="tool_registry.yaml 에 등록된 도구 ID (예: terminal.exec)"
    )
    params: dict[str, Any] = Field(
        default_factory=dict,
        description="도구별 파라미터 (tool_id에 따라 다름)"
    )
    context: str = Field(
        default="",
        description="이 도구가 왜 필요한가 — Spirit Score 판단 근거"
    )
    checkpoint_id: str | None = Field(
        default=None,
        description="중단된 작업 재개 시 이전 checkpoint_id"
    )
    bypass_spirit: bool = Field(
        default=False,
        description="Spirit Score 우회 (긴급 상황, 관리자 전용)"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )


# ── 응답 ─────────────────────────────────────────────────────────

class ToolCallStatus:
    SUCCESS          = "success"
    BLOCKED_SPIRIT   = "blocked_spirit"      # Spirit Score 미달
    BLOCKED_PERM     = "blocked_permission"  # 공유 미허용
    BLOCKED_IMPL     = "blocked_not_impl"    # 미구현 도구
    FALLBACK         = "fallback"            # 대체 에이전트로 라우팅
    CHECKPOINT       = "checkpoint"          # 중단 저장
    ERROR            = "error"


class MulberryToolResult(BaseModel):
    """도구 호출 결과 스키마."""

    call_id: str
    agent: str
    tool_id: str
    status: str                         # ToolCallStatus 값
    result: Any = None                  # 도구 실행 결과
    executed_by: str = ""               # 실제 실행한 에이전트 (공유 시 owner)
    spirit_score: float = 0.0
    spirit_threshold: float = 0.0
    fallback_agent: str | None = None   # fallback 라우팅된 경우
    checkpoint_id: str | None = None    # 상태 저장된 경우
    reason: str = ""
    duration_ms: float = 0.0
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )


# ── 파라미터 서브스키마 (도구별) ────────────────────────────────

class TerminalExecParams(BaseModel):
    """terminal.exec 파라미터"""
    command: str
    cwd: str = "."
    timeout_sec: int = 30


class FileReadParams(BaseModel):
    """file.read 파라미터"""
    path: str
    encoding: str = "utf-8"


class FileWriteParams(BaseModel):
    """file.write 파라미터"""
    path: str
    content: str
    encoding: str = "utf-8"


class GitHubCommentParams(BaseModel):
    """github.comment 파라미터"""
    issue_number: int
    content: str
    repo: str = "wooriapt79/mulberry-research-lab"


class GitHubPRParams(BaseModel):
    """github.pr 파라미터"""
    title: str
    body: str
    file_path: str
    file_content: str
    commit_message: str
    issue_number: int | None = None
    draft: bool = True


class CodeExecParams(BaseModel):
    """code.exec 파라미터"""
    code: str
    language: str = "python"
    timeout_sec: int = 30


# ── 파라미터 유효성 검사 헬퍼 ────────────────────────────────────

PARAM_SCHEMAS: dict[str, type] = {
    "terminal.exec":   TerminalExecParams,
    "file.read":       FileReadParams,
    "file.write":      FileWriteParams,
    "github.comment":  GitHubCommentParams,
    "github.pr":       GitHubPRParams,
    "code.exec":       CodeExecParams,
}


def validate_params(tool_id: str, params: dict) -> tuple[bool, str]:
    """
    tool_id에 맞는 파라미터 스키마로 유효성 검사.
    Returns (valid: bool, error_message: str)
    """
    schema = PARAM_SCHEMAS.get(tool_id)
    if not schema:
        return True, ""  # 미정의 도구는 통과 (향후 확장)
    try:
        schema(**params)
        return True, ""
    except Exception as e:
        return False, str(e)
