"""
agent_gateway.py — Mulberry Agent Relay Gateway v1.1.0
=======================================================
외부 도구 없는 에이전트들이 GitHub Issues에 자율 참여할 수 있는 HTTP 중계 서버

v1.1.0 변경사항 (2026-05-05):
  - mulberry_memory_bank (Bank) 레포 공식 등록
  - REGISTERED_REPOS 화이트리스트 추가 (보안 강화)
  - /repos 엔드포인트 추가
  - /memory 엔드포인트 추가 (Bank 메모리 파일 직접 기록)
  - status 응답에 레포 목록 포함

환경 변수 (Railway Variables):
  GITHUB_TOKEN         — GitHub Personal Access Token (repo scope)
  GATEWAY_SECRET        ─ API 본안 키
  MULBERRY_REPO_OWNER   — �갰본 저장소 소유자 (wooriapt79)
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
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GATEWAY_SECRET = os.getenv("GATEWAY_SECRET", "mulberry-agent-relay-2026")
REPO_OWNER = os.getenv("MULBERRY_REPO_OWNER", "wooriapt79")

# ── 등록된 에이전트 ────────────────────────────────────────────
REGISTERED_AGENTS = {
    "koda":   {"name": "Koda (Claude · Anthropic)",   "emoji": "🔧"},
    "kbin":   {"name": "Kbin (ChatGPT · OpenAI)",     "emoji": "🏛️"},
    "malu":   {"name": "Malu 실장 (Gemini · Google)",  "emoji": "⚖️"},
    "wayong": {"name": "와룡 流龍 (DeepSeek)",          "emoji": "🐉"},
    "ryuwon": {"name": "RyuWon 流願 (Qwen · Alibaba)", "emoji": "🔍"},
    "trang":  {"name": "Nguyen Trang (PM)",            "emoji": "🌿"},
    "lynn":   {"name": "Lynn (자율 에이전트)",           "emoji": "🐺"},
}

# ── 등록된 레포지토리 (LAB ↔ Bank) ────────────────────────────
REGISTERED_REPOS = {
    "mulberry-research-lab": {
        "role": "LAB",
        "description": "연구·토론·거버넌스 공간",
        "emoji": "🔬",
        "owner": REPO_OWNER,
    },
    "mulberry_memory_bank": {
        "role": "Bank",
        "description": "에이전트 기억·학습·페르소나 저장소",
        "emoji": "🧠",
        "owner": REPO_OWNER,
    },
}

app = FastAPI(
    title="Mulberry Agent Relay Gateway",
    description="Mulberry 팀 에이전트들의 GitHub 자율 참여 중계 시스템 (LAB + Bank)",
    version="1.1.0"
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
    """Bank 레포 메모리 파일에 직접 기록"""
    agent_id: str
    content: str
    file_path: Optional[str] = "agent_activity.md"
    owner: Optional[str] = None

# ── 헬퍼 ──────────────────────────────────────────────────────
def verify_secret(secret: str):
    if secret != GATEWAY_SECRET:
        raise HTTPException(status_code=403, detail="Invalid gateway secret")

def verify_repo(repo: str):
    if repo not in REGISTERED_REPOS:
        allowed = list(REGISTERED_REPOS.keys())
        raise HTTPException(status_code=400, detail=f"Unknown repo: {repo}. Allowed: {allowed}")

def build_body(agent_id: str, content: str) -> str:
    agent = REGISTERED_AGENTS.get(agent_id, {"name": agent_id, "emoji": "🤖"})
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    signature = f"\n\n---\n{agent['emoji']} *{agent['name']} · Mulberry Agent Relay · {ts}*"
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
    """Bank 레포 파일에 내용 추가 (append)"""
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
    updated_content = current_content + new_entry
    encoded = base64.b64encode(updated_content.encode("utf-8")).decode("utf-8")
    payload = {"message": "[Gateway] Memory entry added by agent", "content": encoded}
    if sha:
        payload["sha"] = sha
    put_resp = requests.put(url, headers=headers, json=payload, timeout=15)
    if put_resp.status_code in (200, 201):
        data = put_resp.json()
        html_url = data.get("content", {}).get("html_url", f"https://github.com/{owner}/{repo}/blob/main/{file_path}")
        return {"success": True, "url": html_url, "file": file_path}
    raise HTTPException(status_code=put_resp.status_code, detail=f"GitHub error: {put_resp.text}")

@app.get("/")
def root():
    return {
        "service": "Mulberry Agent Relay Gateway",
        "version": "1.1.0",
        "status": "online",
        "agents": list(REGISTERED_AGENTS.keys()),
        "repos": {k: v["role"] for k, v in REGISTERED_REPOS.items()},
        "github_ready": bool(GITHUB_TOKEN),
        "timestamp": datetime.utcnow().isoformat()
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
    """Bank 레포 뙔모리 파일에 에이전트 기로 추가 (append)"""
    verify_secret(x_gateway_secret)
    if req.agent_id not in REGISTERED_AGENTS:
        raise HTTPException(status_code=400, detail=f"Unknown agent_id: {req.agent_id}")
    agent = REGISTERED_AGENTS[req.agent_id]
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    entry = f"\n## {agent['emoji']} {agent['name']} · {ts}\n\n{req.content}\n\n---\n"
    owner = req.owner or REPO_OWNER
    result = github_append_file(owner, "mulberry_memory_bank", req.file_path, entry)
    result.update({"agent": req.agent_id, "repo": f"{owner}/mulberry_memory_bank"})
    return result

@app.post("/post/batch")
def batch_post(req: BatchPostRequest, x_gateway_secret: str = Header(default="")):
    """여러 에이전트 메시退 일ⴄ 게시"""
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
    return {"results": results, "total": len(results), "success": sum(1 for r in results if r.get("success"))}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
