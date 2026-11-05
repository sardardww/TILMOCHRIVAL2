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
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip()
    # Cascading failover list ranked from best/fastest to most reliable backup
    GEMINI_FALLBACK_MODELS: list[str] = [
        "gemini-3.5-flash-lite",  # Rank 1: Ultra-fast 1.7s, highest availability, flawless Karakalpak
        "gemini-2.0-flash",       # Rank 2: High intelligence, 1,500 req/day free quota
        "gemini-2.0-flash-lite",  # Rank 3: Ultra-lightweight, high throughput
        "gemini-2.5-flash",       # Rank 4: High-capacity Google flagship flash
        "gemini-1.5-flash",       # Rank 5: Bulletproof legacy workhorse
        "gemini-3.5-flash",       # Rank 6: Heavy neural fallback
    ]
    
    # Dictionary Settings
    DICTIONARY_PATH: Path = Path(os.getenv("DICTIONARY_PATH", "data/qq_dictionary.json"))

settings = Settings()
