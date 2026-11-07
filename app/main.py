import logging
import os
from pathlib import Path
from typing import Optional, Any
import requests

from fastapi import FastAPI, Header, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

from app.config import settings
from app.dictionary_service import dictionary_service
from app.schemas import (
    BatchTranslationRequest,
    BatchTranslationResponse,
    DictionaryLookupRequest,
    DictionaryLookupResponse,
    HealthResponse,
    TranslationRequest,
    TranslationResponse,
)
from app.translator import translator_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("api")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
# Russian to Karakalpak AI Translation API & News Moderation Bot
Grounded with 16,000+ entries from the Russian-Karakalpak Dictionary and powered by Google AI Studio (Gemini).
Includes 24/7 Telegram moderation webhook for Sardarbek (@sardardww).
""",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def home():
    template_path = Path(__file__).parent / "templates" / "index.html"
    if template_path.exists():
        return HTMLResponse(content=template_path.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Russian to Karakalpak Translation API</h1><p>Visit <a href='/docs'>/docs</a></p>")


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    gemini_key_present = bool(settings.GEMINI_API_KEY)
    return HealthResponse(
        status="healthy",
        service=settings.APP_NAME,
        version=settings.APP_VERSION,
        dictionary_loaded=dictionary_service.is_loaded,
        dictionary_entries=dictionary_service.entry_count,
        gemini_configured=gemini_key_present,
        default_model=settings.GEMINI_MODEL,
    )


@app.post(
    "/translate",
    response_model=TranslationResponse,
    tags=["Translation"],
    summary="Translate Russian text to Karakalpak"
)
async def translate_text(
    payload: TranslationRequest,
    x_gemini_api_key: Optional[str] = Header(None, description="Optional Google AI Studio API key header override")
):
    try:
        result = await translator_service.translate(
            text=payload.text,
            target_script=payload.target_script,
            model_override=payload.model,
            custom_api_key=x_gemini_api_key,
            include_dictionary_matches=payload.include_dictionary_matches,
        )
        return result
    except Exception as e:
        logger.error(f"Translation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@app.post(
    "/translate/batch",
    response_model=BatchTranslationResponse,
    tags=["Translation"],
    summary="Batch translate multiple sentences"
)
async def translate_batch(
    payload: BatchTranslationRequest,
    x_gemini_api_key: Optional[str] = Header(None)
):
    results = []
    for text in payload.texts:
        if not text.strip():
            continue
        res = await translator_service.translate(
            text=text,
            target_script=payload.target_script,
            custom_api_key=x_gemini_api_key,
            include_dictionary_matches=True,
        )
        results.append(res)
    
    return BatchTranslationResponse(
        total=len(results),
        results=results
    )


@app.post(
    "/dictionary/lookup",
    response_model=DictionaryLookupResponse,
    tags=["Dictionary"],
    summary="Search Karakalpak dictionary directly"
)
async def dictionary_lookup(payload: DictionaryLookupRequest):
    matches = dictionary_service.search(query=payload.query, limit=payload.limit)
    return DictionaryLookupResponse(
        query=payload.query,
        total_matches=len(matches),
        results=matches,
    )


# ==============================================================================
# TELEGRAM MODERATION WEBHOOK (24/7 for Sardarbek @sardardww)
# ==============================================================================

def call_tg(method: str, payload: dict[str, Any]) -> dict[str, Any]:
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/{method}"
    try:
        r = requests.post(url, json=payload, timeout=20)
        return r.json()
    except Exception as exc:
        logger.error(f"Telegram API {method} error: {exc}")
        return {"ok": False, "error": str(exc)}


@app.post("/telegram-webhook", include_in_schema=False)
async def telegram_webhook(request: Request):
    """
    Handles interactive moderation from Admin Sardarbek:
    1. Callback queries:
       - 'pub': Copies the approved draft post to @qaraqalpaqshajanaliqlar (-1003987848482)
                Cleanly via copyMessage with NO 'Переслано из' forward header!
       - 'del': Cancels the draft and updates admin message.
    2. Message replies:
       - When admin replies to a draft message with revised text, updates the draft caption via editMessageCaption.
    """
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({"status": "invalid json"}, status_code=400)

    # 1. Handle Inline Button Clicks (callback_query)
    cb = data.get("callback_query")
    if cb:
        cb_id = cb.get("id")
        user_id = str(cb.get("from", {}).get("id"))
        cb_data = cb.get("data", "")
        msg = cb.get("message", {})
        chat_id = msg.get("chat", {}).get("id")
        message_id = msg.get("message_id")

        if user_id != str(settings.ADMIN_CHAT_ID):
            call_tg("answerCallbackQuery", {
                "callback_query_id": cb_id,
                "text": "Ruxsat berilmegen! Tek ǵana admin paydalana aladı.",
                "show_alert": True
            })
            return JSONResponse({"status": "unauthorized"})

        if cb_data == "pub" or cb_data.startswith("pub"):
            # Clean direct copy into public channel (-1003987848482)
            res = call_tg("copyMessage", {
                "chat_id": settings.TELEGRAM_CHAT_ID,
                "from_chat_id": chat_id,
                "message_id": message_id
            })

            if res.get("ok"):
                pub_msg_id = res["result"]["message_id"]
                # Update admin preview message markup to show published status and channel link
                pub_url = f"https://t.me/qaraqalpaqshajanaliqlar/{pub_msg_id}"
                call_tg("editMessageReplyMarkup", {
                    "chat_id": chat_id,
                    "message_id": message_id,
                    "reply_markup": {
                        "inline_keyboard": [
                            [{"text": f"✅ Kanalǵa shıǵarıldı (#{pub_msg_id})", "url": pub_url}]
                        ]
                    }
                })
                call_tg("answerCallbackQuery", {
                    "callback_query_id": cb_id,
                    "text": "🚀 Post kanalǵa tabıslı shıǵarıldı!",
                    "show_alert": False
                })
                logger.info(f"Published draft msg {message_id} to channel as {pub_msg_id}")
            else:
                call_tg("answerCallbackQuery", {
                    "callback_query_id": cb_id,
                    "text": f"Qátelik: {res.get('description', 'Telegram error')}",
                    "show_alert": True
                })

        elif cb_data == "del" or cb_data.startswith("del"):
            call_tg("editMessageReplyMarkup", {
                "chat_id": chat_id,
                "message_id": message_id,
                "reply_markup": {
                    "inline_keyboard": [
                        [{"text": "❌ Biykar etildi", "callback_data": "none"}]
                    ]
                }
            })
            call_tg("answerCallbackQuery", {
                "callback_query_id": cb_id,
                "text": "❌ Post biykar etildi.",
                "show_alert": False
            })

        return JSONResponse({"status": "ok"})

    # 2. Handle Admin Text Messages and Replies
    msg = data.get("message")
    if msg:
        user_id = str(msg.get("from", {}).get("id"))
        chat_id = msg.get("chat", {}).get("id")
        text = msg.get("text", "")
        reply_to = msg.get("reply_to_message")

        if user_id == str(settings.ADMIN_CHAT_ID):
            # If admin replied to a draft with new text -> update draft caption!
            if reply_to and text:
                target_msg_id = reply_to.get("message_id")
                # Try updating caption with HTML parse mode
                edit_res = call_tg("editMessageCaption", {
                    "chat_id": chat_id,
                    "message_id": target_msg_id,
                    "caption": text,
                    "parse_mode": "HTML",
                    "reply_markup": reply_to.get("reply_markup") or {
                        "inline_keyboard": [
                            [
                                {"text": "🚀 Kanalǵa shıǵarıw", "callback_data": "pub"},
                                {"text": "❌ Biykar etiw", "callback_data": "del"}
                            ]
                        ]
                    }
                })
                # If HTML parse error occurred, retry without parse_mode
                if not edit_res.get("ok"):
                    edit_res = call_tg("editMessageCaption", {
                        "chat_id": chat_id,
                        "message_id": target_msg_id,
                        "caption": text,
                        "reply_markup": reply_to.get("reply_markup")
                    })

                if edit_res.get("ok"):
                    call_tg("sendMessage", {
                        "chat_id": chat_id,
                        "text": "✅ <b>Tekst ózgertildi!</b>\nPosttı kanalǵa shıǵarıw ushın «🚀 Kanalǵa shıǵarıw» túymesin basıń.",
                        "parse_mode": "HTML",
                        "reply_to_message_id": msg.get("message_id")
                    })
                else:
                    call_tg("sendMessage", {
                        "chat_id": chat_id,
                        "text": f"⚠️ Tekstti jańalawda qátelik: {edit_res.get('description')}",
                        "reply_to_message_id": msg.get("message_id")
                    })

            elif text == "/start" or text == "/help":
                help_text = (
                    "👋 <b>Assalawma áleykum, Sardarbek!</b>\n\n"
                    "Bul @qaraqalpaqshajanaliqlar avtomatlastırılǵan moderaciya sisteması.\n\n"
                    "<b>Qalay isleydi?</b>\n"
                    "1. Bot jańa xabardı tayarlap, usı jerge (jeke chatıńızǵa) jiberedi.\n"
                    "2. <b>«🚀 Kanalǵa shıǵarıw»</b> túymesin bassańız — post kanalda járiyalanadı.\n"
                    "3. <b>«❌ Biykar etiw»</b> túymesin bassańız — post biykar etiledi.\n"
                    "4. <b>Tekstti ózgertiw:</b> Xabarǵa juwap (Reply) qılıp jańa tekstti jiberiń, "
                    "bot tekstti jańalaydı, soń túymeni basıń!"
                )
                call_tg("sendMessage", {
                    "chat_id": chat_id,
                    "text": help_text,
                    "parse_mode": "HTML"
                })

    return JSONResponse({"status": "ok"})
