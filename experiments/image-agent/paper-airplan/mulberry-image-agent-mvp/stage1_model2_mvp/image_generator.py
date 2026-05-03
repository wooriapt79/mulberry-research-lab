# stage1_model2_mvp/image_generator.py
"""
인제군 계절 감성 이미지 생성 (DALL-E 3)
공동구매 프로모션용 이미지 생성기
"""

import os
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional
from openai import OpenAI

logger = logging.getLogger("ImageGenerator")

# 인제군 계절별 프롬프트 템플릿
INJE_SEASONAL_PROMPTS = {
    "spring": (
        "Beautiful spring landscape of Inje-gun, Gangwon Province, South Korea. "
        "Cherry blossoms along Soyang River, fresh green mountains, "
        "local farmers harvesting spring vegetables. "
        "Warm, inviting community atmosphere. Photorealistic style."
    ),
    "summer": (
        "Lush summer scenery of Inje-gun, Gangwon Province, South Korea. "
        "Deep green Soyang Lake, cool mountain streams, "
        "fresh local produce market with neighbors gathering. "
        "Bright, vibrant community feeling. Photorealistic style."
    ),
    "autumn": (
        "Golden autumn foliage of Inje-gun, Gangwon Province, South Korea. "
        "Red and orange maple leaves along mountain roads, "
        "harvest season with local agricultural products displayed. "
        "Warm, nostalgic community harvest scene. Photorealistic style."
    ),
    "winter": (
        "Serene winter landscape of Inje-gun, Gangwon Province, South Korea. "
        "Snow-covered mountains and traditional village, "
        "warm indoor cooperative market scene, neighbors sharing food. "
        "Cozy, heartwarming community atmosphere. Photorealistic style."
    ),
}

# 공동구매 제품별 추가 프롬프트
PRODUCT_PROMPTS = {
    "potato":    "featuring fresh Inje mountain potatoes prominently displayed",
    "corn":      "featuring sweet Inje corn harvest",
    "kimchi":    "featuring traditional kimchi making scene",
    "mushroom":  "featuring wild Gangwon mushrooms in a basket",
    "general":   "featuring local agricultural products and cooperative market",
}


def get_current_season() -> str:
    month = datetime.now().month
    if month in (3, 4, 5):   return "spring"
    elif month in (6, 7, 8): return "summer"
    elif month in (9, 10, 11): return "autumn"
    else:                    return "winter"


class InjеImageGenerator:
    """인제군 공동구매 프로모션 이미지 생성기"""

    def __init__(self, api_key: str = None, output_dir: str = "output/images"):
        self.client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(
        self,
        product: str = "general",
        season: str = None,
        custom_prompt: str = None,
        size: str = "1024x1024",
    ) -> dict:
        """
        인제군 계절 이미지 생성

        Returns:
            dict: {url, local_path, prompt_used, season, product}
        """
        season = season or get_current_season()
        base_prompt = INJE_SEASONAL_PROMPTS.get(season, INJE_SEASONAL_PROMPTS["autumn"])
        product_detail = PRODUCT_PROMPTS.get(product, PRODUCT_PROMPTS["general"])

        final_prompt = custom_prompt or f"{base_prompt} {product_detail}"
        logger.info("이미지 생성 시작 — season=%s product=%s", season, product)

        response = self.client.images.generate(
            model="dall-e-3",
            prompt=final_prompt,
            size=size,
            quality="standard",
            n=1,
        )

        image_url = response.data[0].url
        revised_prompt = response.data[0].revised_prompt

        # 로컬 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"inje_{season}_{product}_{timestamp}.png"
        local_path = self.output_dir / filename

        import urllib.request
        urllib.request.urlretrieve(image_url, local_path)
        logger.info("이미지 저장 완료: %s", local_path)

        return {
            "url": image_url,
            "local_path": str(local_path),
            "prompt_used": final_prompt,
            "revised_prompt": revised_prompt,
            "season": season,
            "product": product,
            "filename": filename,
        }
