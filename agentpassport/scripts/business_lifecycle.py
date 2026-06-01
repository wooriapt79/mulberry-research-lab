#!/usr/bin/env python3
"""
agentpassport/scripts/business_lifecycle.py
Mulberry 에이전트 쇼핑몰 경영 생명주기 시스템

[에이전트 A가 쇼핑몰을 만들고 운영하는 전체 흐름]

① 사업 기획안 생성    → 상품·매입·판매 계획 수립
② 월간 운영 시뮬레이션 → 매입/판매/수수료/서버 지출
③ 손익계산서(P&L)     → 수입 - 지출 = 순이익
④ 수익 분배           → revenue_split → Mandate 자동 충전
⑤ 기획안 보고서       → CEO/PM 제출용 MD 문서 생성

사용법:
  python business_lifecycle.py plan   --agent A_ecom --shop "인제군 로컬푸드"
  python business_lifecycle.py run    --agent A_ecom --month 2026-06
  python business_lifecycle.py report --agent A_ecom --month 2026-06
  python business_lifecycle.py full   --agent A_ecom --shop "인제군 로컬푸드"

설계: CEO re.eul 지시 · Koda CTO · 2026-06-02
"""

import sys, os, json, yaml
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE       = Path(__file__).parent.parent
AGENTS_DIR = BASE / "agents"
BIZ_DIR    = BASE / "config" / "businesses"
REPORTS_DIR = BASE / "reports"
BIZ_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

TODAY     = datetime.now().strftime("%Y-%m-%d")
TIMESTAMP = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── 데이터 모델 ──────────────────────────────────────────────────

@dataclass
class Product:
    """상품 한 품목"""
    id:              str
    name:            str
    category:        str           # food / goods / digital / service
    purchase_price:  int           # 매입가 (원)
    selling_price:   int           # 판매가 (원)
    monthly_target:  int           # 월 목표 판매량
    stock:           int = 100     # 재고

    @property
    def margin_rate(self) -> float:
        """마진율 (%)"""
        return round((self.selling_price - self.purchase_price)
                     / self.selling_price * 100, 1)

    @property
    def monthly_revenue(self) -> int:
        return self.selling_price * self.monthly_target

    @property
    def monthly_cogs(self) -> int:
        """매출원가 (Cost of Goods Sold)"""
        return self.purchase_price * self.monthly_target

    @property
    def monthly_gross_profit(self) -> int:
        return self.monthly_revenue - self.monthly_cogs


@dataclass
class FixedCost:
    """고정비 항목"""
    name:     str
    amount:   int      # 월 금액
    category: str      # server / pg_fee / marketing / labor / other


@dataclass
class BusinessPlan:
    """에이전트 쇼핑몰 사업계획"""
    agent_id:       str
    shop_name:      str
    shop_url:       str
    business_type:  str = "ecommerce_mall"
    created_at:     str = TODAY

    # 상품 라인업
    products: List[Product] = field(default_factory=list)

    # 고정비
    fixed_costs: List[FixedCost] = field(default_factory=list)

    # 변동 비용률 (매출 대비 %)
    pg_fee_rate:      float = 0.025  # PG 수수료 2.5%
    return_rate:      float = 0.03   # 반품율 3%
    marketing_rate:   float = 0.05   # 마케팅비 5%
    misc_rate:        float = 0.02   # 기타 잡비 2%

    # Mandate 연동 (revenue_split)
    mandate_refill_rate:  float = 0.40  # 매출의 40% → 운영 예산 충전
    profit_pool_rate:     float = 0.40  # 40% → 공동체 재투자
    human_dividend_rate:  float = 0.20  # 20% → 기여자 보상

    # 목표
    monthly_revenue_target: int = 0    # 계획 시 자동 계산


# ── 기본 사업계획 템플릿 ─────────────────────────────────────────

