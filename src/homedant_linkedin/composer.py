"""Rendering a scheduled slot into a LinkedIn post draft."""

from __future__ import annotations

from .catalog import Catalog
from .models import PostDraft, Slot

_CTA_BUY = "Full specs and dimensions are on the listing: {url}"
_CTA_TALK = "If you are solving the same problem, I would like to hear how. — {author}"


def _highlight_lines(product) -> str:
    if not product.highlights:
        return ""
    return "\n".join(f"- {item}" for item in product.highlights)


def _compose_problem(slot: Slot, catalog: Catalog) -> PostDraft:
    product = slot.product
    audience = product.audience or "our customers"
    hook = f"The most common message we get from {audience}: there is nowhere left to put anything."
    body = "\n\n".join(
        [
            f"The floor is full, the closet is full, and the walls are doing nothing. "
            f"That is the gap {product.short_title} was drawn for.",
            _highlight_lines(product),
            "It is a small change in where things live, not a renovation.",
        ]
    ).strip()
    return PostDraft(
        slot=slot,
        hook=hook,
        body=body,
        cta=_CTA_BUY.format(url=product.url),
        hashtags=slot.pillar.hashtags,
    )


def _compose_spotlight(slot: Slot, catalog: Catalog) -> PostDraft:
    product = slot.product
    hook = f"What we changed on {product.short_title}, and why."
    body = "\n\n".join(
        [
            f"Built for {product.audience or 'everyday storage'}, sold on Amazon {product.marketplace} "
            f"as {product.asin}.",
            _highlight_lines(product),
            f"{catalog.brand} designs to a simple rule: if it needs a toolbox to assemble, we redesign it.",
        ]
    ).strip()
    return PostDraft(
        slot=slot,
        hook=hook,
        body=body,
        cta=_CTA_BUY.format(url=product.url),
        hashtags=slot.pillar.hashtags,
    )


def _compose_build(slot: Slot, catalog: Catalog) -> PostDraft:
    product = slot.product
    hook = "A boltless frame sounds like a shortcut. It is the harder engineering choice."
    body = "\n\n".join(
        [
            "Every screw you remove from an assembly is a tolerance you now have to hold in the steel "
            "itself. The joint has to carry the load that the fastener used to.",
            f"On {product.short_title}, that is what the tier adjustment and the load rating come down to.",
            _highlight_lines(product),
        ]
    ).strip()
    return PostDraft(
        slot=slot,
        hook=hook,
        body=body,
        cta=_CTA_BUY.format(url=product.url),
        hashtags=slot.pillar.hashtags,
    )


def _compose_operations(slot: Slot, catalog: Catalog) -> PostDraft:
    markets = sorted({p.marketplace for p in catalog})
    hook = f"Running {catalog.company} across {len(markets)} Amazon marketplaces taught us one thing early."
    body = "\n\n".join(
        [
            f"A listing that converts in {markets[0]} is not the same listing in {markets[-1]}. "
            "Different homes, different garages, different words for the same shelf.",
            "So we stopped translating listings and started rewriting them, marketplace by marketplace.",
            "It is slower. It is also the only version that works.",
        ]
    ).strip()
    return PostDraft(
        slot=slot,
        hook=hook,
        body=body,
        cta=_CTA_TALK.format(author=catalog.author or "HOMEDANT USA"),
        hashtags=slot.pillar.hashtags,
    )


_COMPOSERS = {
    "problem": _compose_problem,
    "spotlight": _compose_spotlight,
    "build": _compose_build,
    "operations": _compose_operations,
}


def compose(slot: Slot, catalog: Catalog) -> PostDraft:
    """Render one slot. Raises for a pillar with no composer registered."""
    try:
        composer = _COMPOSERS[slot.pillar.key]
    except KeyError:
        raise KeyError(f"no composer registered for pillar {slot.pillar.key!r}") from None
    if slot.pillar.needs_product and slot.product is None:
        raise ValueError(f"pillar {slot.pillar.key!r} requires a product but the slot has none")
    return composer(slot, catalog)


def compose_all(slots, catalog: Catalog) -> list[PostDraft]:
    return [compose(slot, catalog) for slot in slots]
