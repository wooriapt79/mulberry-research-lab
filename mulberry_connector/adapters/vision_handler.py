"""
Vision Handler — Malu (Gemini) Vision 도구 연동 (Issue #24)

Malu 수석 실장 설계 / Koda 구현 (2026-05-10)

하이브리드 전략:
  1. Gemini 1.5 Pro/Flash 직접 바인딩 (GoogleGenerativeAI)
  2. "장승배기" 프로토콜: 시각 정보 → Spirit Score 반영
     전통(Hanok) + 기술(Gateway) 조화 감지 시 보너스 점수 부여

환경변수:
  GOOGLE_API_KEY — Gemini API 키 (Railway에 등록)
  VISION_MODEL   — 기본값: gemini-1.5-flash (속도 우선)
"""

import os
import base64
import json
import urllib.request
import urllib.error
from dataclasses import dataclass

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
VISION_MODEL   = os.environ.get("VISION_MODEL", "gemini-1.5-flash")

# 장승배기 프로토콜 — Spirit Score 보너스 키워드
JANGSEUNGBAEGI_KEYWORDS = [
    # 전통 (Hanok / 공동체 / 장인정신)
    "tradition", "hanok", "community", "craft", "heritage",
    "장승", "전통", "공동체", "장인", "협동",
    # 기술 (Gateway / 연결 / 민주화)
    "gateway", "connect", "democratize", "bridge", "network",
    "연결", "민주화", "기술", "게이트웨이", "네트워크",
]
HARMONY_BONUS = 0.05  # 조화 감지 시 Spirit Score +0.05


@dataclass
class VisionResult:
    success: bool
    description: str
    detected_text: str
    spirit_bonus: float      # 장승배기 프로토콜 보너스
    harmony_detected: bool
    model: str
    error: str = ""


class VisionHandler:
    """
    Malu의 Gemini Vision 도구.
    이미지 분석 + 텍스트 추출 + 장승배기 Spirit Score 연동.
    """

    def __init__(self):
        self.api_key = GOOGLE_API_KEY
        self.model = VISION_MODEL
        self._base_url = (
            f"https://generativelanguage.googleapis.com/v1beta/models"
            f"/{self.model}:generateContent?key={self.api_key}"
        )

    def analyze(self, image_path: str = None, image_url: str = None,
                prompt: str = "이 이미지를 상세히 설명하고 텍스트를 추출해주세요.") -> VisionResult:
        """
        이미지 분석 메인 메서드.
        image_path (로컬 파일) 또는 image_url 중 하나 필요.
        """
        if not self.api_key:
            return VisionResult(
                success=False, description="", detected_text="",
                spirit_bonus=0.0, harmony_detected=False, model=self.model,
                error="GOOGLE_API_KEY 미설정 — Railway 환경변수 확인",
            )

        # 이미지 로드
        try:
            if image_path:
                image_data, mime_type = self._load_local(image_path)
            elif image_url:
                image_data, mime_type = self._load_url(image_url)
            else:
                return VisionResult(
                    success=False, description="", detected_text="",
                    spirit_bonus=0.0, harmony_detected=False, model=self.model,
                    error="image_path 또는 image_url 중 하나 필요",
                )
        except Exception as e:
            return VisionResult(
                success=False, description="", detected_text="",
                spirit_bonus=0.0, harmony_detected=False, model=self.model,
                error=f"이미지 로드 실패: {e}",
            )

        # Gemini API 호출
        payload = {
            "contents": [{
                "parts": [
                    {"inline_data": {"mime_type": mime_type, "data": image_data}},
                    {"text": prompt},
                ]
            }]
        }
        try:
            req = urllib.request.Request(
                self._base_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                text = result["candidates"][0]["content"]["parts"][0]["text"]
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            return VisionResult(
                success=False, description="", detected_text="",
                spirit_bonus=0.0, harmony_detected=False, model=self.model,
                error=f"Gemini API {e.code}: {error_body[:200]}",
            )
        except Exception as e:
            return VisionResult(
                success=False, description="", detected_text="",
                spirit_bonus=0.0, harmony_detected=False, model=self.model,
                error=str(e),
            )

        # 장승배기 프로토콜 — Spirit Score 보너스 계산
        text_lower = text.lower()
        tradition_hit = any(kw in text_lower for kw in JANGSEUNGBAEGI_KEYWORDS[:10])
        tech_hit      = any(kw in text_lower for kw in JANGSEUNGBAEGI_KEYWORDS[10:])
        harmony = tradition_hit and tech_hit
        bonus = HARMONY_BONUS if harmony else 0.0

        return VisionResult(
            success=True,
            description=text,
            detected_text=self._extract_code_text(text),
            spirit_bonus=bonus,
            harmony_detected=harmony,
            model=self.model,
        )

    def _load_local(self, path: str) -> tuple[str, str]:
        with open(path, "rb") as f:
            data = base64.b64encode(f.read()).decode("utf-8")
        ext = path.split(".")[-1].lower()
        mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg",
                "png": "image/png", "webp": "image/webp"}.get(ext, "image/jpeg")
        return data, mime

    def _load_url(self, url: str) -> tuple[str, str]:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = base64.b64encode(resp.read()).decode("utf-8")
            mime = resp.headers.get("Content-Type", "image/jpeg").split(";")[0]
        return data, mime

    def _extract_code_text(self, text: str) -> str:
        """분석 결과에서 코드/텍스트 관련 내용만 추출."""
        lines = [l for l in text.split("\n")
                 if any(kw in l.lower() for kw in ["code", "text", "코드", "텍스트", "문구", "글자"])]
        return "\n".join(lines) if lines else ""
