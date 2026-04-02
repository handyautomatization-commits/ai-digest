# 🤖 Squeezed AI — Automated Weekly AI Digest Bot

> A fully automated bot that collects AI news from 15+ sources every week, summarizes it with DeepSeek LLM, and publishes a formatted digest with a cover image to a Telegram channel — hands-free, every Monday at 9 AM.

**Live channel → [@SqueezedAI](https://t.me/SqueezedAI)**

---

## What it does

Every Monday morning the bot:

1. **Collects** fresh AI news from 15+ sources (official blogs, Reddit, Hacker News)
2. **Filters** by relevance and popularity (upvotes / points thresholds)
3. **Summarizes** with DeepSeek LLM into thematic blocks
4. **Generates** a unique branded cover image locally (no external image APIs)
5. **Publishes** cover + digest to Telegram — fully automatically

---

## Example output

```
🤖 Squeezed AI #3 — Week of March 17, 2026

This week was defined by OpenAI's frontier model push...

─────────────────

🚀 Model Releases & Updates

• GPT-5.4 Released — OpenAI's most capable model yet,
  featuring 1M-token context and native computer use.
  ↗ vs GPT-5.3: +40% coding benchmark, 2× cheaper API.
  ⭐9/10 | Read →

🔬 Research Breakthroughs
• ...

🛠️ Tools & Features
• ...

─────────────────

💡 Key Takeaway: The gap between frontier and open-source models is narrowing fast.

#AI #LLM #MachineLearning #SqueezedAI
```

---

## Architecture

```
GitHub Actions (cron: every Monday 09:00 MSK)
        │
        ▼
  fetchers.py ──► 13 RSS feeds (Anthropic, OpenAI, HuggingFace, DeepMind…)
                ──► Reddit RSS  (r/LocalLLaMA, r/MachineLearning, r/artificial)
                ──► Hacker News Algolia API
        │
        ▼
  processor.py ──► DeepSeek API → thematic digest (≤3000 chars)
        │
        ▼
  cover_generator.py ──► Pillow → dark gradient cover image (1280×720)
        │
        ▼
  telegram_bot.py ──► sendPhoto (cover) + sendMessage (digest)
        │
        ▼
  last_run.json ──► committed back to repo (date filter + issue counter)
```

---

## Tech stack

| Layer | Technology |
|---|---|
| Runtime | Python 3.11 |
| Scheduling | GitHub Actions (free tier, cron) |
| LLM | DeepSeek Chat API (via direct HTTP) |
| RSS parsing | feedparser |
| Image generation | Pillow (local, no external APIs) |
| Delivery | Telegram Bot API |
| Secrets | GitHub Actions Secrets |

---

## Sources monitored

**Official AI blogs (RSS)**
Anthropic · OpenAI · HuggingFace · Google DeepMind · Meta AI · Mistral AI

**Newsletters (RSS)**
The Batch (Andrew Ng) · One Useful Thing · The Rundown AI

**Tech media (RSS)**
MIT Tech Review · The Verge AI · VentureBeat AI · Ars Technica AI

**Community**
r/LocalLLaMA · r/MachineLearning · r/artificial (≥100 upvotes via RSS)
Hacker News (≥75 points via Algolia API)

**Vibecoders**
Cursor Blog · ThePrimeagen YouTube

---

## Cost

| Service | Cost |
|---|---|
| GitHub Actions | Free (uses ~10 min/month of 2000 free) |
| DeepSeek API | ~$0.30 / month |
| Telegram Bot API | Free |
| **Total** | **~$0.30 / month** |

---

## Setup

1. Fork this repo
2. Add GitHub Secrets:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - `DEEPSEEK_API_KEY`
   - `TELEGRAM_THREAD_ID` *(optional — for forum topics)*
3. Enable GitHub Actions
4. Trigger manually via **Actions → Run workflow** to test

---

## Project by

Built as part of an automation portfolio.
Interested in a similar bot for your niche? Let's talk.
