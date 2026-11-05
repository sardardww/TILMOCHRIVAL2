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
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
    # Cascading failover list ranked from best/fastest to most reliable backup
    GEMINI_FALLBACK_MODELS: list[str] = [
        "gemini-2.5-flash",       # Rank 1: High intelligence, high quota, perfectly accurate
        "gemini-2.5-flash-lite",  # Rank 2: Ultra-fast, high throughput
        "gemini-flash-latest",    # Rank 3: Latest Google flash endpoint
        "gemini-3.5-flash-lite",  # Rank 4: Ultra-fast 3.x
        "gemini-3.5-flash",       # Rank 5: Heavy neural fallback
    ]
    
    # Dictionary Settings
    DICTIONARY_PATH: Path = Path(os.getenv("DICTIONARY_PATH", "data/qq_dictionary.json"))

settings = Settings()
