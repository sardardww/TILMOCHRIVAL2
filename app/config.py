import os
from pathlib import Path

class Settings:
    APP_NAME: str = "Russian to Karakalpak Translation API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production")
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Gemini AI Studio Settings
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip()
    # Cascading failover list ranked strictly from best/most intelligent to lightweight backup
    GEMINI_FALLBACK_MODELS: list[str] = [
        "gemini-3.8-flash",       # Rank 1: Top-tier flagship model (Best quality)
        "gemini-3.6-flash",       # Rank 2: High intelligence flagship
        "gemini-3.5-flash",       # Rank 3: High reasoning flash
        "gemini-3.5-flash-lite",  # Rank 4: Ultra-fast 3.x
        "gemini-3.1-flash-lite",  # Rank 5: Lightweight backup
    ]
    
    # Dictionary Settings
    DICTIONARY_PATH: Path = Path(os.getenv("DICTIONARY_PATH", "data/qq_dictionary.json"))

settings = Settings()
