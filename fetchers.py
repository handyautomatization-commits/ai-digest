"""
fetchers.py — Collects AI news from RSS feeds and Hacker News.

Reddit note: Reddit blocks requests from cloud servers (GitHub Actions).
We use Reddit's RSS feeds instead — they go through feedparser like any other RSS.
"""

import html
import re
import time
from datetime import datetime, timezone

import feedparser
import requests

# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────

HEADERS = {
    "User-Agent": "AI-Weekly-Digest/1.0 (Open-source educational bot)"
}

HN_MIN_POINTS = 75

RSS_FEEDS = [
    # ── Official AI Lab Blogs ──────────────────────────────────────────
    {"name": "Anthropic Blog",        "url": "https://www.anthropic.com/rss.xml"},
    {"name": "OpenAI Blog",           "url": "https://openai.com/blog/rss.xml"},
    {"name": "HuggingFace Blog",      "url": "https://huggingface.co/blog/feed.xml"},
    {"name": "Google DeepMind",       "url": "https://deepmind.google/blog/rss"},
    {"name": "Meta AI Blog",          "url": "https://ai.meta.com/blog/rss/"},
    {"name": "Mistral AI",            "url": "https://mistral.ai/blog/feed.xml"},

    # ── Newsletters ───────────────────────────────────────────────────
    {"name": "The Batch (Andrew Ng)", "url": "https://www.deeplearning.ai/the-batch/rss/"},
    {"name": "One Useful Thing",      "url": "https://www.oneusefulthing.org/feed"},
    {"name": "The Rundown AI",        "url": "https://www.therundown.ai/rss"},

    # ── Tech Media ────────────────────────────────────────────────────
    {"name": "MIT Tech Review AI",    "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed"},
    {"name": "The Verge AI",          "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"},
    {"name": "VentureBeat AI",        "url": "https://venturebeat.com/category/ai/feed/"},
    {"name": "Ars Technica AI",       "url": "https://arstechnica.com/tag/ai/feed/"},

    # ── Reddit (via RSS — works without authentication) ───────────────
    {"name": "r/LocalLLaMA",         "url": "https://www.reddit.com/r/LocalLLaMA/top.rss?t=week"},
    {"name": "r/MachineLearning",    "url": "https://www.reddit.com/r/MachineLearning/top.rss?t=week"},
    {"name": "r/artificial",         "url": "https://www.reddit.com/r/artificial/top.rss?t=week"},

    # ── Vibecoders (low priority) ─────────────────────────────────────
    {"name": "Cursor Blog",           "url": "https://www.cursor.com/blog/rss"},
    {"name": "ThePrimeagen YouTube",  "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCUyeluBRhGPCW4rPe_UvBZQ"},
]

# Simpler queries = more HN results
HN_QUERIES = [
    "artificial intelligence",
    "LLM language model",
    "GPT Claude Gemini",
    "AI benchmark",
]


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def clean_html(text: str) -> str:
    """Strip HTML tags and decode entities."""
    text = re.sub(r"<[^>]+>", " ", text)
    return html.unescape(text).strip()


# ─────────────────────────────────────────────
# Fetchers
# ─────────────────────────────────────────────

def fetch_rss_feeds(since: datetime) -> list:
    """Fetch articles from all RSS feeds (including Reddit RSS) published after `since`."""
    feedparser.USER_AGENT = HEADERS["User-Agent"]
    articles = []

    for feed_info in RSS_FEEDS:
        name = feed_info["name"]
        count_before = len(articles)
        try:
            feed = feedparser.parse(feed_info["url"])

            for entry in feed.entries:
                pub_date = None
                for attr in ("published_parsed", "updated_parsed"):
                    parsed = getattr(entry, attr, None)
                    if parsed:
                        pub_date = datetime(*parsed[:6], tzinfo=timezone.utc)
                        break

                if pub_date is None or pub_date < since:
                    continue

                summary = clean_html(
                    entry.get("summary", entry.get("description", ""))
                )[:400]

                articles.append({
                    "source": name,
                    "title": entry.get("title", "No title").strip(),
                    "url": entry.get("link", ""),
                    "summary": summary,
                    "date": pub_date.strftime("%Y-%m-%d"),
                    "type": "rss",
                })

            added = len(articles) - count_before
            print(f"  ✓ {name}: {added} items")

        except Exception as exc:
            print(f"  ✗ {name}: {exc}")

        time.sleep(0.5)

    return articles


def fetch_hackernews(since: datetime) -> list:
    """Fetch AI-related HN stories with points >= HN_MIN_POINTS."""
    articles = []
    since_ts = int(since.timestamp())
    seen_ids: set = set()

    for query in HN_QUERIES:
        try:
            resp = requests.get(
                "https://hn.algolia.com/api/v1/search_by_date",
                params={
                    "tags": "story",
                    "query": query,
                    "hitsPerPage": 30,
                    "numericFilters": f"created_at_i>{since_ts},points>{HN_MIN_POINTS}",
                },
                timeout=15,
            )
            resp.raise_for_status()

            for hit in resp.json().get("hits", []):
                oid = hit["objectID"]
                if oid in seen_ids:
                    continue
                seen_ids.add(oid)

                hn_url = f"https://news.ycombinator.com/item?id={oid}"
                articles.append({
                    "source": "Hacker News",
                    "title": hit.get("title", ""),
                    "url": hit.get("url") or hn_url,
                    "hn_url": hn_url,
                    "score": hit.get("points", 0),
                    "date": (hit.get("created_at") or "")[:10],
                    "summary": "",
                    "type": "hn",
                })

        except Exception as exc:
            print(f"  ✗ HN '{query}': {exc}")

        time.sleep(0.5)

    print(f"  ✓ Hacker News: {len(articles)} stories")
    return articles


# ─────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────

def fetch_all(since: datetime) -> list:
    """Collect content from all sources and return a unified list."""
    print("\n📡 RSS feeds (blogs + Reddit)...")
    rss = fetch_rss_feeds(since)

    print("\n🟠 Hacker News...")
    hn = fetch_hackernews(since)

    all_items = rss + hn
    print(f"\n📊 Total collected: {len(all_items)} items")
    return all_items
