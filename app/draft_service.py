import base64
import json
import logging
import os
import threading
import time
import urllib.request
from pathlib import Path
from typing import Any, Optional
import requests

from app.config import settings

logger = logging.getLogger(__name__)

LOCAL_STATE_PATH = Path("data/moderation_state.json")

def call_telegram(method: str, payload: dict[str, Any], files: dict[str, Any] | None = None) -> dict[str, Any]:
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/{method}"
    try:
        if files:
            r = requests.post(url, data=payload, files=files, timeout=15)
        else:
            r = requests.post(url, json=payload, timeout=15)
        return r.json()
    except Exception as exc:
        logger.error(f"Telegram API {method} error: {exc}")
        return {"ok": False, "error": str(exc)}


class PersistentDraftQueueService:
    """
    100% Persistent Sequential Moderation Queue for Sardarbek (@sardardww).
    Backs up all drafts and active status to GitHub repository so container
    restarts / free-tier sleeps NEVER wipe the queue or cause double posts!
    """

    def __init__(self):
        self.lock = threading.Lock()
        self.state: dict[str, Any] = {
            "next_id": 1,
            "active_draft": None,      # The single draft currently displayed to admin
            "pending_queue": [],       # All queued drafts waiting in line
            "blacklisted_urls": [
                "https://t.me/xaliq_ushin/15414"
            ]
        }
        self.load_state()

    def _sync_from_github(self) -> bool:
        if not settings.GITHUB_PAT:
            return False
        url = f"https://api.github.com/repos/{settings.GITHUB_REPO}/contents/data/moderation_state.json"
        req = urllib.request.Request(
            url,
            headers={"Authorization": f"token {settings.GITHUB_PAT}", "User-Agent": "Antigravity"}
        )
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                remote_json = json.loads(base64.b64decode(data["content"]).decode("utf-8"))
                self.state.update(remote_json)
                logger.info(f"Loaded persistent state from GitHub: active={bool(self.state.get('active_draft'))}, pending={len(self.state.get('pending_queue', []))}")
                return True
        except Exception as exc:
            logger.warning(f"Could not load state from GitHub: {exc}")
            return False

    def _sync_to_github_async(self):
        def _do_push():
            if not settings.GITHUB_PAT:
                return
            url = f"https://api.github.com/repos/{settings.GITHUB_REPO}/contents/data/moderation_state.json"
            try:
                # Get current SHA
                sha = None
                req = urllib.request.Request(
                    url,
                    headers={"Authorization": f"token {settings.GITHUB_PAT}", "User-Agent": "Antigravity"}
                )
                try:
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        d = json.loads(resp.read().decode("utf-8"))
                        sha = d.get("sha")
                except urllib.error.HTTPError as e:
                    if e.code != 404:
                        return

                with self.lock:
                    dumped = json.dumps(self.state, ensure_ascii=False, indent=2)

                body = {
                    "message": "sync: update moderation queue persistent state",
                    "content": base64.b64encode(dumped.encode("utf-8")).decode("utf-8")
                }
                if sha:
                    body["sha"] = sha

                req2 = urllib.request.Request(
                    url,
                    data=json.dumps(body).encode("utf-8"),
                    headers={"Authorization": f"token {settings.GITHUB_PAT}", "User-Agent": "Antigravity", "Content-Type": "application/json"},
                    method="PUT"
                )
                urllib.request.urlopen(req2, timeout=15)
                logger.info("Successfully synced moderation state to GitHub.")
            except Exception as exc:
                logger.warning(f"Error syncing state to GitHub: {exc}")

        t = threading.Thread(target=_do_push, daemon=True)
        t.start()

    def load_state(self):
        with self.lock:
            # 1. Try local file first
            if LOCAL_STATE_PATH.exists():
                try:
                    self.state.update(json.loads(LOCAL_STATE_PATH.read_text(encoding="utf-8")))
                except Exception:
                    pass
            # 2. Sync with GitHub for true persistence
            self._sync_from_github()
            self._save_local_state_locked()

    def _save_local_state_locked(self):
        LOCAL_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        LOCAL_STATE_PATH.write_text(json.dumps(self.state, ensure_ascii=False, indent=2), encoding="utf-8")

    def save_state(self):
        with self.lock:
            self._save_local_state_locked()
        self._sync_to_github_async()

    def is_url_seen_or_blacklisted(self, url: str) -> bool:
        if not url:
            return False
        clean = url.strip().split("?")[0].rstrip("/")
        with self.lock:
            if clean in self.state.get("blacklisted_urls", []):
                return True
            active = self.state.get("active_draft")
            if active and active.get("url") == clean:
                return True
            for d in self.state.get("pending_queue", []):
                if d.get("url") == clean:
                    return True
        return False

    def get_blacklisted_and_seen_urls(self) -> list[str]:
        with self.lock:
            urls = list(self.state.get("blacklisted_urls", []))
            active = self.state.get("active_draft")
            if active and active.get("url"):
                urls.append(active["url"])
            for d in self.state.get("pending_queue", []):
                if d.get("url"):
                    urls.append(d["url"])
        return list(set(urls))

    def has_active_draft_for_admin(self) -> bool:
        with self.lock:
            return self.state.get("active_draft") is not None

    def get_pending_count(self) -> int:
        with self.lock:
            return len(self.state.get("pending_queue", []))

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

        with self.lock:
            draft_id = self.state.get("next_id", 1)
            self.state["next_id"] = draft_id + 1

            new_item = {
                "id": draft_id,
                "url": clean_url,
                "headline": headline,
                "caption_html": caption_html,
                "media_type": media_type,
                "media_url": media_url,
                "photo_base64": photo_base64,
                "created_at": time.time()
            }

            has_active = self.state.get("active_draft") is not None
            if not has_active:
                # Deliver this draft immediately as active
                self.state["active_draft"] = new_item
                self.save_state()
                threading.Thread(target=self._deliver_draft_to_telegram, args=(new_item,), daemon=True).start()
                return {"status": "delivered_immediately", "draft_id": draft_id}
            else:
                # Admin already has an active post in chat! Append to queue strictly!
                self.state["pending_queue"].append(new_item)
                self.save_state()
                pending_count = len(self.state["pending_queue"])
                logger.info(f"Draft #{draft_id} added to pending queue (Total in queue: {pending_count}). Admin currently has active post.")
                return {"status": "queued", "draft_id": draft_id, "pending_in_queue": pending_count}

    def _deliver_draft_to_telegram(self, draft: dict[str, Any]) -> bool:
        did = draft["id"]
        dcap = draft["caption_html"]
        mtype = draft.get("media_type", "photo")
        murl = draft.get("media_url", "")
        p_b64 = draft.get("photo_base64")

        with self.lock:
            pending_left = len(self.state.get("pending_queue", []))

        markup_rows = [
            [
                {"text": "🚀 Kanalǵa shıǵarıw", "callback_data": f"pub:{did}"},
                {"text": "❌ Biykar etiw", "callback_data": f"del:{did}"}
            ]
        ]
        if pending_left > 0:
            markup_rows.append([{"text": f"📋 Náwbette jáne {pending_left} post bar", "callback_data": f"info:{did}"}])

        reply_markup = {"inline_keyboard": markup_rows}
        res: dict[str, Any] = {"ok": False}

        # 1. Try sending video
        if mtype == "video" and murl:
            res = call_telegram("sendVideo", {
                "chat_id": settings.ADMIN_CHAT_ID,
                "video": murl,
                "caption": dcap,
                "parse_mode": "HTML",
                "reply_markup": json.dumps(reply_markup)
            })

        # 2. Fallback to sending photo bytes
        if not res.get("ok") and p_b64:
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

        # 3. Fallback to sending photo URL
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
            with self.lock:
                if self.state.get("active_draft"):
                    self.state["active_draft"]["admin_message_id"] = admin_msg_id
            self.save_state()
            logger.info(f"Delivered draft #{did} to Admin msg #{admin_msg_id}")
            return True

        logger.error(f"Failed to deliver draft #{did} to admin: {res}")
        return False

    def send_next_pending_draft(self) -> bool:
        """Pops the next draft in line and delivers it to admin."""
        next_item = None
        with self.lock:
            if self.state.get("pending_queue"):
                next_item = self.state["pending_queue"].pop(0)
                self.state["active_draft"] = next_item
        if next_item:
            self.save_state()
            threading.Thread(target=self._deliver_draft_to_telegram, args=(next_item,), daemon=True).start()
            return True
        else:
            with self.lock:
                self.state["active_draft"] = None
            self.save_state()
            return False

    def mark_published(self, draft_id: Optional[int] = None, channel_message_id: int = 0) -> None:
        with self.lock:
            active = self.state.get("active_draft")
            if active:
                clean = active.get("url")
                if clean and clean not in self.state.get("blacklisted_urls", []):
                    self.state.setdefault("blacklisted_urls", []).append(clean)
                self.state["active_draft"] = None
        self.save_state()

    def mark_rejected(self, draft_id: Optional[int] = None, reason: str = "Admin rejected via button") -> None:
        with self.lock:
            active = self.state.get("active_draft")
            if active:
                clean = active.get("url")
                if clean and clean not in self.state.get("blacklisted_urls", []):
                    self.state.setdefault("blacklisted_urls", []).append(clean)
                self.state["active_draft"] = None
        self.save_state()

    def update_caption(self, admin_message_id: int, new_caption: str) -> Optional[int]:
        with self.lock:
            active = self.state.get("active_draft")
            if active and active.get("admin_message_id") == admin_message_id:
                active["caption_html"] = new_caption
                did = active.get("id")
                self.save_state()
                return did
        return None

draft_service = PersistentDraftQueueService()
