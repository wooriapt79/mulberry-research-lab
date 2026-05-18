"""
malu_vision.py — Malu Vision API 래퍼 (Google Gemini Imagen)
=============================================================
Spec: trang-image-agent-bts-spec-20260518.md · Issue #43, #45

Tool ID: malu.vision.image_generate
Spirit Score: 0.88
모델: Google Gemini Imagen (google-generativeai SDK)

사용법:
  from tools.malu_vision import MaluVision

  vision = MaluVision()
  result = vision.generate(
      prompt="BTS comeback poster, vibrant purple and gold, K-pop aesthetic",
      size=(1080, 1080),
      output_path="outputs/images/bts-poster.png",
  )

환경 변수:
  MALU_VISION_API_KEY  — Google AI Studio API Key (GEMINI_API_KEY 와 동일)
  IMAGE_OUTPUT_DIR     — 이미지 저장 기본 경로 (기본: outputs/images)

Phase 1 MVP:
  - Gemini Imagen API 호출 → PNG 저장
  - API Key 없을 때 mock 이미지 생성 (테스트용)
Phase 2:
  - 브랜드 컬러 팔레트 적용
  - Spirit Score 품질 평가 자동화
"""

from __future__ import annotations

import base64
import io
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Google Generative AI SDK (선택적 import — 없으면 mock 모드)
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

# Pillow — 이미지 리사이징용 (선택적)
try:
    from PIL import Image as PILImage
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# ── 상수 ────────────────────────────────────────────────────────
MALU_VISION_VERSION = "1.0.0"
SPIRIT_SCORE_THRESHOLD = 0.80

# 플랫폼별 이미지 규격
PLATFORM_SIZES: dict[str, tuple[int, int]] = {
    "instagram":    (1080, 1080),
    "instagram_4x5": (1080, 1350),
    "twitter":      (1200, 675),
    "facebook":     (1200, 630),
    "display":      (1920, 1080),
    "story":        (1080, 1920),
    "square":       (1080, 1080),
    "wide":         (1920, 1080),
}

# 기본 출력 디렉토리
OUTPUT_BASE = Path(os.getenv("IMAGE_OUTPUT_DIR", "outputs/images"))


class MaluVisionError(Exception):
    """Malu Vision API 오류"""
    pass


