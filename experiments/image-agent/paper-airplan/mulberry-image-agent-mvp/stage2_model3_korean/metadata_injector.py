# stage2_model3_korean/metadata_injector.py
"""
Model 3 핵심 수정: DALL-E 생성 후 명시적 메타데이터 삽입
DALL-E는 프롬프트를 이미지 파일에 자동 저장하지 않으므로
생성 즉시 revised_prompt + agent 정보를 PNG 메타데이터에 기록
"""

import json
import logging
import urllib.request
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
from PIL import Image
from PIL.PngImagePlugin import PngInfo
from openai import OpenAI

logger = logging.getLogger("MetadataInjector")


class Model3Generator:
    """
    Model 3 개선 버전:
    한국어 감성 프롬프트 → DALL-E 생성 → 즉시 메타데이터 삽입
    (DALL-E가 프롬프트를 자동 저장하지 않는 문제 해결)
    """

    def __init__(self, api_key: str = None, output_dir: str = "output/model3"):
        import os
        self.client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_and_inject(
        self,
        prompt_result: Dict,
        campaign: Dict,
        purchase_code: str,
    ) -> Dict:
        """
        1. 한국어 감성 프롬프트로 DALL-E 이미지 생성
        2. 생성 직후 revised_prompt + 공동구매 정보 메타데이터 삽입
        3. PNG 저장

        Args:
            prompt_result: KoreanPromptBuilder.build() 결과
            campaign: 공동구매 캠페인 정보
            purchase_code: 공동구매 코드

        Returns:
            {local_path, revised_prompt, metadata_injected, purchase_code}
        """
        prompt = prompt_result["prompt"]
        logger.info("DALL-E 생성 시작 (Model 3 한국어 감성)")

        # 1. DALL-E 생성
        response = self.client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )

        image_url = response.data[0].url
        # DALL-E 3는 revised_prompt를 반환 — 이것이 실제 사용된 프롬프트
        revised_prompt = response.data[0].revised_prompt
        logger.info("DALL-E 생성 완료 — revised_prompt 수신")

        # 2. 로컬 저장 (PNG 형식 필수 — 메타데이터 보존)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"model3_{campaign['product']}_{timestamp}.png"
        local_path = self.output_dir / filename
        urllib.request.urlretrieve(image_url, local_path)

        # 3. 메타데이터 즉시 삽입 (Model 3 핵심 수정 사항)
        # DALL-E는 프롬프트를 파일에 저장하지 않으므로 명시적으로 삽입 필요
        img = Image.open(local_path).convert("RGBA")
        metadata = PngInfo()

        agent_payload = {
            "version": "mulberry-v1",
            "model": "model3-korean",
            "purchase_code": purchase_code,
            "campaign_id": campaign["campaign_id"],
            "product": campaign["product"],
            "title": campaign["title"],
            "price": campaign["price"],
            "deadline": campaign.get("deadline", ""),
            "cta_url": campaign.get("cta_url", ""),
            "organizer": campaign.get("organizer", "Mulberry"),
            # Model 3 전용: 프롬프트 정보 보존
            "original_prompt_keywords": prompt_result.get("keywords_used", []),
            "revised_prompt": revised_prompt,
            "season": prompt_result.get("season"),
            "promotion_type": prompt_result.get("promotion_type"),
            "encoded_at": datetime.now().isoformat(),
        }

        metadata.add_text("mulberry_agent", json.dumps(agent_payload, ensure_ascii=False))
        metadata.add_text("mulberry_code", purchase_code)
        metadata.add_text("mulberry_version", "mulberry-v1")
        # revised_prompt도 별도 저장 (검색/감사용)
        metadata.add_text("dall_e_revised_prompt", revised_prompt)

        img.save(str(local_path), "PNG", pnginfo=metadata)
        logger.info("메타데이터 삽입 완료 (Model 3): %s", local_path)

        return {
            "local_path": str(local_path),
            "revised_prompt": revised_prompt,
            "metadata_injected": True,
            "purchase_code": purchase_code,
            "season": prompt_result.get("season"),
        }
