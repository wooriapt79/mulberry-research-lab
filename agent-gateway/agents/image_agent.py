"""
image_agent.py — Mulberry Image Agent
======================================
Spec: trang-image-agent-bts-spec-20260518.md · Issue #45

이벤트 키워드 입력 → Malu Vision API → 광고 이미지 자동 생성 파이프라인.
BTS 시나리오 + 식품사막화 지역 공동구매 이벤트 이미지 자동화 지원.

CLI 사용법:
  python agents/image_agent.py --event bts_comeback --artist "BTS" --platform instagram
  python agents/image_agent.py --event food_desert --region "강원도 태백" --platform display
  python agents/image_agent.py --custom "포스터 직접 설명" --platforms instagram twitter

모듈 사용법:
  from agents.image_agent import ImageAgent

  agent = ImageAgent()
  results = agent.generate(event_params={
      "event_type": "kpop_comeback",
      "artist": "BTS",
      "target_platform": ["instagram", "twitter"],
      "brand_context": "Mulberry Village 공동구매",
      "language": "ko",
      "style": "vibrant, modern, K-pop aesthetic",
  })

환경 변수:
  MALU_VISION_API_KEY   Google AI API Key
  GITHUB_TOKEN          생성 결과 GitHub Issue 보고용
  MULBERRY_REPO_OWNER   GitHub 저장소 소유자

로그: outputs/image_log.jsonl
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests

# 상위 디렉토리 PATH 등록 (tools 모듈 import용)
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from tools.malu_vision import MaluVision

# ── 상수 ────────────────────────────────────────────────────────
AGENT_VERSION = "1.0.0"
IMAGE_LOG = ROOT / "outputs" / "image_log.jsonl"
IMAGE_LOG.parent.mkdir(parents=True, exist_ok=True)

GITHUB_TOKEN   = os.getenv("GITHUB_TOKEN", "")
REPO_OWNER     = os.getenv("MULBERRY_REPO_OWNER", "wooriapt79")
REPORT_REPO    = "mulberry-research-lab"
REPORT_ISSUE   = int(os.getenv("IMAGE_REPORT_ISSUE", "45"))


# ── 이벤트 유형별 프롬프트 템플릿 ────────────────────────────────

EVENT_TEMPLATES: dict[str, dict] = {
    "kpop_comeback": {
        "base_prompt": (
            "{artist} K-pop comeback celebration event poster for Mulberry Village "
            "community group purchase. Vibrant purple and gold colors, modern K-pop aesthetic, "
            "Korean text overlay space, community celebration theme."
        ),
        "style": "vibrant, modern, high energy, festive, Korean pop culture",
        "brand": "Mulberry Village",
    },
    "kpop_world_tour": {
        "base_prompt": (
            "{artist} world tour city poster featuring {city} landmark. "
            "Concert energy, purple and gold gradient, premium event poster style, "
            "Mulberry community banner."
        ),
        "style": "cinematic, premium, concert poster, city landmark, festive",
        "brand": "Mulberry Village",
    },
    "food_desert": {
        "base_prompt": (
            "Fresh organic vegetables and fruits community group purchase event poster "
            "for {region}. Warm and inviting, community togetherness, "
            "Korean rural aesthetic, fresh food abundance."
        ),
        "style": "warm, inviting, community spirit, fresh, natural, Korean countryside",
        "brand": "Mulberry 공동구매",
    },
    "seasonal_event": {
        "base_prompt": (
            "{season} season special community group purchase event in {region}. "
            "Seasonal colors and motifs, Mulberry Village branding, Korean community feel."
        ),
        "style": "seasonal, warm community, Korean traditional + modern fusion",
        "brand": "Mulberry Village",
    },
    "custom": {
        "base_prompt": "{prompt}",
        "style": "",
        "brand": "Mulberry",
    },
}


class ImageAgent:
    """
    Mulberry Image Agent.
    이벤트 파라미터 → 프롬프트 빌드 → Malu Vision 호출 → 결과 기록.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        report_to_github: bool = False,
    ):
        self.vision = MaluVision(api_key=api_key)
        self.report_to_github = report_to_github
        print(f"[ImageAgent] v{AGENT_VERSION} 초기화 — MaluVision({self.vision.status()['mock_mode'] and 'mock' or 'live'})")

    # ── 공개 API ─────────────────────────────────────────────────

    def generate(self, event_params: dict) -> dict:
        """
        메인 생성 함수.

        Args:
            event_params: {
                "event_type": "kpop_comeback" | "food_desert" | "custom" | ...
                "artist": str,
                "region": str,
                "city": str,
                "season": str,
                "prompt": str (custom 시),
                "target_platform": ["instagram", "twitter", "display"],
                "brand_context": str,
                "language": "ko" | "en",
                "style": str,
            }

        Returns:
            {
                "status": "success" | "partial" | "error",
                "images": [...결과 목록],
                "event_type": str,
                "generated_at": ISO str,
                "agent": "ImageAgent-Malu",
            }
        """
        event_type = event_params.get("event_type", "custom")
        platforms = event_params.get("target_platform", ["instagram"])
        if isinstance(platforms, str):
            platforms = [platforms]

        # 프롬프트 생성
        prompt = self._build_prompt(event_params)
        if not prompt:
            return {"status": "error", "error": "프롬프트를 생성할 수 없습니다."}

        print(f"[ImageAgent] 이벤트: {event_type} | 플랫폼: {platforms}")
        print(f"[ImageAgent] 프롬프트: {prompt[:80]}...")

        # 베이스 파일명
        ts = datetime.now(timezone.utc).strftime("%Y%m%d")
        artist = event_params.get("artist", "").replace(" ", "").lower()
        base_name = f"{event_type[:10]}-{artist or 'event'}-{ts}"

        # 플랫폼별 이미지 생성
        style = event_params.get("style", EVENT_TEMPLATES.get(event_type, {}).get("style", ""))
        images = self.vision.generate_multi_platform(
            prompt=prompt,
            platforms=platforms,
            base_filename=base_name,
            style_suffix=style,
        )

        success_count = sum(1 for img in images if img.get("status") in ("success", "mock"))
        overall_status = (
            "success" if success_count == len(images)
            else "partial" if success_count > 0
            else "error"
        )

        result = {
            "status": overall_status,
            "images": images,
            "event_type": event_type,
            "prompt_used": prompt,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "agent": "ImageAgent-Malu",
            "spirit_score": self.vision.spirit_score,
        }

        # 로그 기록
        self._write_log(result, event_params)

        # GitHub 보고 (옵션)
        if self.report_to_github and overall_status in ("success", "partial"):
            self._report_to_github(result, event_params)

        return result

    def generate_bts_comeback(
        self,
        platforms: Optional[list[str]] = None,
        event_name: str = "BTS 컴백",
    ) -> dict:
        """
        BTS 컴백 시나리오 원클릭 실행.
        첫 번째 타겟 시나리오 — 즉시 사용 가능.
        """
        return self.generate({
            "event_type": "kpop_comeback",
            "artist": "BTS",
            "event_name": event_name,
            "target_platform": platforms or ["instagram", "twitter", "display"],
            "brand_context": "Mulberry Village 공동구매 이벤트",
            "language": "ko",
            "style": "vibrant, modern, K-pop aesthetic, purple and gold",
        })

    def generate_food_desert(
        self,
        region: str,
        platforms: Optional[list[str]] = None,
    ) -> dict:
        """
        식품사막화 지역 공동구매 이벤트 이미지.
        """
        return self.generate({
            "event_type": "food_desert",
            "region": region,
            "target_platform": platforms or ["instagram", "display"],
            "brand_context": "Mulberry 공동구매",
            "language": "ko",
        })

    # ── 내부 메서드 ───────────────────────────────────────────────

    def _build_prompt(self, params: dict) -> str:
        """이벤트 파라미터 → MaluVision 프롬프트 문자열 생성"""
        event_type = params.get("event_type", "custom")
        template_info = EVENT_TEMPLATES.get(event_type, EVENT_TEMPLATES["custom"])
        template = template_info["base_prompt"]

        # 템플릿 변수 치환
        substitutions = {
            "artist": params.get("artist", ""),
            "region": params.get("region", ""),
            "city": params.get("city", ""),
            "season": params.get("season", ""),
            "prompt": params.get("prompt", ""),
        }
        try:
            prompt = template.format(**substitutions)
        except KeyError:
            prompt = template

        # brand_context 추가
        brand = params.get("brand_context", template_info.get("brand", "Mulberry"))
        if brand and brand not in prompt:
            prompt += f" Brand: {brand}."

        # 언어 지시
        lang = params.get("language", "ko")
        if lang == "ko":
            prompt += " Include Korean text space. Korean community aesthetic."

        return prompt.strip()

    def _write_log(self, result: dict, params: dict) -> None:
        """image_log.jsonl에 생성 결과 기록"""
        log_entry = {
            "generated_at": result["generated_at"],
            "event_type": result["event_type"],
            "agent": result["agent"],
            "status": result["status"],
            "spirit_score": result.get("spirit_score"),
            "image_count": len(result.get("images", [])),
            "files": [img.get("file", "") for img in result.get("images", [])],
            "prompt_used": result.get("prompt_used", ""),
            "params": {k: v for k, v in params.items() if k != "prompt"},
        }
        try:
            with open(IMAGE_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"[ImageAgent] 로그 기록 실패: {e}")

    def _report_to_github(self, result: dict, params: dict) -> None:
        """생성 결과를 GitHub Issue #45에 보고"""
        if not GITHUB_TOKEN:
            return
        files_list = "\n".join(
            f"  - `{Path(img.get('file', '')).name}` ({img.get('platform', '')} {img.get('size', '')})"
            for img in result.get("images", [])
        )
        body = (
            f"## 🖼️ Image Agent 생성 완료\n\n"
            f"**이벤트**: {params.get('event_type', '')} — {params.get('artist', params.get('region', ''))}\n"
            f"**상태**: {result['status']}\n"
            f"**생성 이미지** ({len(result.get('images', []))}건):\n{files_list}\n\n"
            f"**Spirit Score**: {result.get('spirit_score', 'N/A')}\n"
            f"**생성 시각**: {result['generated_at']}\n\n"
            f"*ImageAgent-Malu v{AGENT_VERSION} · Mulberry Research Lab*"
        )
        url = f"https://api.github.com/repos/{REPO_OWNER}/{REPORT_REPO}/issues/{REPORT_ISSUE}/comments"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
        }
        try:
            resp = requests.post(
                url,
                headers=headers,
                data=json.dumps({"body": body}, ensure_ascii=False).encode("utf-8"),
                timeout=15,
            )
            if resp.status_code == 201:
                print(f"[ImageAgent] GitHub 보고 완료: {resp.json()['html_url']}")
        except Exception as e:
            print(f"[ImageAgent] GitHub 보고 실패: {e}")


