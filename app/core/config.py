from pydantic_settings import BaseSettings
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # App
    APP_NAME: str = "Stock Analyzer API"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:password@localhost:5432/stock_analyzer"
    )
    
    # CORS
    # ALLOWED_ORIGINS: List[str] = [
    #     "http://localhost:3000",
    #     "http://localhost:8081",
    #     "http://127.0.0.1:8081",
    #     "http://10.118.97.153:8081",
    #     "http://10.118.97.153:3000",
    # ]

    ALLOWED_ORIGINS = ["*"]

    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Stock Data API
    ALPHA_VANTAGE_API_KEY: str = os.getenv("ALPHA_VANTAGE_API_KEY", "")
    FINNHUB_API_KEY: str = os.getenv("FINNHUB_API_KEY", "")

    # Angel One (SmartAPI)
    ANGEL_ONE_BASE_URL: str = os.getenv("ANGEL_ONE_BASE_URL", "https://apiconnect.angelbroking.com")
    ANGEL_ONE_BASE_URL_ALT: str = os.getenv("ANGEL_ONE_BASE_URL_ALT", "https://apiconnect.angelone.in")
    ANGEL_ONE_API_KEY: str = os.getenv("ANGEL_ONE_API_KEY", "")
    
    # Redis (for caching)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # ML Model
    ML_MODEL_PATH: str = os.getenv("ML_MODEL_PATH", "./models/stock_predictor.pkl")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields in .env

settings = Settings()
