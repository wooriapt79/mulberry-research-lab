# mulberry_connector/api/fastapi_app.py
"""
Mulberry Agent Execution API — 단일 진입점 (CSA Kbin 설계)

POST /v1/action/execute
    -> Spirit Score 검증 (류원)
    -> Hesitation 체크 (류원)
    -> Decision Code 결정 (Kbin)
    -> GitHub / SNS 게시

7개 에이전트 모두 이 하나의 API 사용.
agent 필드로 구분 — 개별 트리거 불필요.
"""

import os
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from core import PolicyEngine, Decision
from core.handoff import HandoffGate
from adapters.github import GitHubAdapter
from adapters.github_pr import GitHubPRAdapter, PR_SPIRIT_THRESHOLD
from adapters.sns import SNSAdapter
from core.tool_registry import ToolRegistry

app = FastAPI(
    title="Mulberry Connector API",
    description="Agent Execution Infrastructure — 'Systems where AI knows when NOT to act'",
    version="1.0.0",
)

GATEWAY_SECRET = os.environ.get("GATEWAY_SECRET", "mulberry-agent-relay-2026")
VALID_AGENTS = {"koda", "kbin", "malu", "wayong", "ryuwon", "trang", "lynn", "jr"}

policy = PolicyEngine()
handoff = HandoffGate()
github = GitHubAdapter()
github_pr = GitHubPRAdapter()
sns = SNSAdapter()
registry = ToolRegistry()


class ActionRequest(BaseModel):
    agent: str
    intent: str  # "github.comment" | "github.pr" | "sns.slack" | ...
    content: str
    repo: str = "wooriapt79/mulberry-research-lab"
    issue_number: int | None = None
    bypass_spirit: bool = False  # 비상 우회 (Spirit Score 무시)
    # github.pr 전용 필드
    pr_title: str | None = None
    pr_file_path: str | None = None
    pr_file_content: str | None = None
    pr_commit_message: str | None = None
    pr_draft: bool = True


class ActionResponse(BaseModel):
    decision: str
    status: str
    url: str = ""
    spirit_score: float = 0.0
    uncertainty: float = 0.0
    reason: str = ""


def _verify_secret(secret: str) -> None:
    if secret != GATEWAY_SECRET:
        raise HTTPException(status_code=401, detail="Invalid gateway secret")


@app.get("/status")
def status():
    reg_summary = registry.summary()
    return {
        "service": "Mulberry Connector API",
        "version": "1.1.0",
        "status": "online",
        "agents": sorted(VALID_AGENTS),
        "tool_registry": reg_summary,
    }


# ── Tool Registry 엔드포인트 ──────────────────────────────────────

@app.get("/v1/tools")
def list_all_tools():
    """전체 도구 목록 — 브랜드별 소유 및 공유 가능 여부 포함."""
    tools = registry.all_tools()
    return {
        "total": len(tools),
        "tools": [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "owner": t.owner,
                "borrowable_by": t.borrowable_by,
                "implemented": t.implemented,
                "risk_level": t.risk_level,
            }
            for t in tools
        ],
    }


@app.get("/v1/tools/agents/{agent_id}")
def agent_tool_card(agent_id: str):
    """
    특정 에이전트의 도구 카드.
    소유 도구 + 빌려 쓸 수 있는 도구 목록 반환.
    """
    if agent_id.lower() not in VALID_AGENTS:
        raise HTTPException(status_code=404, detail=f"Unknown agent: {agent_id}")
    return registry.agent_card(agent_id)


