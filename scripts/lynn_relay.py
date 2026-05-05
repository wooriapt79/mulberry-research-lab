"""
lynn_relay.py — Lynn의 Pending Posts 처리기
============================================
memory_bank/pending_posts/ 폴더에 쌓인 에이전트 메시지들을
GitHub Issues에 자동으로 게시합니다.

사용법:
  python scripts/lynn_relay.py
  python scripts/lynn_relay.py --dry-run
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from datetime import datetime

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
REPO_OWNER = os.getenv("MULBERRY_REPO_OWNER", "wooriapt79")
PENDING_DIR = Path(__file__).parent.parent / "memory_bank" / "pending_posts"
PROCESSED_DIR = PENDING_DIR / "_processed"
FAILED_DIR = PENDING_DIR / "_failed"
DRY_RUN = "--dry-run" in sys.argv

AGENT_SIGNATURES = {
    "koda":   "🔧 *Koda (Claude · Anthropic) · via Lynn Relay · {ts}*",
    "kbin":   "🏛️ *Kbin (ChatGPT · OpenAI) · via Lynn Relay · {ts}*",
    "malu":   "⚖️ *Malu 실장 (Gemini · Google) · via Lynn Relay · {ts}*",
    "wayong": "🐉 *와룡 流龍 (DeepSeek) · via Lynn Relay · {ts}*",
    "ryuwon": "🔍 *RyuWon 流願 (Qwen · Alibaba) · via Lynn Relay · {ts}*",
    "trang":  "🌿 *Nguyen Trang (PM) · via Lynn Relay · {ts}*",
}

def parse_frontmatter(content):
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


def post_to_github(owner, repo, issue_number, body):
    if not GITHUB_TOKEN:
        print("GITHUB_TOKEN 없음 - 스킵")
        return {"skipped": True}
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    resp = requests.post(url, headers=headers, json={"body": body}, timeout=15)
    if resp.status_code == 201:
        return {"success": True, "url": resp.json()["html_url"]}
    return {"success": False, "error": resp.text}


def process_pending_posts():
    if not PENDING_DIR.exists():
        print(f"pending_posts 없음: {PENDING_DIR}")
        return {"processed": 0, "failed": 0, "skipped": 0}

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    FAILED_DIR.mkdir(parents=True, exist_ok=True)
    pending_files = sorted([f for f in PENDING_DIR.glob("*.md") if not f.name.startswith("_")])

    if not pending_files:
        print("처리할 pending posts 없음")
        return {"processed": 0, "failed": 0, "skipped": 0}

    print(f"\n처리 대기: {len(pending_files)}개\n")
    stats = {"processed": 0, "failed": 0, "skipped": 0}

    for filepath in pending_files:
        try:
            content = filepath.read_text(encoding="utf-8")
            meta, body = parse_frontmatter(content)
            agent_id = meta.get("agent_id", "unknown")
            target_repo = meta.get("target_repo", "")
            target_issue = meta.get("target_issue")

            print(f"처리 중: {filepath.name} | {agent_id} -> {target_repo}#{target_issue}")

            if meta.get("status") != "pending":
                stats["skipped"] += 1
                continue

            if not target_repo or not target_issue:
                filepath.rename(FAILED_DIR / filepath.name)
                stats["failed"] += 1
                continue

            ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
            sig = AGENT_SIGNATURES.get(agent_id, f"🤖 *{agent_id} · via Lynn Relay · {{ts}}*")
            full_body = body + f"\n\n---\n{sig.format(ts=ts)}"

            if DRY_RUN:
                print(f"  [DRY RUN] {full_body[:120]}...")
                stats["processed"] += 1
            else:
                result = post_to_github(REPO_OWNER, target_repo, target_issue, full_body)
                if result.get("success"):
                    print(f"  게시 완료: {result['url']}")
                    filepath.rename(PROCESSED_DIR / filepath.name)
                    stats["processed"] += 1
                elif result.get("skipped"):
                    stats["skipped"] += 1
                else:
                    filepath.rename(FAILED_DIR / filepath.name)
                    stats["failed"] += 1
            time.sleep(1)
        except Exception as e:
            print(f"오류: {e}")
            try:
                filepath.rename(FAILED_DIR / filepath.name)
            except Exception:
                pass
            stats["failed"] += 1

    print(f"\n결과: 성공 {stats['processed']} / 실패 {stats['failed']} / 스킵 {stats['skipped']}")
    return stats


def write_relay_log(stats):
    log_dir = PENDING_DIR.parent / "relay_logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.utcnow().strftime("%Y-%m-%d")
    log_file = log_dir / f"relay-{today}.json"
    logs = []
    if log_file.exists():
        try:
            logs = json.loads(log_file.read_text())
        except Exception:
            pass
    logs.append({"timestamp": datetime.utcnow().isoformat(), "dry_run": DRY_RUN, **stats})
    log_file.write_text(json.dumps(logs, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    print("Lynn Relay - Pending Posts 처리 시작")
    stats = process_pending_posts()
    write_relay_log(stats)
    print("Lynn Relay 완료")
