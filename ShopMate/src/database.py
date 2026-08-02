"""
ShopMate Database Module
Handles PostgreSQL and Vector DB connections
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json

Base = declarative_base()

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True)
    product_id = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    category = Column(String)
    brand = Column(String)
    
    # Price tracking
    current_price = Column(Float)
    original_price = Column(Float)
    currency = Column(String, default="KRW")
    price_history = Column(JSON, default=list)  # [{timestamp, price, source}]
    
    # Validation metrics
    verified_price = Column(Float)
    confidence_score = Column(Float, default=0.0)
    validation_status = Column(String, default="pending")  # pending, verified, suspicious
    
    # Metadata
    source_url = Column(String)
    crawled_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "name": self.name,
            "current_price": self.current_price,
            "verified_price": self.verified_price,
            "confidence_score": self.confidence_score,
            "validation_status": self.validation_status,
            "crawled_at": self.crawled_at.isoformat() if self.crawled_at else None
        }

class UserPreference(Base):
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, unique=True, nullable=False)
    
    # Privacy-preserving local storage
    taste_profile = Column(JSON, default=dict)  # Encrypted on edge
    budget_range = Column(JSON, default={"min": 0, "max": 1000000})
    preferred_categories = Column(JSON, default=list)
    privacy_level = Column(String, default="strict")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class GroupBuyOrder(Base):
    __tablename__ = "group_buy_orders"
    
    id = Column(Integer, primary_key=True)
    order_id = Column(String, unique=True, nullable=False)
    product_id = Column(String, nullable=False)
    
    # Group buy specifics
    target_price = Column(Float)
    current_price = Column(Float)
    min_participants = Column(Integer)
    current_participants = Column(Integer, default=0)
    
    status = Column(String, default="open")  # open, filled, closed, cancelled
    deadline = Column(DateTime)
    
    participants = Column(JSON, default=list)  # Encrypted user IDs
    created_at = Column(DateTime, default=datetime.utcnow)

def get_database_session(database_url: str):
    engine = create_engine(database_url, echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()
