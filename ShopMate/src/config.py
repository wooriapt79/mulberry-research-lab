"""
ShopMate Configuration
Mulberry Research Lab - Autonomous Shopping Agent System
"""

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Application Settings
    APP_NAME = "ShopMate"
    VERSION = "0.1.0"
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # Database Settings
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/shopmate")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # AI Model Settings
    DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-ai/deepseek-r1-distill-qwen-1.5b")
    MODEL_QUANTIZATION = "4bit"
    MAX_TOKENS = 512
    TEMPERATURE = 0.7
    
    # Edge Device Settings (Raspberry Pi)
    EDGE_DEVICE_ID = os.getenv("EDGE_DEVICE_ID", "rpi_001")
    LOCAL_MODEL_PATH = os.getenv("LOCAL_MODEL_PATH", "/models/deepseek-1.5b-4bit.gguf")
    
    # API Endpoints
    RAILWAY_API_URL = os.getenv("RAILWAY_API_URL", "https://shopmate-backend.railway.app")
    HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")
    
    # Agent Settings
    AGENT_TIMEOUT = 30  # seconds
    MAX_RETRIES = 3
    CONCURRENT_REQUESTS = 5
    
    # Security
    API_SECRET_KEY = os.getenv("API_SECRET_KEY", "change-this-in-production")
    PRIVACY_MODE = os.getenv("PRIVACY_MODE", "strict")  # strict, balanced, open
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "/var/log/shopmate.log")
