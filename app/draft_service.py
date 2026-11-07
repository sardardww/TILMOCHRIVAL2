import base64
import json
import logging
import os
import sqlite3
from pathlib import Path
from typing import Any, Optional, Tuple
import requests

from app.config import settings

logger = logging.getLogger(__name__)

DB_PATH = Path("data/moderation_queue.db")

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS drafts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT UNIQUE,
        headline TEXT,
        caption_html TEXT,
        media_type TEXT,
        media_url TEXT,
        photo_base64 TEXT,
        status TEXT DEFAULT 'pending',
        admin_message_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS blacklisted_urls (
        url TEXT PRIMARY KEY,
        reason TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

# Initialize DB on import
init_db()


def call_telegram(method: str, payload: dict[str, Any], files: dict[str, Any] | None = None) -> dict[str, Any]:
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/{method}"
    try:
        if files:
            r = requests.post(url, data=payload, files=files, timeout=40)
        else:
            r = requests.post(url, json=payload, timeout=25)
        return r.json()
    except Exception as exc:
        logger.error(f"Telegram API {method} error: {exc}")
        return {"ok": False, "error": str(exc)}


class DraftQueueService:
    def __init__(self):
        init_db()

    def get_conn(self) -> sqlite3.Connection:
        return sqlite3.connect(DB_PATH)

    def is_url_seen_or_blacklisted(self, url: str) -> bool:
        if not url:
            return False
        clean_url = url.strip().split("?")[0].rstrip("/")
        conn = self.get_conn()
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM blacklisted_urls WHERE url = ? LIMIT 1", (clean_url,))
        if cur.fetchone():
            conn.close()
            return True
        cur.execute("SELECT 1 FROM drafts WHERE url = ? LIMIT 1", (clean_url,))
        res = cur.fetchone() is not None
        conn.close()
        return res

    def get_blacklisted_and_seen_urls(self) -> list[str]:
        conn = self.get_conn()
        cur = conn.cursor()
        cur.execute("SELECT url FROM blacklisted_urls UNION SELECT url FROM drafts")
        rows = [r[0] for r in cur.fetchall()]
        conn.close()
        return rows

    def has_active_draft_for_admin(self) -> bool:
        conn = self.get_conn()
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM drafts WHERE status = 'active' LIMIT 1")
        res = cur.fetchone() is not None
        conn.close()
        return res

    def get_pending_count(self) -> int:
        conn = self.get_conn()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM drafts WHERE status = 'pending'")
        count = cur.fetchone()[0]
        conn.close()
        return count

    def enqueue_draft(
        self,
        url: str,
        headline: str,
        caption_html: str,
        media_type: str = "photo",
        media_url: str = "",
        photo_base64: Optional[str] = None
    ) -> dict[str, Any]:
        clean_url = url.strip().split("?")[0].rstrip("/")
        if self.is_url_seen_or_blacklisted(clean_url):
            return {"status": "skipped", "reason": "URL already enqueued or blacklisted"}

        conn = self.get_conn()
        cur = conn.cursor()
        try:
            cur.execute("""
            INSERT INTO drafts (url, headline, caption_html, media_type, media_url, photo_base64, status)
            VALUES (?, ?, ?, ?, ?, ?, 'pending')
            """, (clean_url, headline, caption_html, media_type, media_url, photo_base64))
            conn.commit()
            draft_id = cur.lastrowid
        except sqlite3.IntegrityError:
            conn.close()
            return {"status": "skipped", "reason": "IntegrityError: duplicate URL"}
        conn.close()

        # If no active draft is currently waiting for admin, deliver this draft immediately!
        if not self.has_active_draft_for_admin():
            sent = self.send_draft_to_admin(draft_id)
            return {"status": "delivered_immediately", "draft_id": draft_id, "telegram": sent}

        pending = self.get_pending_count()
        return {"status": "queued", "draft_id": draft_id, "pending_in_queue": pending}

    def send_draft_to_admin(self, draft_id: int) -> bool:
        conn = self.get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, url, headline, caption_html, media_type, media_url, photo_base64 FROM drafts WHERE id = ?", (draft_id,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return False

        did, durl, dhead, dcap, mtype, murl, p_b64 = row
        pending_after = self.get_pending_count() - 1

        markup_rows = [
            [
                {"text": "🚀 Kanalǵa shıǵarıw", "callback_data": f"pub:{did}"},
                {"text": "❌ Biykar etiw", "callback_data": f"del:{did}"}
            ]
        ]
        if pending_after > 0:
            markup_rows.append([{"text": f"📋 Náwbette jáne {pending_after} post bar", "callback_data": f"info:{did}"}])

        reply_markup = {"inline_keyboard": markup_rows}
        res: dict[str, Any] = {"ok": False}

        # 1. Try sending video if media_type == 'video'
        if mtype == "video" and murl:
            res = call_telegram("sendVideo", {
                "chat_id": settings.ADMIN_CHAT_ID,
                "video": murl,
                "caption": dcap,
                "parse_mode": "HTML",
                "reply_markup": json.dumps(reply_markup)
            })

        # 2. Fallback to sending photo
        if not res.get("ok"):
            if p_b64:
                try:
                    p_bytes = base64.b64decode(p_b64)
                    res = call_telegram(
                        "sendPhoto",
                        {
                            "chat_id": settings.ADMIN_CHAT_ID,
                            "caption": dcap,
                            "parse_mode": "HTML",
                            "reply_markup": json.dumps(reply_markup)
                        },
                        files={"photo": ("news.jpg", p_bytes, "image/jpeg")}
                    )
                except Exception as exc:
                    logger.error(f"Error sending photo_base64: {exc}")

        # 3. If still not ok and murl is http
        if not res.get("ok") and murl and murl.startswith("http"):
            res = call_telegram("sendPhoto", {
                "chat_id": settings.ADMIN_CHAT_ID,
                "photo": murl,
                "caption": dcap,
                "parse_mode": "HTML",
                "reply_markup": json.dumps(reply_markup)
            })

        if res.get("ok"):
            admin_msg_id = res["result"]["message_id"]
            cur.execute("UPDATE drafts SET status = 'active', admin_message_id = ? WHERE id = ?", (admin_msg_id, did))
            conn.commit()
            conn.close()
            logger.info(f"Delivered draft #{did} to Admin msg #{admin_msg_id}")
            return True

        logger.error(f"Failed to deliver draft #{did} to admin: {res}")
        conn.close()
        return False

    def send_next_pending_draft(self) -> bool:
        """Pops the oldest pending draft and delivers it to admin."""
        conn = self.get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id FROM drafts WHERE status = 'pending' ORDER BY id ASC LIMIT 1")
        row = cur.fetchone()
        conn.close()
        if row:
            return self.send_draft_to_admin(row[0])
        return False

    def mark_published(self, draft_id: int, channel_message_id: int) -> None:
        conn = self.get_conn()
        cur = conn.cursor()
        cur.execute("UPDATE drafts SET status = 'published' WHERE id = ?", (draft_id,))
        conn.commit()
        conn.close()

    def mark_rejected(self, draft_id: int, reason: str = "Admin rejected via button") -> None:
        conn = self.get_conn()
        cur = conn.cursor()
        cur.execute("SELECT url FROM drafts WHERE id = ?", (draft_id,))
        row = cur.fetchone()
        if row and row[0]:
            clean_url = row[0].strip().split("?")[0].rstrip("/")
            cur.execute("INSERT OR REPLACE INTO blacklisted_urls (url, reason) VALUES (?, ?)", (clean_url, reason))
        cur.execute("UPDATE drafts SET status = 'rejected' WHERE id = ?", (draft_id,))
        conn.commit()
        conn.close()

    def update_caption(self, admin_message_id: int, new_caption: str) -> Optional[int]:
        conn = self.get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id FROM drafts WHERE admin_message_id = ? AND status = 'active'", (admin_message_id,))
        row = cur.fetchone()
        if row:
            did = row[0]
            cur.execute("UPDATE drafts SET caption_html = ? WHERE id = ?", (new_caption, did))
            conn.commit()
            conn.close()
            return did
        conn.close()
        return None

draft_service = DraftQueueService()
