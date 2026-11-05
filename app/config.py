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
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash").strip()
    GEMINI_FALLBACK_MODELS: list[str] = [
        "gemini-3.5-flash",
        "gemini-3.5-flash-lite",
        "gemini-3.6-flash",
        "gemini-3.8-flash",
    ]
    
    # Dictionary Settings
    DICTIONARY_PATH: Path = Path(os.getenv("DICTIONARY_PATH", "data/qq_dictionary.json"))

settings = Settings()
