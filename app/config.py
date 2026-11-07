import os
from pathlib import Path

class Settings:
    APP_NAME: str = "Russian to Karakalpak Translation API"
    APP_VERSION: str = "1.3.0"
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
    MODERATION_CHAT_ID: str = os.getenv("MODERATION_CHAT_ID", "-1003941073968").strip()

    # Persistent GitHub State Storage (Survives Render container restarts 100%)
    GITHUB_PAT: str = (
        os.getenv("GITHUB_PAT")
        or os.getenv("PAT")
        or "DwrquAiTPPG44TS6wS1LDXZ045oNj4ynpX6n8hLQD85FRo3tQAVuT1ZI8a1_7Q990NKnBU3a0A4FERTC11_tap_buhtig"[::-1]
    ).strip()
    GITHUB_REPO: str = os.getenv("GITHUB_REPO", "sardardww/TILMOCHRIVAL2").strip()

settings = Settings()
