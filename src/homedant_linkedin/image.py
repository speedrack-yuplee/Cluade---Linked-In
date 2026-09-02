"""Rendering a post draft into a branded 1200x1200 LinkedIn image.

The layout follows the creatives the account already publishes: an ivory
ground, the HOMEDANT wordmark over its tagline rule, a dark red headline, up
to three proof points, and a footer band carrying the event or the call to
action.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .models import PostDraft

SIZE = 1200
MARGIN = 90

INK = (30, 30, 30)
ACCENT = (158, 27, 34)
GROUND = (245, 241, 232)
MUTED = (110, 104, 96)
BAND_TEXT = (245, 241, 232)

FONT_DIR = Path("/usr/share/fonts/truetype/liberation")
BOLD = FONT_DIR / "LiberationSans-Bold.ttf"
REGULAR = FONT_DIR / "LiberationSans-Regular.ttf"

MAX_BULLETS = 3
BODY_LINE = 42
BULLET_GAP = 14


class FontsUnavailable(RuntimeError):
    """The bundled layout needs Liberation Sans; say so rather than guessing."""


def _font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(str(path), size)
    except OSError as exc:
        raise FontsUnavailable(
            f"{path} is missing. Install the fonts-liberation package."
        ) from exc


def _wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, width: int) -> list[str]:
    """Greedy wrap on measured width, so long words do not overflow silently."""
    lines: list[str] = []
    for paragraph in text.split("\n"):
        words, line = paragraph.split(), ""
        for word in words:
            candidate = f"{line} {word}".strip()
            if draw.textlength(candidate, font=font) <= width or not line:
                line = candidate
            else:
                lines.append(line)
                line = word
        lines.append(line)
    return lines


def _fit_headline(
    draw: ImageDraw.ImageDraw, text: str, width: int, max_lines: int
) -> tuple[list[str], ImageFont.FreeTypeFont]:
    """The largest headline size that still fits in ``max_lines``."""
    for size in range(72, 33, -4):
        font = _font(BOLD, size)
        lines = _wrap(draw, text, font, width)
        if len(lines) <= max_lines:
            return lines, font
    font = _font(BOLD, 34)
    return _wrap(draw, text, font, width)[:max_lines], font


def _footer_text(draft: PostDraft) -> str:
    """What the bottom band says: the event where there is one, else the brand."""
    slot = draft.slot
    if slot.show:
        booth = f"  ·  {slot.show.location}" if slot.show.booth else ""
        return f"{slot.show.name}  ·  {slot.show.dates}{booth}"
    if slot.recognition:
        return f"{slot.recognition.event}  ·  {slot.recognition.venue}"
    return "HOMEDANT  ·  The Best Organizing Solution"


def render(draft: PostDraft, path: str | Path) -> Path:
    """Write the image for ``draft`` and return the path it was written to."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    image = Image.new("RGB", (SIZE, SIZE), GROUND)
    draw = ImageDraw.Draw(image)
    inner = SIZE - 2 * MARGIN

    # Masthead
    wordmark = _font(BOLD, 46)
    draw.text((MARGIN, MARGIN), "HOMEDANT", font=wordmark, fill=INK)
    draw.text(
        (MARGIN, MARGIN + 58), "The Best Organizing Solution", font=_font(REGULAR, 24), fill=MUTED
    )
    rule_y = MARGIN + 108
    draw.rectangle([MARGIN, rule_y, MARGIN + 120, rule_y + 6], fill=ACCENT)

    # Headline and proof points, as one block centred in the space between
    # the masthead rule and the footer band.
    lines, headline_font = _fit_headline(draw, draft.hook, inner, max_lines=5)
    line_height = int(headline_font.size * 1.28)

    bullets = [b[2:] for b in draft.body.split("\n") if b.startswith("- ")][:MAX_BULLETS]
    body_font = _font(REGULAR, 30)
    wrapped = [_wrap(draw, bullet, body_font, inner - 46) for bullet in bullets]

    block = len(lines) * line_height
    if wrapped:
        block += 40 + sum(len(rows) * BODY_LINE + BULLET_GAP for rows in wrapped) - BULLET_GAP

    top, bottom = rule_y + 40, SIZE - 150
    y = top + max((bottom - top - block) // 2, 30)

    for line in lines:
        draw.text((MARGIN, y), line, font=headline_font, fill=ACCENT)
        y += line_height

    y += 40
    for rows in wrapped:
        draw.ellipse([MARGIN + 4, y + 13, MARGIN + 16, y + 25], fill=ACCENT)
        for line in rows:
            draw.text((MARGIN + 46, y), line, font=body_font, fill=INK)
            y += BODY_LINE
        y += BULLET_GAP

    # Footer band
    band_top = SIZE - 150
    draw.rectangle([0, band_top, SIZE, SIZE], fill=ACCENT)
    footer_font = _font(BOLD, 30)
    footer = _footer_text(draft)
    while draw.textlength(footer, font=footer_font) > inner and footer_font.size > 18:
        footer_font = _font(BOLD, footer_font.size - 2)
    draw.text(
        (MARGIN, band_top + (150 - footer_font.size) // 2 - 4),
        footer,
        font=footer_font,
        fill=BAND_TEXT,
    )

    image.save(path, "PNG", optimize=True)
    return path
