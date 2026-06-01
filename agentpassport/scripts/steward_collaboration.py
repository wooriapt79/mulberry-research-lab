#!/usr/bin/env python3
"""
agentpassport/scripts/steward_collaboration.py
Mulberry 에이전트 × 스튜어드 협업 시스템

[핵심 철학]
에이전트는 계획하고, 인간 스튜어드는 실제 세계와 연결한다.
디지털 영역은 에이전트가, 물리적·법적 영역은 인간이 담당한다.

[협업 흐름]
① 에이전트 기획안 준비
        ↓
② 에이전트 → 스튜어드 협의 요청 (무엇이 자율/인간 필요인지 분류)
        ↓
③ 스튜어드 검토 + 승인/조정
        ↓
④ 에이전트: 디지털 작업 자율 실행
   스튜어드: 물리적 매입·계약·결제 실행
        ↓
⑤ 에이전트 ← 스튜어드 실행 완료 보고
        ↓
⑥ 에이전트: 운영 시작 + 보고서 생성

[스튜어드 유형]
  human_steward: CEO re.eul · PM Trang
  ai_steward:    Kbin (거버넌스) · Malu (법률·계약)

설계: CEO re.eul 지시 · Koda CTO · 2026-06-02
"""

import sys, os, json, yaml
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import List, Optional

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE         = Path(__file__).parent.parent
COLLAB_DIR   = BASE / "config" / "collaborations"
REPORTS_DIR  = BASE / "reports"
COLLAB_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

GH_TOKEN  = os.getenv("GITHUB_TOKEN", "")
REPO      = os.getenv("REPO_FULL", "wooriapt79/mulberry-research-lab")
TODAY     = datetime.now().strftime("%Y-%m-%d")
TIMESTAMP = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── 분류 기준 ────────────────────────────────────────────────────

class TaskDomain(str, Enum):
    DIGITAL  = "digital"   # 에이전트 자율
    PHYSICAL = "physical"  # 인간 스튜어드 필수
    LEGAL    = "legal"     # 법적 구속력 → 인간 필수
    HYBRID   = "hybrid"    # 협의 후 결정


class StewardType(str, Enum):
    HUMAN_CEO  = "CEO re.eul"
    HUMAN_PM   = "PM Trang"
    AI_KBIN    = "Kbin (CSA)"
    AI_MALU    = "Malu (법률)"


# ── 작업 아이템 ──────────────────────────────────────────────────

@dataclass
class CollabTask:
    task_id:     str
    name:        str
    description: str
    domain:      TaskDomain
    steward:     Optional[StewardType]  # 담당 스튜어드
    amount:      int = 0                # 관련 금액
    status:      str = "PENDING"        # PENDING / IN_PROGRESS / DONE
    agent_note:  str = ""               # 에이전트의 의견·제안
    steward_note: str = ""              # 스튜어드 피드백


@dataclass
class CollaborationPlan:
    """에이전트-스튜어드 협업 계획서"""
    plan_id:    str
    agent_id:   str
    shop_name:  str
    created_at: str = TODAY
    status:     str = "DRAFT"   # DRAFT / IN_REVIEW / APPROVED / RUNNING

    # 에이전트 자율 작업
    agent_tasks: List[CollabTask] = field(default_factory=list)

    # 스튜어드 협업 필요 작업
    steward_tasks: List[CollabTask] = field(default_factory=list)

    # 물리적 매입 목록
    procurement_items: List[dict] = field(default_factory=list)

    steward_approval: Optional[str] = None
    approved_at:      Optional[str] = None


# ── 기획안 자동 분류 ─────────────────────────────────────────────