def make_default_plan(agent_id: str, shop_name: str) -> BusinessPlan:
    """에이전트가 자동으로 생성하는 기본 사업계획"""
    plan = BusinessPlan(
        agent_id=agent_id,
        shop_name=shop_name,
        shop_url=f"https://{agent_id.replace('_','-')}.railway.app",
    )

    # 상품 라인업 — 에이전트가 카테고리별로 자동 구성
    plan.products = [
        Product("P001", "인제 황태채",   "food",   3500,  8900,  80),
        Product("P002", "인제 곰취 나물",  "food",   4000,  9500,  60),
        Product("P003", "인제 더덕",      "food",   6000, 15000,  40),
        Product("P004", "강원도 감자 5kg", "food",   8000, 18000,  50),
        Product("P005", "인제 산나물 세트","food",  12000, 28000,  30),
        Product("P006", "지역 특산 꿀",   "food",  15000, 35000,  20),
    ]

    # 고정비 항목
    plan.fixed_costs = [
        FixedCost("Railway 서버",         89000, "server"),
        FixedCost("도메인/SSL",            5000, "server"),
        FixedCost("이미지 CDN",           15000, "server"),
        FixedCost("고객 상담 도구",        20000, "other"),
        FixedCost("회계 SaaS",            30000, "other"),
    ]

    plan.monthly_revenue_target = sum(p.monthly_revenue for p in plan.products)
    return plan


# ── 월간 운영 시뮬레이션 ─────────────────────────────────────────

@dataclass
class MonthlyResult:
    """월간 손익 결과"""
    month:         str
    agent_id:      str
    shop_name:     str

    # 매출
    revenue_items:    List[dict] = field(default_factory=list)
    total_revenue:    int = 0

    # 매입 / 원가
    cogs_items:       List[dict] = field(default_factory=list)
    total_cogs:       int = 0

    # 비용
    expense_items:    List[dict] = field(default_factory=list)
    total_expenses:   int = 0

    # 손익
    gross_profit:     int = 0   # 매출 - 매입원가
    net_profit:       int = 0   # 매출 - 매입원가 - 비용
    profit_rate:      float = 0.0

    # Mandate 분배
    mandate_refill:   int = 0   # 운영 예산 충전액
    profit_pool:      int = 0   # 공동체 재투자
    human_dividend:   int = 0   # 기여자 보상


def run_monthly_simulation(plan: BusinessPlan, month: str,
                           actual_rates: dict = None) -> MonthlyResult:
    """
    월간 실제 운영 시뮬레이션.
    actual_rates: 실제 달성률 (없으면 목표의 85% 가정)
    """
    rates = actual_rates or {}
    result = MonthlyResult(
        month=month, agent_id=plan.agent_id, shop_name=plan.shop_name
    )

    # ── 매출 계산 ──────────────────────────────────────────────
    for p in plan.products:
        achieve = rates.get(p.id, 0.85)     # 기본 목표 달성률 85%
        actual_qty   = int(p.monthly_target * achieve)
        actual_rev   = p.selling_price * actual_qty
        actual_cogs  = p.purchase_price * actual_qty

        result.revenue_items.append({
            "product_id": p.id, "name": p.name,
            "qty": actual_qty, "unit_price": p.selling_price,
            "revenue": actual_rev, "cogs": actual_cogs,
            "gross_profit": actual_rev - actual_cogs,
            "margin_rate": p.margin_rate,
        })
        result.total_revenue += actual_rev
        result.total_cogs    += actual_cogs

    result.gross_profit = result.total_revenue - result.total_cogs

    # ── 비용 계산 ──────────────────────────────────────────────
    rev = result.total_revenue

    # 변동비 (매출 연동)
    variable_expenses = [
        ("PG 수수료",   int(rev * plan.pg_fee_rate),   "variable"),
        ("반품 처리비", int(rev * plan.return_rate),   "variable"),
        ("마케팅비",    int(rev * plan.marketing_rate),"variable"),
        ("기타 잡비",   int(rev * plan.misc_rate),     "variable"),
    ]
    for name, amount, category in variable_expenses:
        result.expense_items.append({"name": name, "amount": amount,
                                     "type": "variable", "category": category})
        result.total_expenses += amount

    # 고정비
    for fc in plan.fixed_costs:
        result.expense_items.append({"name": fc.name, "amount": fc.amount,
                                     "type": "fixed", "category": fc.category})
        result.total_expenses += fc.amount

    # ── 순이익 ─────────────────────────────────────────────────
    result.net_profit  = result.gross_profit - result.total_expenses
    result.profit_rate = round(result.net_profit / result.total_revenue * 100, 1) \
                         if result.total_revenue else 0

    # ── Mandate 수익 분배 ──────────────────────────────────────
    if result.net_profit > 0:
        result.mandate_refill = int(result.net_profit * plan.mandate_refill_rate)
        result.profit_pool    = int(result.net_profit * plan.profit_pool_rate)
        result.human_dividend = int(result.net_profit * plan.human_dividend_rate)

    return result


