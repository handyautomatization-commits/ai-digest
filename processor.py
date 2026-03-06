"""
processor.py — Sends collected articles to DeepSeek and returns a formatted digest.
Uses requests directly (no openai SDK needed).
"""

import json
import os
from datetime import datetime, timezone

import requests

DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"


def _build_prompt(articles: list) -> str:
    """Construct the prompt for DeepSeek."""
    week_label = datetime.now(timezone.utc).strftime("Week of %B %d, %Y")

    # Trim to 60 items max and simplify fields to save tokens
    simplified = [
        {
            "source": a["source"],
            "title": a["title"],
            "url": a.get("url") or a.get("hn_url") or a.get("reddit_url") or "",
            "summary": a.get("summary", "")[:250],
            "score": a.get("score", ""),
            "date": a.get("date", ""),
        }
        for a in articles[:60]
    ]

    items_json = json.dumps(simplified, ensure_ascii=False)

    return f"""You are an AI news curator. Create a weekly digest for a PUBLIC Telegram channel about AI breakthroughs and updates.

WEEK: {week_label}

━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT FORMAT (Telegram HTML only — zero Markdown):
━━━━━━━━━━━━━━━━━━━━━━━━━━

🤖 <b>AI Weekly Digest — {week_label}</b>

[2-sentence intro: highlight the biggest theme of this week]

─────────────────

🚀 <b>Model Releases & Updates</b>
• <b>[Short title]</b> — [2 sentences: what it is + why it matters]. ⭐[X]/10 | <a href="[URL]">Read →</a>

🔬 <b>Research Breakthroughs</b>
• ...

🛠️ <b>Tools & Features</b>
• ... (put Cursor / vibe coding news here if present)

📊 <b>Benchmarks & Comparisons</b>
• ... (include model comparisons, leaderboard changes)

🌍 <b>Industry News</b>
• ...

─────────────────

💡 <b>Key Takeaway:</b> [One powerful sentence about the week]

<i>📡 Sources: Official AI blogs · r/LocalLLaMA · r/MachineLearning · Hacker News</i>

━━━━━━━━━━━━━━━━━━━━━━━━━━
STRICT RULES:
━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Only include blocks that have relevant content — skip empty blocks entirely.
2. Max 4 items per block. Choose the most impactful ones.
3. Impact score guide: 10 = AGI-level event | 8-9 = major model release | 6-7 = important feature | 4-5 = tool update | 1-3 = minor news.
4. Every item MUST end with: ⭐X/10 | <a href="URL">Read →</a>
5. Use ONLY these HTML tags: <b>, <i>, <a href="">. NO markdown (no **, no __, no ##).
6. Skip opinion pieces, duplicate items, or vague/minor updates.
7. Total output MUST be under 3800 characters.
8. Never invent facts — only use what is in the data below.

━━━━━━━━━━━━━━━━━━━━━━━━━━
NEWS ITEMS (JSON):
━━━━━━━━━━━━━━━━━━━━━━━━━━
{items_json}"""


def process_with_deepseek(articles: list) -> str:
    """Send articles to DeepSeek and return a Telegram-ready digest string."""
    prompt = _build_prompt(articles)
    print(f"📤 Sending {len(articles)} items to DeepSeek...")

    resp = requests.post(
        DEEPSEEK_URL,
        headers={
            "Authorization": f"Bearer {os.environ['DEEPSEEK_API_KEY']}",
            "Content-Type": "application/json",
        },
        json={
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 2500,
            "temperature": 0.4,
        },
        timeout=120,
    )
    resp.raise_for_status()

    data = resp.json()
    digest = data["choices"][0]["message"]["content"].strip()
    usage = data.get("usage", {})
    print(
        f"📥 Digest received ({len(digest)} chars) | "
        f"Tokens: {usage.get('prompt_tokens', '?')} in / {usage.get('completion_tokens', '?')} out"
    )
    return digest