# ── CLI ──────────────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Mulberry Image Agent CLI")
    parser.add_argument("--event", default="kpop_comeback",
                        choices=list(EVENT_TEMPLATES.keys()),
                        help="이벤트 유형")
    parser.add_argument("--artist", default="BTS", help="아티스트명 (K-pop 이벤트)")
    parser.add_argument("--region", default="", help="지역명 (식품사막화 이벤트)")
    parser.add_argument("--city", default="", help="도시명 (월드투어 이벤트)")
    parser.add_argument("--custom", default="", help="커스텀 프롬프트 (--event custom 시)")
    parser.add_argument("--platforms", nargs="+",
                        default=["instagram"],
                        help="생성할 플랫폼 목록 (instagram twitter display story ...)")
    parser.add_argument("--style", default="", help="추가 스타일 설명")
    parser.add_argument("--report", action="store_true", help="GitHub Issue에 결과 보고")
    parser.add_argument("--status", action="store_true", help="Malu Vision 상태 출력")
    args = parser.parse_args()

    agent = ImageAgent(report_to_github=args.report)

    if args.status:
        import json as _json
        print(_json.dumps(agent.vision.status(), ensure_ascii=False, indent=2))
        return

    params = {
        "event_type": args.event,
        "artist": args.artist,
        "region": args.region,
        "city": args.city,
        "target_platform": args.platforms,
        "style": args.style,
        "language": "ko",
    }
    if args.event == "custom" and args.custom:
        params["prompt"] = args.custom

    result = agent.generate(params)

    print(f"\n{'='*50}")
    print(f"상태: {result['status'].upper()}")
    print(f"생성 이미지: {len(result.get('images', []))}건")
    for img in result.get("images", []):
        status_icon = "✅" if img.get("status") in ("success", "mock") else "❌"
        print(f"  {status_icon} {Path(img.get('file', '')).name} ({img.get('platform')} {img.get('size')})")
    print(f"Spirit Score: {result.get('spirit_score', 'N/A')}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