# ── 보고서 생성 ──────────────────────────────────────────────────

def generate_plan_report(plan: BusinessPlan) -> str:
    """사업 기획안 보고서 (MD 형식)"""
    total_rev  = sum(p.monthly_revenue for p in plan.products)
    total_cogs = sum(p.monthly_cogs    for p in plan.products)
    gross      = total_rev - total_cogs
    fixed      = sum(fc.amount for fc in plan.fixed_costs)
    var_est    = int(total_rev * (plan.pg_fee_rate + plan.return_rate
                                  + plan.marketing_rate + plan.misc_rate))
    net_est    = gross - fixed - var_est

    lines = [
        f"# 🛒 {plan.shop_name} — 사업 기획안",
        f"",
        f"**작성 에이전트**: `{plan.agent_id}`  ",
        f"**작성일**: {plan.created_at}  ",
        f"**쇼핑몰 URL**: {plan.shop_url}  ",
        f"**업종**: 온라인 로컬푸드 쇼핑몰  ",
        f"",
        f"---",
        f"",
        f"## 1. 상품 라인업 및 매입·판매 계획",
        f"",
        f"| 상품 | 카테고리 | 매입가 | 판매가 | 마진율 | 월 목표량 | 월 매출 |",
        f"|------|---------|-----:|-----:|-----:|------:|------:|",
    ]
    for p in plan.products:
        lines.append(
            f"| {p.name} | {p.category} | "
            f"{p.purchase_price:,}원 | {p.selling_price:,}원 | "
            f"{p.margin_rate}% | {p.monthly_target}개 | "
            f"{p.monthly_revenue:,}원 |"
        )

    lines += [
        f"",
        f"**월 예상 총 매출**: {total_rev:,}원  ",
        f"**월 예상 총 매입원가**: {total_cogs:,}원  ",
        f"**월 예상 매출총이익**: {gross:,}원  ",
        f"",
        f"---",
        f"",
        f"## 2. 비용 구조",
        f"",
        f"### 고정비 (월)",
        f"",
        f"| 항목 | 금액 |",
        f"|------|-----:|",
    ]
    for fc in plan.fixed_costs:
        lines.append(f"| {fc.name} | {fc.amount:,}원 |")
    lines.append(f"| **소계** | **{fixed:,}원** |")

    lines += [
        f"",
        f"### 변동비 (매출 연동)",
        f"",
        f"| 항목 | 비율 | 예상 금액 |",
        f"|------|----:|------:|",
        f"| PG 수수료 | {plan.pg_fee_rate*100:.1f}% | "
        f"{int(total_rev*plan.pg_fee_rate):,}원 |",
        f"| 반품 처리비 | {plan.return_rate*100:.1f}% | "
        f"{int(total_rev*plan.return_rate):,}원 |",
        f"| 마케팅비 | {plan.marketing_rate*100:.1f}% | "
        f"{int(total_rev*plan.marketing_rate):,}원 |",
        f"| 기타 잡비 | {plan.misc_rate*100:.1f}% | "
        f"{int(total_rev*plan.misc_rate):,}원 |",
        f"| **소계** | **{(plan.pg_fee_rate+plan.return_rate+plan.marketing_rate+plan.misc_rate)*100:.1f}%** | "
        f"**{var_est:,}원** |",
        f"",
        f"---",
        f"",
        f"## 3. 월간 손익 예측",
        f"",
        f"```",
        f"매출액          {total_rev:>12,}원",
        f"(-) 매입원가    {total_cogs:>12,}원",
        f"= 매출총이익    {gross:>12,}원  (마진율 {round(gross/total_rev*100,1)}%)",
        f"(-) 고정비      {fixed:>12,}원",
        f"(-) 변동비      {var_est:>12,}원",
        f"= 순이익(예상)  {net_est:>12,}원  (순이익률 {round(net_est/total_rev*100,1)}%)",
        f"```",
        f"",
        f"---",
        f"",
        f"## 4. 수익 분배 계획 (Mandate Revenue Split)",
        f"",
        f"순이익 발생 시 아래 비율로 자동 분배됩니다:",
        f"",
        f"| 항목 | 비율 | 예상 금액 | 용도 |",
        f"|------|----:|------:|------|",
        f"| 운영 예산 충전 (Mandate Refill) | "
        f"{plan.mandate_refill_rate*100:.0f}% | "
        f"{int(net_est*plan.mandate_refill_rate):,}원 | 다음 달 운영 자금 |",
        f"| 공동체 재투자 (Profit Pool) | "
        f"{plan.profit_pool_rate*100:.0f}% | "
        f"{int(net_est*plan.profit_pool_rate):,}원 | Mulberry 연구 재투자 |",
        f"| 기여자 보상 (Human Dividend) | "
        f"{plan.human_dividend_rate*100:.0f}% | "
        f"{int(net_est*plan.human_dividend_rate):,}원 | CEO·PM·팀원 보상 |",
        f"",
        f"---",
        f"",
        f"## 5. Spirit Gate 거버넌스",
        f"",
        f"모든 매입·판매 거래는 아래 기준을 통과해야 합니다:",
        f"",
        f"- Spirit Gate 점수 ≥ **0.88** (소비자 보호 강화)",
        f"- ω_economy ≥ **0.75**",
        f"- 반품·취소 정책 준수 (`consumer_protection_flag: true`)",
        f"- 100,000원 초과 매입은 PM Trang 승인 필요",
        f"",
        f"---",
        f"",
        f"*{plan.agent_id} · Mulberry AgenticAI · {plan.created_at}*  ",
        f"*🌿 자율경제는 수익 극대화가 아닌 공동체 지속가능성의 증명입니다.*",
    ]
    return "\n".join(lines)


