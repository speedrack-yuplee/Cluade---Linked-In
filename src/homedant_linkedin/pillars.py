"""The content pillars the posting plan rotates through.

Ordered by what the account's own history shows: the Retailers' Choice award
post reached 698 impressions with 10 reactions and 8 comments, against 18 to 42
impressions for product-led posts. Third-party recognition and trade show
presence lead; product posts support them.
"""

from __future__ import annotations

from .models import Pillar

PILLARS: tuple[Pillar, ...] = (
    Pillar(
        key="recognition",
        name="Third-party recognition",
        intent="Lead with an award or buyer-platform listing, thank the organization by name, "
        "and invite the buyers who saw it to connect.",
        hashtags=("HOMEDANT", "StorageSolutions", "KoreanMade", "B2B"),
        needs="recognition",
    ),
    Pillar(
        key="tradeshow",
        name="Trade show",
        intent="Name the show, the booth and the dates, and say what a buyer will see there.",
        hashtags=("HOMEDANT", "StorageSolutions", "KoreanMade", "B2B"),
        needs="show",
    ),
    Pillar(
        key="reference",
        name="Installed reference",
        intent="A room the shelving is standing in, photographed after it went up. What the "
        "building needed, and what the install actually took.",
        hashtags=("HOMEDANT", "SteelShelving", "StorageSolutions", "KoreanMade", "B2B"),
        needs="installation",
    ),
    Pillar(
        key="project",
        name="Project solution",
        intent="Open with the storage problem a hospitality or multifamily project runs into, "
        "then the system that answers it without construction work.",
        hashtags=(
            "HOMEDANT",
            "HospitalityDesign",
            "Multifamily",
            "StorageSolutions",
            "KoreanMade",
            "B2B",
        ),
        segment="project",
    ),
    Pillar(
        key="retail",
        name="Retail fit",
        intent="Answer a buyer's merchandising question: how the product sits on a shelf, "
        "in a planogram, on a pallet.",
        hashtags=("HOMEDANT", "RetailBuyers", "SteelShelving", "StorageSolutions", "B2B"),
        segment="retail",
    ),
    Pillar(
        key="manufacturing",
        name="Made in Korea",
        intent="Explain a manufacturing or design decision, and the control that owning the "
        "factory gives over it.",
        hashtags=("HOMEDANT", "KoreanMade", "SteelShelving", "Manufacturing", "B2B"),
    ),
    Pillar(
        key="seasonal",
        name="Q4 seasonal",
        intent="Holiday decor comes out of storage and goes back into it. Same SKU, two peak "
        "sell-through moments, and the buy happens months earlier.",
        hashtags=("HOMEDANT", "RetailBuyers", "StorageSolutions", "SeasonalRetail", "B2B"),
        months=(10, 11, 12),
        segment="retail",
    ),
    Pillar(
        key="supply",
        name="Supply and logistics",
        intent="Answer the question every buyer asks second: can you actually ship it.",
        hashtags=("HOMEDANT", "Distribution", "StorageSolutions", "B2B"),
        needs=None,
    ),
)

PILLARS_BY_KEY = {pillar.key: pillar for pillar in PILLARS}


def get_pillar(key: str) -> Pillar:
    try:
        return PILLARS_BY_KEY[key]
    except KeyError:
        known = ", ".join(sorted(PILLARS_BY_KEY))
        raise KeyError(f"unknown pillar {key!r}; known pillars: {known}") from None