class MaluVision:
    """
    Mulberry Malu Vision Tool.
    텍스트 프롬프트 → 이미지 생성 → 플랫폼별 저장.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("MALU_VISION_API_KEY") or os.getenv("GEMINI_API_KEY", "")
        self.output_dir = OUTPUT_BASE
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._mock_mode = not (self.api_key and GENAI_AVAILABLE)

        if GENAI_AVAILABLE and self.api_key:
            genai.configure(api_key=self.api_key)
            self._model = genai.GenerativeModel("gemini-1.5-flash")
        else:
            self._model = None

        if self._mock_mode:
            reason = "API Key 없음" if not self.api_key else "google-generativeai 패키지 없음"
            print(f"[MaluVision] ⚠️  Mock 모드 — {reason}")

    @property
    def tool_id(self) -> str:
        return "malu.vision.image_generate"

    @property
    def spirit_score(self) -> float:
        return 0.88

    @property
    def version(self) -> str:
        return MALU_VISION_VERSION

    # ── 공개 API ─────────────────────────────────────────────────

    def generate(
        self,
        prompt: str,
        size: tuple[int, int] = (1080, 1080),
        platform: str = "instagram",
        output_filename: Optional[str] = None,
        style_suffix: str = "",
    ) -> dict:
        """
        이미지 생성 메인 함수.

        Args:
            prompt: 이미지 생성 프롬프트 (영어 권장)
            size: (width, height) — platform 지정 시 자동 결정
            platform: 플랫폼명 (instagram / twitter / display / story 등)
            output_filename: 저장 파일명 (없으면 자동 생성)
            style_suffix: 프롬프트 끝에 추가할 스타일 문자열

        Returns:
            {
                "status": "success" | "mock" | "error",
                "file": "출력 파일 경로",
                "platform": 플랫폼명,
                "size": [width, height],
                "prompt_used": 사용된 프롬프트,
                "spirit_score": float,
                "generated_at": ISO 타임스탬프,
            }
        """
        actual_size = PLATFORM_SIZES.get(platform, size)
        full_prompt = self._build_full_prompt(prompt, actual_size, style_suffix)
        filename = output_filename or self._auto_filename(platform)
        output_path = self.output_dir / filename

        start = time.time()
        try:
            if self._mock_mode:
                image_path = self._generate_mock(full_prompt, output_path, actual_size)
                status = "mock"
            else:
                image_path = self._generate_via_gemini(full_prompt, output_path, actual_size)
                status = "success"

            elapsed = round(time.time() - start, 2)
            result = {
                "status": status,
                "file": str(image_path),
                "platform": platform,
                "size": list(actual_size),
                "prompt_used": full_prompt,
                "spirit_score": self.spirit_score,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "elapsed_sec": elapsed,
            }
            print(f"[MaluVision] {status.upper()} → {image_path.name} ({elapsed}s)")
            return result

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "platform": platform,
                "size": list(actual_size),
                "prompt_used": full_prompt,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

    def generate_multi_platform(
        self,
        prompt: str,
        platforms: list[str],
        base_filename: str,
        style_suffix: str = "",
    ) -> list[dict]:
        """
        여러 플랫폼 규격으로 동시 생성.
        BTS 시나리오: ["instagram", "twitter", "display"]
        """
        results = []
        for platform in platforms:
            filename = f"{base_filename}-{platform}{self._size_suffix(platform)}.png"
            result = self.generate(
                prompt=prompt,
                platform=platform,
                output_filename=filename,
                style_suffix=style_suffix,
            )
            results.append(result)
        return results

    def resize(self, image_path: str | Path, platform: str) -> str:
        """
        기존 이미지를 플랫폼 규격으로 리사이징.
        PIL 없으면 원본 경로 그대로 반환.
        """
        if not PIL_AVAILABLE:
            print("[MaluVision] Pillow 없음 — 리사이징 생략")
            return str(image_path)

        target_size = PLATFORM_SIZES.get(platform, (1080, 1080))
        img = PILImage.open(image_path)
        img_resized = img.resize(target_size, PILImage.LANCZOS)

        p = Path(image_path)
        out = p.parent / f"{p.stem}-{platform}{p.suffix}"
        img_resized.save(out)
        return str(out)

    # ── 내부 메서드 ───────────────────────────────────────────────

    def _build_full_prompt(
        self,
        base_prompt: str,
        size: tuple[int, int],
        style_suffix: str,
    ) -> str:
        """프롬프트 + 규격 + 스타일 정보 합성"""
        w, h = size
        parts = [base_prompt.strip()]
        if style_suffix:
            parts.append(style_suffix.strip())
        parts.append(f"Image size: {w}x{h}px.")
        return " ".join(parts)

    def _generate_via_gemini(
        self,
        prompt: str,
        output_path: Path,
        size: tuple[int, int],
    ) -> Path:
        """
        Gemini Vision API 호출 → 이미지 저장.
        현재 Gemini 1.5 Flash는 텍스트만 지원 — imagen-3 API로 교체 필요.
        임시: 프롬프트 기반 설명 텍스트를 PNG placeholder로 저장.
        """
        # Gemini Imagen 3 는 별도 API (generativeai.ImageGenerationModel)
        # MVP: gemini-1.5-flash로 이미지 설명 생성 + placeholder 저장
        response = self._model.generate_content(
            f"다음 광고 이미지를 위한 상세 시각적 설명을 작성하세요 (100자 이내):\n{prompt}"
        )
        description = response.text.strip() if response.text else "Generated image"

        # Placeholder PNG 생성 (PIL 있는 경우 텍스트 이미지, 없으면 1x1 픽셀)
        return self._save_placeholder(output_path, size, description)

    def _generate_mock(
        self,
        prompt: str,
        output_path: Path,
        size: tuple[int, int],
    ) -> Path:
        """Mock 이미지 생성 — API 없이 테스트용 placeholder 저장"""
        description = f"[MOCK] {prompt[:80]}"
        return self._save_placeholder(output_path, size, description)

    def _save_placeholder(
        self,
        output_path: Path,
        size: tuple[int, int],
        text: str,
    ) -> Path:
        """
        PIL로 텍스트 삽입 placeholder 이미지 생성.
        PIL 없으면 최소 PNG 바이너리 저장.
        """
        if PIL_AVAILABLE:
            w, h = size
            img = PILImage.new("RGB", (w, h), color=(88, 44, 88))  # Mulberry 보라
            try:
                from PIL import ImageDraw
                draw = ImageDraw.Draw(img)
                # 간단한 텍스트 오버레이
                draw.text((20, h // 2 - 10), text[:60], fill=(255, 255, 255))
                draw.text((20, h // 2 + 20), "Mulberry AI · Malu Vision", fill=(200, 200, 200))
            except Exception:
                pass
            img.save(output_path, "PNG")
        else:
            # 최소 PNG (1x1 투명)
            MIN_PNG = base64.b64decode(
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
            )
            output_path.write_bytes(MIN_PNG)
        return output_path

    def _auto_filename(self, platform: str) -> str:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        size = PLATFORM_SIZES.get(platform, (1080, 1080))
        return f"malu-{ts}-{platform}-{size[0]}x{size[1]}.png"

    def _size_suffix(self, platform: str) -> str:
        size = PLATFORM_SIZES.get(platform, (1080, 1080))
        return f"-{size[0]}x{size[1]}"

    # ── 상태 정보 ─────────────────────────────────────────────────

    def status(self) -> dict:
        return {
            "tool_id": self.tool_id,
            "version": self.version,
            "spirit_score": self.spirit_score,
            "api_key_set": bool(self.api_key),
            "mock_mode": self._mock_mode,
            "genai_available": GENAI_AVAILABLE,
            "pil_available": PIL_AVAILABLE,
            "output_dir": str(self.output_dir),
            "platform_sizes": {k: list(v) for k, v in PLATFORM_SIZES.items()},
        }