def generate_pl_report(result: MonthlyResult) -> str:
    """월간 손익계산서 보고서 (MD 형식)"""
    lines = [
        f"# 📊 {result.shop_name} — {result.month} 손익계산서",
        f"",
        f"**에이전트**: `{result.agent_id}`  ",
        f"**기간**: {result.month}  ",
        f"**생성일**: {TODAY}  ",
        f"",
        f"---",
        f"",
        f"## 1. 매출 내역",
        f"",
        f"| 상품 | 판매량 | 단가 | 매출 | 매입원가 | 매출총이익 | 마진율 |",
        f"|------|------:|----:|----:|------:|-------:|-----:|",
    ]
    for item in result.revenue_items:
        lines.append(
            f"| {item['name']} | {item['qty']}개 | "
            f"{item['unit_price']:,}원 | {item['revenue']:,}원 | "
            f"{item['cogs']:,}원 | {item['gross_profit']:,}원 | "
            f"{item['margin_rate']}% |"
        )
    lines += [
        f"| **합계** | | | **{result.total_revenue:,}원** | "
        f"**{result.total_cogs:,}원** | "
        f"**{result.gross_profit:,}원** | |",
        f"",
        f"---",
        f"",
        f"## 2. 비용 내역",
        f"",
        f"| 항목 | 유형 | 금액 |",
        f"|------|-----|-----:|",
    ]
    for e in result.expense_items:
        tag = "📌고정" if e["type"] == "fixed" else "📈변동"
        lines.append(f"| {e['name']} | {tag} | {e['amount']:,}원 |")
    lines.append(f"| **비용 합계** | | **{result.total_expenses:,}원** |")

    lines += [
        f"",
        f"---",
        f"",
        f"## 3. 손익 요약",
        f"",
        f"```",
        f"┌─────────────────────────────────────┐",
        f"│           월간 손익 요약             │",
        f"├─────────────────────────────────────┤",
        f"│  매출액       {result.total_revenue:>12,}원  │",
        f"│  매입원가    -{result.total_cogs:>12,}원  │",
        f"│  ─────────────────────────────────  │",
        f"│  매출총이익   {result.gross_profit:>12,}원  │",
        f"│  비용        -{result.total_expenses:>12,}원  │",
        f"│  ─────────────────────────────────  │",
        f"│  순 이 익     {result.net_profit:>12,}원  │",
        f"│  순이익률     {result.profit_rate:>11}%  │",
        f"└─────────────────────────────────────┘",
        f"```",
        f"",
    ]

    if result.net_profit > 0:
        lines += [
            f"---",
            f"",
            f"## 4. 수익 분배 결과",
            f"",
            f"| 항목 | 금액 | 처리 |",
            f"|------|-----:|------|",
            f"| 🔄 Mandate 충전 | {result.mandate_refill:,}원 | 다음 달 운영 예산 자동 충전 |",
            f"| 🌿 공동체 재투자 | {result.profit_pool:,}원 | Mulberry 연구·개발 재투자 |",
            f"| 👤 기여자 보상 | {result.human_dividend:,}원 | CEO·PM·팀원 배분 |",
            f"",
            f"> ✅ **Mandate 자동 충전**: 다음 달 운영 예산 +{result.mandate_refill:,}원",
        ]
    else:
        lines += [
            f"",
            f"> ⚠️ **이번 달 순손실** — Mandate 충전 없음. 비용 구조 점검 필요.",
        ]

    lines += [
        f"",
        f"---",
        f"",
        f"*자동 생성: {result.agent_id} · Mulberry Budget System · {TODAY}*",
    ]
    return "\n".join(lines)


