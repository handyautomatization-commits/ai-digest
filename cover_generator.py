"""
cover_generator.py — Generates a branded cover image for Squeezed AI digest.
Uses Pillow only — no external APIs, always works.
"""

import io
import random

from PIL import Image, ImageDraw, ImageFont


# ─────────────────────────────────────────────
# Font loader (works on Linux/Windows/macOS)
# ─────────────────────────────────────────────

def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    suffix = "Bold" if bold else "Regular"
    candidates = [
        # Linux (GitHub Actions)
        f"/usr/share/fonts/truetype/liberation/LiberationSans-{suffix}.ttf",
        f"/usr/share/fonts/truetype/dejavu/DejaVuSans-{'Bold' if bold else ''}.ttf",
        # Windows
        f"C:/Windows/Fonts/{'arialbd' if bold else 'arial'}.ttf",
        # macOS
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


# ─────────────────────────────────────────────
# Cover generator
# ─────────────────────────────────────────────

def generate_cover(issue_number: int, week_label: str) -> bytes:
    """
    Generate a dark, branded cover image for the digest.
    Returns JPEG bytes ready to send to Telegram.
    """
    W, H = 1280, 720
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img, "RGBA")

    # ── 1. Dark gradient background ──────────────────────────────────
    for y in range(H):
        t = y / H
        r = int(8  + 10 * t)
        g = int(10 + 12 * t)
        b = int(28 + 30 * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # ── 2. Glowing dots (neural network feel) ────────────────────────
    rng = random.Random(issue_number)
    palettes = [
        (60,  120, 255),   # blue
        (130,  60, 255),   # purple
        (60,  200, 255),   # cyan
    ]
    for _ in range(50):
        cx = rng.randint(0, W)
        cy = rng.randint(0, H)
        radius = rng.randint(2, 10)
        color = rng.choice(palettes)
        # Soft outer glow
        for layer in range(4, 0, -1):
            draw.ellipse(
                [cx - radius * layer, cy - radius * layer,
                 cx + radius * layer, cy + radius * layer],
                fill=(*color, 18 * layer),
            )
        # Bright core
        draw.ellipse(
            [cx - radius, cy - radius, cx + radius, cy + radius],
            fill=(*color, 200),
        )

    # ── 3. Subtle horizontal lines (decoration) ───────────────────────
    line_color = (60, 100, 255, 60)
    for lx in range(0, W, 80):
        draw.line([(lx, 0), (lx, H)], fill=line_color, width=1)

    # ── 4. Centre card (semi-transparent dark panel) ──────────────────
    card_w, card_h = 700, 260
    card_x = (W - card_w) // 2
    card_y = (H - card_h) // 2
    draw.rounded_rectangle(
        [card_x, card_y, card_x + card_w, card_y + card_h],
        radius=20,
        fill=(10, 12, 25, 200),
        outline=(70, 110, 255, 120),
        width=2,
    )

    # ── 5. Text ───────────────────────────────────────────────────────
    font_title  = _load_font(72, bold=True)
    font_issue  = _load_font(36, bold=False)
    font_week   = _load_font(24, bold=False)

    cx = W // 2
    # "Squeezed AI"
    draw.text((cx, card_y + 80), "Squeezed AI",
              fill=(255, 255, 255), font=font_title, anchor="mm")
    # "Weekly Digest  #N"
    draw.text((cx, card_y + 155), f"Weekly Digest  #{issue_number}",
              fill=(140, 175, 255), font=font_issue, anchor="mm")
    # week label
    draw.text((cx, card_y + 210), week_label,
              fill=(100, 125, 180), font=font_week, anchor="mm")

    # ── 6. Encode to JPEG bytes ───────────────────────────────────────
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=92)
    return buf.getvalue()