def classify_tasks(agent_id: str, shop_name: str,
                   products: list = None) -> CollaborationPlan:
    """
    에이전트가 작업을 디지털/물리적으로 자동 분류하여 협업 계획서를 생성한다.
    """
    plan_id = f"COLLAB-{TODAY.replace('-','')}-{agent_id[:4].upper()}"

    plan = CollaborationPlan(
        plan_id=plan_id,
        agent_id=agent_id,
        shop_name=shop_name,
    )

    # ── 에이전트 자율 작업 (디지털) ───────────────────────────────
    plan.agent_tasks = [
        CollabTask(
            task_id="A-001",
            name="쇼핑몰 코드 자동 생성",
            description="Auto Code Pilot으로 FastAPI + 결제 연동 코드 생성",
            domain=TaskDomain.DIGITAL,
            steward=None,
            agent_note="Spirit Gate + Quality Gate 검증 후 Railway 자동 배포",
        ),
        CollabTask(
            task_id="A-002",
            name="상품 페이지 제작",
            description="상품 이미지·설명·가격 표시 HTML 자동 생성",
            domain=TaskDomain.DIGITAL,
            steward=None,
            agent_note="상품 데이터는 스튜어드가 제공한 정보 사용",
        ),
        CollabTask(
            task_id="A-003",
            name="주문·결제 시스템 연동",
            description="PG 결제 테스트 환경 연동 (실 결제는 스튜어드 승인 후)",
            domain=TaskDomain.DIGITAL,
            steward=None,
            agent_note="테스트 모드로 먼저 구동. 실 결제 전환은 Malu 검토 필요",
        ),
        CollabTask(
            task_id="A-004",
            name="고객 알림 이메일·SMS 시스템",
            description="주문확인·배송안내 자동 발송 로직 구현",
            domain=TaskDomain.DIGITAL,
            steward=None,
        ),
        CollabTask(
            task_id="A-005",
            name="재고·주문 관리 대시보드",
            description="실시간 재고 현황·주문 처리 현황 모니터링 화면",
            domain=TaskDomain.DIGITAL,
            steward=None,
        ),
        CollabTask(
            task_id="A-006",
            name="월간 손익 보고서 자동 생성",
            description="매월 1일 P&L 보고서 자동 생성 + CEO 보고",
            domain=TaskDomain.DIGITAL,
            steward=None,
        ),
    ]

    # ── 스튜어드 협업 필요 작업 ────────────────────────────────────
    plan.steward_tasks = [
        CollabTask(
            task_id="S-001",
            name="공급사 선정 및 계약",
            description="실제 로컬푸드 공급사(농가·협동조합) 발굴·계약 체결",
            domain=TaskDomain.LEGAL,
            steward=StewardType.HUMAN_PM,
            amount=0,
            agent_note=(
                "에이전트 추천 공급사 리스트 제공 가능.\n"
                "최종 계약은 PM Trang 또는 CEO re.eul 서명 필요."
            ),
        ),
        CollabTask(
            task_id="S-002",
            name="초기 상품 매입 (실물)",
            description="첫 달 재고 매입 — 실제 대금 지급",
            domain=TaskDomain.PHYSICAL,
            steward=StewardType.HUMAN_CEO,
            amount=1820000,   # 예상 매입원가
            agent_note=(
                "매입 상품·수량·단가는 사업계획서 기준.\n"
                "실제 대금 이체는 CEO re.eul 최종 승인 후 진행."
            ),
        ),
        CollabTask(
            task_id="S-003",
            name="PG사 실계약 체결",
            description="KCP·Toss·Inicis 등 실 결제 PG 계약 (사업자 등록 필요)",
            domain=TaskDomain.LEGAL,
            steward=StewardType.AI_MALU,
            amount=0,
            agent_note=(
                "Malu가 계약 조건·수수료율 검토.\n"
                "사업자등록번호·통장사본은 CEO re.eul 제공 필요."
            ),
        ),
        CollabTask(
            task_id="S-004",
            name="물류·배송 업체 계약",
            description="CJ대한통운·롯데택배 등 배송 계약 및 단가 협상",
            domain=TaskDomain.PHYSICAL,
            steward=StewardType.HUMAN_PM,
            amount=0,
            agent_note=(
                "에이전트는 배송 추적 API 연동만 담당.\n"
                "배송 업체 계약·단가 협상은 PM Trang 직접 처리."
            ),
        ),
        CollabTask(
            task_id="S-005",
            name="식품 위생·통신판매 신고",
            description="식품 온라인 판매를 위한 법적 신고·인허가",
            domain=TaskDomain.LEGAL,
            steward=StewardType.HUMAN_CEO,
            amount=0,
            agent_note=(
                "법적 신고는 에이전트 권한 외.\n"
                "관할 기관 제출 서류는 에이전트가 초안 작성 지원 가능."
            ),
        ),
        CollabTask(
            task_id="S-006",
            name="반품·환불 실물 처리",
            description="반품 접수 시 실물 회수·재검수·재고 복구",
            domain=TaskDomain.PHYSICAL,
            steward=StewardType.HUMAN_PM,
            amount=0,
            agent_note=(
                "반품 접수·고객 안내는 에이전트 자율 처리.\n"
                "실물 회수 후 재고 데이터 갱신은 에이전트가 처리."
            ),
        ),
    ]

    # ── 물리적 매입 목록 ──────────────────────────────────────────
    default_products = products or [
        {"name":"인제 황태채",    "qty":80,  "unit":3500, "supplier":"인제군 황태 협동조합"},
        {"name":"인제 곰취 나물", "qty":60,  "unit":4000, "supplier":"강원 산채 영농조합"},
        {"name":"인제 더덕",      "qty":40,  "unit":6000, "supplier":"인제 약초 영농조합"},
        {"name":"강원도 감자 5kg","qty":50,  "unit":8000, "supplier":"강원 감자 협동조합"},
        {"name":"인제 산나물 세트","qty":30, "unit":12000,"supplier":"인제군 산나물 영농조합"},
        {"name":"지역 특산 꿀",   "qty":20,  "unit":15000,"supplier":"인제 양봉 협동조합"},
    ]
    for p in default_products:
        p["total"] = p["qty"] * p["unit"]
        p["status"] = "PENDING_STEWARD"   # 스튜어드 실행 필요
        plan.procurement_items.append(p)

    return plan


