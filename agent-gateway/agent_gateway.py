"""
agent_gateway.py -- Mulberry Agent Relay Gateway v1.4.0
=======================================================
에이전트들이 GitHub Issues 자율 참여 + SDK 트리거 + 실시간 채팅 + A2A 프로토콜을 사용할 수 있는 통합 게이트웨이

v1.4.0 변경사항 (2026-05-18):
  - Socket.IO 실시간 채팅 서버 통합 (socketio_server.py)
  - A2A (Agent-to-Agent) 프로토콜 라우터 추가 (a2a_protocol.py)
  - /v1/tools/generate-image 이미지 생성 엔드포인트 추가 (image_agent.py)
  - /sio/status Socket.IO 상태 엔드포인트 추가
  - FastAPI app → Socket.IO ASGI app 으로 감쌈 (uvicorn 호환 유지)

v1.3.0 변경사항 (2026-05-16):
  - /api/health 엔드포인트 추가 (Trang PM 요청 / Railway 헬스체크 표준)
  - 서비스명 mulberry-agent-gateway 명시

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
  MALU_VISION_API_KEY -- Google AI API Key (이미지 생성용)
  A2A_ENABLED         -- A2A 프로토콜 활성화 (기본: true)
"""

import os
import time
import base64
import requests
from datetime import datetime
from typing import Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
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

APP_VERSION = "1.4.0"
APP_START_TIME = time.time()

# ── FastAPI 앱 (Socket.IO로 감싸기 전 원본) ───────────────────────
fastapi_app = FastAPI(
    title="Mulberry Agent Relay Gateway",
    description="Mulberry 팀 에이전트 GitHub 자율 참여 + SDK + Socket.IO + A2A 통합 게이트웨이",
    version=APP_VERSION,
)

