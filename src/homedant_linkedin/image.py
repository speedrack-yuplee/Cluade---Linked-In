"""Rendering a post draft into a branded 1200x1200 LinkedIn image.

Each pillar gets the treatment its subject deserves rather than one template
with the words swapped: a show post is a dark event card built around the
countdown, an award post carries its badge, and a product post is led by the
product. Where an optional asset is missing the layout closes up around it, so
a post always renders.
"""

from __future__ import annotations

import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .models import PostDraft

SIZE = 1200
MARGIN = 90
BAND = 150

# Warm ivory ground with the brand red, as on the account's own creatives.
INK = (30, 30, 30)
ACCENT = (158, 27, 34)
GROUND = (245, 241, 232)
PANEL = (255, 255, 255)
MUTED = (110, 104, 96)
LIGHT_TEXT = (245, 241, 232)

# Show posts run on steel, so they read as an event at a glance in the feed.
SHOW_GROUND = (27, 42, 51)
SHOW_ACCENT = (214, 168, 88)
SEASON_ACCENT = (138, 106, 34)

FONT_DIR = Path("/usr/share/fonts/truetype/liberation")
BOLD = FONT_DIR / "LiberationSans-Bold.ttf"
REGULAR = FONT_DIR / "LiberationSans-Regular.ttf"

ASSET_DIR = Path(__file__).resolve().parent.parent.parent / "assets"
MAX_BULLETS = 3
BODY_LINE = 42
BULLET_GAP = 14


class FontsUnavailable(RuntimeError):
    """The bundled layout needs Liberation Sans; say so rather than guessing."""


def slug(name: str) -> str:
    """The file stem an asset for ``name`` is looked up under."""
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def asset_path(kind: str, name: str) -> Path:
    """Where the optional logo or badge for ``name`` would live."""
    return ASSET_DIR / kind / f"{slug(name)}.png"


