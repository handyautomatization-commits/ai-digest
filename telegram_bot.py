"""
telegram_bot.py — Sends the formatted digest to a Telegram channel.
Cover image generated via Pollinations.ai (free, no API key needed).
"""

import os
import time

import requests

TELEGRAM_API = "https://api.telegram.org"
MAX_LENGTH = 4096  # Telegram hard limit per message


# ─────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────

def send_digest(text: str, issue_number: int, week_label: str) -> None:
    """Send cover image + digest text to the Telegram channel."""
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]

    # 1. Try to send cover image (fails gracefully if Pollinations is down)
    _send_cover(token, chat_id, issue_number, week_label)
    time.sleep(1)

    # 2. Send digest text (split if over 4096 chars)
    chunks = _split(text)
    print(f"📨 Sending {len(chunks)} text message(s)...")
    for i, chunk in enumerate(chunks, start=1):
        if i > 1:
            time.sleep(2)
        _send_chunk(token, chat_id, chunk)


# ─────────────────────────────────────────────
# Cover image
# ─────────────────────────────────────────────

def _send_cover(token: str, chat_id: str, issue_number: int, week_label: str) -> None:
    """Generate a cover image via Pollinations.ai and send it with a short caption."""
    try:
        prompt = (
            "Squeezed AI weekly newsletter cover art, "
            "dark background with glowing neural network connections, "
            "deep blue and purple gradient, minimalist tech aesthetic, "
            "professional digital magazine style, high quality"
        )
        encoded = requests.utils.quote(prompt)
        image_url = (
            f"https://image.pollinations.ai/prompt/{encoded}"
            f"?width=1280&height=720&nologo=true&seed={issue_number}"
        )

        print("🎨 Generating cover image...")
        img_resp = requests.get(image_url, timeout=60)
        img_resp.raise_for_status()

        caption = f"🤖 <b>Squeezed AI #{issue_number}</b> · <i>{week_label}</i>"

        resp = requests.post(
            f"{TELEGRAM_API}/bot{token}/sendPhoto",
            files={"photo": ("cover.jpg", img_resp.content, "image/jpeg")},
            data={"chat_id": chat_id, "caption": caption, "parse_mode": "HTML"},
            timeout=30,
        )

        if resp.ok:
            print("  ✓ Cover image sent")
        else:
            print(f"  ⚠️  Cover send failed: {resp.text[:120]}")

    except Exception as exc:
        print(f"  ⚠️  Cover image skipped ({exc}). Sending text only.")


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


def _send_chunk(token: str, chat_id: str, text: str) -> None:
    """POST a single text chunk to the Telegram Bot API."""
    url = f"{TELEGRAM_API}/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
        "link_preview_options": {"is_disabled": True},
    }

    resp = requests.post(url, json=payload, timeout=30)

    if not resp.ok:
        print(f"  ⚠️  HTML parse error: {resp.text[:200]}. Retrying as plain text...")
        payload.pop("parse_mode", None)
        resp = requests.post(url, json=payload, timeout=30)

    if not resp.ok:
        raise RuntimeError(f"Telegram send failed: {resp.text}")

    print(f"  ✓ Sent ({len(text)} chars)")


# ─────────────────────────────────────────────
# Legacy helper (kept for compatibility)
# ─────────────────────────────────────────────

def send_message(text: str) -> None:
    """Send plain text without cover image (used as fallback)."""
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    for chunk in _split(text):
        _send_chunk(token, chat_id, chunk)
