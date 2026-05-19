#!/usr/bin/env python3
"""
lynn_research.py — Lynn 🐺 Research Intelligence Module
=========================================================
arXiv API를 통해 Mulberry 연구 영역 최신 논문을 자동 수집·요약하고
research/papers/ 에 주간 다이제스트를 커밋합니다.

외부 기술 트렌드 vs Mulberry 현재 위치 파악용
작성: Nguyen Trang (2026-05-19)
"""

import os
import sys
import json
import time
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ── 경로 설정 ──────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
RESEARCH_DIR = ROOT / "research" / "papers"
RESEARCH_DIR.mkdir(parents=True, exist_ok=True)

# ── Mulberry 핵심 연구 키워드 ──────────────────────────────────
SEARCH_QUERIES = [
    {
        "topic": "multi_agent",
        "label": "Multi-Agent Systems",
        "query": "multi-agent cooperation autonomous agent protocol",
        "mulberry_relevance": "A2A Protocol · 팀 에이전트 협업 구조와 직결",
    },
    {
        "topic": "agentic_commerce",
        "label": "Agentic Commerce",
        "query": "agentic commerce AI agent payment autonomous transaction",
        "mulberry_relevance": "AP2 · AI Commerce Protocol · 에이전트 경제 구현",
    },
    {
        "topic": "edge_ai",
        "label": "Edge AI / On-Device",
        "query": "edge AI on-device inference lightweight model deployment",
        "mulberry_relevance": "RPi5 StudentJr 45.4M 모델 · 인제군 현장 배포",
    },
    {
        "topic": "knowledge_distillation",
        "label": "Knowledge Distillation",
        "query": "knowledge distillation teacher student LLM compression",
        "mulberry_relevance": "Dual-Teacher Ethics Distillation 파이프라인",
    },
    {
        "topic": "food_access",
        "label": "AI × Food Access",
        "query": "AI food access rural community elderly voice assistant",
        "mulberry_relevance": "식품사막화 제로 · 인제군 65세+ 어르신 파일럿",
    },
    {
        "topic": "llm_agent",
        "label": "LLM Agent Orchestration",
        "query": "LLM agent orchestration tool use reasoning autonomous",
        "mulberry_relevance": "AgentFactory · Spirit Gate · 장승배기 헌법 Agent",
    },
]

ARXIV_API = "https://export.arxiv.org/api/query"
MAX_RESULTS_PER_TOPIC = 3
DAYS_BACK = 7

# ── 이모지 관련성 스코어 ──────────────────────────────────────
RELEVANCE_LEVELS = {
    5: "🔴 핵심 직결",
    4: "🟠 높은 관련",
    3: "🟡 참고 가능",
    2: "🟢 간접 연관",
    1: "⚪ 트렌드 참고",
}


def fetch_arxiv(query: str, max_results: int = 3, days_back: int = 7) -> list[dict]:
    """arXiv API 호출 — 최근 N일 논문 수집."""
    since = (datetime.now(timezone.utc) - timedelta(days=days_back)).strftime("%Y%m%d")

    params = urllib.parse.urlencode({
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results * 2,  # 날짜 필터 후 여유분
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    })
    url = f"{ARXIV_API}?{params}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mulberry-Research-Bot/1.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            content = resp.read().decode("utf-8")
    except Exception as e:
        print(f"  [arXiv] 오류: {e}", file=sys.stderr)
        return []

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    try:
        root = ET.fromstring(content)
    except ET.ParseError as e:
        print(f"  [arXiv] XML 파싱 오류: {e}", file=sys.stderr)
        return []

    papers = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)

    for entry in root.findall("atom:entry", ns):
        published_str = entry.findtext("atom:published", "", ns)
        try:
            published = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
        except Exception:
            continue

        if published < cutoff:
            continue

        title = (entry.findtext("atom:title", "", ns) or "").strip().replace("\n", " ")
        summary = (entry.findtext("atom:summary", "", ns) or "").strip().replace("\n", " ")
        arxiv_id = (entry.findtext("atom:id", "", ns) or "").strip()

        authors = [
            a.findtext("atom:name", "", ns)
            for a in entry.findall("atom:author", ns)
        ][:3]  # 최대 3명

        papers.append({
            "title": title,
            "summary": summary[:400] + "..." if len(summary) > 400 else summary,
            "authors": authors,
            "published": published.strftime("%Y-%m-%d"),
            "url": arxiv_id,
        })

        if len(papers) >= max_results:
            break

    return papers


