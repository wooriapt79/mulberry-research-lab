"""
Resonance Engine: Archetypal Emotion Recognition & Synchronicity Calculator
Based on Mulberry Research Lab's "Resonance AI" Paper (HuggingFace Discussion #25)

This engine maps user inputs to Jungian archetypes (Tarot Major Arcana),
calculates synchronicity scores, and recommends products based on emotional resonance.
"""

import math
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# -----------------------------------------------------------------------------
# 1. Archetype Definitions (22 Major Arcana)
# -----------------------------------------------------------------------------

class Archetype(Enum):
    FOOL = "The Fool"
    MAGICIAN = "The Magician"
    EMPRESS = "The Empress"
    EMPEROR = "The Emperor"
    HIEROPHANT = "The Hierophant"
    LOVERS = "The Lovers"
    CHARIOT = "The Chariot"
    STRENGTH = "Strength"
    HERMIT = "The Hermit"
    WHEEL_OF_FORTUNE = "Wheel of Fortune"
    JUSTICE = "Justice"
    HANGED_MAN = "The Hanged Man"
    DEATH = "Death"
    TEMPERANCE = "Temperance"
    DEVIL = "The Devil"
    TOWER = "The Tower"
    STAR = "The Star"
    MOON = "The Moon"
    SUN = "The Sun"
    JUDGEMENT = "Judgement"
    WORLD = "The World"

@dataclass
class ArchetypeProfile:
    card_name: str
    primary_emotion: str
    secondary_emotions: List[str]
    product_categories: List[str]
    keywords: List[str]
    embedding_vector: List[float]  # Simplified placeholder for demo

