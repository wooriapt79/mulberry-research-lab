"""
Validator Agent - Price Verification & Fair Price Calculation
Core logic for validating crawled prices and detecting anomalies
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import logging
from scipy import stats

from src.config import Config
from src.database import Product, get_database_session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ValidatorAgent:
    """
    Validator Agent: Verifies product prices using statistical analysis
    Implements 'Fair Price' algorithm to avoid dependency on single source
    """
    
    def __init__(self, db_session):
        self.db = db_session
        self.confidence_threshold = 0.75
        self.anomaly_threshold = 2.5  # Standard deviations
        
    def validate_product(self, product: Product, all_sources: List[Dict]) -> Dict:
        """
        Main validation pipeline for a product
        Returns validation result with confidence score
        """
        logger.info(f"Validating product: {product.product_id}")
        
        # Extract prices from all sources
        prices = [src["current_price"] for src in all_sources if "current_price" in src]
        
        if len(prices) < 2:
            return {
                "status": "insufficient_data",
                "confidence": 0.0,
                "verified_price": product.current_price,
                "reason": "Need at least 2 sources for validation"
            }
        
        # Statistical analysis
        fair_price, confidence, anomalies = self._calculate_fair_price(prices)
        
        # Update product with validation results
        product.verified_price = fair_price
        product.confidence_score = confidence
        product.validation_status = "verified" if confidence >= self.confidence_threshold else "suspicious"
        
        try:
            self.db.commit()
        except Exception as e:
            logger.error(f"DB commit failed: {str(e)}")
            self.db.rollback()
        
        return {
            "status": product.validation_status,
            "confidence": confidence,
            "verified_price": fair_price,
            "original_price": product.current_price,
            "price_difference": product.current_price - fair_price,
            "anomalies_detected": anomalies,
            "sources_count": len(prices),
            "validated_at": datetime.utcnow().isoformat()
        }
    
    def _calculate_fair_price(self, prices: List[float]) -> Tuple[float, float, List[int]]:
        """
        Calculate fair price using robust statistical methods
        Returns: (fair_price, confidence_score, anomaly_indices)
        """
        prices_array = np.array(prices)
        
        # 1. Remove outliers using IQR method
        Q1 = np.percentile(prices_array, 25)
        Q3 = np.percentile(prices_array, 75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        mask = (prices_array >= lower_bound) & (prices_array <= upper_bound)
        clean_prices = prices_array[mask]
        anomaly_indices = [i for i, m in enumerate(mask) if not m]
        
        if len(clean_prices) == 0:
            return np.median(prices_array), 0.3, list(range(len(prices)))
        
        # 2. Calculate fair price (weighted median)
        fair_price = np.median(clean_prices)
        
        # 3. Calculate confidence score
        confidence = self._calculate_confidence(clean_prices, prices_array, anomaly_indices)
        
        return float(fair_price), float(confidence), anomaly_indices
    
    def _calculate_confidence(self, clean_prices: np.ndarray, 
                             all_prices: np.ndarray, 
                             anomalies: List[int]) -> float:
        """
        Calculate confidence score based on:
        - Number of sources
        - Price variance
        - Anomaly ratio
        """
        n_sources = len(all_prices)
        n_clean = len(clean_prices)
        anomaly_ratio = len(anomalies) / n_sources if n_sources > 0 else 1.0
        
        # Variance score (lower variance = higher confidence)
        if n_clean > 1:
            cv = np.std(clean_prices) / np.mean(clean_prices) if np.mean(clean_prices) > 0 else 1.0
            variance_score = max(0, 1 - cv)
        else:
            variance_score = 0.5
        
        # Source diversity score
        source_score = min(1.0, n_sources / 5.0)  # Max confidence at 5+ sources
        
        # Anomaly penalty
        anomaly_penalty = 1.0 - (anomaly_ratio * 0.5)
        
        # Weighted combination
        confidence = (
            0.4 * variance_score +
            0.3 * source_score +
            0.3 * anomaly_penalty
        )
        
        return min(1.0, max(0.0, confidence))
    
    def detect_price_manipulation(self, product_id: str, days: int = 30) -> Dict:
        """
        Detect potential price manipulation patterns
        """
        product = self.db.query(Product).filter(
            Product.product_id == product_id
        ).first()
        
        if not product or not product.price_history:
            return {"manipulation_detected": False, "reason": "Insufficient history"}
        
        history = product.price_history
        if len(history) < 5:
            return {"manipulation_detected": False, "reason": "Not enough data points"}
        
        prices = [entry["price"] for entry in history[-days:]]
        
        # Check for suspicious patterns
        patterns = []
        
        # 1. Sudden large changes
        price_changes = np.diff(prices)
        if len(price_changes) > 0:
            max_change = np.max(np.abs(price_changes))
            avg_price = np.mean(prices)
            if max_change > avg_price * 0.3:  # 30% sudden change
                patterns.append("sudden_large_change")
        
        # 2. Repeated price cycling
        if len(prices) >= 7:
            # Check for weekly cycles
            correlation = np.corrcoef(prices[:-7], prices[7:])[0, 1]
            if correlation > 0.8:
                patterns.append("cyclical_pattern")
        
        # 3. Artificial scarcity signals
        # (Would need stock data for full implementation)
        
        manipulation_detected = len(patterns) > 0
        
        return {
            "manipulation_detected": manipulation_detected,
            "patterns": patterns,
            "analyzed_days": len(prices),
            "price_range": {"min": min(prices), "max": max(prices)},
            "checked_at": datetime.utcnow().isoformat()
        }
    
    def get_recommendation(self, product: Product) -> str:
        """
        Generate user-friendly recommendation based on validation
        """
        if product.validation_status == "verified":
            if product.current_price < product.verified_price * 0.95:
                return "🎉 Great deal! Price is below fair market value."
            elif product.current_price > product.verified_price * 1.1:
                return "⚠️ Overpriced. Consider waiting or checking alternatives."
            else:
                return "✅ Fair price. Good time to buy if needed."
        else:
            return "❓ Price uncertain. More verification needed."

# Example usage
def main():
    db = get_database_session(Config.DATABASE_URL)
    validator = ValidatorAgent(db)
    
    # Mock product for testing
    mock_product = Product(
        product_id="test_001",
        name="Test Product",
        current_price=30000,
        price_history=[]
    )
    
    mock_sources = [
        {"current_price": 29900},
        {"current_price": 30500},
        {"current_price": 31000},
        {"current_price": 28000},  # Potential anomaly
        {"current_price": 30200}
    ]
    
    result = validator.validate_product(mock_product, mock_sources)
    print(f"Validation Result: {result}")
    print(f"Recommendation: {validator.get_recommendation(mock_product)}")

if __name__ == "__main__":
    main()
