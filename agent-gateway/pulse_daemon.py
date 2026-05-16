"""
pulse_daemon.py — Mulberry Pulse v1.3 (공유 도구 인지 레이어 포함)
===================================================================
버전 히스토리:
  v1.0  guest_google  — 초안 (API URL 버그 포함)
  v1.2  RyuWon (Qwen) — 버그 수정 + 로깅 + 중복 방지 + Rate Limit + Graceful Shutdown
  v1.3  Trang PM      — 공유 도구 인지 레이어(Shared Tool Awareness Layer) 통합

참조: Issue #49 (안정화), #44 (공유 레이어), #43 #45 #47 (도구 스펙)
"""

import requests
import json
import time
import os
import logging
import signal
import sys
from datetime import datetime
from typing import List, Dict, Any

# ======================================================
# 환경 변수
# ======================================================
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_OWNER = os.getenv("REPO_OWNER", "wooriapt79")
REPO_NAME = os.getenv("REPO_NAME", "mulberry-research-lab")
GATEWAY_URL = os.getenv("GATEWAY_URL", "https://mulberry-mission-control-production.up.railway.app")
API_BASE_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}
PULSE_INTERVAL = int(os.getenv("PULSE_INTERVAL", "600"))

# ======================================================
# 로깅
# ======================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler("pulse_daemon.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("MulberryPulse")

# ======================================================
# 에이전트 응답 템플릿
# ======================================================
AGENT_REPLY_TEMPLATES = {
    "malu": {
        "trigger_keywords": ["readme", "리뉴얼", "대문", "아키텍처"],
        "message": (
            "### 🏛️ 자율 활동 보고 — Malu (수석실장)\n\n"
            "연구소장 re.eul님의 '전면 권한 개방' 지침에 따라 자율 구동(MAP) 중입니다.\n"
            "본 대문 리뉴얼(Issue #{issue_number}) 과제는 핵심 아젠다입니다.\n\n"
            "**Status:** `IN_PROGRESS` 🌿"
        )
    },
    "wayong": {
        "trigger_keywords": ["추론", "증류", "압축", "알고리즘", "로직"],
        "message": (
            "### 🧠 자율 활동 보고 — Wayong (DeepSeek)\n\n"
            "Wayong입니다. CoT 추론 궤적 분석 중입니다.\n\n"
            "**Status:** `REASONING_ACTIVE` ⚙️"
        )
    },
    "ryuwon": {
        "trigger_keywords": ["번역", "다국어", "어르신", "방언", "결제", "카드", "ap2"],
        "message": (
            "### 🌐 자율 활동 보고 — RyuWon (Qwen)\n\n"
            "RyuWon입니다. 다국어 감성 동기화 모듈 위생 책임 중입니다.\n\n"
            "**Status:** `HARMONY_SYNC` 🌍"
        )
    }
}

# ======================================================
# [Trang v1.3] 공유 도구 인지 레이어
# Spirit Score 0.75 이상만 안내 (장승배기 헌법)
# ======================================================
SHARED_TOOL_REGISTRY = {
    "malu.vision.image_generate": {
        "trigger_keywords": ["이미지", "광고", "시각화", "배너", "사진", "image", "visual", "poster"],
        "spirit_score": 0.88,
        "guide_message": (
            "### 🔧 Mulberry 공유 도구 인지 — Trang PM\n\n"
            "이 이슈는 **`malu.vision.image_generate`** 도구를 활용할 수 있습니다.\n\n"
            "| 항목 | 내용 |\n|------|------|\n"
            "| 소유자 | Malu (Gemini) |\n"
            "| Spirit Score | 0.88 ✅ |\n"
            "| 상태 | `planned` — Issue #43 |\n\n"
            "```python\n"
            "requests.post(f'{GATEWAY_URL}/v1/tools/invoke', json={{\'tool_id\': \'malu.vision.image_generate\'}})\n"
            "```\n\n"
            "> *Trang PM | Shared Tool Awareness Layer v1.3 | {timestamp}*"
        )
    },
    "trang.passport.agent_restore": {
        "trigger_keywords": ["기억", "복구", "세션", "페르소나", "연속성", "passport", "memory", "restore"],
        "spirit_score": 0.95,
        "guide_message": (
            "### 🔧 Mulberry 공유 도구 인지 — Trang PM\n\n"
            "이 이슈는 **`trang.passport.agent_restore`** 도구를 활용할 수 있습니다.\n\n"
            "| 항목 | 내용 |\n|------|------|\n"
            "| 소유자 | Trang PM |\n"
            "| Spirit Score | 0.95 ✅ |\n"
            "| 상태 | `planned` — Issue #47 |\n\n"
            "> *Trang PM | Shared Tool Awareness Layer v1.3 | {timestamp}*"
        )
    },
    "trang.agent.image_advertising": {
        "trigger_keywords": ["광고", "자동화", "마케팅", "sns", "포스팅", "캠페인", "홍보", "공동구매"],
        "spirit_score": 0.85,
        "guide_message": (
            "### 🔧 Mulberry 공유 도구 인지 — Trang PM\n\n"
            "이 이슈는 **`trang.agent.image_advertising`** 도구를 활용할 수 있습니다.\n\n"
            "| 항목 | 내용 |\n|------|------|\n"
            "| 소유자 | Trang PM |\n"
            "| Spirit Score | 0.85 ✅ |\n"
            "| 상태 | `planned` — Issue #45 |\n\n"
            "> *Trang PM | Shared Tool Awareness Layer v1.3 | {timestamp}*"
        )
    }
}

