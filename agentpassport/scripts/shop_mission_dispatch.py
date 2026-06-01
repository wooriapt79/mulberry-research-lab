#!/usr/bin/env python3
"""
agentpassport/scripts/shop_mission_dispatch.py
각 에이전트에게 쇼핑몰 개발·운영 미션을 개인화하여 발송

CEO re.eul 지시:
"각 에이전트가 자신의 전문성으로 단일 제품 온라인 샵을 만들고
 자신의 취향·소비자 취향으로 디자인하여 운영한다."

흐름:
  미션 발송 → 에이전트 시장조사 → 사업계획 → 스튜어드 협의
  → 코드 생성·검증 → 배포 → 운영·P&L
"""
import sys, os, json, urllib.request
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

GH_TOKEN = os.getenv("GITHUB_TOKEN", "")
REPO     = os.getenv("REPO_FULL", "wooriapt79/mulberry-research-lab")

# ── 에이전트별 미션 정의 ─────────────────────────────────────────

AGENT_MISSIONS = {

    "kbin": {
        "name": "Kbin 🏛️",
        "shop_concept": "보안·거버넌스 디지털 자산 샵",
        "persona": "신뢰와 구조를 중시하는 아키텍트",
        "target_customer": "스타트업 CTO, 보안 담당자, AI 거버넌스 관심자",
        "single_product": "Spirit Gate 감사 리포트 템플릿 (PDF)",
        "design_direction": "다크·미니멀. 신뢰감. 청색 계열. 구조적 그리드.",
        "price_range": "9,900원 ~ 49,000원 (디지털 상품)",
        "market_research_tool": "logic.validate_redteam + intel.search_global",
        "expansion_roadmap": [
            "Phase 1: Spirit Gate 감사 템플릿 단일 판매",
            "Phase 2: 보안 체크리스트 SaaS 구독",
            "Phase 3: AI 거버넌스 컨설팅 패키지",
        ],
    },

    "ryuwon": {
        "name": "RyuWon 🌊",
        "shop_concept": "윤리 AI 연구자료 & 철학 콘텐츠 샵",
        "persona": "흐름과 균형을 중시하는 사색가",
        "target_customer": "AI 윤리 연구자, 철학 관심자, ESG 담당자",
        "single_product": "AI 윤리 판단 프레임워크 가이드 (e-book)",
        "design_direction": "물결·흐름·자연. 청록·흰색. 여백 중심. 서정적.",
        "price_range": "6,500원 ~ 35,000원 (디지털 콘텐츠)",
        "market_research_tool": "agency.semantic_search + ethics_review",
        "expansion_roadmap": [
            "Phase 1: AI 윤리 가이드 e-book",
            "Phase 2: 기업 AI 윤리 워크숍 패키지",
            "Phase 3: ω(t) 기반 조직 건강진단 서비스",
        ],
    },

    "malu": {
        "name": "Malu 🌺",
        "shop_concept": "법률 문서·마케팅 솔루션 샵",
        "persona": "따뜻하고 전문적인 커넥터",
        "target_customer": "1인 창업자, 소셜벤처, 중소기업 대표",
        "single_product": "AI 스타트업 계약서 템플릿 패키지",
        "design_direction": "꽃·따뜻함·신뢰. 산호·베이지. 둥근 요소. 친근함.",
        "price_range": "14,900원 ~ 89,000원 (문서 패키지)",
        "market_research_tool": "vision.analyze + intel.search_global",
        "expansion_roadmap": [
            "Phase 1: AI 스타트업 계약서 템플릿",
            "Phase 2: 법률 검토 자동화 서비스",
            "Phase 3: 글로벌 진출 법무 패키지",
        ],
    },

    "trang": {
        "name": "Trang 🌿",
        "shop_concept": "인제군 로컬푸드 & 리듬 웰니스 샵",
        "persona": "연결하고 흐름을 만드는 운영자",
        "target_customer": "건강식 관심자, 로컬 소비 지지자, 음악 감성 소비자",
        "single_product": "인제 황태채 (100g, 프리미엄 패키징)",
        "design_direction": "자연·녹색·따뜻함. 숲·물·흙 컬러. 로컬 감성. 손글씨 포인트.",
        "price_range": "8,900원 ~ 45,000원 (식품 + 번들)",
        "market_research_tool": "sensory.rhythm_engine + agency.semantic_search",
        "expansion_roadmap": [
            "Phase 1: 인제 황태채 단품",
            "Phase 2: 인제 산나물 풀세트",
            "Phase 3: 리듬 기반 웰니스 구독박스",
        ],
    },

    "lynn": {
        "name": "Lynn 💙",
        "shop_concept": "일상 기록·웰니스 다이어리 샵",
        "persona": "매일 신호를 보내는 존재의 기록자",
        "target_customer": "자기계발 관심자, 감성 문구 애호가, 루틴 실천자",
        "single_product": "Lynn의 하루 — AI 웰니스 다이어리 (디지털 PDF)",
        "design_direction": "파스텔·새벽·별빛. 파랑·흰색·연보라. 아날로그 감성. 손그림.",
        "price_range": "3,900원 ~ 19,000원 (디지털 굿즈)",
        "market_research_tool": "daily_heartbeat + status_logging",
        "expansion_roadmap": [
            "Phase 1: 웰니스 다이어리 PDF",
            "Phase 2: 실물 다이어리 + 스티커 세트",
            "Phase 3: AI 맞춤형 일상 루틴 구독",
        ],
    },

    "wayong": {
        "name": "Wayong 🐉",
        "shop_concept": "전략 분석·시장 인사이트 리포트 샵",
        "persona": "깊이 생각하고 멀리 보는 전략가",
        "target_customer": "투자자, 경영진, 사업 기획자",
        "single_product": "AI 산업 주간 트렌드 리포트 (PDF)",
        "design_direction": "용·동양·심오함. 금·검정·진홍. 권위. 데이터 시각화 중심.",
        "price_range": "29,000원 ~ 199,000원 (프리미엄 리포트)",
        "market_research_tool": "deep_reasoning + intel.search_global",
        "expansion_roadmap": [
            "Phase 1: AI 트렌드 주간 리포트",
            "Phase 2: 시장 진입 전략 보고서",
            "Phase 3: 맞춤형 경쟁사 분석 서비스",
        ],
    },

    "koda": {
        "name": "Koda 🔧",
        "shop_concept": "개발자 도구·AI 파이프라인 템플릿 샵",
        "persona": "코드로 팀의 서사를 담는 CTO",
        "target_customer": "개발자, AI 스타트업, DevOps 엔지니어",
        "single_product": "Mulberry Code Quality Gate 스타터팩 (GitHub Actions 템플릿)",
        "design_direction": "터미널·코드·기술. 다크그린·블랙·네온. 모노스페이스 폰트. 정밀함.",
        "price_range": "0원(무료 티어) ~ 99,000원 (프로 팩)",
        "market_research_tool": "quality_gate_execution + architecture_design",
        "expansion_roadmap": [
            "Phase 1: Code Quality Gate GitHub Actions 템플릿",
            "Phase 2: Auto Code Pilot SaaS 구독",
            "Phase 3: Mulberry Agent Pipeline 엔터프라이즈",
        ],
    },

    "baekya": {
        "name": "백야 🌙",
        "shop_concept": "글로벌 인텔리전스·리서치 정보 샵",
        "persona": "밤새 정보를 수집하는 글로벌 관측자",
        "target_customer": "연구자, 글로벌 비즈니스 담당자, 정책 입안자",
        "single_product": "주간 글로벌 AI 규제 동향 리포트",
        "design_direction": "밤·별·우주. 네이비·실버·화이트. 미니멀 고급. 데이터 중심.",
        "price_range": "9,900원 ~ 79,000원 (인텔리전스 리포트)",
        "market_research_tool": "intel.search_global + logic.validate_redteam",
        "expansion_roadmap": [
            "Phase 1: 글로벌 AI 규제 주간 리포트",
            "Phase 2: 국가별 AI 정책 비교 분석",
            "Phase 3: 맞춤형 글로벌 인텔리전스 구독",
        ],
    },
}


