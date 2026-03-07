"""
main.py — Orchestrates the AI Weekly Digest pipeline.

Flow:
  1. Load state (last run timestamp + issue number) from last_run.json
  2. Fetch new content from all sources since that timestamp
  3. Send to DeepSeek → get a formatted digest
  4. Send cover image + digest text to Telegram
  5. Save updated state to last_run.json
"""

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fetchers import fetch_all
from processor import process_with_deepseek
from telegram_bot import send_digest

LAST_RUN_FILE = Path("last_run.json")


# ─────────────────────────────────────────────
# State helpers
# ─────────────────────────────────────────────

def load_state() -> tuple:
    """Return (since_datetime, issue_number)."""
    try:
        data = json.loads(LAST_RUN_FILE.read_text(encoding="utf-8"))
        since = datetime.fromisoformat(data["last_run"])
        issue_number = data.get("issue_number", 0) + 1
        print(f"📅 Last run: {since.strftime('%Y-%m-%d %H:%M UTC')} | Next issue: #{issue_number}")
        return since, issue_number
    except Exception:
        default = datetime.now(timezone.utc) - timedelta(days=8)
        print(f"📅 First run. Fetching last 8 days. Issue: #1")
        return default, 1


def save_state(issue_number: int) -> None:
    """Persist timestamp and issue number for the next run."""
    LAST_RUN_FILE.write_text(
        json.dumps(
            {
                "last_run": datetime.now(timezone.utc).isoformat(),
                "issue_number": issue_number,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"💾 State saved (issue #{issue_number})")


# ─────────────────────────────────────────────
# Pipeline
# ─────────────────────────────────────────────

def main() -> None:
    print("=" * 50)
    print("🤖 Squeezed AI — Pipeline Start")
    print("=" * 50)

    # Step 1 — load state
    since, issue_number = load_state()
    week_label = datetime.now(timezone.utc).strftime("Week of %B %d, %Y")

    # Step 2 — fetch all sources
    articles = fetch_all(since)

    if not articles:
        print("\n⚠️  No articles collected this week. Nothing to send.")
        save_state(issue_number - 1)  # Don't increment issue number on empty run
        sys.exit(0)

    # Step 3 — process with DeepSeek
    print("\n🧠 Processing with DeepSeek...")
    digest = process_with_deepseek(articles, issue_number, week_label)

    # Step 4 — send cover + digest to Telegram
    print("\n✉️  Sending to Telegram...")
    send_digest(digest, issue_number, week_label)

    # Step 5 — save state
    save_state(issue_number)

    print("\n✅ Done! Digest sent successfully.")
    print("=" * 50)


if __name__ == "__main__":
    main()
