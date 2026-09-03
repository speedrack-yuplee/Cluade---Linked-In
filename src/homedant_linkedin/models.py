"""Core value objects for the HOMEDANT LinkedIn agent."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date

MAX_POST_CHARS = 3000
"""LinkedIn rejects a post body longer than this."""

MAX_HOOK_CHARS = 210
"""LinkedIn collapses a post behind "...see more" past roughly this point."""


@dataclass(frozen=True)
class Product:
    """One HOMEDANT product the agent can write about, framed for a buyer."""

    asin: str
    sku: str
    title: str
    category: str
    marketplace: str
    url: str
    highlights: tuple[str, ...] = ()
    audience: str = ""
    short_name: str = ""
    retail_fit: str = ""
    segments: tuple[str, ...] = ()
    image_url: str = ""
    load_per_tier: str = ""
    load_total: str = ""

    @classmethod
    def from_dict(cls, raw: dict) -> "Product":
        missing = [k for k in ("asin", "sku", "title", "category", "marketplace", "url") if not raw.get(k)]
        if missing:
            raise ValueError(f"product is missing required field(s): {', '.join(missing)}")
        return cls(
            asin=raw["asin"],
            sku=raw["sku"],
            title=raw["title"],
            category=raw["category"],
            marketplace=raw["marketplace"],
            url=raw["url"],
            highlights=tuple(raw.get("highlights", ())),
            audience=raw.get("audience", ""),
            short_name=raw.get("short_name", ""),
            retail_fit=raw.get("retail_fit", ""),
            segments=tuple(raw.get("segments", ())),
            image_url=raw.get("image_url", ""),
            load_per_tier=raw.get("load_per_tier", ""),
            load_total=raw.get("load_total", ""),
        )

    @property
    def short_title(self) -> str:
        """How the product is named inside a post.

        Amazon titles are keyword stuffed and unreadable in prose, so the
        catalog carries a hand-written ``short_name``. Products without one
        fall back to the title with the brand prefix and size tail removed.
        """
        if self.short_name:
            return self.short_name
        title = re.sub(r"^HOMEDANT\s*[-–]?\s*", "", self.title).strip()
        title = re.split(r"\s+\d+(?:\.\d+)?\"", title)[0].strip()
        return title or self.title

    @property
    def sentence_name(self) -> str:
        """``short_title`` capitalised for the start of a sentence."""
        name = self.short_title
        return name[:1].upper() + name[1:] if name else name


@dataclass(frozen=True)
class Recognition:
    """An award or listing a third party gave the brand.

    These are the highest performing posts by a wide margin, so the plan
    leads with them whenever one is available.
    """

    name: str
    org: str
    event: str
    venue: str
    date: date
    thanks: tuple[str, ...] = ()
    hashtags: tuple[str, ...] = ()
    city: str = ""
    award: str = ""
    posted_on: date | None = None
    """When this was already announced on LinkedIn. A recognition that has been
    posted is never announced again; it is revisited from a new angle."""

    headline: str = ""
    """The opening line, written by hand. ``{company}`` is substituted in."""

    @classmethod
    def from_dict(cls, raw: dict) -> "Recognition":
        return cls(
            name=raw["name"],
            org=raw["org"],
            event=raw.get("event", ""),
            venue=raw.get("venue", ""),
            date=date.fromisoformat(raw["date"]),
            thanks=tuple(raw.get("thanks", ())),
            hashtags=tuple(raw.get("hashtags", ())),
            headline=raw.get("headline", ""),
            city=raw.get("city", ""),
            award=raw.get("award", ""),
            posted_on=date.fromisoformat(raw["posted_on"]) if raw.get("posted_on") else None,
        )

    def opening(self, company: str) -> str:
        if self.headline:
            return self.headline.format(company=company)
        return f"{company} has been recognized by {self.org}."


@dataclass(frozen=True)
class TradeShow:
    """A show the company exhibits at."""

    name: str
    venue: str
    start: date
    end: date
    booth: str | None = None
    booth_label: str = "Booth"
    """Shows differ: NY NOW numbers booths, High Point numbers showroom spaces."""

    hashtags: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, raw: dict) -> "TradeShow":
        return cls(
            name=raw["name"],
            venue=raw.get("venue", ""),
            start=date.fromisoformat(raw["start"]),
            end=date.fromisoformat(raw["end"]),
            booth=raw.get("booth"),
            booth_label=raw.get("booth_label", "Booth"),
            hashtags=tuple(raw.get("hashtags", ())),
        )

    def days_until(self, day: date) -> int:
        """Days from ``day`` to the opening. Negative once the show has opened."""
        return (self.start - day).days

    def is_running(self, day: date) -> bool:
        return self.start <= day <= self.end

    @property
    def location(self) -> str:
        """How the stand is named on the show floor, e.g. "Space M-1007".

        The number sign only reads correctly on a bare number, so a space
        carrying a letter prefix goes without it.
        """
        if not self.booth:
            return ""
        prefix = "#" if self.booth.isdigit() else ""
        return f"{self.booth_label} {prefix}{self.booth}"

    @property
    def dates(self) -> str:
        if self.start.month == self.end.month:
            return f"{self.start:%B} {self.start.day}-{self.end.day}, {self.end.year}"
        return f"{self.start:%B %-d} - {self.end:%B %-d, %Y}"


@dataclass(frozen=True)
class Brand:
    """Who is posting, and the facts every post can draw on."""

    brand: str
    company: str
    tagline: str
    author: str
    role: str
    audiences: tuple[str, ...]
    proof_points: tuple[str, ...]
    positioning: str = ""
    founded: int | None = None
    capability: str = ""
    offer: str = ""
    coined_terms: dict = field(default_factory=dict)
    """A name we invented, mapped to the words that explain it. A post using
    the name has to carry one of them."""

    recognitions: tuple[Recognition, ...] = ()
    trade_shows: tuple[TradeShow, ...] = ()
    blackout_dates: frozenset = frozenset()
    """Days nothing goes out: US holidays, when a B2B feed is not being read."""

    plan_anchor: date | None = None
    """The day the rotation starts counting from, so an unattended run lands on
    the same slot the calendar shows. Nothing is due before it."""

    @classmethod
    def from_dict(cls, raw: dict) -> "Brand":
        return cls(
            brand=raw.get("brand", "HOMEDANT"),
            company=raw["company"],
            tagline=raw.get("tagline", ""),
            author=raw.get("author", ""),
            role=raw.get("role", ""),
            audiences=tuple(raw.get("audiences", ())),
            proof_points=tuple(raw.get("proof_points", ())),
            positioning=raw.get("positioning", ""),
            founded=raw.get("founded"),
            capability=raw.get("capability", ""),
            offer=raw.get("offer", ""),
            coined_terms={k: tuple(v) for k, v in raw.get("coined_terms", {}).items()},
            recognitions=tuple(Recognition.from_dict(r) for r in raw.get("recognitions", ())),
            trade_shows=tuple(TradeShow.from_dict(s) for s in raw.get("trade_shows", ())),
            plan_anchor=date.fromisoformat(raw["plan_anchor"]) if raw.get("plan_anchor") else None,
            blackout_dates=frozenset(date.fromisoformat(d) for d in raw.get("blackout_dates", ())),
        )

    @property
    def audience_phrase(self) -> str:
        """The audiences as the posts address them: "a, b, and c"."""
        items = list(self.audiences)
        if len(items) < 2:
            return items[0] if items else "partners"
        return ", ".join(items[:-1]) + f", and {items[-1]}"


@dataclass(frozen=True)
class Pillar:
    """A recurring content theme. The plan rotates through these."""

    key: str
    name: str
    intent: str
    hashtags: tuple[str, ...]
    needs: str | None = "product"
    """What the slot must carry: "product", "recognition", "show", or None."""

    months: tuple[int, ...] = ()
    """Restrict the pillar to these calendar months. Empty means all year."""

    segment: str | None = None
    """Restrict the product pool to products carrying this segment tag. A
    hospitality hook over a pallet-configuration product reads as a mismatch,
    so each product-led pillar draws from its own pool."""


@dataclass(frozen=True)
class Slot:
    """A pillar scheduled on a date, with whatever subject it needs."""

    scheduled_for: date
    pillar: Pillar
    product: Product | None = None
    recognition: Recognition | None = None
    show: TradeShow | None = None
    feature: Product | None = None
    """A product shown in the image only. A show or brand post has no product
    subject, but it still has something to show."""

    @property
    def pictured(self) -> Product | None:
        """The product the image should show, whether or not the text is about it."""
        return self.product or self.feature

    @property
    def subject(self) -> str:
        """A one-line label for the calendar."""
        if self.product:
            return self.product.short_title
        if self.recognition:
            return self.recognition.name
        if self.show:
            return self.show.name
        return "(brand)"


@dataclass(frozen=True)
class PostDraft:
    """A rendered post, ready for review."""

    slot: Slot
    hook: str
    body: str
    cta: str
    closing: str = ""
    """A line that follows the call to action, such as the thank-you the award
    posts end on."""

    hashtags: tuple[str, ...] = field(default=())
    points: tuple[str, ...] = ()
    """Proof points for the image. The posts themselves run as prose, so these
    are never rendered into the text."""

    @property
    def scheduled_for(self) -> date:
        return self.slot.scheduled_for

    @property
    def pillar(self) -> Pillar:
        return self.slot.pillar

    @property
    def product(self) -> Product | None:
        return self.slot.product

    def render(self) -> str:
        """The exact text to paste into LinkedIn."""
        blocks = [self.hook, self.body, self.cta, self.closing]
        if self.hashtags:
            blocks.append(" ".join(f"#{tag}" for tag in self.hashtags))
        return "\n\n".join(block for block in blocks if block)

    @property
    def char_count(self) -> int:
        return len(self.render())