@app.get("/v1/tools/{tool_id}/can-use/{agent_id}")
def can_use_tool(tool_id: str, agent_id: str):
    """에이전트가 해당 도구를 사용할 수 있는지 확인."""
    tool = registry.get(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool not found: {tool_id}")
    can = registry.can_borrow(agent_id, tool_id)
    return {
        "agent": agent_id,
        "tool_id": tool_id,
        "can_use": can,
        "owner": tool.owner,
        "implemented": tool.implemented,
        "spirit_required": registry.spirit_required(tool_id),
        "reason": (
            "자신 소유" if tool.owner == agent_id.lower()
            else "공유 허용" if can
            else "미구현" if not tool.implemented
            else "공유 미허용"
        ),
    }


@app.post("/v1/action/execute", response_model=ActionResponse)
def execute(
    req: ActionRequest,
    x_gateway_secret: str = Header(default=""),
):
    _verify_secret(x_gateway_secret)

    # 에이전트 유효성
    if req.agent.lower() not in VALID_AGENTS:
        raise HTTPException(status_code=400, detail=f"Unknown agent: {req.agent}")

    # 0. Tool Registry — 도구 사용 권한 확인
    tool = registry.get(req.intent)
    if tool and not registry.can_borrow(req.agent, req.intent):
        return ActionResponse(
            decision="BLOCK",
            status="blocked",
            spirit_score=0.0,
            reason=(
                f"'{req.agent}'은 '{req.intent}' 도구를 사용할 권한이 없습니다. "
                f"소유자: {tool.owner} | 미구현: {not tool.implemented}"
            ),
        )

    # 1. Policy 검증 (Spirit + Hesitation)
    # Tool Registry 기준 Spirit threshold 적용
    min_spirit = registry.spirit_required(req.intent) if tool else 0.75
    result = policy.evaluate(req.content, req.intent, bypass=req.bypass_spirit)
    base_response = ActionResponse(
        decision=result.decision.value,
        spirit_score=result.spirit.score,
        uncertainty=result.hesitation.uncertainty,
        reason=result.reason,
        status="blocked",
    )

    # BLOCK / HUMAN_REVIEW / CONFIRM -> 실행 안 함
    if result.decision in (Decision.BLOCK, Decision.HUMAN_REVIEW):
        return base_response
    if result.decision == Decision.CONFIRM:
        base_response.status = "pending_confirmation"
        return base_response

    # 2. Handoff 검증
    hf = handoff.check(req.content, req.agent)
    if not hf.ready:
        base_response.decision = "CONFIRM"
        base_response.status = "handoff_incomplete"
        base_response.reason = " | ".join(hf.feedback)
        return base_response

    # 3. 실행
    if req.intent == "github.pr":
        # PR 생성 — Spirit Score 기준 더 높음 (0.85)
        if result.spirit.score < PR_SPIRIT_THRESHOLD and not req.bypass_spirit:
            base_response.status = "blocked"
            base_response.reason = f"PR 생성은 Spirit Score {PR_SPIRIT_THRESHOLD} 이상 필요 (현재: {result.spirit.score:.2f})"
            return base_response
        if not all([req.pr_title, req.pr_file_path, req.pr_file_content]):
            raise HTTPException(status_code=400, detail="github.pr 에는 pr_title, pr_file_path, pr_file_content 필수")
        pr_result = github_pr.create_pr(
            agent_id=req.agent,
            title=req.pr_title,
            body=req.content,
            file_path=req.pr_file_path,
            file_content=req.pr_file_content,
            commit_message=req.pr_commit_message or f"feat: {req.pr_title}",
            linked_issue=req.issue_number,
            draft=req.pr_draft,
        )
        base_response.status = "success" if pr_result.success else "error"
        base_response.url = pr_result.pr_url
        if not pr_result.success:
            base_response.reason = pr_result.error
    elif req.intent.startswith("github") and req.issue_number:
        post_result = github.post_comment(
            issue_number=req.issue_number,
            content=req.content,
            agent_id=req.agent,
            decision_code=result.decision.value,
        )
        base_response.status = "success" if post_result.success else "error"
        base_response.url = post_result.url
        if not post_result.success:
            base_response.reason = post_result.error
    elif req.intent.startswith("sns"):
        channel = req.intent.split(".")[-1]
        sns_result = sns.post(channel, req.content, req.agent)
        base_response.status = "success" if sns_result.success else "error"

    return base_response