def creatives_for(pillar: str) -> list[Path]:
    """Ready-made panels for ``pillar``, in name order.

    The brand's own A+ content is finished artwork: on-brand, in English, and
    better than anything the generated layout can do for a product argument.
    Where a panel exists it becomes the post image, and the hook stays in the
    caption where LinkedIn shows it anyway.
    """
    directory = ASSET_DIR / "creatives" / pillar
    if not directory.is_dir():
        return []
    return sorted(p for p in directory.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png"})


def creative_for(draft: PostDraft) -> Path | None:
    """The panel to run for ``draft``, rotated by week, or None.

    Show and award posts always render: their images carry a countdown or a
    badge that no fixed panel can state.
    """
    if draft.slot.show or draft.slot.recognition:
        return None
    panels = creatives_for(draft.pillar.key)
    if not panels:
        return None
    return panels[draft.scheduled_for.isocalendar()[1] % len(panels)]


def product_photo_path(asin: str) -> Path | None:
    """A supplied photo for ``asin``, if there is one.

    Lifestyle photography reads far better in a feed than a listing cut on
    white, so a file dropped in assets/products wins over the CDN.
    """
    for suffix in (".jpg", ".jpeg", ".png", ".webp"):
        candidate = ASSET_DIR / "products" / f"{asin}{suffix}"
        if candidate.exists():
            return candidate
    return None


def load_asset(path: Path):
    """The image at ``path``, or None when it has not been supplied."""
    try:
        return Image.open(path).convert("RGBA")
    except Exception:
        return None


def _font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(str(path), size)
    except OSError as exc:
        raise FontsUnavailable(f"{path} is missing. Install the fonts-liberation package.") from exc


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


def _fit(draw, text: str, width: int, max_lines: int, largest: int, smallest: int):
    """The largest size at which ``text`` still fits in ``max_lines``."""
    for size in range(largest, smallest - 1, -4):
        font = _font(BOLD, size)
        lines = _wrap(draw, text, font, width)
        if len(lines) <= max_lines:
            return lines, font
    font = _font(BOLD, smallest)
    return _wrap(draw, text, font, width)[:max_lines], font


def _paste(canvas, art, box: tuple[int, int, int, int]) -> None:
    """Fit ``art`` inside ``box`` and centre it, keeping any transparency."""
    left, top, right, bottom = box
    fitted = art.copy()
    fitted.thumbnail((right - left, bottom - top), Image.LANCZOS)
    x = left + (right - left - fitted.width) // 2
    y = top + (bottom - top - fitted.height) // 2
    canvas.paste(fitted, (x, y), fitted if fitted.mode == "RGBA" else None)


def _masthead(image, draw, dark: bool) -> int:
    """The wordmark, or the supplied logo. Returns the y the content starts at."""
    logo = load_asset(ASSET_DIR / "logo.png")
    if logo is not None and not dark:
        _paste(image, logo, (MARGIN, MARGIN, MARGIN + 380, MARGIN + 96))
        return MARGIN + 130
    ink = LIGHT_TEXT if dark else INK
    sub = (170, 180, 188) if dark else MUTED
    draw.text((MARGIN, MARGIN), "HOMEDANT", font=_font(BOLD, 46), fill=ink)
    draw.text((MARGIN, MARGIN + 58), "The Best Organizing Solution", font=_font(REGULAR, 24), fill=sub)
    rule = MARGIN + 108
    draw.rectangle([MARGIN, rule, MARGIN + 120, rule + 6], fill=SHOW_ACCENT if dark else ACCENT)
    return rule + 46


def _band(image, draw, text: str, ground, ink) -> None:
    top = SIZE - BAND
    draw.rectangle([0, top, SIZE, SIZE], fill=ground)
    font = _font(BOLD, 30)
    while draw.textlength(text, font=font) > SIZE - 2 * MARGIN and font.size > 17:
        font = _font(BOLD, font.size - 2)
    draw.text((MARGIN, top + (BAND - font.size) // 2 - 4), text, font=font, fill=ink)


def _bullets(image, draw, points, top: int, width: int, ink, dot) -> int:
    font = _font(REGULAR, 30)
    y = top
    for point in list(points)[:MAX_BULLETS]:
        draw.ellipse([MARGIN + 4, y + 13, MARGIN + 16, y + 25], fill=dot)
        for line in _wrap(draw, point, font, width - 46):
            draw.text((MARGIN + 46, y), line, font=font, fill=ink)
            y += BODY_LINE
        y += BULLET_GAP
    return y


def _footer_text(draft: PostDraft) -> str:
    """What the bottom band says: the event where there is one, else the brand."""
    slot = draft.slot
    if slot.show:
        booth = f"   ·   {slot.show.location}" if slot.show.booth else ""
        return f"{slot.show.venue}   ·   {slot.show.dates}{booth}"
    if slot.recognition:
        return f"{slot.recognition.event}   ·   {slot.recognition.venue}"
    if slot.product:
        return f"{slot.product.short_title}   ·   Made in Korea"
    return "HOMEDANT   ·   The Best Organizing Solution"


def _layout_show(image, draw, draft: PostDraft, photo) -> None:
    """A dark event card: the countdown is the picture."""
    show = draft.slot.show
    draw.rectangle([0, 0, SIZE, SIZE], fill=SHOW_GROUND)
    top = _masthead(image, draw, dark=True)

    logo = load_asset(asset_path("shows", show.name))
    if logo is not None:
        _paste(image, logo, (SIZE - MARGIN - 300, MARGIN - 10, SIZE - MARGIN, MARGIN + 130))

    width = SIZE - 2 * MARGIN
    if photo is not None:
        panel = 740
        draw.rectangle([panel, 0, SIZE, SIZE - BAND], fill=PANEL)
        _paste(image, photo.convert("RGBA"), (panel + 24, 150, SIZE - 24, SIZE - BAND - 50))
        width = panel - MARGIN - 44

    days = show.days_until(draft.scheduled_for)
    if show.is_running(draft.scheduled_for):
        big, small = "OPEN", "NOW"
    elif days <= 30:
        big, small = str(days), "DAY" if days == 1 else "DAYS TO GO"
    else:
        big, small = "SAVE", "THE DATE"

    numeral = _font(BOLD, 250 if big.isdigit() else 150)
    draw.text((MARGIN, top + 10), big, font=numeral, fill=SHOW_ACCENT)
    label_y = top + 10 + int(numeral.size * 0.98)
    draw.text((MARGIN + 6, label_y), small, font=_font(BOLD, 46), fill=LIGHT_TEXT)

    name, name_font = _fit(draw, show.name, width, 2, 66, 34)
    y = label_y + 84
    for line in name:
        draw.text((MARGIN, y), line, font=name_font, fill=LIGHT_TEXT)
        y += int(name_font.size * 1.2)

    _bullets(image, draw, draft.points, y + 34, width, LIGHT_TEXT, SHOW_ACCENT)
    _band(image, draw, _footer_text(draft), SHOW_ACCENT, SHOW_GROUND)


def _layout_award(image, draw, draft: PostDraft, photo) -> None:
    """The badge earns the space; the headline sits beside it."""
    award = draft.slot.recognition
    top = _masthead(image, draw, dark=False)
    badge = load_asset(asset_path("awards", award.name))

    width = SIZE - 2 * MARGIN
    if badge is not None:
        _paste(image, badge, (SIZE - MARGIN - 320, top, SIZE - MARGIN, top + 320))
        width = SIZE - 2 * MARGIN - 360
    elif photo is not None:
        panel = 700
        draw.rectangle([panel, 0, SIZE, SIZE - BAND], fill=PANEL)
        _paste(image, photo.convert("RGBA"), (panel + 26, 150, SIZE - 26, SIZE - BAND - 50))
        width = panel - MARGIN - 46

    lines, font = _fit(draw, draft.hook, width, 5, 68, 36)
    y = top + 30
    for line in lines:
        draw.text((MARGIN, y), line, font=font, fill=ACCENT)
        y += int(font.size * 1.26)

    _bullets(image, draw, draft.points, y + 40, width, INK, ACCENT)
    _band(image, draw, _footer_text(draft), ACCENT, LIGHT_TEXT)


def _layout_product(image, draw, draft: PostDraft, photo) -> None:
    """The product fills the right half; the argument runs down the left."""
    accent = SEASON_ACCENT if draft.pillar.key == "seasonal" else ACCENT
    top = _masthead(image, draw, dark=False)

    width = SIZE - 2 * MARGIN
    if photo is not None:
        panel_left = 660
        draw.rectangle([panel_left, 0, SIZE, SIZE - BAND], fill=PANEL)
        _paste(image, photo.convert("RGBA"), (panel_left + 30, 120, SIZE - 30, SIZE - BAND - 60))
        width = panel_left - MARGIN - 50

    lines, font = _fit(draw, draft.hook, width, 6, 60, 32)
    y = top + 20
    for line in lines:
        draw.text((MARGIN, y), line, font=font, fill=accent)
        y += int(font.size * 1.24)

    _bullets(image, draw, draft.points, y + 34, width, INK, accent)

    _band(image, draw, _footer_text(draft), accent, LIGHT_TEXT)


def _layout_plain(image, draw, draft: PostDraft, photo) -> None:
    """No subject to picture: the sentence carries it."""
    top = _masthead(image, draw, dark=False)
    width = SIZE - 2 * MARGIN
    if photo is not None:
        panel = 700
        draw.rectangle([panel, 0, SIZE, SIZE - BAND], fill=PANEL)
        _paste(image, photo.convert("RGBA"), (panel + 26, 150, SIZE - 26, SIZE - BAND - 50))
        width = panel - MARGIN - 46
    lines, font = _fit(draw, draft.hook, width, 6, 62, 32)
    y = top + 40
    for line in lines:
        draw.text((MARGIN, y), line, font=font, fill=ACCENT)
        y += int(font.size * 1.26)
    _bullets(image, draw, draft.points, y + 44, width, INK, ACCENT)
    _band(image, draw, _footer_text(draft), ACCENT, LIGHT_TEXT)


def render(draft: PostDraft, path: str | Path, photo=None, use_creatives: bool = True) -> Path:
    """Write the image for ``draft`` and return the path it was written to.

    A ready-made panel is copied out as-is where one covers this pillar;
    otherwise the layout for the post's subject is drawn.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    panel = creative_for(draft) if use_creatives else None
    if panel is not None:
        with Image.open(panel) as art:
            art.convert("RGB").save(path, "PNG", optimize=True)
        return path

    image = Image.new("RGB", (SIZE, SIZE), GROUND)
    draw = ImageDraw.Draw(image)

    if draft.slot.show:
        _layout_show(image, draw, draft, photo)
    elif draft.slot.recognition:
        _layout_award(image, draw, draft, photo)
    elif draft.product:
        _layout_product(image, draw, draft, photo)
    else:
        _layout_plain(image, draw, draft, photo)

    image.save(path, "PNG", optimize=True)
    return path


def photo_for(draft: PostDraft, timeout: int = 20):
    """The photo to use for ``draft``, or None.

    A file in assets/products wins; otherwise the listing image is fetched.
    """
    product = draft.slot.pictured
    if product is None:
        return None
    local = product_photo_path(product.asin)
    if local is not None:
        from PIL import Image as PILImage

        try:
            return PILImage.open(local).convert("RGB")
        except Exception:
            pass
    return fetch_product_image(product.image_url, timeout=timeout)


def fetch_product_image(url: str, timeout: int = 20):
    """The product photo for a post, or None when it cannot be fetched.

    The scheduled job runs where the CDN is reachable; a developer machine
    behind a restricted network is not, and a missing photo must degrade to the
    type-only layout rather than fail the run.
    """
    if not url:
        return None
    import io
    import urllib.request

    from PIL import Image as PILImage

    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            data = response.read()
        return PILImage.open(io.BytesIO(data)).convert("RGB")
    except Exception:
        return None