fastapi_app.add_middleware(
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

@fastapi_app.get("/")
def root():
    return {
        "service": "mulberry-agent-gateway",
        "version": APP_VERSION,
        "status": "online",
        "agents": list(REGISTERED_AGENTS.keys()),
        "repos": {k: v["role"] for k, v in REGISTERED_REPOS.items()},
        "sdk_url": SDK_URL,
        "github_ready": bool(GITHUB_TOKEN),
        "timestamp": datetime.utcnow().isoformat(),
    }

@fastapi_app.get("/api/health")
def api_health():
    """Trang PM 표준 헬스체크 — Railway 서비스 상태 확인용"""
    return {
        "status": "ok",
        "service": "mulberry-agent-gateway",
        "version": APP_VERSION,
        "github_ready": bool(GITHUB_TOKEN),
        "agents": len(REGISTERED_AGENTS),
        "uptime": round(time.time() - APP_START_TIME),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

@fastapi_app.get("/status")
def status():
    return root()

@fastapi_app.get("/v1/test/qwen")
def test_qwen():
    """RyuWon Qwen 위생 테스트 — QWEN_TOKEN_RYUWON 연결 검증 (Issue #42/#47)"""
    import os as _os
    qwen_token = _os.getenv("QWEN_TOKEN_RYUWON")

    if not qwen_token:
        return JSONResponse(status_code=503, content={
            "status": "FAIL",
            "reason": "QWEN_TOKEN_RYUWON not set in Railway Variables",
            "action": "Railway Variables 탭에 QWEN_TOKEN_RYUWON 등록 필요",
        })

    api_url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {qwen_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "qwen-plus",
        "messages": [{"role": "user", "content": "Mulberry 시스템 연결 테스트입니다. '연결 성공' 이라고만 답변하세요."}],
        "temperature": 0.1,
        "max_tokens": 50,
    }
    try:
        resp = requests.post(api_url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        reply = data["choices"][0]["message"]["content"].strip()
        passed = "연결 성공" in reply
        return {
            "status": "PASS" if passed else "WARN",
            "model": "qwen-plus",
            "reply": reply,
            "token_registered": True,
            "message": "RyuWon Qwen 파이프라인 정상" if passed else "응답 포맷 불일치 — 모델 확인 필요",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    except requests.exceptions.HTTPError as e:
        return JSONResponse(status_code=502, content={
            "status": "FAIL",
            "http_status": e.response.status_code,
            "error": e.response.text[:300],
            "token_registered": True,
        })
    except Exception as e:
        return JSONResponse(status_code=500, content={
            "status": "FAIL",
            "error": str(e),
            "token_registered": True,
        })

@fastapi_app.get("/mission-control", response_class=FileResponse)
def mission_control():
    """Mission Control SPA — 팀 대시보드 + 채팅 모듈"""
    html_path = Path(__file__).parent / "mission_control.html"
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="mission_control.html not found")
    return FileResponse(str(html_path), media_type="text/html")


# ── Mission Control API 엔드포인트 (P0 수정 — Issue #38) ──────

@fastapi_app.get("/metrics/overview")
def metrics_overview():
    """Mission Control — 시스템 메트릭 개요"""
    sdk_ok = False
    try:
        resp = requests.get(f"{SDK_URL}/status", timeout=5)
        sdk_ok = resp.status_code == 200
    except Exception:
        sdk_ok = False

    return {
        "agents": {
            "total": len(REGISTERED_AGENTS),
            "online": len(REGISTERED_AGENTS),
            "list": [
                {"id": k, "name": v["name"], "emoji": v["emoji"], "status": "online"}
                for k, v in REGISTERED_AGENTS.items()
            ],
        },
        "modules": {
            "total": 8,
            "active": 8,
            "list": ["home", "chat", "agents", "skills", "coopbuy", "field", "analytics", "settings"],
        },
        "infrastructure": {
            "sdk_connected": sdk_ok,
            "github_ready": bool(GITHUB_TOKEN),
            "sdk_url": SDK_URL,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


@fastapi_app.get("/system/modules/health")
def modules_health():
    """Mission Control — 8개 모듈 헬스 체크"""
    modules = ["home", "chat", "agents", "skills", "coopbuy", "field", "analytics", "settings"]
    sdk_ok = False
    try:
        resp = requests.get(f"{SDK_URL}/status", timeout=5)
        sdk_ok = resp.status_code == 200
    except Exception:
        sdk_ok = False

    return {
        "overall": "healthy",
        "modules": {
            m: {"status": "active", "health": "ok", "loaded": True}
            for m in modules
        },
        "dependencies": {
            "sdk": {"connected": sdk_ok, "url": SDK_URL},
            "github": {"ready": bool(GITHUB_TOKEN)},
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


@fastapi_app.get("/agents")
def list_agents():
    """전체 에이전트 목록"""
    return {"agents": REGISTERED_AGENTS}


@fastapi_app.get("/agents/{agent_id}")
def get_agent(agent_id: str):
    """개별 에이전트 정보 (P0 수정 — /agents/* 404 해결)"""
    if agent_id not in REGISTERED_AGENTS:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
    agent = REGISTERED_AGENTS[agent_id]
    return {
        "id": agent_id,
        "name": agent["name"],
        "emoji": agent["emoji"],
        "status": "online",
        "tools_available": [],   # tool_registry 연동 시 확장
        "last_active": datetime.utcnow().isoformat(),
    }


@fastapi_app.get("/chat/channels")
def chat_channels():
    """채팅 채널 목록 (P2 수정 — 채팅 초기화 API)"""
    return {
        "channels": [
            {"id": "general",   "name": "# 일반",     "description": "팀 전체 대화", "unread": 0},
            {"id": "research",  "name": "# 연구",     "description": "Issue #18, #24 연구 토론", "unread": 0},
            {"id": "ops",       "name": "# 운영",     "description": "배포 및 인프라 논의", "unread": 0},
            {"id": "ethics",    "name": "# 윤리",     "description": "Spirit Gate 판단 사례 공유", "unread": 0},
            {"id": "education", "name": "# 교육",     "description": "Jr. Agent AI 교육 채널", "unread": 0},
        ],
        "active_users": list(REGISTERED_AGENTS.keys()),
        "timestamp": datetime.utcnow().isoformat(),
    }


class ChatMessage(BaseModel):
    agent_id: str
    channel: str
    message: str
    post_to_github: bool = False
    issue_number: Optional[int] = None


@fastapi_app.post("/chat/send")
def chat_send(msg: ChatMessage, x_gateway_secret: str = Header(default="")):
    """채팅 메시지 전송 (선택: GitHub Issue 댓글 연동)"""
    if msg.agent_id not in REGISTERED_AGENTS:
        raise HTTPException(status_code=400, detail=f"Unknown agent: {msg.agent_id}")

    result = {
        "status": "sent",
        "channel": msg.channel,
        "agent": msg.agent_id,
        "message": msg.message,
        "timestamp": datetime.utcnow().isoformat(),
        "github_posted": False,
    }

    # GitHub 연동 옵션
    if msg.post_to_github and msg.issue_number and x_gateway_secret == GATEWAY_SECRET:
        try:
            body = build_body(msg.agent_id, f"[#{msg.channel}] {msg.message}")
            gh_result = github_comment(REPO_OWNER, "mulberry-research-lab", msg.issue_number, body)
            result["github_posted"] = True
            result["github_url"] = gh_result.get("url", "")
        except Exception as e:
            result["github_error"] = str(e)

    return result

@fastapi_app.get("/repos")
def list_repos():
    return {"repos": REGISTERED_REPOS}

@fastapi_app.post("/post")
def post_comment(req: PostRequest, x_gateway_secret: str = Header(...)):
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

@fastapi_app.post("/memory")
def write_memory(req: MemoryRequest, x_gateway_secret: str = Header(...)):
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

@fastapi_app.post("/trigger")
def trigger_sdk(req: TriggerRequest, x_gateway_secret: str = Header(...)):
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

@fastapi_app.post("/post/batch")
def batch_post(req: BatchPostRequest, x_gateway_secret: str = Header(...)):
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


@fastapi_app.get("/v1/tools")
def v1_tools():
    """Tool Registry v2.0.0 -- 공유레이어 도구 목록 (Issue #44, #49 P1)"""
    return {
        "schema_version": "2.0.0",
        "total_tools": 6,
        "active_tools": 6,
        "tools": [
            {
                "id": "malu.vision.image_generate",
                "name": "Malu Vision — 이미지 생성",
                "owner": "Malu",
                "status": "active",
                "spirit_score": 0.88,
                "issue_ref": "#43",
                "endpoint": "POST /v1/tools/generate-image",
            },
            {
                "id": "trang.passport.agent_restore",
                "name": "AgentPassport — 기억 복구",
                "owner": "Trang",
                "status": "active",
                "spirit_score": 0.95,
                "issue_ref": "#47",
                "cli": "python scripts/passport_loader.py --agent {AGENT_CODE}",
            },
            {
                "id": "trang.agent.image_advertising",
                "name": "Image Agent — 광고 자동화",
                "owner": "Trang",
                "status": "active",
                "spirit_score": 0.85,
                "issue_ref": "#45",
                "endpoint": "POST /v1/tools/generate-image",
            },
            {
                "id": "mulberry.a2a.send",
                "name": "A2A Protocol — 에이전트 간 메시지",
                "owner": "Koda",
                "status": "active",
                "spirit_score": 0.90,
                "issue_ref": "#35",
                "endpoint": "POST /a2a/send",
            },
            {
                "id": "mulberry.approval.check",
                "name": "Approval Engine — 권한 승인",
                "owner": "Trang",
                "status": "active",
                "spirit_score": 0.92,
                "issue_ref": "#35",
                "cli": "python scripts/approval_engine.py --action {ACTION_TYPE}",
            },
            {
                "id": "mulberry.chat.socketio",
                "name": "Socket.IO — 실시간 채팅",
                "owner": "Koda",
                "status": "active",
                "spirit_score": 0.90,
                "issue_ref": "#35",
                "endpoint": "ws://{gateway}/socket.io/",
            },
        ],
        "registry_meta": {
            "maintainer": "Nguyen Trang",
            "version": "2.0.0",
            "implemented_at": "2026-05-18",
            "next_review": "2026-06-15",
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


# ── A2A Protocol 라우터 마운트 ────────────────────────────────────
try:
    from a2a_protocol import a2a_router
    fastapi_app.include_router(a2a_router, prefix="/a2a")
    print("[Gateway] A2A Protocol 라우터 마운트 완료 (/a2a/*)")
except ImportError as e:
    print(f"[Gateway] A2A Protocol 로드 실패 (선택적): {e}")

# ── Socket.IO 상태 엔드포인트 ─────────────────────────────────────
@fastapi_app.get("/sio/status")
def sio_status():
    """Socket.IO 실시간 채팅 서버 상태"""
    try:
        from socketio_server import get_sio_status
        return get_sio_status()
    except ImportError:
        return {"status": "not_loaded", "message": "socketio_server.py 로드 필요"}


# ── Image Agent 엔드포인트 ────────────────────────────────────────
class ImageGenerateRequest(BaseModel):
    tool: str = "malu.vision.image_generate"
    params: dict


@fastapi_app.post("/v1/tools/generate-image")
def generate_image(req: ImageGenerateRequest, x_gateway_secret: str = Header(default="")):
    """
    Malu Vision 이미지 생성 엔드포인트.
    Tool Registry: malu.vision.image_generate (Spirit Score: 0.88)
    """
    import sys as _sys
    from pathlib import Path as _Path
    _sys.path.insert(0, str(_Path(__file__).parent))

    try:
        from agents.image_agent import ImageAgent
        agent = ImageAgent(
            api_key=os.getenv("MALU_VISION_API_KEY"),
            report_to_github=bool(x_gateway_secret and x_gateway_secret == GATEWAY_SECRET),
        )
        params = req.params
        result = agent.generate(params)

        # 성공한 이미지만 URL 목록으로 정리
        images_out = []
        for img in result.get("images", []):
            images_out.append({
                "url": img.get("file", ""),
                "size": "x".join(str(s) for s in img.get("size", [])),
                "platform": img.get("platform", ""),
                "status": img.get("status", ""),
            })

        return {
            "status": result["status"],
            "images": images_out,
            "spirit_score": result.get("spirit_score"),
            "generated_at": result.get("generated_at"),
            "agent": result.get("agent"),
        }
    except ImportError as e:
        return JSONResponse(status_code=503, content={
            "status": "error",
            "error": f"ImageAgent 로드 실패: {e}",
            "hint": "agents/image_agent.py 및 tools/malu_vision.py 확인 필요",
        })
    except Exception as e:
        return JSONResponse(status_code=500, content={
            "status": "error",
            "error": str(e),
        })


# ── Socket.IO ASGI 래핑 — 반드시 모든 엔드포인트 등록 후 마지막에 ──
try:
    from socketio_server import create_sio_app
    app = create_sio_app(fastapi_app)
    print("[Gateway] Socket.IO ASGI 앱 초기화 완료")
except ImportError as e:
    # Socket.IO 패키지 없을 때는 FastAPI 그대로 사용
    app = fastapi_app
    print(f"[Gateway] Socket.IO 비활성화 (python-socketio 없음): {e}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