def score_relevance(paper: dict, topic_config: dict) -> int:
    """Mulberry 관련성 점수 계산 (1~5)."""
    text = (paper["title"] + " " + paper["summary"]).lower()

    # 키워드 매칭
    high_keywords = ["agent", "autonomous", "multi-agent", "edge", "distill",
                     "elderly", "food", "rural", "commerce", "payment"]
    mid_keywords = ["llm", "inference", "lightweight", "cooperation", "voice",
                    "community", "protocol", "orchestrat"]

    high_hits = sum(1 for kw in high_keywords if kw in text)
    mid_hits = sum(1 for kw in mid_keywords if kw in text)

    score = 1 + min(high_hits, 3) + min(mid_hits // 2, 1)
    return min(score, 5)


def summarize_paper(paper: dict) -> str:
    """논문 3줄 핵심 요약 생성."""
    summary = paper["summary"]
    sentences = [s.strip() for s in summary.replace("  ", " ").split(". ") if len(s.strip()) > 20]

    if len(sentences) >= 3:
        return ". ".join(sentences[:3]) + "."
    return summary[:300] + "..." if len(summary) > 300 else summary


def generate_digest(results: list[dict], date_str: str) -> str:
    """주간 다이제스트 마크다운 생성."""
    total_papers = sum(len(r["papers"]) for r in results)

    lines = [
        f"# 📚 Mulberry Research Digest — {date_str}",
        f"",
        f"> **Lynn 🐺 자동 수집** | arXiv 최근 7일 | {total_papers}편",
        f"> 목적: 외부 기술 트렌드 vs Mulberry 현재 위치 파악",
        f"",
        f"---",
        f"",
        f"## 🗺️ Mulberry 위치 요약",
        f"",
        f"| 연구 영역 | 외부 트렌드 | Mulberry 현황 |",
        f"|-----------|------------|---------------|",
    ]

    # 위치 요약 테이블
    for r in results:
        if not r["papers"]:
            continue
        top_title = r["papers"][0]["title"][:40] + "..." if len(r["papers"][0]["title"]) > 40 else r["papers"][0]["title"]
        lines.append(f"| {r['label']} | {top_title} | {r['mulberry_relevance'].split('·')[0].strip()} |")

    lines += ["", "---", ""]

    # 토픽별 상세
    for r in results:
        if not r["papers"]:
            continue

        lines += [
            f"## {r['label']}",
            f"*Mulberry 연관: {r['mulberry_relevance']}*",
            f"",
        ]

        for p in r["papers"]:
            score = p["score"]
            relevance_label = RELEVANCE_LEVELS.get(score, "⚪")
            authors_str = ", ".join(p["authors"]) if p["authors"] else "N/A"

            lines += [
                f"### {p['title']}",
                f"- **저자**: {authors_str}",
                f"- **게시**: {p['published']} | **관련성**: {relevance_label} ({score}/5)",
                f"- **링크**: {p['url']}",
                f"",
                f"**핵심 요약**:",
                f"> {p['summary_3line']}",
                f"",
                f"**Mulberry 시사점**: {r['mulberry_relevance']}",
                f"",
            ]

    lines += [
        "---",
        "",
        f"*Lynn 🐺 Research Intelligence · Mulberry Research Lab · {date_str}*",
        f"*자동 수집 — arXiv API · 장승배기 헌법 정신 기반 연구소*",
    ]

    return "\n".join(lines)


def main():
    print("[Lynn Research] 🐺 arXiv 논문 수집 시작...")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # 이미 오늘 다이제스트가 있으면 스킵
    output_file = RESEARCH_DIR / f"{today}-weekly-digest.md"
    if output_file.exists():
        print(f"[Lynn Research] 오늘 다이제스트 이미 존재 — 스킵: {output_file.name}")
        sys.exit(0)

    all_results = []
    total_found = 0

    for config in SEARCH_QUERIES:
        print(f"  [{config['label']}] 검색 중...")
        time.sleep(1)  # arXiv rate limit 배려

        papers = fetch_arxiv(config["query"], MAX_RESULTS_PER_TOPIC, DAYS_BACK)

        enriched = []
        for p in papers:
            p["score"] = score_relevance(p, config)
            p["summary_3line"] = summarize_paper(p)
            enriched.append(p)

        # 관련성 높은 순 정렬
        enriched.sort(key=lambda x: x["score"], reverse=True)

        print(f"    → {len(enriched)}편 수집 (관련성 상위: {enriched[0]['score'] if enriched else 0}/5)")
        total_found += len(enriched)

        all_results.append({
            "topic": config["topic"],
            "label": config["label"],
            "mulberry_relevance": config["mulberry_relevance"],
            "papers": enriched,
        })

    if total_found == 0:
        print("[Lynn Research] ⚠️  수집된 논문 없음 (API 오류 또는 최근 논문 없음)")
        # 빈 파일 생성 (heartbeat 목적)
        output_file.write_text(
            f"# 📚 Mulberry Research Digest — {today}\n\n"
            f"> Lynn 🐺 수집 시도 완료 — 최근 7일 신규 논문 없음\n",
            encoding="utf-8"
        )
        sys.exit(0)

    # 다이제스트 생성
    digest = generate_digest(all_results, today)
    output_file.write_text(digest, encoding="utf-8")
    print(f"[Lynn Research] ✅ 다이제스트 저장: {output_file}")

    # JSON 메타데이터 (heartbeat 연동용)
    meta_file = RESEARCH_DIR / f"{today}-meta.json"
    meta = {
        "date": today,
        "total_papers": total_found,
        "topics": [
            {
                "topic": r["topic"],
                "label": r["label"],
                "count": len(r["papers"]),
                "top_score": r["papers"][0]["score"] if r["papers"] else 0,
            }
            for r in all_results
        ],
        "digest_file": str(output_file.name),
        "agent": "lynn",
        "status": "completed",
    }
    meta_file.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[Lynn Research] ✅ 메타 저장: {meta_file.name}")
    print(f"[Lynn Research] 🌿 완료 — 총 {total_found}편 수집")


if __name__ == "__main__":
    main()
