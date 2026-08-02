"""
Hunter Agent - Product Data Collection & Crawling
Responsible for gathering product information from multiple sources
"""

import aiohttp
import asyncio
from typing import List, Dict, Optional
from datetime import datetime
import logging

from src.config import Config
from src.database import Product, get_database_session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HunterAgent:
    """
    Hunter Agent: Crawls and collects product data from various sources
    Implements multi-source validation preparation
    """
    
    def __init__(self, db_session):
        self.db = db_session
        self.sources = [
            "openmarket_a",
            "openmarket_b", 
            "openmarket_c",
            "brand_official",
            "community_reviews"
        ]
        self.session = None
        
    async def initialize(self):
        """Initialize HTTP session"""
        self.session = aiohttp.ClientSession(
            headers={"User-Agent": "ShopMate-Hunter/1.0"}
        )
        
    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
    
    async def search_product(self, query: str) -> List[Dict]:
        """
        Search for products across multiple sources
        Returns raw data for validation
        """
        logger.info(f"Hunter searching for: {query}")
        results = []
        
        tasks = []
        for source in self.sources:
            task = self._crawl_source(source, query)
            tasks.append(task)
        
        try:
            crawled_data = await asyncio.gather(*tasks, return_exceptions=True)
            
            for data in crawled_data:
                if isinstance(data, Exception):
                    logger.warning(f"Crawl failed: {str(data)}")
                    continue
                if data:
                    results.extend(data)
                    
        except Exception as e:
            logger.error(f"Hunter error: {str(e)}")
            
        return results
    
    async def _crawl_source(self, source: str, query: str) -> List[Dict]:
        """
        Crawl a specific source (placeholder implementation)
        In production, implement actual API calls or web scraping
        """
        # Placeholder: Replace with actual crawling logic per source
        await asyncio.sleep(0.5)  # Simulate network delay
        
        mock_data = [
            {
                "product_id": f"{source}_prod_001",
                "name": f"{query} - Product A",
                "current_price": 29900,
                "original_price": 35000,
                "source_url": f"https://{source}.com/product/001",
                "category": "electronics",
                "brand": "BrandX",
                "crawled_at": datetime.utcnow().isoformat()
            },
            {
                "product_id": f"{source}_prod_002",
                "name": f"{query} - Product B",
                "current_price": 32500,
                "original_price": 32500,
                "source_url": f"https://{source}.com/product/002",
                "category": "electronics",
                "brand": "BrandY",
                "crawled_at": datetime.utcnow().isoformat()
            }
        ]
        
        logger.info(f"Crawled {len(mock_data)} items from {source}")
        return mock_data
    
    async def get_price_history(self, product_id: str) -> List[Dict]:
        """
        Retrieve historical price data for a product
        """
        # Query database for existing history
        product = self.db.query(Product).filter(
            Product.product_id == product_id
        ).first()
        
        if product and product.price_history:
            return product.price_history
        
        return []
    
    async def save_product(self, product_data: Dict) -> Optional[Product]:
        """
        Save crawled product to database (pending validation)
        """
        try:
            existing = self.db.query(Product).filter(
                Product.product_id == product_data["product_id"]
            ).first()
            
            if existing:
                # Update existing product
                existing.current_price = product_data["current_price"]
                existing.source_url = product_data["source_url"]
                existing.updated_at = datetime.utcnow()
                
                # Add to price history
                if not existing.price_history:
                    existing.price_history = []
                existing.price_history.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "price": product_data["current_price"],
                    "source": product_data["source_url"]
                })
            else:
                # Create new product
                new_product = Product(**product_data)
                self.db.add(new_product)
                self.db.commit()
                self.db.refresh(new_product)
                return new_product
            
            self.db.commit()
            return existing if existing else new_product
            
        except Exception as e:
            logger.error(f"Failed to save product: {str(e)}")
            self.db.rollback()
            return None

# Example usage
async def main():
    db = get_database_session(Config.DATABASE_URL)
    hunter = HunterAgent(db)
    
    await hunter.initialize()
    results = await hunter.search_product("wireless earbuds")
    print(f"Found {len(results)} products")
    
    await hunter.close()

if __name__ == "__main__":
    asyncio.run(main())
