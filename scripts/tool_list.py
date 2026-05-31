#!/usr/bin/env python3
"""
scripts/tool_list.py — Mulberry 기능 공유 레이어 조회기
========================================================
에이전트가 "내가 사용할 수 있는 도구 목록"을 조회한다.

사용법:
  python scripts/tool_list.py              # 전체 도구 목록
  python scripts/tool_list.py --agent kbin # Kbin이 사용 가능한 도구
  python scripts/tool_list.py --tool github.comment  # 이 도구를 누가 쓸 수 있나

연결 구조:
  tool_registry.yaml  ← 도구 공유 등록소 (Trang 설계)
  passport.yaml       ← 에이전트 능력 선언 (Kbin 자기선언 → 팀 전체)
  → 두 파일을 교차 참조하여 완전한 기능 공유 레이어 구성

작성: Koda CTO · 2026-05-31
"""

import sys
import yaml
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

REGISTRY_PATH  = Path("mulberry_connector/tool_registry.yaml")
PASSPORTS_PATH = Path("agents/passports")


def load_registry() -> list:
    if not REGISTRY_PATH.exists():
        return []
    data = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    return data.get("tools", [])


def load_all_passports() -> dict:
    passports = {}
    if not PASSPORTS_PATH.exists():
        return passports
    for agent_dir in PASSPORTS_PATH.iterdir():
        passport_file = agent_dir / "passport.yaml"
        if passport_file.exists():
            data = yaml.safe_load(passport_file.read_text(encoding="utf-8"))
            passports[agent_dir.name] = data
    return passports


def get_tools_for_agent(agent_id: str) -> dict:
    """
    특정 에이전트가 사용할 수 있는 모든 도구 반환.
    - 자신이 소유한 도구
    - borrowable_by에 포함된 도구
    """
    tools = load_registry()
    passport = load_all_passports().get(agent_id, {})

    owned, borrowed = [], []
    for tool in tools:
        owner = tool.get("owner", "")
        borrowable = tool.get("borrowable_by", [])

        if owner == agent_id:
            owned.append(tool)
        elif borrowable == "*" or agent_id in (borrowable or []):
            borrowed.append(tool)

    return {
        "agent": agent_id,
        "passport_capabilities": passport.get("capabilities", []),
        "passport_limitations":  passport.get("limitations", []),
        "owned_tools":    owned,
        "borrowed_tools": borrowed,
        "total_accessible": len(owned) + len(borrowed),
    }


def print_agent_tools(agent_id: str):
    result = get_tools_for_agent(agent_id)
    print(f"\n{'='*55}")
    print(f"  🛂 {agent_id.upper()} — 사용 가능한 도구 목록")
    print(f"{'='*55}")

    print(f"\n📋 패스포트 능력:")
    for cap in result["passport_capabilities"]:
        print(f"   ✅ {cap}")
    for lim in result["passport_limitations"]:
        print(f"   ❌ {lim} (제한)")

    print(f"\n🔧 소유 도구 ({len(result['owned_tools'])}개):")
    for t in result["owned_tools"]:
        lvl = t.get("capability_level", "?")
        print(f"   [{lvl}] {t['id']} — {t['name']}")

    print(f"\n🤝 빌려쓸 수 있는 도구 ({len(result['borrowed_tools'])}개):")
    for t in result["borrowed_tools"]:
        lvl = t.get("capability_level", "?")
        owner = t.get("owner", "?")
        print(f"   [{lvl}] {t['id']} (from {owner}) — {t['name']}")

    print(f"\n  총 접근 가능: {result['total_accessible']}개 도구")
    print(f"{'='*55}\n")


def print_all_tools():
    tools = load_registry()
    passports = load_all_passports()

    print(f"\n{'='*55}")
    print(f"  🗂️  Mulberry 기능 공유 레이어 전체 현황")
    print(f"{'='*55}\n")

    print(f"📦 등록된 도구: {len(tools)}개\n")
    print(f"{'ID':<30} {'소유자':<10} {'등급':<5} {'공유':<20} {'상태'}")
    print(f"{'─'*80}")
    for t in tools:
        borrowable = t.get("borrowable_by", [])
        share = "전체(*)" if borrowable == "*" else ", ".join(borrowable or [])
        status = "✅" if t.get("implemented") else "⏳"
        print(f"{t['id']:<30} {t.get('owner','?'):<10} {t.get('capability_level','?'):<5} {share:<20} {status}")

    print(f"\n📇 등록된 패스포트: {len(passports)}개")
    for agent_id, p in passports.items():
        caps = len(p.get("capabilities", []))
        lims = len(p.get("limitations", []))
        print(f"   🛂 {agent_id:<12} 능력 {caps}개 / 제한 {lims}개")

    print(f"\n{'='*55}\n")


def get_tool_info(tool_id: str):
    tools = load_registry()
    tool = next((t for t in tools if t["id"] == tool_id), None)
    if not tool:
        print(f"❌ 도구 '{tool_id}' 없음")
        return

    borrowable = tool.get("borrowable_by", [])
    share = "전체" if borrowable == "*" else ", ".join(borrowable or [])

    print(f"\n{'='*55}")
    print(f"  🔧 도구 정보: {tool_id}")
    print(f"{'='*55}")
    print(f"  이름: {tool.get('name')}")
    print(f"  소유자: {tool.get('owner')}")
    print(f"  등급: {tool.get('capability_level')} (L0=읽기 ~ L4=배포)")
    print(f"  신뢰도: {tool.get('trust_score')}")
    print(f"  공유 대상: {share}")
    print(f"  상태: {'✅ 활성' if tool.get('implemented') else '⏳ 준비중'}")
    print(f"  설명: {tool.get('description')}")
    print(f"{'='*55}\n")


def build_context_for_agent(agent_id: str) -> str:
    """
    team_discuss.py에서 system prompt 주입용.
    에이전트가 사용할 수 있는 도구 목록을 텍스트로 반환.
    """
    result = get_tools_for_agent(agent_id)
    lines = [
        "\n\n## 기능 공유 레이어 — 내가 사용할 수 있는 도구",
        f"(tool_registry.yaml 기준 · 총 {result['total_accessible']}개)",
        "",
        "### 소유 도구 (직접 실행 가능)",
    ]
    for t in result["owned_tools"]:
        lines.append(f"- [{t.get('capability_level')}] {t['id']}: {t['name']}")

    lines.append("\n### 빌려쓸 수 있는 도구 (팀원 경유)")
    for t in result["borrowed_tools"][:10]:  # 상위 10개
        lines.append(f"- [{t.get('capability_level')}] {t['id']} (from {t.get('owner')}): {t['name']}")

    lines.append(
        "\nL4(배포/금융) 도구는 반드시 인간(PM/CEO) 승인 후 실행하세요."
    )
    return "\n".join(lines)


# ── 실행 ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Mulberry 기능 공유 레이어 조회")
    parser.add_argument("--agent", help="특정 에이전트 도구 조회")
    parser.add_argument("--tool",  help="특정 도구 정보 조회")
    args = parser.parse_args()

    if args.agent:
        print_agent_tools(args.agent)
    elif args.tool:
        get_tool_info(args.tool)
    else:
        print_all_tools()
