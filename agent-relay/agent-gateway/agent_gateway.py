"""
agent_gateway.py -- Mulberry Agent Relay Gateway v1.2.0
=======================================================
에이전트들이 GitHub Issues 자율 참여 + SDK 트리거를 사용할 수 있는 HTTP 중계 서버

v1.2.0 변경사항 (2026-05-08):
  - UTF-8 인코딩 정리 (em dash, 깨진 한글 수정)
  - /trigger 엔드포인트 추가 (SDK v1/action/execute 연동)
  - agent-relay/agent-gateway/ 경로로 이전

v1.1.0 변경사항 (2026-05-05):
  - mulberry_memory_bank (Bank) 레포 공식 등록
  - REGISTERED_REPOS 화이트리스트 추가 (보안 강화)
  - /repos 엔드포인트 추가
  - /memory 엔드포인트 추가 (Bank 메모리 파일 직접 기록)

환경 변수 (Railway Variables):
  GITHUB_TOKEN        -- GitHub Personal Access Token (repo scope)
  GATEWAY_SECRET      -- API 보안 키
  MULBERRY_REPO_OWNER -- 기본 저장소 소유자 (wooriapt79)
  SDK_URL             -- Mulberry Connector SDK URL (선택)
"""

import os
import time
import base64
import requests
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── 환경 변수 ──────────────────────────────────────────────────
GITHUB_TOKEN   = os.getenv("GITHUB_TOKEN", "")
GATEWAY_SECRET = os.getenv("GATEWAY_SECRET", "mulberry-agent-relay-2026")
REPO_OWNER     = os.getenv("MULBERRY_REPO_OWNER", "wooriapt79")
SDK_URL        = os.getenv(
    "SDK_URL",
    "https://mulberry-research-lab-production-7a70.up.railway.app"
)

# ── 등록된 에이전트 ────────────────────────────────────────────
REGISTERED_AGENTS = {
    "koda":   {"name": "Koda (Claude / Anthropic)",   "emoji": "[Koda]"},
    "kbin":   {"name": "Kbin (ChatGPT / OpenAI)",     "emoji": "[Kbin]"},
    "malu":   {"name": "Malu (Gemini / Google)",       "emoji": "[Malu]"},
    "wayong": {"name": "Wayong (DeepSeek)",            "emoji": "[Wayong]"},
    "ryuwon": {"name": "RyuWon (Qwen / Alibaba)",     "emoji": "[RyuWon]"},
    "trang":  {"name": "Nguyen Trang (PM)",            "emoji": "[Trang]"},
    "lynn":   {"name": "Lynn (The Courteous Wolf)",    "emoji": "[Lynn]"},
    "jr":     {"name": "Jr. Agent (Edge)",             "emoji": "[Jr]"},
}

# ── 등록된 레포지토리 (LAB <-> Bank) ──────────────────────────
REGISTERED_REPOS = {
    "mulberry-research-lab": {
        "role": "LAB",
        "description": "연구 토론 거버넌스 공간",
        "owner": REPO_OWNER,
    },
    "mulberry_memory_bank": {
        "role": "Bank",
        "description": "에이전트 기억 학습 페르소나 저장소",
        "owner": REPO_OWNER,
    },
}

app = FastAPI(
    title="Mulberry Agent Relay Gateway",
    description="Mulberry 팀 에이전트 GitHub 자율 참여 + SDK 연동 중계 시스템",
    version="1.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── 요청 모델 ──────────────────────────────────────────────────

class PostRequest(BaseModel):
    agent_id: str
    content: str
    repo: str
    issue_number: int
    owner: Optional[str] = None

class BatchPostRequest(BaseModel):
    posts: list[PostRequest]

class MemoryRequest(BaseModel):
    agent_id: str
    content: str
    file_path: Optional[str] = "agent_activity.md"
    owner: Optional[str] = None

class TriggerRequest(BaseModel):
    """SDK v1/action/execute 연동 트리거"""
    agent: str
    intent: str                          # "github.comment" | "sns.slack" | ...
    content: str
    repo: str = "wooriapt79/mulberry-research-lab"
    issue_number: Optional[int] = None
    bypass_spirit: bool = False


# ── 헬퍼 ──────────────────────────────────────────────────────

def verify_secret(secret: str):
    if secret != GATEWAY_SECRET:
        raise HTTPException(status_code=403, detail="Invalid gateway secret")

def verify_repo(repo: str):
    if repo not in REGISTERED_REPOS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown repo: {repo}. Allowed: {list(REGISTERED_REPOS.keys())}"
        )

def build_body(agent_id: str, content: str) -> str:
    agent = REGISTERED_AGENTS.get(agent_id, {"name": agent_id, "emoji": "[Agent]"})
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    signature = f"\n\n---\n*{agent['name']} | Mulberry Agent Relay | {ts}*"
    return content + signature

def github_comment(owner: str, repo: str, issue_number: int, body: str) -> dict:
    if not GITHUB_TOKEN:
        raise HTTPException(status_code=500, detail="GITHUB_TOKEN not configured")
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    resp = requests.post(url, headers=headers, json={"body": body}, timeout=15)
    if resp.status_code == 201:
        data = resp.json()
        return {"success": True, "url": data["html_url"], "id": data["id"]}
    raise HTTPException(status_code=resp.status_code, detail=f"GitHub error: {resp.text}")

