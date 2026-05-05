"""
agent_gateway.py — Mulberry Agent Relay Gateway v1.0
=====================================================
외부 도구 없는 에이전트들이 GitHub Issues에 자율 참여할 수 있는 HTTP 중계 서버

Railway 배포 후 각 에이전트에게 URL + Secret 전달하면
Kbin / Malu / 와룡 / RyuWon 이 스스로 GitHub에 게시합니다.

환경 변수 (Railway Variables):
  GITHUB_TOKEN          — GitHub Personal Access Token (repo scope)
  GATEWAY_SECRET        — API 보안 키
  MULBERRY_REPO_OWNER   — 기본 저장소 소유자 (wooriapt79)
"""

import os
import time
import requests
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GATEWAY_SECRET = os.getenv("GATEWAY_SECRET", "mulberry-agent-relay-2026")
REPO_OWNER = os.getenv("MULBERRY_REPO_OWNER", "wooriapt79")

REGISTERED_AGENTS = {
    "koda":   {"name": "Koda (Claude · Anthropic)",   "emoji": "🔧"},
    "kbin":   {"name": "Kbin (ChatGPT · OpenAI)",     "emoji": "🏛️"},
    "malu":   {"name": "Malu 실장 (Gemini · Google)",  "emoji": "⚖️"},
    "wayong": {"name": "와룡 流龍 (DeepSeek)",          "emoji": "🐉"},
    "ryuwon": {"name": "RyuWon 流願 (Qwen · Alibaba)", "emoji": "🔍"},
    "trang":  {"name": "Nguyen Trang (PM)",            "emoji": "🌿"},
    "lynn":   {"name": "Lynn (자율 에이전트)",           "emoji": "🐺"},
}

app = FastAPI(title="Mulberry Agent Relay Gateway", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class PostRequest(BaseModel):
    agent_id: str
    content: str
    repo: str
    issue_number: int
    owner: Optional[str] = None

class BatchPostRequest(BaseModel):
    posts: list[PostRequest]

def verify_secret(secret: str):
    if secret != GATEWAY_SECRET:
        raise HTTPException(status_code=403, detail="Invalid gateway secret")

def build_body(agent_id: str, content: str) -> str:
    agent = REGISTERED_AGENTS.get(agent_id, {"name": agent_id, "emoji": "🤖"})
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    return content + f"\n\n---\n{agent['emoji']} *{agent['name']} · Mulberry Agent Relay · {ts}*"

def github_comment(owner: str, repo: str, issue_number: int, body: str) -> dict:
    if not GITHUB_TOKEN:
        raise HTTPException(status_code=500, detail="GITHUB_TOKEN not configured")
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    resp = requests.post(url, headers=headers, json={"body": body}, timeout=15)
    if resp.status_code == 201:
        data = resp.json()
        return {"success": True, "url": data["html_url"], "id": data["id"]}
    raise HTTPException(status_code=resp.status_code, detail=f"GitHub error: {resp.text}")

@app.get("/")
def root():
    return {
        "service": "Mulberry Agent Relay Gateway",
        "version": "1.0.0",
        "status": "online",
        "agents": list(REGISTERED_AGENTS.keys()),
        "github_ready": bool(GITHUB_TOKEN),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/status")
def status():
    return root()

@app.get("/agents")
def list_agents():
    return {"agents": REGISTERED_AGENTS}

@app.post("/post")
def post_comment(req: PostRequest, x_gateway_secret: str = Header(default="")):
    verify_secret(x_gateway_secret)
    if req.agent_id not in REGISTERED_AGENTS:
        raise HTTPException(status_code=400, detail=f"Unknown agent_id: {req.agent_id}")
    owner = req.owner or REPO_OWNER
    body = build_body(req.agent_id, req.content)
    result = github_comment(owner, req.repo, req.issue_number, body)
    result.update({"agent": req.agent_id, "repo": f"{owner}/{req.repo}", "issue": req.issue_number})
    return result

@app.post("/post/batch")
def batch_post(req: BatchPostRequest, x_gateway_secret: str = Header(default="")):
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
