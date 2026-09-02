"""The content pillars the posting plan rotates through."""

from __future__ import annotations

from .models import Pillar

PILLARS: tuple[Pillar, ...] = (
    Pillar(
        key="problem",
        name="Problem we keep hearing",
        intent="Open with a storage problem a real buyer described, then show how the product answers it.",
        hashtags=("HomeOrganization", "StorageSolutions", "HOMEDANT"),
    ),
    Pillar(
        key="spotlight",
        name="Product spotlight",
        intent="Walk through one listing's design decisions and who it is built for.",
        hashtags=("GarageStorage", "ShelvingUnit", "HOMEDANT"),
    ),
    Pillar(
        key="build",
        name="How it is built",
        intent="Explain a manufacturing or design choice behind the product.",
        hashtags=("ProductDesign", "Manufacturing", "HOMEDANT"),
    ),
    Pillar(
        key="operations",
        name="Behind the operation",
        intent="Share an operating lesson from running HOMEDANT USA across Amazon marketplaces.",
        hashtags=("Ecommerce", "AmazonFBA", "HOMEDANT"),
        needs_product=False,
    ),
)

PILLARS_BY_KEY = {pillar.key: pillar for pillar in PILLARS}


def get_pillar(key: str) -> Pillar:
    try:
        return PILLARS_BY_KEY[key]
    except KeyError:
        known = ", ".join(sorted(PILLARS_BY_KEY))
        raise KeyError(f"unknown pillar {key!r}; known pillars: {known}") from None
