"""
fetchers.py — Collects AI news from RSS feeds, Reddit, and Hacker News.
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

REDDIT_MIN_SCORE = 100
HN_MIN_POINTS = 75

RSS_FEEDS = [
    # ── Official AI Lab Blogs ──────────────────────────────────────────
    {"name": "Anthropic Blog",       "url": "https://www.anthropic.com/rss.xml"},
    {"name": "OpenAI Blog",          "url": "https://openai.com/blog/rss.xml"},
    {"name": "HuggingFace Blog",     "url": "https://huggingface.co/blog/feed.xml"},
    {"name": "Google DeepMind",      "url": "https://deepmind.google/blog/rss"},
    {"name": "Meta AI Blog",         "url": "https://ai.meta.com/blog/rss/"},
    {"name": "Mistral AI",           "url": "https://mistral.ai/blog/feed.xml"},

    # ── Newsletters ───────────────────────────────────────────────────
    {"name": "The Batch (Andrew Ng)","url": "https://www.deeplearning.ai/the-batch/rss/"},
    {"name": "One Useful Thing",     "url": "https://www.oneusefulthing.org/feed"},
    {"name": "The Rundown AI",       "url": "https://www.therundown.ai/rss"},

    # ── Tech Media ────────────────────────────────────────────────────
    {"name": "MIT Tech Review AI",   "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed"},
    {"name": "The Verge AI",         "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"},
    {"name": "VentureBeat AI",       "url": "https://venturebeat.com/category/ai/feed/"},
    {"name": "Ars Technica AI",      "url": "https://arstechnica.com/tag/ai/feed/"},

    # ── Vibecoders (low priority) ─────────────────────────────────────
    {"name": "Cursor Blog",          "url": "https://www.cursor.com/blog/rss"},
    {"name": "ThePrimeagen YouTube", "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCUyeluBRhGPCW4rPe_UvBZQ"},
]

REDDIT_SUBREDDITS = ["LocalLLaMA", "MachineLearning", "artificial"]

HN_QUERIES = [
    "artificial intelligence model release",
    "LLM GPT Claude Gemini Llama",
    "machine learning breakthrough research",
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
    """Fetch articles from all RSS feeds published after `since`."""
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


def fetch_reddit(since: datetime) -> list:
    """Fetch top posts from AI subreddits with score >= REDDIT_MIN_SCORE."""
    articles = []

    for sub in REDDIT_SUBREDDITS:
        try:
            url = f"https://www.reddit.com/r/{sub}/top.json?t=week&limit=50"
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()

            count = 0
            for post in resp.json()["data"]["children"]:
                p = post["data"]
                post_time = datetime.fromtimestamp(p["created_utc"], tz=timezone.utc)

                if post_time < since or p["score"] < REDDIT_MIN_SCORE:
                    continue

                # Link posts → external URL; text posts → Reddit permalink
                is_self = p.get("is_self", False)
                main_url = (
                    f"https://reddit.com{p['permalink']}"
                    if is_self
                    else p.get("url", f"https://reddit.com{p['permalink']}")
                )

                articles.append({
                    "source": f"r/{sub}",
                    "title": p["title"],
                    "url": main_url,
                    "reddit_url": f"https://reddit.com{p['permalink']}",
                    "summary": p.get("selftext", "")[:300] if is_self else "",
                    "score": p["score"],
                    "date": post_time.strftime("%Y-%m-%d"),
                    "type": "reddit",
                })
                count += 1

            print(f"  ✓ r/{sub}: {count} posts")

        except Exception as exc:
            print(f"  ✗ r/{sub}: {exc}")

        time.sleep(1.0)

    return articles


def fetch_hackernews(since: datetime) -> list:
    """Fetch AI-related HN stories with points >= HN_MIN_POINTS."""
    articles = []
    since_ts = int(since.timestamp())
    seen_ids: set = set()

    for query in HN_QUERIES:
        try:
            resp = requests.get(
                "https://hn.algolia.com/api/v1/search",
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
    print("\n📡 RSS feeds...")
    rss = fetch_rss_feeds(since)

    print("\n🔴 Reddit...")
    reddit = fetch_reddit(since)

    print("\n🟠 Hacker News...")
    hn = fetch_hackernews(since)

    all_items = rss + reddit + hn
    print(f"\n📊 Total collected: {len(all_items)} items")
    return all_items