# ── 보고서 생성 ──────────────────────────────────────────────────

def generate_collab_report(plan: CollaborationPlan) -> str:
    total_procurement = sum(p["total"] for p in plan.procurement_items)
    agent_count   = len(plan.agent_tasks)
    steward_count = len(plan.steward_tasks)

    lines = [
        f"# 🤝 {plan.shop_name} — 에이전트·스튜어드 협업 계획서",
        f"",
        f"**계획서 번호**: `{plan.plan_id}`  ",
        f"**요청 에이전트**: `{plan.agent_id}`  ",
        f"**작성일**: {plan.created_at}  ",
        f"**상태**: {plan.status}  ",
        f"",
        f"---",
        f"",
        f"## 개요",
        f"",
        f"| 구분 | 작업 수 | 담당 |",
        f"|------|------:|------|",
        f"| 🤖 에이전트 자율 작업 | {agent_count}건 | `{plan.agent_id}` 단독 실행 |",
        f"| 🤝 스튜어드 협업 필요 | {steward_count}건 | 인간·AI 스튜어드 참여 |",
        f"| 💰 초기 실물 매입 예상 | | {total_procurement:,}원 |",
        f"",
        f"> **원칙**: 에이전트는 디지털 영역을 자율 실행.",
        f"> 실물 매입·법적 계약·현금 지급은 반드시 스튜어드와 협업.",
        f"",
        f"---",
        f"",
        f"## 1. 에이전트 자율 실행 작업 (디지털)",
        f"",
        f"| ID | 작업 | 설명 | 에이전트 노트 |",
        f"|----|------|------|-------------|",
    ]
    for t in plan.agent_tasks:
        lines.append(
            f"| {t.task_id} | **{t.name}** | {t.description} | {t.agent_note or '-'} |"
        )

    lines += [
        f"",
        f"---",
        f"",
        f"## 2. 스튜어드 협업 필요 작업",
        f"",
        f"| ID | 작업 | 영역 | 담당 스튜어드 | 금액 | 에이전트 제안 |",
        f"|----|------|-----|------------|----:|------------|",
    ]
    domain_emoji = {
        "digital": "🤖", "physical": "📦",
        "legal": "⚖️", "hybrid": "🔀"
    }
    for t in plan.steward_tasks:
        emoji = domain_emoji.get(t.domain.value, "")
        amt   = f"{t.amount:,}원" if t.amount else "-"
        lines.append(
            f"| {t.task_id} | **{t.name}** | "
            f"{emoji} {t.domain.value} | "
            f"{t.steward.value if t.steward else '-'} | "
            f"{amt} | {t.agent_note[:40] if t.agent_note else '-'}... |"
        )

    lines += [
        f"",
        f"---",
        f"",
        f"## 3. 실물 매입 목록 (스튜어드 실행 필요)",
        f"",
        f"⚠️ **아래 매입은 실제 대금 지급이 수반됩니다. CEO re.eul 승인 필수.**",
        f"",
        f"| 상품 | 공급사 | 수량 | 단가 | 소계 | 상태 |",
        f"|------|--------|----:|----:|----:|------|",
    ]
    for p in plan.procurement_items:
        lines.append(
            f"| {p['name']} | {p['supplier']} | "
            f"{p['qty']}개 | {p['unit']:,}원 | "
            f"{p['total']:,}원 | ⏳ 스튜어드 대기 |"
        )
    lines.append(
        f"| **합계** | | | | **{total_procurement:,}원** | |"
    )

    lines += [
        f"",
        f"---",
        f"",
        f"## 4. 협업 프로세스",
        f"",
        f"```",
        f"[에이전트 {plan.agent_id}]",
        f"  ① 이 계획서 생성 및 제출",
        f"  ② A-001~A-006 디지털 작업 준비 완료",
        f"        ↓",
        f"[스튜어드 검토]",
        f"  ③ PM Trang: S-001 공급사 계약 협의",
        f"  ③ Malu(AI): S-003 PG 계약 조건 검토",
        f"  ③ CEO re.eul: S-002 매입 대금 최종 승인",
        f"        ↓",
        f"[병렬 실행]",
        f"  에이전트: 쇼핑몰 코드 배포 · 결제 테스트",
        f"  스튜어드: 공급사 매입 · PG 계약 · 물류 계약",
        f"        ↓",
        f"[운영 시작]",
        f"  ④ 스튜어드: 실물 입고 완료 보고 → 에이전트 재고 데이터 갱신",
        f"  ④ 에이전트: 실 결제 전환 → 쇼핑몰 오픈",
        f"  ④ 에이전트: 매월 P&L 보고서 자동 생성 → CEO 보고",
        f"```",
        f"",
        f"---",
        f"",
        f"## 5. 스튜어드 승인 요청",
        f"",
        f"아래 내용을 확인 후 댓글로 회신해 주세요:",
        f"",
        f"- ✅ **APPROVED** — 계획 승인, 각 담당자 실행 시작",
        f"- 📝 **MODIFY [항목ID] [내용]** — 수정 요청",
        f"- ❌ **HOLD** — 보류 (사유 기재)",
        f"",
        f"---",
        f"",
        f"*{plan.agent_id} · Mulberry AgenticAI · {plan.created_at}*  ",
        f"*🌿 에이전트는 계획하고, 스튜어드는 실제 세계와 연결한다.*",
    ]
    return "\n".join(lines)