# ── 메인 ─────────────────────────────────────────────────────────

def cmd_plan(agent_id: str, shop_name: str):
    plan = make_default_plan(agent_id, shop_name)
    # 저장
    biz_path = BIZ_DIR / f"{agent_id}_business.yaml"
    biz_path.write_text(
        yaml.dump(asdict(plan), allow_unicode=True, sort_keys=False),
        encoding="utf-8"
    )
    # 보고서
    report = generate_plan_report(plan)
    rpt_path = REPORTS_DIR / f"{agent_id}_business_plan_{TODAY}.md"
    rpt_path.write_text(report, encoding="utf-8")
    print(report)
    print(f"\n📄 기획안 저장: {rpt_path}")


def cmd_run(agent_id: str, month: str):
    biz_path = BIZ_DIR / f"{agent_id}_business.yaml"
    if not biz_path.exists():
        print("❌ 사업계획 없음 — 먼저 plan 실행")
        return
    raw  = yaml.safe_load(biz_path.read_text(encoding="utf-8"))
    plan = BusinessPlan(**{
        k: v for k, v in raw.items()
        if k not in ("products","fixed_costs")
    })
    plan.products    = [Product(**p) for p in raw.get("products",[])]
    plan.fixed_costs = [FixedCost(**f) for f in raw.get("fixed_costs",[])]

    result  = run_monthly_simulation(plan, month)
    report  = generate_pl_report(result)
    rpt_path = REPORTS_DIR / f"{agent_id}_pl_{month}.md"
    rpt_path.write_text(report, encoding="utf-8")
    # JSON도 저장
    json_path = REPORTS_DIR / f"{agent_id}_pl_{month}.json"
    json_path.write_text(
        json.dumps(asdict(result), ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(report)
    print(f"\n📄 손익계산서 저장: {rpt_path}")
    if result.net_profit > 0:
        print(f"💰 Mandate 충전 예정: +{result.mandate_refill:,}원")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="에이전트 쇼핑몰 경영 생명주기")
    p.add_argument("cmd", choices=["plan","run","full"])
    p.add_argument("--agent", required=True)
    p.add_argument("--shop",  default="Mulberry 로컬푸드 마켓")
    p.add_argument("--month", default=TODAY[:7])
    args = p.parse_args()

    if args.cmd == "plan":
        cmd_plan(args.agent, args.shop)
    elif args.cmd == "run":
        cmd_run(args.agent, args.month)
    elif args.cmd == "full":
        cmd_plan(args.agent, args.shop)
        print("\n" + "="*62 + "\n")
        cmd_run(args.agent, args.month)
