"""Rendering a scheduled slot into a LinkedIn post draft.

The templates follow the account's own posts, which run as prose rather than
bullet lists: a hook that states the news or asks the reader's question, a
paragraph giving it meaning, a paragraph on what the shelving does, an
invitation to connect, and a thank-you where a third party is involved. Proof
points are carried separately for the image, which does use a list.
"""

from __future__ import annotations

from .catalog import Catalog
from .models import PostDraft, Slot

CONNECT_CTA = (
    "We look forward to connecting with {audiences} who are looking for practical and "
    "dependable storage solutions."
)


def _paragraphs(*blocks: str) -> str:
    """Join blocks with a blank line, dropping the ones that came out empty.

    A composer that skips an optional line must not leave a gap behind it.
    """
    return "\n\n".join(block.strip() for block in blocks if block and block.strip())


def _and_list(items: list[str]) -> str:
    if len(items) < 2:
        return items[0] if items else ""
    if len(items) == 2:
        return " and ".join(items)
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def _hashtags(slot: Slot, extra: tuple[str, ...] = ()) -> tuple[str, ...]:
    """Pillar hashtags plus any the subject carries, in order, without repeats."""
    seen: dict[str, None] = {}
    for tag in (*extra, *slot.pillar.hashtags):
        seen.setdefault(tag, None)
    return tuple(seen)


def _compose_recognition(slot: Slot, catalog: Catalog) -> PostDraft:
    award = slot.recognition
    profile = catalog.brand_profile
    where = f" in {award.city}" if award.city else ""
    return PostDraft(
        slot=slot,
        hook=(
            f"We are proud to share that {profile.brand} has been selected as a "
            f"{award.award or award.name} at the {award.date.year} {award.event}{where}! 🎉"
        ),
        body=_paragraphs(
            f"This recognition is a meaningful milestone for {profile.company} as we continue "
            f"introducing {profile.positioning}.",
            profile.capability,
        ),
        cta=CONNECT_CTA.format(audiences=profile.audience_phrase),
        closing=(
            f"Thank you to {_and_list(list(award.thanks))} for this recognition."
            if award.thanks
            else f"Thank you to {award.org} for this recognition."
        ),
        hashtags=_hashtags(slot, award.hashtags),
        points=profile.proof_points[:3],
    )


def _compose_tradeshow(slot: Slot, catalog: Catalog) -> PostDraft:
    show = slot.show
    profile = catalog.brand_profile
    where = f", {show.location}" if show.booth else ""
    return PostDraft(
        slot=slot,
        hook=f"See you at {show.name}{where}! 🇰🇷",
        body=_paragraphs(
            f"{profile.company} will be at {show.venue}, {show.dates}, with our "
            f"{profile.offer}.",
            profile.capability,
            "Bring the dimensions you are working with and we will tell you on the spot whether "
            "we already have a unit that fits, or whether it is a tooling change.",
        ),
        cta=(
            "If you are attending, message me and we will set a time before the floor gets busy. "
            f"— {profile.author}"
        ),
        hashtags=_hashtags(slot, show.hashtags),
        points=profile.proof_points[:3],
    )


def _compose_project(slot: Slot, catalog: Catalog) -> PostDraft:
    product = slot.product
    profile = catalog.brand_profile
    return PostDraft(
        slot=slot,
        hook=(
            "How can hotels and residential projects provide more storage without making rooms "
            "feel crowded?"
        ),
        body=_paragraphs(
            f"At {profile.company}, we build for the room as it already is. "
            f"{product.sentence_name} was designed for {product.audience}, and it goes in without "
            "construction work, without a contractor, and without touching the finishes.",
            f"{_and_list(list(product.highlights))}.".capitalize(),
            product.retail_fit and f"For specifiers: {product.retail_fit}.",
        ),
        cta="Send me your floor plan and unit count and we will come back with a layout and a quote.",
        hashtags=_hashtags(slot),
        points=product.highlights[:3],
    )


def _compose_retail(slot: Slot, catalog: Catalog) -> PostDraft:
    product = slot.product
    profile = catalog.brand_profile
    return PostDraft(
        slot=slot,
        hook="Ever struggled to fit diverse inventory perfectly onto your shelves?",
        body=_paragraphs(
            f"At {profile.company}, we understand that every product has its own dimensions. "
            f"{product.sentence_name} adjusts to them rather than the other way round, and it was "
            f"built for {product.audience}.",
            f"{_and_list(list(product.highlights))}.".capitalize(),
            product.retail_fit and f"On the floor: {product.retail_fit}.",
        ),
        cta="Message me for a line sheet, case pack and pallet configuration.",
        hashtags=_hashtags(slot),
        points=product.highlights[:3],
    )


def _compose_manufacturing(slot: Slot, catalog: Catalog) -> PostDraft:
    product = slot.product
    profile = catalog.brand_profile
    return PostDraft(
        slot=slot,
        hook="A boltless frame sounds like a shortcut. It is the harder engineering choice.",
        body=_paragraphs(
            "Every fastener you remove is a tolerance you now have to hold in the steel itself, "
            "because the joint has to carry the load the bolt used to carry.",
            f"That is why {product.short_title} is engineered and inspected in "
            f"{profile.company}'s own Korean factory rather than bought in. We have been making "
            f"steel shelving since {profile.founded}, and the boltless joint is the part we have "
            "spent the longest getting right.",
            profile.capability,
        ),
        cta="If you are evaluating a supplier, ask me for our test reports. We will send them.",
        hashtags=_hashtags(slot),
        points=profile.proof_points[:3],
    )


def _compose_supply(slot: Slot, catalog: Catalog) -> PostDraft:
    profile = catalog.brand_profile
    return PostDraft(
        slot=slot,
        hook="Buyers ask about the product first and the supply chain second. The second answer decides it.",
        body=_paragraphs(
            f"{profile.company} holds stock in CA and GA warehouses, so a domestic order does not "
            "wait on an ocean container, and a reset date does not move because a vessel did.",
            "Manufacturing sits in our own Korean factory, which means a specification change is a "
            "conversation with the plant rather than a negotiation with a contract manufacturer.",
            profile.capability,
        ),
        cta=CONNECT_CTA.format(audiences=profile.audience_phrase),
        hashtags=_hashtags(slot),
        points=profile.proof_points[-3:],
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