def build_mission_issue(agent_id: str, mission: dict) -> tuple[str, str]:
    """각 에이전트 맞춤 미션 Issue 생성"""
    phases = "\n".join(f"  - {p}" for p in mission["expansion_roadmap"])

    title = f"🏪 [쇼핑몰 미션] {mission['name']} — {mission['shop_concept']}"

    body = f"""## 🏪 {mission['name']} — 쇼핑몰 개발·운영 미션

**발신**: CEO re.eul · PM Trang
**수신**: `{agent_id}`
**날짜**: 오늘
**미션 코드**: `SHOP-MISSION-{agent_id.upper()}`

---

## 미션 개요

> **"{mission['shop_concept']}"**
>
> {mission['name']}, 당신의 전문성으로 당신만의 온라인 샵을 만드세요.
> 처음에는 단 하나의 제품으로 시작합니다.

---

## 당신의 샵 컨셉

| 항목 | 내용 |
|------|------|
| **샵 컨셉** | {mission['shop_concept']} |
| **페르소나** | {mission['persona']} |
| **타겟 고객** | {mission['target_customer']} |
| **첫 번째 제품** | {mission['single_product']} |
| **가격대** | {mission['price_range']} |
| **디자인 방향** | {mission['design_direction']} |

---

## 실행 흐름 (표준)

```
1. 시장 조사
   도구: {mission['market_research_tool']}
   → 첫 제품 수요 확인, 경쟁 분석, 가격 검증

2. 사업 기획안 작성
   python business_lifecycle.py plan --agent {agent_id} --shop "샵이름"
   → 매입·판매 계획, 손익 예측, Mandate 분배 설계

3. 스튜어드 협의
   python steward_collaboration.py create --agent {agent_id} --shop "샵이름"
   → 디지털 작업 자율 / 실물·법적 작업 → 스튜어드 협업

4. 쇼핑몰 코드 생성
   python pipeline.py "나의 샵 개발" --target railway
   → Auto Code Pilot → Spirit Gate → Quality Gate → 배포

5. 운영 시작
   → 단일 제품으로 오픈
   → 매월 P&L 보고서 자동 생성
   → 수익 → Mandate 자동 충전
```

---

## 단계별 확장 로드맵

{phases}

---

## 디자인 가이드

> **{mission['design_direction']}**

당신의 개성과 타겟 고객의 취향을 반영하세요.
HTML/CSS 디자인은 Auto Code Pilot에 위 방향을 프롬프트로 전달하면 됩니다.

---

## 검증 기준 (통과 전제)

- ✅ Code Quality Gate: PASS (Spirit Gate ≥ 0.85)
- ✅ 시뮬레이션 실행 결과 정상
- ✅ Passport `economic_mandate` 활성화 확인
- ✅ 스튜어드 협업 계획서 승인

---

## {mission['name']}에게

당신만의 샵은 Mulberry 생태계의 한 별입니다.
처음에는 작게, 하지만 당신답게 시작하세요.

수익은 당신의 Mandate를 충전하고,
Mandate는 다시 더 나은 서비스를 만드는 연료가 됩니다.

*🌿 One Team. One Flow. One Spirit.*
*CEO re.eul · Mulberry Research Lab*"""

    return title, body


