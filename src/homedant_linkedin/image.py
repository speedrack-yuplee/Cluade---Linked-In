"""Rendering a post draft into a branded 1200x1200 LinkedIn image.

Each pillar gets the treatment its subject deserves rather than one template
with the words swapped: a show post is a dark event card built around the
countdown, an award post carries its badge, and a product post is led by the
product. Where an optional asset is missing the layout closes up around it, so
a post always renders.
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .composer import _sentence
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
PHOTO_SUFFIXES = (".jpg", ".jpeg", ".png", ".webp")
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


LIBRARY_DIR = ASSET_DIR / "library"
PHOTO_POOL_DIRS = ("library/sns", "products")
"""Where the photograph on a product post comes from.

The A+ panels used to be the image itself, one per pillar rotated by week. Two
of those pillars only ever had one panel, so every seasonal and every supply
post went out carrying the same picture — which is the fastest way to teach a
feed to scroll past you. The panels stay in the repository as reference; the
post now gets a photograph from the working copy of the library instead.
"""


def photo_pool() -> list[Path]:
    """Every photograph a product post may be built on, in a stable order."""
    out: list[Path] = []
    for relative in PHOTO_POOL_DIRS:
        directory = ASSET_DIR / relative
        if not directory.is_dir():
            continue
        out += [
            p
            for p in sorted(directory.rglob("*"))
            if p.suffix.lower() in PHOTO_SUFFIXES and not p.name.startswith(".")
        ]
    return out


POOL_EPOCH = date(2026, 1, 1)
POSTING_WEEKDAYS = (0, 2, 4)


def _posting_index(day) -> int:
    """How many posting days have passed since the epoch, counting this one.

    Stepping the pool by the date itself circles: posting days are two and
    three apart, so a modulo of the ordinal revisits the same handful of
    pictures. Counting posting days steps the pool exactly once per post, so
    the whole library is walked before anything repeats.
    """
    days = (day - POOL_EPOCH).days
    whole, rest = divmod(days, 7)
    return whole * len(POSTING_WEEKDAYS) + sum(
        1 for w in POSTING_WEEKDAYS if (POOL_EPOCH.weekday() + rest) % 7 >= w
    )


def pooled_photo(day) -> Path | None:
    """The photograph for ``day``, one step along the pool per post."""
    pool = photo_pool()
    return pool[_posting_index(day) % len(pool)] if pool else None


def product_photo_path(asin: str) -> Path | None:
    """A supplied photo for ``asin``, if there is one.

    Lifestyle photography reads far better in a feed than a listing cut on
    white, so a file dropped in assets/products wins over the CDN.
    """
    for suffix in PHOTO_SUFFIXES:
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
    logo = load_asset(ASSET_DIR / ("logo-light.png" if dark else "logo.png"))
    if logo is not None:
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


BULLET_FLOOR = SIZE - BAND - 26
"""The lowest a bullet may reach. Below this it runs under the footer band and
the reader sees half a sentence, which is worse than not saying it."""


def _bullets(image, draw, points, top: int, width: int, ink, dot) -> int:
    """Draw the points, shrinking to fit and dropping what still will not.

    A supply post whose third point was one line too long had that line
    painted over by the band. The type gets smaller first, and only what is
    still too long is left out.
    """
    wanted = list(points)[:MAX_BULLETS]

    def laid_out(size: int):
        font = _font(REGULAR, size)
        step = int(size * 1.4)
        rows, y = [], top
        for point in wanted:
            lines = _wrap(draw, point, font, width - 46)
            if y + len(lines) * step > BULLET_FLOOR:
                break
            rows.append((y, lines))
            y += len(lines) * step + BULLET_GAP
        return font, step, rows, y

    for size in (30, 28, 26, 24, 22):
        font, step, rows, end = laid_out(size)
        if len(rows) == len(wanted):
            break

    for start, lines in rows:
        draw.ellipse([MARGIN + 4, start + 13, MARGIN + 16, start + 25], fill=dot)
        y = start
        for line in lines:
            draw.text((MARGIN + 46, y), line, font=font, fill=ink)
            y += step
    return end


def _footer_text(draft: PostDraft) -> str:
    """What the bottom band says: the event where there is one, else the brand."""
    slot = draft.slot
    if slot.show:
        booth = f"   ·   {slot.show.location}" if slot.show.booth else ""
        return f"{slot.show.venue}   ·   {slot.show.dates}{booth}"
    if slot.recognition:
        return f"{slot.recognition.event}   ·   {slot.recognition.venue}"
    if slot.installation:
        return "HOMEDANT boltless steel shelving"
    if slot.product:
        return f"{slot.product.short_title}   ·   Made in Korea"
    return "HOMEDANT   ·   The Best Organizing Solution"


def _layout_show(image, draw, draft: PostDraft, photo) -> None:
    """A dark event card: the countdown is the picture."""
    show = draft.slot.show
    draw.rectangle([0, 0, SIZE, SIZE], fill=SHOW_GROUND)
    top = _masthead(image, draw, dark=True)

    width = SIZE - 2 * MARGIN
    panel_left = None
    if photo is not None:
        panel_left = 740
        draw.rectangle([panel_left, 0, SIZE, SIZE - BAND], fill=PANEL)
        _paste(image, photo.convert("RGBA"), (panel_left + 24, 235, SIZE - 24, SIZE - BAND - 40))
        width = panel_left - MARGIN - 44

    # After the panel, never before it: the panel is opaque and would paint
    # over a logo placed first. With a photo the logo sits on the panel, where
    # a dark show mark reads; without one it sits on the dark ground.
    logo = load_asset(asset_path("shows", show.name))
    if logo is not None:
        box = (
            (panel_left + 80, 52, SIZE - 80, 152)
            if panel_left
            else (SIZE - MARGIN - 300, MARGIN, SIZE - MARGIN, MARGIN + 110)
        )
        _paste(image, logo, box)

    days = show.days_until(draft.scheduled_for)
    if show.is_running(draft.scheduled_for):
        big, small = "OPEN", "NOW"
    elif days <= 30:
        big, small = str(days), "DAY" if days == 1 else "DAYS TO GO"
    else:
        big, small = "SAVE", "THE DATE"

    # A word-form countdown sets smaller than a numeral, so the block drops by
    # the difference and the card stays balanced either way.
    numeral = _font(BOLD, 250 if big.isdigit() else 150)
    top += 250 - numeral.size
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
    """The badge earns the space; the headline sits beside it.

    The badge and the product both belong here: the badge says a third party
    vouched for this, and the photograph says what they vouched for. So the
    badge crowns the panel rather than replacing it.
    """
    award = draft.slot.recognition
    top = _masthead(image, draw, dark=False)
    badge = load_asset(asset_path("awards", award.name))

    width = SIZE - 2 * MARGIN
    panel_left = None
    if photo is not None:
        panel_left = 700
        draw.rectangle([panel_left, 0, SIZE, SIZE - BAND], fill=PANEL)
        photo_top = 300 if badge is not None else 150
        _paste(image, photo.convert("RGBA"), (panel_left + 26, photo_top, SIZE - 26, SIZE - BAND - 50))
        width = panel_left - MARGIN - 46

    # After the panel, never before it: the panel is opaque and would paint
    # over a badge placed first.
    if badge is not None:
        if panel_left is None:
            _paste(image, badge, (SIZE - MARGIN - 320, top, SIZE - MARGIN, top + 320))
            width = SIZE - 2 * MARGIN - 360
        else:
            _paste(image, badge, (panel_left + 40, 60, SIZE - 40, 270))

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


def _cover(art, size: int):
    """``art`` scaled to fill a ``size`` square and centre-cropped.

    A room photograph is landscape and the feed wants a square, so the choice
    is between letterboxing it and cropping it. Cropping keeps the picture
    filling the frame, which is the whole point of using a real one.
    """
    art = art.convert("RGB")
    scale = size / min(art.size)
    art = art.resize((max(size, round(art.width * scale)), max(size, round(art.height * scale))), Image.LANCZOS)
    left = (art.width - size) // 2
    top = (art.height - size) // 2
    return art.crop((left, top, left + size, top + size))


def _scrim(image, top: int, opacity: int = 225) -> None:
    """Darken the frame from ``top`` down, fading in over the first stretch.

    Type over a photograph is unreadable wherever the photograph is pale, and
    a hard-edged band across the picture looks like a mistake. A gradient does
    neither.
    """
    overlay = Image.new("RGBA", (1, SIZE), (0, 0, 0, 0))
    fade = int((SIZE - top) * 0.45) or 1
    for y in range(top, SIZE):
        alpha = min(opacity, int(opacity * (y - top) / fade))
        overlay.putpixel((0, y), (14, 20, 24, alpha))
    image.paste(
        overlay.resize((SIZE, SIZE), Image.NEAREST),
        (0, 0),
        overlay.resize((SIZE, SIZE), Image.NEAREST),
    )


def _layout_reference(image, draw, draft: PostDraft, photo) -> None:
    """The photograph is the image; the words sit in the dark at the bottom.

    Nothing is drawn over the room itself. A real installation only carries a
    post if it is allowed to look like a photograph rather than a template
    with a picture pasted into a slot.
    """
    site = draft.slot.installation
    room = photo if photo is not None else None
    if room is None:
        _layout_plain(image, draw, draft, None)
        return

    image.paste(_cover(room, SIZE), (0, 0))
    _scrim(image, 520)

    draw.text((MARGIN, MARGIN), "HOMEDANT", font=_font(BOLD, 44), fill=LIGHT_TEXT)
    draw.rectangle([MARGIN, MARGIN + 62, MARGIN + 110, MARGIN + 68], fill=ACCENT)

    label = "INSTALLED" if not site.named else site.customer.upper()
    draw.text((MARGIN, 620), label, font=_font(BOLD, 30), fill=SHOW_ACCENT)

    width = SIZE - 2 * MARGIN
    lines, font = _fit(draw, _sentence(site.described_as), width, 2, 76, 44)
    y = 668
    for line in lines:
        draw.text((MARGIN, y), line, font=font, fill=LIGHT_TEXT)
        y += int(font.size * 1.16)

    caption = _font(REGULAR, 34)
    for line in _wrap(draw, _sentence(site.room), caption, width)[:2]:
        draw.text((MARGIN, y + 18), line, font=caption, fill=(214, 214, 210))
        y += int(caption.size * 1.3)

    _bullets(image, draw, draft.points[1:], y + 40, width, LIGHT_TEXT, ACCENT)

    foot = _font(REGULAR, 26)
    draw.text(
        (MARGIN, SIZE - MARGIN - 10),
        f"Made in Korea since 1979   \u00b7   {_footer_text(draft)}",
        font=foot,
        fill=(170, 176, 178),
    )


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


def render(draft: PostDraft, path: str | Path, photo=None, use_creatives: bool = False) -> Path:
    """Write the image for ``draft`` and return the path it was written to.

    ``use_creatives`` is kept so older callers still work; it no longer does
    anything, because a fixed panel per pillar is what made every seasonal post
    look like the last one.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    image = Image.new("RGB", (SIZE, SIZE), GROUND)
    draw = ImageDraw.Draw(image)

    if draft.slot.installation:
        _layout_reference(image, draw, draft, photo)
    elif draft.slot.show:
        _layout_show(image, draw, draft, photo)
    elif draft.slot.recognition:
        _layout_award(image, draw, draft, photo)
    elif draft.product:
        _layout_product(image, draw, draft, photo)
    else:
        _layout_plain(image, draw, draft, photo)

    image.save(path, "PNG", optimize=True)
    return path