# ── 스튜어드 승인 처리 ───────────────────────────────────────────

def process_steward_approval(plan_id: str, steward: str,
                             decision: str, notes: str = "") -> bool:
    path = COLLAB_DIR / f"{plan_id}.yaml"
    if not path.exists():
        print(f"❌ 계획서 없음: {plan_id}")
        return False

    raw  = yaml.safe_load(path.read_text(encoding="utf-8"))
    raw["status"]            = "APPROVED" if "APPROVED" in decision.upper() else "HOLD"
    raw["steward_approval"]  = decision
    raw["approved_at"]       = TIMESTAMP
    raw["approved_by"]       = steward
    raw["steward_notes"]     = notes

    path.write_text(yaml.dump(raw, allow_unicode=True, sort_keys=False),
                    encoding="utf-8")

    print(f"✅ 스튜어드 결정 기록: {decision}")
    print(f"   계획서: {plan_id}")
    print(f"   스튜어드: {steward}")
    return True


# ── 메인 ─────────────────────────────────────────────────────────

def cmd_create(agent_id: str, shop_name: str):
    plan    = classify_tasks(agent_id, shop_name)
    report  = generate_collab_report(plan)

    # 파일 저장
    plan_path = COLLAB_DIR / f"{plan.plan_id}.yaml"
    plan_path.write_text(
        yaml.dump(asdict(plan), allow_unicode=True, sort_keys=False),
        encoding="utf-8"
    )
    rpt_path = REPORTS_DIR / f"{plan.plan_id}_collab.md"
    rpt_path.write_text(report, encoding="utf-8")

    print(report)
    print(f"\n📄 협업 계획서 저장: {rpt_path}")

    # GitHub Issue 게시
    if GH_TOKEN:
        import urllib.request
        payload = json.dumps({
            "title": f"🤝 [협업 요청] {shop_name} 운영 준비 — 스튜어드 검토 요청",
            "body":  report,
            "labels": ["steward-review", "collaboration", "pending-approval"],
        }).encode("utf-8")
        req = urllib.request.Request(
            f"https://api.github.com/repos/{REPO}/issues",
            data=payload,
            headers={"Authorization": f"token {GH_TOKEN}",
                     "Content-Type": "application/json"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                result = json.loads(r.read())
                print(f"📋 GitHub 이슈 생성: #{result.get('number')} {result.get('html_url')}")
        except Exception as e:
            print(f"  (이슈 생성 실패: {e})")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="에이전트·스튜어드 협업 시스템")
    sub = p.add_subparsers(dest="cmd")

    cr = sub.add_parser("create", help="협업 계획서 생성")
    cr.add_argument("--agent", required=True)
    cr.add_argument("--shop",  required=True)

    ap = sub.add_parser("approve", help="스튜어드 승인 처리")
    ap.add_argument("--plan-id",  required=True)
    ap.add_argument("--steward",  required=True)
    ap.add_argument("--decision", required=True)
    ap.add_argument("--notes",    default="")

    args = p.parse_args()
    if args.cmd == "create":
        cmd_create(args.agent, args.shop)
    elif args.cmd == "approve":
        process_steward_approval(
            args.plan_id, args.steward, args.decision, args.notes)
    else:
        p.print_help()
