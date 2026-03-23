"""
telegram_bot.py — Sends the formatted digest to a Telegram channel or forum topic.
Cover image is generated locally via Pillow (no external APIs).
"""

import os
import time

import requests

from cover_generator import generate_cover

TELEGRAM_API = "https://api.telegram.org"
MAX_LENGTH = 4096  # Telegram hard limit per message


def _get_thread_id() -> int | None:
    """Return message_thread_id if TELEGRAM_THREAD_ID is set, else None."""
    val = os.environ.get("TELEGRAM_THREAD_ID", "").strip()
    return int(val) if val else None


# ─────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────

def send_digest(text: str, issue_number: int, week_label: str) -> None:
    """Send cover image + digest text to the Telegram channel/topic."""
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    thread_id = _get_thread_id()

    # 1. Send cover image
    _send_cover(token, chat_id, thread_id, issue_number, week_label)
    time.sleep(1)

    # 2. Send digest text (split if over 4096 chars)
    chunks = _split(text)
    print(f"📨 Sending {len(chunks)} text message(s)...")
    for i, chunk in enumerate(chunks, start=1):
        if i > 1:
            time.sleep(2)
        _send_chunk(token, chat_id, thread_id, chunk)


# ─────────────────────────────────────────────
# Cover image
# ─────────────────────────────────────────────

def _send_cover(token: str, chat_id: str, thread_id: int | None,
                issue_number: int, week_label: str) -> None:
    """Generate cover locally and send as photo with short caption."""
    try:
        print(f"🎨 Generating cover image (issue #{issue_number})...")
        image_bytes = generate_cover(issue_number, week_label)
        print(f"  ✓ Image generated ({len(image_bytes)} bytes)")

        caption = f"🤖 <b>Squeezed AI #{issue_number}</b> · <i>{week_label}</i>"

        data = {"chat_id": chat_id, "caption": caption, "parse_mode": "HTML"}
        if thread_id:
            data["message_thread_id"] = thread_id

        resp = requests.post(
            f"{TELEGRAM_API}/bot{token}/sendPhoto",
            files={"photo": ("cover.jpg", image_bytes, "image/jpeg")},
            data=data,
            timeout=30,
        )

        if resp.ok:
            print("  ✓ Cover sent to Telegram")
        else:
            print(f"  ⚠️  Cover send failed: {resp.text[:120]}")

    except Exception as exc:
        print(f"  ⚠️  Cover skipped: {exc}. Continuing with text only.")


# ─────────────────────────────────────────────
# Text helpers
# ─────────────────────────────────────────────

def _split(text: str) -> list:
    """Split text into Telegram-safe chunks at paragraph boundaries."""
    if len(text) <= MAX_LENGTH:
        return [text]

    chunks = []
    while len(text) > MAX_LENGTH:
        split_at = text.rfind("\n\n", 0, MAX_LENGTH)
        if split_at == -1:
            split_at = text.rfind("\n", 0, MAX_LENGTH)
        if split_at == -1:
            split_at = MAX_LENGTH
        chunks.append(text[:split_at].rstrip())
        text = text[split_at:].lstrip()

    if text:
        chunks.append(text)
    return chunks


def _send_chunk(token: str, chat_id: str, thread_id: int | None, text: str) -> None:
    """POST a single text chunk to the Telegram Bot API."""
    url = f"{TELEGRAM_API}/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
        "link_preview_options": {"is_disabled": True},
    }
    if thread_id:
        payload["message_thread_id"] = thread_id

    resp = requests.post(url, json=payload, timeout=30)

    if not resp.ok:
        print(f"  ⚠️  HTML parse error: {resp.text[:200]}. Retrying as plain text...")
        payload.pop("parse_mode", None)
        resp = requests.post(url, json=payload, timeout=30)

    if not resp.ok:
        raise RuntimeError(f"Telegram send failed: {resp.text}")

    print(f"  ✓ Sent ({len(text)} chars)")


# ─────────────────────────────────────────────
# Legacy helper
# ─────────────────────────────────────────────

def send_message(text: str) -> None:
    """Send plain text without cover image (fallback)."""
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    thread_id = _get_thread_id()
    for chunk in _split(text):
        _send_chunk(token, chat_id, thread_id, chunk)
