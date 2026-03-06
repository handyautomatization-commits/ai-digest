"""
main.py — Orchestrates the AI Weekly Digest pipeline.

Flow:
  1. Load the timestamp of the last successful run (last_run.json)
  2. Fetch new content from all sources since that timestamp
  3. Send to DeepSeek → get a formatted digest
  4. Post digest to Telegram channel
  5. Save the current timestamp to last_run.json
"""

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fetchers import fetch_all
from processor import process_with_deepseek
from telegram_bot import send_message

LAST_RUN_FILE = Path("last_run.json")


# ─────────────────────────────────────────────
# Timestamp helpers
# ─────────────────────────────────────────────

def load_since() -> datetime:
    """Return the timestamp of the last run, or 8 days ago as default."""
    try:
        data = json.loads(LAST_RUN_FILE.read_text(encoding="utf-8"))
        since = datetime.fromisoformat(data["last_run"])
        print(f"📅 Last run: {since.strftime('%Y-%m-%d %H:%M UTC')}")
        return since
    except Exception:
        default = datetime.now(timezone.utc) - timedelta(days=8)
        print(f"📅 No previous run found. Fetching last 8 days (since {default.strftime('%Y-%m-%d')})")
        return default


def save_run_time() -> None:
    """Persist the current UTC timestamp so the next run knows where to start."""
    LAST_RUN_FILE.write_text(
        json.dumps({"last_run": datetime.now(timezone.utc).isoformat()}, indent=2),
        encoding="utf-8",
    )
    print("💾 last_run.json updated")


# ─────────────────────────────────────────────
# Pipeline
# ─────────────────────────────────────────────

def main() -> None:
    print("=" * 50)
    print("🤖 AI Weekly Digest — Pipeline Start")
    print("=" * 50)

    # Step 1 — determine date window
    since = load_since()

    # Step 2 — fetch all sources
    articles = fetch_all(since)

    if not articles:
        print("\n⚠️  No articles collected this week. Nothing to send.")
        # Still update last_run so we don't re-fetch the same empty window next time
        save_run_time()
        sys.exit(0)

    # Step 3 — process with DeepSeek
    print("\n🧠 Processing with DeepSeek...")
    digest = process_with_deepseek(articles)

    # Step 4 — send to Telegram
    print("\n✉️  Sending to Telegram...")
    send_message(digest)

    # Step 5 — save run timestamp
    save_run_time()

    print("\n✅ Done! Digest sent successfully.")
    print("=" * 50)


if __name__ == "__main__":
    main()
