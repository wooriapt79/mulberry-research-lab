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
from adapters.sns import SNSAdapter

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
sns = SNSAdapter()


class ActionRequest(BaseModel):
    agent: str
    intent: str  # "github.comment" | "sns.slack" | ...
    content: str
    repo: str = "wooriapt79/mulberry-research-lab"
    issue_number: int | None = None
    bypass_spirit: bool = False  # 비상 우회 (Spirit Score 무시)


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
    return {
        "service": "Mulberry Connector API",
        "version": "1.0.0",
        "status": "online",
        "agents": sorted(VALID_AGENTS),
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

    # 1. Policy 검증 (Spirit + Hesitation)
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
    if req.intent.startswith("github") and req.issue_number:
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
