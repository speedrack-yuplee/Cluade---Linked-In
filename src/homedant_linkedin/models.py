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
    """One HOMEDANT listing the agent can write about."""

    asin: str
    sku: str
    title: str
    category: str
    marketplace: str
    url: str
    highlights: tuple[str, ...] = ()
    audience: str = ""
    short_name: str = ""

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


@dataclass(frozen=True)
class Pillar:
    """A recurring content theme. The plan rotates through these."""

    key: str
    name: str
    intent: str
    hashtags: tuple[str, ...]
    needs_product: bool = True


@dataclass(frozen=True)
class Slot:
    """A pillar scheduled on a date, optionally bound to a product."""

    scheduled_for: date
    pillar: Pillar
    product: Product | None = None


@dataclass(frozen=True)
class PostDraft:
    """A rendered post, ready for review."""

    slot: Slot
    hook: str
    body: str
    cta: str
    hashtags: tuple[str, ...] = field(default=())

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
        blocks = [self.hook, self.body, self.cta]
        if self.hashtags:
            blocks.append(" ".join(f"#{tag}" for tag in self.hashtags))
        return "\n\n".join(block for block in blocks if block)

    @property
    def char_count(self) -> int:
        return len(self.render())
