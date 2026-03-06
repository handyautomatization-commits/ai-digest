"""
telegram_bot.py — Sends the formatted digest to a Telegram channel.
"""

import os

import requests

TELEGRAM_API = "https://api.telegram.org"
MAX_LENGTH = 4096  # Telegram hard limit per message


def send_message(text: str) -> None:
    """Send digest to the configured Telegram channel.
    Splits automatically if the text exceeds 4096 characters.
    """
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]

    chunks = _split(text)
    print(f"📨 Sending {len(chunks)} message(s) to Telegram...")

    for i, chunk in enumerate(chunks, start=1):
        label = f"(Part {i}/{len(chunks)})\n" if len(chunks) > 1 else ""
        _send_chunk(token, chat_id, label + chunk)


def _split(text: str) -> list:
    """Split text into Telegram-safe chunks at paragraph boundaries."""
    if len(text) <= MAX_LENGTH:
        return [text]

    chunks = []
    while len(text) > MAX_LENGTH:
        # Try to split at a double newline (paragraph boundary)
        split_at = text.rfind("\n\n", 0, MAX_LENGTH)
        if split_at == -1:
            # Fallback: single newline
            split_at = text.rfind("\n", 0, MAX_LENGTH)
        if split_at == -1:
            # Hard cut
            split_at = MAX_LENGTH

        chunks.append(text[:split_at].rstrip())
        text = text[split_at:].lstrip()

    if text:
        chunks.append(text)

    return chunks


def _send_chunk(token: str, chat_id: str, text: str) -> None:
    """POST a single chunk to the Telegram Bot API."""
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
        # Retry without HTML parsing (plain-text fallback)
        print(f"  ⚠️  HTML parse error: {resp.text[:200]}. Retrying as plain text...")
        payload.pop("parse_mode", None)
        resp = requests.post(url, json=payload, timeout=30)

    if not resp.ok:
        raise RuntimeError(f"Telegram send failed: {resp.text}")

    print(f"  ✓ Sent ({len(text)} chars)")