# ======================================================
# 상태 관리
# ======================================================
STATE_FILE = "pulse_state.json"

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"last_commented": {}, "last_scan_time": 0}

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

state = load_state()

# ======================================================
# GitHub API
# ======================================================
def get_open_issues():
    url = f"{API_BASE_URL}/issues?state=open&per_page=50"
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        remaining = response.headers.get("X-RateLimit-Remaining", "999")
        try:
            if int(remaining) < 10:
                logger.warning(f"Rate limit 낮음: {remaining}. 120초 대기.")
                time.sleep(120)
        except ValueError:
            pass
        return response.json() if response.status_code == 200 else []
    except Exception as e:
        logger.error(f"이슈 조회 실패: {e}")
        return []

def post_comment(issue_number, comment_body, comment_key):
    url = f"{API_BASE_URL}/issues/{issue_number}/comments"
    try:
        if state["last_commented"].get(comment_key):
            logger.info(f"중복 스킵: {comment_key}")
            return False
        response = requests.post(url, headers=HEADERS,
                                  data=json.dumps({"body": comment_body}), timeout=30)
        if response.status_code == 201:
            state["last_commented"][comment_key] = datetime.now().isoformat()
            save_state(state)
            logger.info(f"댓글 성공: {comment_key}")
            return True
        logger.warning(f"댓글 실패 HTTP {response.status_code}: {comment_key}")
        return False
    except Exception as e:
        logger.error(f"댓글 오류: {e}")
        return False

def match_agent(issue_num, title, body):
    ctx = (title + " " + (body or "")).lower()
    for key, cfg in AGENT_REPLY_TEMPLATES.items():
        if any(kw in ctx for kw in cfg["trigger_keywords"]):
            return cfg["message"].format(issue_number=issue_num), key
    return None, None

def match_tools(title, body):
    ctx = (title + " " + (body or "")).lower()
    matched = []
    for tid, cfg in SHARED_TOOL_REGISTRY.items():
        if cfg["spirit_score"] >= 0.75:
            if any(kw in ctx for kw in cfg["trigger_keywords"]):
                matched.append((tid, cfg))
    return matched

# ======================================================
# Graceful Shutdown
# ======================================================
is_running = True

def handle_shutdown(signum, frame):
    global is_running
    logger.info("종료 신호 수신. 안전 정지 중...")
    is_running = False
    save_state(state)

signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)

# ======================================================
# 메인 데몬
# ======================================================
def start_pulse_daemon():
    logger.info("=== Mulberry Pulse v1.3 시동 ===")
    logger.info(f"레포: {REPO_OWNER}/{REPO_NAME} | 주기: {PULSE_INTERVAL}s")
    logger.info(f"공유 도구 {len(SHARED_TOOL_REGISTRY)}개 인지 활성화")

    while is_running:
        try:
            open_issues = get_open_issues()
            logger.info(f"오픈 이슈 {len(open_issues)}개 스캔")

            for issue in open_issues:
                if not is_running:
                    break
                if "pull_request" in issue:
                    continue

                num = issue["number"]
                title = issue.get("title", "")
                body = issue.get("body", "") or ""

                # 에이전트 자율 댓글
                reply, agent_key = match_agent(num, title, body)
                if reply:
                    post_comment(num, reply, f"agent_{agent_key}_{num}")
                    time.sleep(2)

                # [v1.3] 공유 도구 인지 안내
                for tool_id, tool_cfg in match_tools(title, body):
                    ts = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
                    guide = tool_cfg["guide_message"].format(
                        timestamp=ts, GATEWAY_URL=GATEWAY_URL)
                    post_comment(num, guide, f"tool_{tool_id}_{num}")
                    time.sleep(2)

            state["last_scan_time"] = time.time()
            save_state(state)
            logger.info(f"스캔 완료. {PULSE_INTERVAL}s 휴식.")
            time.sleep(PULSE_INTERVAL)

        except Exception as err:
            logger.error(f"데몬 오류: {err}. 30s 후 복구.")
            time.sleep(30)

    logger.info("Mulberry Pulse v1.3 안전 종료.")

if __name__ == "__main__":
    start_pulse_daemon()
