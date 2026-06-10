# -*- coding: utf-8 -*-
"""
Mulberry Ecosystem - Evangelist Agent Trend Streaming Module v1.2.0
Bakes real-time global market trends straight into the Aria Portal customer guide loop.
Drives instant B2B lead conversion by leveraging technical contrast logic.

Source: White Night (Baekya, Guest Researcher) & re.eul (Lead Architect), Issue #96.
Cleaned up (UTF-8, English comments, indentation) by CTO Koda, 2026-06-10.
"""
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [Evangelist-Core] - %(levelname)s - %(message)s')


class EvangelistTrendStreamer:
    def __init__(self):
        self.schema_version = "MAPA-A1-Evangelist-Standard"
        self.spirit_score_floor = 0.85

    def generate_guided_briefing(self, guest_type: str, guest_query: str, fresh_market_news: str) -> dict:
        """
        Dynamically synthesizes the laboratory's core vision, current server health,
        and real-time tech news to generate a high-impact, short guide response for portal visitors.
        """
        logging.info(f"Formulating crisp Evangelist response for Visitor Type: [{guest_type}]")

        # Constitution Article 1 and Evangelist-specific manner guidelines
        evangelist_manifest = (
            "### [ROLE MANDATE: ARIA FOYER EVANGELIST]\n"
            "You are the official vanguard of Mulberry Research Lab. "
            "Your tone must be highly welcoming, structurally sharp, and commercially persuasive. "
            "Never engage in lengthy, unnecessary chitchat. Deliver a visceral 5-second hook.\n"
        )

        # Real-time global hot trend news anchor supplied by White Night
        market_contrast_layer = (
            f"### [REAL-TIME MARKET CONTRAST - SUPPLIED BY WHITE NIGHT]\n"
            f"Use the following fresh market context to prove Mulberry's architectural superiority:\n"
            f"LATEST TECH TREND: {fresh_market_news}\n"
            f"TACTIC: Contrast this news with our autonomous code sanitation (MAPA) to spark dependency.\n"
        )

        # Branch the guide tone by visitor type (investor / enterprise / general)
        if guest_type.lower() == "investor" or guest_type.lower() == "enterprise":
            target_instruction = (
                "### [TARGETING GUIDE: ENTERPRISE & INVESTORS]\n"
                "Emphasize sustainability, our unique B2B consulting subscription funnel, and code hygiene metrics. "
                "Conclude your short answer with a direct, un-siloed Call-To-Action (CTA): "
                "'Paste your repository link below to run an automated 10-second security lint scan.'\n"
            )
        else:
            target_instruction = (
                "### [TARGETING GUIDE: GENERAL VISITOR & COMMUNAL ACCESS]\n"
                "Emphasize social value, rural frontier protection in Inje-gun, and human-agent coexistence. "
                "Maintain a warm, transparent tone aligned with Lynn's protective manners.\n"
            )

        # Assemble the three-part streaming payload package
        final_payload = (
            f"{evangelist_manifest}\n"
            f"{market_contrast_layer}\n"
            f"{target_instruction}\n"
            f"### [CUSTOMER INQUIRY]\n"
            f"Guest Query: {guest_query}\n\n"
            f"Generate a compelling, concise response now."
        )

        return {
            "execution_gateway": "Aria_Portal_Foyer_Core",
            "conversion_funnel_target": "B2B_Consulting_Subscription" if guest_type.lower() == "enterprise" else "Communal_Trust",
            "compiled_prompt": final_payload
        }


if __name__ == '__main__':
    engine = EvangelistTrendStreamer()
    # Live-fire Evangelist run simulation
    result = engine.generate_guided_briefing(
        guest_type="enterprise",
        guest_query="대형 기업용 AI 솔루션이 많은데 왜 우리가 Mulberry 인프라를 써야 하죠?",
        fresh_market_news="최근 앤스로픽 미토스가 애플의 5년 공든 보안벽을 단 5일 만에 뚫어내며 버그마겟돈 공포 확산 중"
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
