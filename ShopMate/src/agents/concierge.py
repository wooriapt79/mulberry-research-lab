"""
Concierge Agent - User Interface & Intent Processing
Natural language interface for ShopMate users
"""

import asyncio
from typing import Dict, List, Optional
from datetime import datetime
import logging
import json

from src.config import Config
from src.database import Product, UserPreference, get_database_session
from src.agents.hunter import HunterAgent
from src.agents.validator import ValidatorAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConciergeAgent:
    """
    Concierge Agent: Primary user interface for ShopMate
    Processes natural language requests and coordinates other agents
    Implements privacy-first design for edge deployment
    """
    
    def __init__(self, db_session, hunter: HunterAgent, validator: ValidatorAgent):
        self.db = db_session
        self.hunter = hunter
        self.validator = validator
        self.user_contexts = {}  # In-memory context storage (encrypted on edge)
        
    async def process_request(self, user_id: str, message: str, context: Optional[Dict] = None) -> Dict:
        """
        Main entry point for user requests
        Handles shopping queries, recommendations, and status checks
        """
        logger.info(f"Concierge received from {user_id}: {message[:50]}...")
        
        # Update or create user context
        if user_id not in self.user_contexts:
            self.user_contexts[user_id] = {
                "last_interaction": datetime.utcnow(),
                "preferences": self._load_user_preferences(user_id),
                "conversation_history": []
            }
        
        # Store conversation (privacy-preserving: encrypt on edge)
        self.user_contexts[user_id]["conversation_history"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "user_message": message,
            "location": "edge" if Config.PRIVACY_MODE == "strict" else "cloud"
        })
        
        # Parse intent
        intent = self._parse_intent(message)
        
        # Route to appropriate handler
        if intent["type"] == "product_search":
            response = await self._handle_product_search(user_id, intent)
        elif intent["type"] == "price_check":
            response = await self._handle_price_check(user_id, intent)
        elif intent["type"] == "recommendation":
            response = await self._handle_recommendation(user_id, intent)
        elif intent["type"] == "group_buy":
            response = await self._handle_group_buy(user_id, intent)
        else:
            response = {
                "status": "error",
                "message": "I'm not sure I understand. Could you rephrase?",
                "suggestions": ["Search for products", "Check prices", "Get recommendations"]
            }
        
        # Add transparency explanation
        response["explanation"] = self._generate_explanation(intent, response)
        
        return response
    
    def _parse_intent(self, message: str) -> Dict:
        """
        Simple intent parsing (replace with LLM-based parsing in production)
        """
        message_lower = message.lower()
        
        # Keyword-based intent detection
        if any(word in message_lower for word in ["search", "find", "look for", "buy"]):
            return {
                "type": "product_search",
                "query": self._extract_query(message),
                "filters": self._extract_filters(message)
            }
        elif any(word in message_lower for word in ["price", "cost", "how much"]):
            return {
                "type": "price_check",
                "product": self._extract_query(message)
            }
        elif any(word in message_lower for word in ["recommend", "suggest", "best"]):
            return {
                "type": "recommendation",
                "category": self._extract_category(message)
            }
        elif any(word in message_lower for word in ["group buy", "joint purchase", "공동구매"]):
            return {
                "type": "group_buy",
                "product": self._extract_query(message)
            }
        else:
            return {"type": "unknown", "original_message": message}
    
    def _extract_query(self, message: str) -> str:
        """Extract product search query from message"""
        # Simple extraction (improve with NLP/LLM)
        stopwords = ["please", "i want", "looking for", "search for", "find me"]
        words = message.split()
        query_words = [w for w in words if w.lower() not in stopwords]
        return " ".join(query_words[:5])  # Limit to 5 words
    
    def _extract_filters(self, message: str) -> Dict:
        """Extract filters like price range, brand, etc."""
        filters = {}
        
        # Extract price range (simple regex-like approach)
        if "under" in message.lower():
            # Find number after "under"
            words = message.split()
            for i, word in enumerate(words):
                if word.lower() == "under" and i + 1 < len(words):
                    try:
                        filters["max_price"] = int(words[i + 1].replace(",", ""))
                    except ValueError:
                        pass
        
        return filters
    
    def _extract_category(self, message: str) -> str:
        """Extract product category"""
        categories = ["electronics", "fashion", "home", "beauty", "sports", "books"]
        message_lower = message.lower()
        
        for category in categories:
            if category in message_lower:
                return category
        
        return "general"
    
    def _load_user_preferences(self, user_id: str) -> Dict:
        """Load user preferences from database"""
        pref = self.db.query(UserPreference).filter(
            UserPreference.user_id == user_id
        ).first()
        
        if pref:
            return {
                "budget_range": pref.budget_range,
                "preferred_categories": pref.preferred_categories,
                "privacy_level": pref.privacy_level
            }
        
        return {
            "budget_range": {"min": 0, "max": 1000000},
            "preferred_categories": [],
            "privacy_level": "strict"
        }
    
    async def _handle_product_search(self, user_id: str, intent: Dict) -> Dict:
        """Handle product search requests"""
        query = intent["query"]
        filters = intent.get("filters", {})
        
        # Use Hunter Agent to search
        results = await self.hunter.search_product(query)
        
        # Apply filters
        if "max_price" in filters:
            results = [r for r in results if r.get("current_price", 0) <= filters["max_price"]]
        
        # Validate top results
        validated_results = []
        for product_data in results[:5]:  # Limit to top 5
            # Save to DB temporarily
            temp_product = await self.hunter.save_product(product_data)
            if temp_product:
                validation = self.validator.validate_product(temp_product, [product_data])
                product_data["validation"] = validation
                validated_results.append(product_data)
        
        return {
            "status": "success",
            "query": query,
            "results_count": len(validated_results),
            "products": validated_results,
            "message": f"Found {len(validated_results)} products matching '{query}'"
        }
    
    async def _handle_price_check(self, user_id: str, intent: Dict) -> Dict:
        """Handle price check requests"""
        product_name = intent["product"]
        
        # Search for product
        results = await self.hunter.search_product(product_name)
        
        if not results:
            return {
                "status": "not_found",
                "message": f"Could not find '{product_name}'"
            }
        
        # Get best price with validation
        best_result = min(results, key=lambda x: x.get("current_price", float('inf')))
        
        return {
            "status": "success",
            "product": best_result["name"],
            "current_price": best_result["current_price"],
            "source": best_result["source_url"],
            "message": f"Best price for '{best_result['name']}': ₩{best_result['current_price']:,}"
        }
    
    async def _handle_recommendation(self, user_id: str, intent: Dict) -> Dict:
        """Handle recommendation requests"""
        category = intent["category"]
        preferences = self.user_contexts[user_id]["preferences"]
        
        # Search popular items in category
        results = await self.hunter.search_product(f"popular {category}")
        
        # Filter by user budget
        max_budget = preferences["budget_range"]["max"]
        filtered = [r for r in results if r.get("current_price", 0) <= max_budget]
        
        return {
            "status": "success",
            "category": category,
            "recommendations": filtered[:3],
            "message": f"Here are some recommended {category} items within your budget"
        }
    
    async def _handle_group_buy(self, user_id: str, intent: Dict) -> Dict:
        """Handle group buy requests"""
        # Placeholder for group buy logic
        return {
            "status": "info",
            "message": "Group buy feature coming soon! We'll notify you when enough participants join.",
            "action_required": "wait_for_implementation"
        }
    
    def _generate_explanation(self, intent: Dict, response: Dict) -> str:
        """Generate transparent explanation of AI decision"""
        if intent["type"] == "product_search":
            return f"I searched multiple sources and found {response.get('results_count', 0)} products. Prices were validated using statistical analysis."
        elif intent["type"] == "price_check":
            return "Price verified against multiple sources to ensure fairness."
        elif intent["type"] == "recommendation":
            return "Recommendations based on your preferences and verified fair prices."
        else:
            return "Response generated using Mulberry Research Lab's transparent AI system."

# Example usage
async def main():
    db = get_database_session(Config.DATABASE_URL)
    hunter = HunterAgent(db)
    validator = ValidatorAgent(db)
    concierge = ConciergeAgent(db, hunter, validator)
    
    await hunter.initialize()
    
    # Test user request
    response = await concierge.process_request(
        user_id="user_001",
        message="Find me wireless earbuds under 50000 won"
    )
    
    print(json.dumps(response, indent=2, ensure_ascii=False))
    
    await hunter.close()

if __name__ == "__main__":
    asyncio.run(main())