ARCHETYPE_LIBRARY: Dict[Archetype, ArchetypeProfile] = {
    Archetype.FOOL: ArchetypeProfile(
        card_name="The Fool",
        primary_emotion="Hope",
        secondary_emotions=["Vulnerability", "Excitement", "Naivety"],
        product_categories=["Travel", "Adventure Gear", "Beginner Kits", "Spontaneous Gifts"],
        keywords=["new beginning", "leap of faith", "innocence", "spontaneous", "risk"],
        embedding_vector=[0.8, 0.2, 0.9, 0.1, 0.5] # Dummy vector
    ),
    Archetype.MAGICIAN: ArchetypeProfile(
        card_name="The Magician",
        primary_emotion="Empowerment",
        secondary_emotions=["Creativity", "Willpower", "Focus"],
        product_categories=["Tools", "Art Supplies", "Software", "Educational Courses"],
        keywords=["manifest", "create", "skill", "power", "transform"],
        embedding_vector=[0.9, 0.8, 0.7, 0.2, 0.6]
    ),
    Archetype.EMPRESS: ArchetypeProfile(
        card_name="The Empress",
        primary_emotion="Nurture",
        secondary_emotions=["Abundance", "Sensuality", "Comfort"],
        product_categories=["Beauty", "Home Decor", "Gardening", "Luxury Food"],
        keywords=["nurture", "abundance", "beauty", "nature", "motherhood"],
        embedding_vector=[0.7, 0.9, 0.8, 0.3, 0.4]
    ),
    Archetype.EMPEROR: ArchetypeProfile(
        card_name="The Emperor",
        primary_emotion="Authority",
        secondary_emotions=["Control", "Structure", "Discipline"],
        product_categories=["Fitness Equipment", "Organization Tools", "Business Books", "Suits"],
        keywords=["authority", "structure", "control", "discipline", "leadership"],
        embedding_vector=[0.9, 0.7, 0.6, 0.8, 0.5]
    ),
    Archetype.HIEROPHANT: ArchetypeProfile(
        card_name="The Hierophant",
        primary_emotion="Meaning",
        secondary_emotions=["Tradition", "Belief", "Learning"],
        product_categories=["Books", "Religious Items", "Courses", "Mentorship"],
        keywords=["tradition", "belief", "learning", "spiritual", "guidance"],
        embedding_vector=[0.6, 0.8, 0.7, 0.9, 0.4]
    ),
    Archetype.LOVERS: ArchetypeProfile(
        card_name="The Lovers",
        primary_emotion="Connection",
        secondary_emotions=["Choice", "Harmony", "Passion"],
        product_categories=["Relationship Gifts", "Events", "Fashion", "Jewelry"],
        keywords=["love", "choice", "harmony", "partnership", "values"],
        embedding_vector=[0.8, 0.9, 0.5, 0.7, 0.6]
    ),
    Archetype.CHARIOT: ArchetypeProfile(
        card_name="The Chariot",
        primary_emotion="Action",
        secondary_emotions=["Movement", "Victory", "Determination"],
        product_categories=["Sports Gear", "Travel", "Vehicles", "Goal Trackers"],
        keywords=["action", "movement", "victory", "determination", "travel"],
        embedding_vector=[0.9, 0.6, 0.8, 0.7, 0.5]
    ),
    Archetype.STRENGTH: ArchetypeProfile(
        card_name="Strength",
        primary_emotion="Courage",
        secondary_emotions=["Calm", "Patience", "Inner Power"],
        product_categories=["Wellness", "Meditation Apps", "Yoga Mats", "Self-Help Books"],
        keywords=["courage", "patience", "inner strength", "calm", "compassion"],
        embedding_vector=[0.7, 0.8, 0.9, 0.6, 0.5]
    ),
    Archetype.HERMIT: ArchetypeProfile(
        card_name="The Hermit",
        primary_emotion="Reflection",
        secondary_emotions=["Solitude", "Wisdom", "Introspection"],
        product_categories=["Journals", "Quiet Retreats", "Books", "Meditation Cushions"],
        keywords=["solitude", "wisdom", "introspection", "search", "guidance"],
        embedding_vector=[0.5, 0.7, 0.9, 0.8, 0.4]
    ),
    Archetype.WHEEL_OF_FORTUNE: ArchetypeProfile(
        card_name="Wheel of Fortune",
        primary_emotion="Change",
        secondary_emotions=["Acceptance", "Luck", "Cycles"],
        product_categories=["New Experiences", "Games", "Lottery", "Surprise Boxes"],
        keywords=["change", "luck", "cycles", "destiny", "turning point"],
        embedding_vector=[0.8, 0.5, 0.7, 0.9, 0.6]
    ),
    Archetype.JUSTICE: ArchetypeProfile(
        card_name="Justice",
        primary_emotion="Clarity",
        secondary_emotions=["Truth", "Fairness", "Law"],
        product_categories=["Learning", "Legal Services", "Courses", "Ethical Brands"],
        keywords=["truth", "justice", "fairness", "law", "clarity"],
        embedding_vector=[0.9, 0.8, 0.7, 0.6, 0.5]
    ),
    Archetype.HANGED_MAN: ArchetypeProfile(
        card_name="The Hanged Man",
        primary_emotion="Perspective",
        secondary_emotions=["Surrender", "Pause", "Letting Go"],
        product_categories=["Art", "Spirituality Items", "Hammocks", "Mindfulness Apps"],
        keywords=["surrender", "pause", "new perspective", "letting go", "sacrifice"],
        embedding_vector=[0.6, 0.7, 0.8, 0.9, 0.5]
    ),
    Archetype.DEATH: ArchetypeProfile(
        card_name="Death",
        primary_emotion="Transformation",
        secondary_emotions=["Release", "Endings", "Rebirth"],
        product_categories=["Renewal Products", "Cleansing Kits", "Makeover Services", "Decluttering Tools"],
        keywords=["transformation", "endings", "rebirth", "change", "release"],
        embedding_vector=[0.9, 0.6, 0.8, 0.7, 0.5]
    ),
    Archetype.TEMPERANCE: ArchetypeProfile(
        card_name="Temperance",
        primary_emotion="Balance",
        secondary_emotions=["Moderation", "Harmony", "Patience"],
        product_categories=["Wellness", "Balance Tools", "Tea", "Yoga Equipment"],
        keywords=["balance", "moderation", "harmony", "patience", "flow"],
        embedding_vector=[0.7, 0.8, 0.9, 0.6, 0.5]
    ),
    Archetype.DEVIL: ArchetypeProfile(
        card_name="The Devil",
        primary_emotion="Freedom",
        secondary_emotions=["Shadow", "Addiction", "Materialism"],
        product_categories=["Music", "Expressive Art", "Luxury Items", "Indulgences"],
        keywords=["bondage", "materialism", "shadow", "freedom", "temptation"],
        embedding_vector=[0.8, 0.9, 0.6, 0.7, 0.4]
    ),
    Archetype.TOWER: ArchetypeProfile(
        card_name="The Tower",
        primary_emotion="Disruption",
        secondary_emotions=["Clarity", "Shock", "Awakening"],
        product_categories=["Renewal", "Reset Kits", "Emergency Prep", "Bold Fashion"],
        keywords=["disruption", "shock", "awakening", "sudden change", "revelation"],
        embedding_vector=[0.9, 0.7, 0.8, 0.6, 0.5]
    ),
    Archetype.STAR: ArchetypeProfile(
        card_name="The Star",
        primary_emotion="Hope",
        secondary_emotions=["Inspiration", "Healing", "Renewal"],
        product_categories=["Inspirational Books", "Beauty", "Wellness", "Art"],
        keywords=["hope", "inspiration", "healing", "renewal", "faith"],
        embedding_vector=[0.8, 0.9, 0.7, 0.6, 0.5]
    ),
    Archetype.MOON: ArchetypeProfile(
        card_name="The Moon",
        primary_emotion="Intuition",
        secondary_emotions=["Mystery", "Illusion", "Dreams"],
        product_categories=["Creativity Tools", "Dream Journals", "Mystery Games", "Night Lights"],
        keywords=["intuition", "dreams", "illusion", "mystery", "subconscious"],
        embedding_vector=[0.7, 0.8, 0.9, 0.6, 0.5]
    ),
    Archetype.SUN: ArchetypeProfile(
        card_name="The Sun",
        primary_emotion="Joy",
        secondary_emotions=["Vitality", "Success", "Warmth"],
        product_categories=["Celebration Items", "Energy Drinks", "Outdoor Gear", "Toys"],
        keywords=["joy", "success", "vitality", "warmth", "celebration"],
        embedding_vector=[0.9, 0.8, 0.7, 0.6, 0.5]
    ),
    Archetype.JUDGEMENT: ArchetypeProfile(
        card_name="Judgement",
        primary_emotion="Calling",
        secondary_emotions=["Awakening", "Rebirth", "Decision"],
        product_categories=["Transformation Courses", "Coaching", "Religious Items", "Career Tools"],
        keywords=["awakening", "calling", "rebirth", "decision", "absolution"],
        embedding_vector=[0.8, 0.9, 0.7, 0.6, 0.5]
    ),
    Archetype.WORLD: ArchetypeProfile(
        card_name="The World",
        primary_emotion="Completion",
        secondary_emotions=["Wholeness", "Achievement", "Travel"],
        product_categories=["Celebration Gifts", "Travel Packages", "Completion Certificates", "Luxury Items"],
        keywords=["completion", "wholeness", "achievement", "travel", "integration"],
        embedding_vector=[0.9, 0.8, 0.7, 0.6, 0.5]
    ),
}

