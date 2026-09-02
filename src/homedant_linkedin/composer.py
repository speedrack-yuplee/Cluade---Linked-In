"""Rendering a scheduled slot into a LinkedIn post draft.

The templates copy the account's own voice: a question or a plain statement to
open, no contractions, the company named as it is tagged on LinkedIn, an
explicit thank-you where a third party is involved, and a closing invitation to
connect rather than a link to buy.
"""

from __future__ import annotations

from .catalog import Catalog
from .models import PostDraft, Slot

CONNECT_CTA = (
    "We look forward to connecting with {audiences} who are looking for practical and "
    "dependable storage solutions."
)


def _bullets(items) -> str:
    return "\n".join(f"- {item}" for item in items if item)


def _paragraphs(*blocks: str) -> str:
    """Join blocks with a blank line, dropping the ones that came out empty.

    A composer that skips an optional line must not leave a gap behind it.
    """
    return "\n\n".join(block.strip() for block in blocks if block and block.strip())


def _fit_line(product, prefix: str) -> str:
    """The merchandising note, unless a bullet already made the same point."""
    if not product.retail_fit or product.retail_fit in product.highlights:
        return ""
    return f"{prefix} {product.retail_fit}."


def _and_list(items: list[str]) -> str:
    if len(items) < 2:
        return items[0] if items else ""
    return " and ".join([", ".join(items[:-1]), items[-1]]) if len(items) > 2 else " and ".join(items)


def _hashtags(slot: Slot, extra: tuple[str, ...] = ()) -> tuple[str, ...]:
    """Pillar hashtags plus any the subject carries, in order, without repeats."""
    seen: dict[str, None] = {}
    for tag in (*extra, *slot.pillar.hashtags):
        seen.setdefault(tag, None)
    return tuple(seen)


def _compose_recognition(slot: Slot, catalog: Catalog) -> PostDraft:
    award = slot.recognition
    profile = catalog.brand_profile
    hook = award.opening(profile.company)
    body = _paragraphs(
        f"It is especially meaningful for us to see {profile.company} recognized alongside other "
        f"award-winning brands at {award.venue}.",
        "The recognition is for the work that is easy to miss on a shelf:",
        _bullets(profile.proof_points[:3]),
        f"Thank you to {_and_list(list(award.thanks))} for this recognition."
        if award.thanks
        else f"Thank you to {award.org} for this recognition.",
    )
    return PostDraft(
        slot=slot,
        hook=hook,
        body=body,
        cta=CONNECT_CTA.format(audiences=profile.audience_phrase),
        hashtags=_hashtags(slot, award.hashtags),
    )


def _compose_tradeshow(slot: Slot, catalog: Catalog) -> PostDraft:
    show = slot.show
    profile = catalog.brand_profile
    booth = f" at Booth #{show.booth}" if show.booth else ""
    hook = f"See you at {show.name}{booth}."
    body = _paragraphs(
        f"{profile.company} will be at {show.venue}, {show.dates}.",
        "What you will see on the stand:",
        _bullets(profile.proof_points[:3]),
        "Bring the dimensions you are working with and we will tell you, on the spot, whether we "
        "have a unit that fits or whether it is a tooling change.",
    )
    return PostDraft(
        slot=slot,
        hook=hook,
        body=body,
        cta=f"If you are attending, message me and we will set a time. — {profile.author}",
        hashtags=_hashtags(slot, show.hashtags),
    )


def _compose_project(slot: Slot, catalog: Catalog) -> PostDraft:
    product = slot.product
    profile = catalog.brand_profile
    hook = (
        "How can hotels and residential projects provide more storage without making rooms feel "
        "crowded?"
    )
    body = _paragraphs(
        f"{profile.company}'s answer is {product.short_title}. It is designed for "
        f"{product.audience}, and it goes in without construction work.",
        _bullets(product.highlights),
        _fit_line(product, "For specifiers:"),
    )
    return PostDraft(
        slot=slot,
        hook=hook,
        body=body,
        cta="Send me your floor plan and unit count and we will come back with a layout and a quote.",
        hashtags=_hashtags(slot),
    )


def _compose_retail(slot: Slot, catalog: Catalog) -> PostDraft:
    product = slot.product
    profile = catalog.brand_profile
    hook = "Ever struggled to fit diverse inventory perfectly onto your shelves?"
    body = _paragraphs(
        f"{product.sentence_name} was built for {product.audience}.",
        _bullets(product.highlights),
        _fit_line(product, "On the floor:"),
        f"{profile.company} builds the fixture, not only what goes on it, and the two have to "
        "hold to the same standard.",
    )
    return PostDraft(
        slot=slot,
        hook=hook,
        body=body,
        cta="Message me for a line sheet, case pack and pallet configuration.",
        hashtags=_hashtags(slot),
    )


def _compose_manufacturing(slot: Slot, catalog: Catalog) -> PostDraft:
    product = slot.product
    profile = catalog.brand_profile
    hook = "A boltless frame sounds like a shortcut. It is the harder engineering choice."
    body = _paragraphs(
        "Every fastener you remove is a tolerance you now have to hold in the steel itself. The "
        "joint has to carry the load the bolt used to carry.",
        f"That is why {product.short_title} is engineered and inspected in {profile.company}'s own "
        "Korean factory rather than bought in.",
        _bullets(product.highlights[:2]),
        f"Across the range that adds up to {profile.proof_points[1]}.",
    )
    return PostDraft(
        slot=slot,
        hook=hook,
        body=body,
        cta="If you are evaluating a supplier, ask for our test reports. We will send them.",
        hashtags=_hashtags(slot),
    )


def _compose_supply(slot: Slot, catalog: Catalog) -> PostDraft:
    profile = catalog.brand_profile
    hook = "Buyers ask about the product first and the supply chain second. The second answer decides it."
    body = _paragraphs(
        f"{profile.company} holds stock in CA and US warehouses, so a domestic order does not wait "
        "on an ocean container.",
        _bullets(profile.proof_points[-2:]),
        "It is a slower way to run inventory. It is also the only version that holds a reset date.",
    )
    return PostDraft(
        slot=slot,
        hook=hook,
        body=body,
        cta=CONNECT_CTA.format(audiences=profile.audience_phrase),
        hashtags=_hashtags(slot),
    )


_COMPOSERS = {
    "recognition": _compose_recognition,
    "tradeshow": _compose_tradeshow,
    "project": _compose_project,
    "retail": _compose_retail,
    "manufacturing": _compose_manufacturing,
    "supply": _compose_supply,
}

_SUBJECT_ATTR = {"product": "product", "recognition": "recognition", "show": "show"}


def compose(slot: Slot, catalog: Catalog) -> PostDraft:
    """Render one slot. Raises for a pillar with no composer or no subject."""
    try:
        composer = _COMPOSERS[slot.pillar.key]
    except KeyError:
        raise KeyError(f"no composer registered for pillar {slot.pillar.key!r}") from None
    needs = slot.pillar.needs
    if needs and getattr(slot, _SUBJECT_ATTR[needs]) is None:
        raise ValueError(f"pillar {slot.pillar.key!r} requires a {needs} but the slot has none")
    return composer(slot, catalog)


def compose_all(slots, catalog: Catalog) -> list[PostDraft]:
    return [compose(slot, catalog) for slot in slots]
