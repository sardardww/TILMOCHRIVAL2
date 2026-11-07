import base64
import json
import logging
import os
from pathlib import Path
from typing import Any, Optional
import requests

from fastapi import FastAPI, Header, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from app.config import settings
from app.dictionary_service import dictionary_service
from app.draft_service import draft_service, call_telegram
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
# Russian to Karakalpak AI Translation API & Sequential Draft Moderation Queue
Grounded with 16,000+ entries from the Russian-Karakalpak Dictionary and powered by Google AI Studio (Gemini).
Sequential 1-by-1 Moderation Queue for Sardarbek (@sardardww).
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


@app.post("/translate", response_model=TranslationResponse, tags=["Translation"])
async def translate_text(
    payload: TranslationRequest,
    x_gemini_api_key: Optional[str] = Header(None)
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


@app.post("/translate/batch", response_model=BatchTranslationResponse, tags=["Translation"])
async def translate_batch(payload: BatchTranslationRequest, x_gemini_api_key: Optional[str] = Header(None)):
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
    return BatchTranslationResponse(total=len(results), results=results)


@app.post("/dictionary/lookup", response_model=DictionaryLookupResponse, tags=["Dictionary"])
async def dictionary_lookup(payload: DictionaryLookupRequest):
    matches = dictionary_service.search(query=payload.query, limit=payload.limit)
    return DictionaryLookupResponse(query=payload.query, total_matches=len(matches), results=matches)


# ==============================================================================
# DRAFT QUEUE ENDPOINTS
# ==============================================================================

class EnqueueDraftRequest(BaseModel):
    url: str
    headline: str
    caption_html: str
    media_type: str = "photo"
    media_url: str = ""
    photo_base64: Optional[str] = None


@app.post("/drafts/enqueue", tags=["Draft Moderation"])
async def enqueue_draft(req: EnqueueDraftRequest):
    """
    Called by cloud_poster.py every 15 minutes.
    Adds a curated post to the queue.
    If admin currently has no active draft, sends it immediately.
    If admin already has an active draft, queues it safely so admin can review 1-by-1.
    """
    res = draft_service.enqueue_draft(
        url=req.url,
        headline=req.headline,
        caption_html=req.caption_html,
        media_type=req.media_type,
        media_url=req.media_url,
        photo_base64=req.photo_base64
    )
    return res


@app.get("/drafts/seen_urls", tags=["Draft Moderation"])
async def get_seen_and_blacklisted_urls():
    """Returns list of all URLs currently enqueued, published, or rejected/blacklisted."""
    return {"urls": draft_service.get_blacklisted_and_seen_urls()}


@app.get("/drafts/status", tags=["Draft Moderation"])
async def get_queue_status():
    pending = draft_service.get_pending_count()
    has_active = draft_service.has_active_draft_for_admin()
    return {"pending_in_queue": pending, "has_active_waiting_admin": has_active}


# ==============================================================================
# TELEGRAM MODERATION WEBHOOK (Sequential 1-by-1 Flow for Sardarbek)
# ==============================================================================

@app.post("/telegram-webhook", include_in_schema=False)
async def telegram_webhook(request: Request):
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
            call_telegram("answerCallbackQuery", {
                "callback_query_id": cb_id,
                "text": "Ruxsat berilmegen! Tek ǵana admin paydalana aladı.",
                "show_alert": True
            })
            return JSONResponse({"status": "unauthorized"})

        # Extract draft ID if passed e.g. "pub:12" or "del:12"
        draft_id = None
        if ":" in cb_data:
            parts = cb_data.split(":")
            cb_action = parts[0]
            try:
                draft_id = int(parts[1])
            except ValueError:
                pass
        else:
            cb_action = cb_data

        if cb_action.startswith("info"):
            pending = draft_service.get_pending_count()
            call_telegram("answerCallbackQuery", {
                "callback_query_id": cb_id,
                "text": f"📋 Náwbette jáne {pending} post tayın turıptı. Usını shıǵarsańız yamasa biykarlasańız, keyingisi avtomat túrde shıǵadı.",
                "show_alert": True
            })
            return JSONResponse({"status": "ok"})

        if cb_action.startswith("pub"):
            # Copy cleanly to public channel (-1003987848482)
            res = call_telegram("copyMessage", {
                "chat_id": settings.TELEGRAM_CHAT_ID,
                "from_chat_id": chat_id,
                "message_id": message_id
            })

            if res.get("ok"):
                pub_msg_id = res["result"]["message_id"]
                pub_url = f"https://t.me/qaraqalpaqshajanaliqlar/{pub_msg_id}"
                call_telegram("editMessageReplyMarkup", {
                    "chat_id": chat_id,
                    "message_id": message_id,
                    "reply_markup": {
                        "inline_keyboard": [
                            [{"text": f"✅ Kanalǵa shıǵarıldı (#{pub_msg_id})", "url": pub_url}]
                        ]
                    }
                })
                draft_service.mark_published(draft_id, pub_msg_id)

                pending_left = draft_service.get_pending_count()
                call_telegram("answerCallbackQuery", {
                    "callback_query_id": cb_id,
                    "text": f"🚀 Post kanalǵa shıǵarıldı! (Náwbette: {pending_left})",
                    "show_alert": False
                })

                # IMMEDIATELY DELIVER NEXT DRAFT IN QUEUE!
                popped = draft_service.send_next_pending_draft()
                if not popped and pending_left == 0:
                    call_telegram("sendMessage", {
                        "chat_id": chat_id,
                        "text": "🎉 <b>Barlıq postlar tekserildi!</b>\nNáwbet bos. Jańa postlar hár 15 minutda tayarlanıp baradı.",
                        "parse_mode": "HTML"
                    })

            else:
                call_telegram("answerCallbackQuery", {
                    "callback_query_id": cb_id,
                    "text": f"Qátelik: {res.get('description', 'Telegram error')}",
                    "show_alert": True
                })

        elif cb_action.startswith("del"):
            call_telegram("editMessageReplyMarkup", {
                "chat_id": chat_id,
                "message_id": message_id,
                "reply_markup": {
                    "inline_keyboard": [
                        [{"text": "❌ Biykar etildi", "callback_data": "none"}]
                    ]
                }
            })
            draft_service.mark_rejected(draft_id)

            pending_left = draft_service.get_pending_count()
            call_telegram("answerCallbackQuery", {
                "callback_query_id": cb_id,
                "text": f"❌ Post biykar etildi. (Náwbette: {pending_left})",
                "show_alert": False
            })

            # IMMEDIATELY DELIVER NEXT DRAFT IN QUEUE!
            popped = draft_service.send_next_pending_draft()
            if not popped and pending_left == 0:
                call_telegram("sendMessage", {
                    "chat_id": chat_id,
                    "text": "🎉 <b>Barlıq postlar tekserildi!</b>\nNáwbet bos. Jańa postlar hár 15 minutda tayarlanıp baradı.",
                    "parse_mode": "HTML"
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
                updated_draft_id = draft_service.update_caption(target_msg_id, text)

                reply_markup = reply_to.get("reply_markup") or {
                    "inline_keyboard": [
                        [
                            {"text": "🚀 Kanalǵa shıǵarıw", "callback_data": f"pub:{updated_draft_id or ''}"},
                            {"text": "❌ Biykar etiw", "callback_data": f"del:{updated_draft_id or ''}"}
                        ]
                    ]
                }
                edit_res = call_telegram("editMessageCaption", {
                    "chat_id": chat_id,
                    "message_id": target_msg_id,
                    "caption": text,
                    "parse_mode": "HTML",
                    "reply_markup": reply_markup
                })
                if not edit_res.get("ok"):
                    edit_res = call_telegram("editMessageCaption", {
                        "chat_id": chat_id,
                        "message_id": target_msg_id,
                        "caption": text,
                        "reply_markup": reply_markup
                    })

                if edit_res.get("ok"):
                    call_telegram("sendMessage", {
                        "chat_id": chat_id,
                        "text": "✅ <b>Tekst ózgertildi!</b>\nKanalǵa shıǵarıw ushın «🚀 Kanalǵa shıǵarıw» túymesin basıń.",
                        "parse_mode": "HTML",
                        "reply_to_message_id": msg.get("message_id")
                    })

            elif text in ("/status", "/queue"):
                pending = draft_service.get_pending_count()
                call_telegram("sendMessage", {
                    "chat_id": chat_id,
                    "text": f"📊 <b>Moderaciya Náwbeti:</b>\n- Náwbette kútilip atırǵan postlar: <b>{pending}</b>\n\nPostlar hár 15 minutda tayarlanıp, Siz teksergen sayın birimlep jetkerip beriledi.",
                    "parse_mode": "HTML"
                })

            elif text in ("/start", "/help"):
                call_telegram("sendMessage", {
                    "chat_id": chat_id,
                    "text": (
                        "👋 <b>Assalawma áleykum, Sardarbek!</b>\n\n"
                        "Bul @qaraqalpaqshajanaliqlar náwbetli moderaciya sisteması.\n\n"
                        "<b>Qalay isleydi?</b>\n"
                        "1. Postlar hár 15 minutda tayarlanıp náwbetke qosıladı.\n"
                        "2. Sizge birimlep (náwbet penen) jiberiledi.\n"
                        "3. Bir posttı <b>«🚀 Kanalǵa shıǵarıw»</b> yamasa <b>«❌ Biykar etiw»</b> etkenińizde, "
                        "bot dárriw náwbettegi keyingi posttı shıǵaradı!\n"
                        "4. Eger 1 saat kirmeseńiz — 4 post náwbette tayın turadı hám birimlep tekseresińiz."
                    ),
                    "parse_mode": "HTML"
                })

    return JSONResponse({"status": "ok"})