def _open(path: Path):
    from PIL import Image as PILImage

    try:
        return PILImage.open(path).convert("RGB")
    except Exception:
        return None


def _any_supplied_photo(day):
    """A photograph from the pool, chosen by date.

    A post that could carry a picture should not lose it because that day's
    rotation landed on a product whose photo has not been supplied and whose
    listing image cannot be reached.
    """
    chosen = pooled_photo(day)
    return _open(chosen) if chosen else None


def photo_for(draft: PostDraft, timeout: int = 20):
    """The photo to use for ``draft``, or None.

    A file supplied for this product wins, then its listing image, then any
    other supplied photo.
    """
    if draft.slot.installation:
        # The picture for one of these is the room itself, already in the
        # repository; nothing to fetch and nothing to fall back to.
        return _open(ASSET_DIR / "library" / draft.slot.installation.photo)

    # The library is deep enough that walking it beats showing the same
    # listing cut twice a fortnight, so the pool leads and the product's own
    # photograph is the fallback rather than the other way round.
    pooled = _any_supplied_photo(draft.scheduled_for)
    if pooled is not None:
        return pooled

    product = draft.slot.pictured
    if product is None:
        return None
    local = product_photo_path(product.asin)
    if local is not None and (image := _open(local)) is not None:
        return image
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