# -----------------------------------------------------------------------------
# 2. Resonance Engine Class
# -----------------------------------------------------------------------------

class ResonanceEngine:
    """
    Core engine for calculating emotional resonance and synchronicity scores.
    Maps user input -> Archetype -> Product Recommendations.
    """

    def __init__(self):
        self.archetype_library = ARCHETYPE_LIBRARY

    def detect_archetype(self, user_input: str, context: Optional[Dict] = None) -> Archetype:
        """
        Simple keyword-based archetype detection (Placeholder for ML Model).
        In production, this would use a fine-tuned BERT model.
        """
        input_lower = user_input.lower()
        scores = {}

        for archetype, profile in self.archetype_library.items():
            score = 0
            # Keyword matching
            for keyword in profile.keywords:
                if keyword in input_lower:
                    score += 1
            # Emotion matching
            if profile.primary_emotion.lower() in input_lower:
                score += 3
            for emo in profile.secondary_emotions:
                if emo.lower() in input_lower:
                    score += 1
            
            scores[archetype] = score

        # Return highest scoring archetype
        if not scores or max(scores.values()) == 0:
            return Archetype.FOOL # Default
        
        return max(scores, key=scores.get)

    def calculate_synchronicity_score(
        self, 
        user_emotion_embedding: List[float], 
        selected_card: Archetype,
        user_history: Optional[List[Dict]] = None
    ) -> float:
        """
        Calculates the synchronicity score (0.0 - 1.0) based on:
        1. Immediate Resonance (Cosine Similarity)
        2. Contextual Resonance (Temporal/Context match)
        3. Predictive Resonance (Future need anticipation)
        """
        card_profile = self.archetype_library[selected_card]
        card_embedding = card_profile.embedding_vector

        # 1. Immediate Resonance (Cosine Similarity)
        dot_product = sum(a * b for a, b in zip(user_emotion_embedding, card_embedding))
        norm_user = math.sqrt(sum(a * a for a in user_emotion_embedding))
        norm_card = math.sqrt(sum(b * b for b in card_embedding))
        
        if norm_user == 0 or norm_card == 0:
            immediate_match = 0.0
        else:
            immediate_match = dot_product / (norm_user * norm_card)

        # 2. Contextual Resonance (Simplified: Random boost for demo)
        contextual_match = 0.5 # Placeholder for temporal alignment logic

        # 3. Predictive Resonance (Simplified)
        predictive_match = 0.5 # Placeholder for trajectory logic

        # Weighted Sum
        final_score = (0.4 * immediate_match) + (0.3 * contextual_match) + (0.3 * predictive_match)
        
        return min(max(final_score, 0.0), 1.0)

    def get_recommendation_explanation(self, archetype: Archetype, product_name: str) -> str:
        """
        Generates a 'Mood Mode' explanation for why this product was recommended.
        Uses Semantic Reframing technique from the paper.
        """
        profile = self.archetype_library[archetype]
        
        templates = [
            f"Your current energy resonates with **{profile.card_name}** ({profile.primary_emotion}). "
            f"This item supports your journey towards {profile.keywords[0]}.",
            
            f"In **{profile.card_name}** mode, you are seeking {profile.primary_emotion}. "
            f"{product_name} aligns with this emotional need by offering {profile.keywords[1]}.",
            
            f"The cards suggest a need for {profile.primary_emotion}. "
            f"Consider {product_name} as a tool for {profile.keywords[2]}."
        ]
        
        # Simple selection logic (could be ML-based)
        return templates[0]

# -----------------------------------------------------------------------------
# 3. Example Usage (for testing)
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    engine = ResonanceEngine()
    
    user_text = "I feel stuck and need a big change in my life. I want to let go of the past."
    detected_archetype = engine.detect_archetype(user_text)
    
    print(f"Detected Archetype: {detected_archetype.value}")
    print(f"Primary Emotion: {engine.archetype_library[detected_archetype].primary_emotion}")
    
    # Mock embedding
    mock_embedding = [0.5, 0.5, 0.5, 0.5, 0.5]
    sync_score = engine.calculate_synchronicity_score(mock_embedding, detected_archetype)
    print(f"Synchronicity Score: {sync_score:.2f}")
    
    explanation = engine.get_recommendation_explanation(detected_archetype, "Decluttering Kit")
    print(f"Recommendation Explanation: {explanation}")
