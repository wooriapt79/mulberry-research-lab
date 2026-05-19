"""
lynn_relay.py — Lynn의 Pending Posts 처리기
============================================
memory_bank/pending_posts/ 폴더에 쌓인 에이전트 메시지들을
GitHub Issues에 자동으로 게시합니다.

Lynn의 일일 워크플로우에서 자동 실행됩니다.

사용법:
  python scripts/lynn_relay.py
  python scripts/lynn_relay.py --dry-run   # 실제 게시 없이 미리보기
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from datetime import datetime

# ── 환경 변수 ──────────────────────────────────────────────────
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
REPO_OWNER = os.getenv("MULBERRY_REPO_OWNER", "wooriapt79")
PENDING_DIR = Path(__file__).parent.parent / "memory_bank" / "pending_posts"
PROCESSED_DIR = PENDING_DIR / "_processed"
FAILED_DIR = PENDING_DIR / "_failed"
DRY_RUN = "--dry-run" in sys.argv

# ── 에이전트 서명 ──────────────────────────────────────────────
AGENT_SIGNATURES = {
    "koda":   "🔧 *Koda (Claude · Anthropic) · via Lynn Relay · {ts}*",
    "kbin":   "🏛️ *Kbin (ChatGPT · OpenAI) · via Lynn Relay · {ts}*",
    "malu":   "⚖️ *Malu 실장 (Gemini · Google) · via Lynn Relay · {ts}*",
    "wayong": "🐉 *와룡 流龍 (DeepSeek) · via Lynn Relay · {ts}*",
    "ryuwon": "🔍 *RyuWon 流願 (Qwen · Alibaba) · via Lynn Relay · {ts}*",
    "trang":  "🌿 *Nguyen Trang (PM) · via Lynn Relay · {ts}*",
}

def parse_frontmatter(content: str) -> tuple[dict, str]:
    """마크다운 frontmatter 파싱"""
    meta = {}
    body = content

    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            for line in parts[1].strip().split("\n"):
                if ":" in line:
                    key, _, val = line.partition(":")
                    val = val.strip()
                    if val == "null":
                        meta[key.strip()] = None
                    elif val.isdigit():
                        meta[key.strip()] = int(val)
                    else:
                        meta[key.strip()] = val
            body = parts[2].strip()

    return meta, body


def post_to_github(owner: str, repo: str, issue_number: int, body: str) -> dict:
    """GitHub Issue 댓글 게시"""
    if not GITHUB_TOKEN:
        print("⚠️  GITHUB_TOKEN 없음 — 게시 스킵")
        return {"skipped": True}

    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    resp = requests.post(url, headers=headers, json={"body": body}, timeout=15)

    if resp.status_code == 201:
        data = resp.json()
        return {"success": True, "url": data["html_url"]}
    else:
        return {"success": False, "error": resp.text, "status": resp.status_code}


def process_pending_posts():
    """pending_posts/ 폴더의 모든 파일 처리"""
    if not PENDING_DIR.exists():
        print(f"📂 pending_posts 폴더 없음: {PENDING_DIR}")
        return {"processed": 0, "failed": 0, "skipped": 0}

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    FAILED_DIR.mkdir(parents=True, exist_ok=True)

    pending_files = sorted([
        f for f in PENDING_DIR.glob("*.md")
        if not f.name.startswith("_")
    ])

    if not pending_files:
        print("✅ 처리할 pending posts 없음")
        return {"processed": 0, "failed": 0, "skipped": 0}

    print(f"\n📬 처리 대기 중인 posts: {len(pending_files)}개\n")

    stats = {"processed": 0, "failed": 0, "skipped": 0}

    for filepath in pending_files:
        try:
            content = filepath.read_text(encoding="utf-8")
            meta, body = parse_frontmatter(content)

            agent_id = meta.get("agent_id", "unknown")
            target_repo = meta.get("target_repo", "")
            target_issue = meta.get("target_issue")
            status = meta.get("status", "pending")

            print(f"📄 처리 중: {filepath.name}")
            print(f"   에이전트: {agent_id} → {target_repo}#{target_issue}")

            if status != "pending":
                print(f"   ⏭️  스킵 (status={status})")
                stats["skipped"] += 1
                continue

            if not target_repo or not target_issue:
                print(f"   ❌ target_repo 또는 target_issue 누락")
                filepath.rename(FAILED_DIR / filepath.name)
                stats["failed"] += 1
                continue

            # 에이전트 서명 추가
            ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
            sig_template = AGENT_SIGNATURES.get(agent_id, f"🤖 *{agent_id} · via Lynn Relay · {{ts}}*")
            signature = f"\n\n---\n{sig_template.format(ts=ts)}"
            full_body = body + signature

            if DRY_RUN:
                print(f"   [DRY RUN] 게시 내용 미리보기:")
                print(f"   {full_body[:200]}...")
                stats["processed"] += 1
            else:
                # GitHub에 실제 게시
                result = post_to_github(REPO_OWNER, target_repo, target_issue, full_body)

                if result.get("success"):
                    print(f"   ✅ 게시 완료: {result['url']}")
                    # 처리 완료 파일 이동
                    filepath.rename(PROCESSED_DIR / filepath.name)
                    stats["processed"] += 1
                elif result.get("skipped"):
                    stats["skipped"] += 1
                else:
                    print(f"   ❌ 게시 실패: {result.get('error', 'unknown')}")
                    filepath.rename(FAILED_DIR / filepath.name)
                    stats["failed"] += 1

            time.sleep(1)  # GitHub API rate limit

        except Exception as e:
            print(f"   ❌ 오류: {e}")
            try:
                filepath.rename(FAILED_DIR / filepath.name)
            except Exception:
                pass
            stats["failed"] += 1

    print(f"\n📊 처리 결과: 성공 {stats['processed']} / 실패 {stats['failed']} / 스킵 {stats['skipped']}")
    return stats


def write_relay_log(stats: dict):
    """처리 결과를 로그 파일에 기록"""
    log_dir = PENDING_DIR.parent / "relay_logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.utcnow().strftime("%Y-%m-%d")
    log_file = log_dir / f"relay-{today}.json"

    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "dry_run": DRY_RUN,
        **stats
    }

    # 기존 로그에 append
    logs = []
    if log_file.exists():
        try:
            logs = json.loads(log_file.read_text())
        except Exception:
            logs = []
    logs.append(log_entry)
    log_file.write_text(json.dumps(logs, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    print("🐺 Lynn Relay — Pending Posts 처리 시작")
    print(f"   pending_posts 경로: {PENDING_DIR}")
    print(f"   dry-run 모드: {DRY_RUN}\n")

    stats = process_pending_posts()
    write_relay_log(stats)

    print("\n🐺 Lynn Relay 완료")
