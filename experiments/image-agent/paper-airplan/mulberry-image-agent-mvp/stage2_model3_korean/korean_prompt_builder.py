# stage2_model3_korean/korean_prompt_builder.py
"""
Model 3 개선: 한국어 감성 키워드 기반 프롬프트 빌더
DALL-E가 영어 gibberish를 변형하는 문제 해결
→ 자연스러운 한국 농촌 감성 이미지 생성
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger("KoreanPromptBuilder")

# 인제군 지역 감성 키워드 사전
# 영어 자연스러운 표현으로 변환 (DALL-E 품질 확보)
KOREAN_EMOTIONAL_KEYWORDS = {
    # 정(情) / 관계
    "jeong":        "heartwarming neighborly bond",
    "이웃":          "friendly neighborhood community",
    "함께":          "people gathered together in unity",
    "정겨운":        "warm and familiar",
    "사람냄새":      "authentic human warmth",

    # 인제군 지역성
    "인제":          "Inje mountain village",
    "소양강":        "Soyang River valley",
    "설악":          "Seorak mountain backdrop",
    "강원도":        "Gangwon highland",

    # 계절/자연
    "봄나물":        "fresh spring wild vegetables",
    "여름햇살":      "bright summer sunlight",
    "가을걷이":      "autumn harvest gathering",
    "겨울온기":      "cozy winter warmth",

    # 농산물
    "인제 감자":     "Inje highland potatoes",
    "인제 옥수수":   "sweet Inje corn",
    "산나물":        "mountain wild greens",
    "로컬푸드":      "local farm fresh produce",

    # 공동구매/협동
    "공동구매":      "community cooperative purchase",
    "직거래":        "direct farm-to-table",
    "협동조합":      "agricultural cooperative",
    "한살림":        "wholesome living together",
}

# 프로모션 타입별 프롬프트 구조
PROMOTION_TEMPLATES = {
    "cooperative_purchase": (
        "A warm and inviting promotional poster for {product_kr} from Inje-gun, "
        "Gangwon Province, South Korea. {seasonal_mood} {community_feel} "
        "The image conveys {emotional_keywords}. "
        "Clean, modern design with Korean rural aesthetics. "
        "Suitable for KakaoTalk sharing. No text overlays."
    ),
    "harvest_event": (
        "A festive harvest celebration scene in Inje-gun mountain village. "
        "{seasonal_mood} Local farmers proudly displaying {product_kr}. "
        "{community_feel} Warm, joyful atmosphere. "
        "Traditional Korean rural community spirit. "
        "No text overlays. High quality photorealistic."
    ),
    "direct_trade": (
        "A fresh and trustworthy direct farm market scene in Inje-gun. "
        "Farmer handing {product_kr} directly to a smiling customer. "
        "{seasonal_mood} {community_feel} "
        "Clean, transparent, honest transaction feeling. "
        "No text overlays. Bright and welcoming."
    ),
}

SEASONAL_MOODS = {
    "spring": "Fresh spring atmosphere with pale green mountains and clear sky.",
    "summer": "Vibrant summer greenery with golden sunlight.",
    "autumn": "Rich autumn foliage with warm amber tones.",
    "winter": "Cozy winter scene with soft snow and warm indoor lighting.",
}

COMMUNITY_FEELS = [
    "Neighbors smiling and chatting in the background.",
    "A sense of genuine community trust and connection.",
    "Elderly and young people sharing a warm moment.",
    "The feeling of a tight-knit mountain village community.",
]


class KoreanPromptBuilder:
    """한국 농촌 감성 기반 DALL-E 프롬프트 빌더"""

    def build(
        self,
        product: str,
        product_kr: str,
        season: str,
        promotion_type: str = "cooperative_purchase",
        extra_keywords: List[str] = None,
    ) -> Dict:
        """
        한국어 감성 키워드 기반 프롬프트 생성

        Args:
            product: 영문 제품명 ("potato")
            product_kr: 한글 제품명 ("인제 감자")
            season: "spring"|"summer"|"autumn"|"winter"
            promotion_type: "cooperative_purchase"|"harvest_event"|"direct_trade"
            extra_keywords: 추가 감성 키워드 리스트

        Returns:
            {prompt, keywords_used, season, product}
        """
        template = PROMOTION_TEMPLATES.get(
            promotion_type, PROMOTION_TEMPLATES["cooperative_purchase"]
        )
        seasonal_mood = SEASONAL_MOODS.get(season, SEASONAL_MOODS["autumn"])

        # 커뮤니티 감성 선택 (product 기반 해시로 일관성 유지)
        community_idx = hash(product) % len(COMMUNITY_FEELS)
        community_feel = COMMUNITY_FEELS[community_idx]

        # 추가 감성 키워드 영문 변환
        extra_en = []
        if extra_keywords:
            for kw in extra_keywords:
                en = KOREAN_EMOTIONAL_KEYWORDS.get(kw)
                if en:
                    extra_en.append(en)

        emotional_str = ", ".join(extra_en) if extra_en else "authentic local community warmth"

        # 한글 제품명 영문 매핑
        product_en = KOREAN_EMOTIONAL_KEYWORDS.get(product_kr, product_kr)

        prompt = template.format(
            product_kr=product_en,
            seasonal_mood=seasonal_mood,
            community_feel=community_feel,
            emotional_keywords=emotional_str,
        )

        logger.info(
            "프롬프트 생성 — product=%s season=%s type=%s",
            product, season, promotion_type,
        )

        return {
            "prompt": prompt,
            "keywords_used": extra_en,
            "season": season,
            "product": product,
            "promotion_type": promotion_type,
        }
