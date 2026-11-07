import os
from pathlib import Path

class Settings:
    APP_NAME: str = "Russian to Karakalpak Translation API"
    APP_VERSION: str = "1.2.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production")
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Gemini AI Studio Settings
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip()
    GEMINI_FALLBACK_MODELS: list[str] = [
        "gemini-3.5-flash-lite",
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "gemini-2.5-flash",
        "gemini-1.5-flash",
        "gemini-3.5-flash",
    ]
    
    # Dictionary Settings
    DICTIONARY_PATH: Path = Path(os.getenv("DICTIONARY_PATH", "data/qq_dictionary.json"))

    # Telegram Moderation & Bot Settings
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "9218407703:AAFSOcaVFSJafUL4liO-TS982y58ODYY2BA").strip()
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "-1003987848482").strip()
    ADMIN_CHAT_ID: str = os.getenv("ADMIN_CHAT_ID", "5649102659").strip()

settings = Settings()