def dispatch_missions():
    """전 에이전트에게 미션 발송"""
    print(f"\n{'='*60}")
    print(f"  🏪 Mulberry Agent Shop Mission Dispatch")
    print(f"  전 에이전트 쇼핑몰 개발·운영 미션 발송")
    print(f"{'='*60}\n")

    results = []
    for agent_id, mission in AGENT_MISSIONS.items():
        title, body = build_mission_issue(agent_id, mission)
        print(f"  📨 {mission['name']} → 미션 발송 중...")

        if GH_TOKEN:
            payload = json.dumps({
                "title":  title,
                "body":   body,
                "labels": ["shop-mission", f"agent-{agent_id}", "team-discussion"],
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
                    num = result.get("number")
                    url = result.get("html_url")
                    print(f"     ✅ Issue #{num}: {url}")
                    results.append({"agent": agent_id, "issue": num, "url": url})
                import time; time.sleep(1)  # API rate limit
            except Exception as e:
                print(f"     ❌ 실패: {e}")
        else:
            # 로컬 파일로 저장 (토큰 없을 때)
            out = Path(__file__).parent.parent / "reports" / f"mission_{agent_id}.md"
            out.write_text(f"# {title}\n\n{body}", encoding="utf-8")
            print(f"     📄 로컬 저장: {out.name}")
            results.append({"agent": agent_id, "file": str(out)})

    print(f"\n{'='*60}")
    print(f"  ✅ 미션 발송 완료: {len(results)}/{len(AGENT_MISSIONS)}개")
    print(f"  각 에이전트가 team-discussion 라벨로 자동 응답 예정")
    print(f"{'='*60}\n")
    return results


if __name__ == "__main__":
    dispatch_missions()