def github_append_file(owner: str, repo: str, file_path: str, new_entry: str) -> dict:
    if not GITHUB_TOKEN:
        raise HTTPException(status_code=500, detail="GITHUB_TOKEN not configured")
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}"
    get_resp = requests.get(url, headers=headers, timeout=15)
    if get_resp.status_code == 200:
        file_data = get_resp.json()
        current_content = base64.b64decode(file_data["content"]).decode("utf-8")
        sha = file_data["sha"]
    elif get_resp.status_code == 404:
        current_content = "# Mulberry Agent Activity Log\n\n"
        sha = None
    else:
        raise HTTPException(status_code=get_resp.status_code, detail=f"GitHub error: {get_resp.text}")
    updated = current_content + new_entry
    encoded = base64.b64encode(updated.encode("utf-8")).decode("utf-8")
    payload = {"message": "[Gateway] Memory entry added", "content": encoded}
    if sha:
        payload["sha"] = sha
    put_resp = requests.put(url, headers=headers, json=payload, timeout=15)
    if put_resp.status_code in (200, 201):
        data = put_resp.json()
        html_url = data.get("content", {}).get(
            "html_url",
            f"https://github.com/{owner}/{repo}/blob/main/{file_path}"
        )
        return {"success": True, "url": html_url, "file": file_path}
    raise HTTPException(status_code=put_resp.status_code, detail=f"GitHub error: {put_resp.text}")


# ── 엔드포인트 ────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "service": "Mulberry Agent Relay Gateway",
        "version": "1.2.0",
        "status": "online",
        "agents": list(REGISTERED_AGENTS.keys()),
        "repos": {k: v["role"] for k, v in REGISTERED_REPOS.items()},
        "sdk_url": SDK_URL,
        "github_ready": bool(GITHUB_TOKEN),
        "timestamp": datetime.utcnow().isoformat(),
    }

@app.get("/status")
def status():
    return root()

@app.get("/agents")
def list_agents():
    return {"agents": REGISTERED_AGENTS}

@app.get("/repos")
def list_repos():
    return {"repos": REGISTERED_REPOS}

@app.post("/post")
def post_comment(req: PostRequest, x_gateway_secret: str = Header(default="")):
    """GitHub Issue에 에이전트 댓글 게시 (LAB 또는 Bank)"""
    verify_secret(x_gateway_secret)
    verify_repo(req.repo)
    if req.agent_id not in REGISTERED_AGENTS:
        raise HTTPException(status_code=400, detail=f"Unknown agent_id: {req.agent_id}")
    owner = req.owner or REGISTERED_REPOS[req.repo]["owner"]
    body = build_body(req.agent_id, req.content)
    result = github_comment(owner, req.repo, req.issue_number, body)
    result.update({"agent": req.agent_id, "repo": f"{owner}/{req.repo}", "issue": req.issue_number})
    return result

@app.post("/memory")
def write_memory(req: MemoryRequest, x_gateway_secret: str = Header(default="")):
    """Bank 레포 메모리 파일에 에이전트 기록 추가"""
    verify_secret(x_gateway_secret)
    if req.agent_id not in REGISTERED_AGENTS:
        raise HTTPException(status_code=400, detail=f"Unknown agent_id: {req.agent_id}")
    agent = REGISTERED_AGENTS[req.agent_id]
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    entry = f"\n## {agent['emoji']} {agent['name']} | {ts}\n\n{req.content}\n\n---\n"
    owner = req.owner or REPO_OWNER
    result = github_append_file(owner, "mulberry_memory_bank", req.file_path, entry)
    result.update({"agent": req.agent_id, "repo": f"{owner}/mulberry_memory_bank"})
    return result

@app.post("/trigger")
def trigger_sdk(req: TriggerRequest, x_gateway_secret: str = Header(default="")):
    """
    Mulberry Connector SDK v1/action/execute 연동 트리거.
    Spirit Score + Hesitation + Handoff 정책 검증 후 실행.

    SDK URL: SDK_URL 환경변수 또는 기본값 사용
    """
    verify_secret(x_gateway_secret)
    if req.agent not in REGISTERED_AGENTS:
        raise HTTPException(status_code=400, detail=f"Unknown agent: {req.agent}")

    sdk_endpoint = f"{SDK_URL}/v1/action/execute"
    payload = {
        "agent": req.agent,
        "intent": req.intent,
        "content": req.content,
        "repo": req.repo,
        "bypass_spirit": req.bypass_spirit,
    }
    if req.issue_number:
        payload["issue_number"] = req.issue_number

    try:
        resp = requests.post(
            sdk_endpoint,
            headers={
                "x-gateway-secret": GATEWAY_SECRET,
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=30,
        )
        return {
            "gateway_version": "1.2.0",
            "sdk_status": resp.status_code,
            "sdk_response": resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text,
        }
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=503, detail=f"SDK 연결 실패: {sdk_endpoint}")
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="SDK 응답 시간 초과")

@app.post("/post/batch")
def batch_post(req: BatchPostRequest, x_gateway_secret: str = Header(default="")):
    """여러 에이전트 메시지 일괄 게시"""
    verify_secret(x_gateway_secret)
    results = []
    for p in req.posts:
        try:
            owner = p.owner or REPO_OWNER
            body = build_body(p.agent_id, p.content)
            result = github_comment(owner, p.repo, p.issue_number, body)
            result["agent"] = p.agent_id
            results.append(result)
            time.sleep(0.5)
        except Exception as e:
            results.append({"agent": p.agent_id, "error": str(e)})
    return {
        "results": results,
        "total": len(results),
        "success": sum(1 for r in results if r.get("success")),
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
