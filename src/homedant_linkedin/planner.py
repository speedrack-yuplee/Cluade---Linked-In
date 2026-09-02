"""Turning a catalog and a calendar into a rotation of scheduled slots."""

from __future__ import annotations

from datetime import date, timedelta

from .catalog import Catalog
from .models import Pillar, Slot
from .pillars import PILLARS

POSTING_WEEKDAYS: tuple[int, ...] = (1, 3)
"""Tuesday and Thursday. LinkedIn engagement for B2B sits mid-week."""


def posting_dates(start: date, weeks: int, weekdays: tuple[int, ...] = POSTING_WEEKDAYS) -> list[date]:
    """Every posting date in ``weeks`` weeks, starting on or after ``start``."""
    if weeks < 1:
        raise ValueError("weeks must be at least 1")
    if not weekdays:
        raise ValueError("at least one posting weekday is required")

    week_start = start - timedelta(days=start.weekday())
    dates: list[date] = []
    for week in range(weeks):
        for weekday in sorted(weekdays):
            day = week_start + timedelta(weeks=week, days=weekday)
            if day >= start:
                dates.append(day)
    return dates


def _segment_pool(catalog: Catalog, segment: str) -> list:
    """Products tagged for ``segment``, exclusive ones first.

    A product tagged for this segment alone is the clearer illustration, so it
    leads; products shared with another segment fill in behind it.
    """
    tagged = [p for p in catalog.products if segment in p.segments]
    tagged.sort(key=lambda p: len(p.segments))
    return tagged or catalog.products


def _upcoming_shows(catalog: Catalog, start: date) -> list:
    """Shows that have not finished yet.

    "See you at" a show that closed last month is worse than no post, so a
    past show is dropped and the trade show pillar falls out of the rotation
    until an upcoming one is added to the brand profile.
    """
    return [show for show in catalog.brand_profile.trade_shows if show.end >= start]


def _usable_pillars(catalog: Catalog, pillars: tuple[Pillar, ...], start: date) -> tuple[Pillar, ...]:
    """Drop pillars whose subject the brand profile cannot supply.

    A recognition pillar with no award on file would render an empty post, so
    it is skipped rather than guessed at.
    """
    profile = catalog.brand_profile
    available = {
        "product": len(catalog) > 0,
        "recognition": bool(profile.recognitions),
        "show": bool(_upcoming_shows(catalog, start)),
        None: True,
    }
    return tuple(p for p in pillars if available.get(p.needs, False))


def build_plan(
    catalog: Catalog,
    start: date,
    weeks: int = 4,
    pillars: tuple[Pillar, ...] = PILLARS,
    weekdays: tuple[int, ...] = POSTING_WEEKDAYS,
) -> list[Slot]:
    """Assign a pillar and its subject to every posting date.

    Pillars rotate in order. Products, recognitions and shows each round-robin
    on their own counter, so a subject only repeats once its pool is exhausted.
    """
    if not pillars:
        raise ValueError("at least one pillar is required")
    if len(catalog) == 0:
        raise ValueError("catalog is empty")

    usable = _usable_pillars(catalog, pillars, start)
    if not usable:
        raise ValueError("no pillar can be filled from this catalog and brand profile")

    profile = catalog.brand_profile
    pools = {
        "product": catalog.products,
        "recognition": list(profile.recognitions),
        "show": _upcoming_shows(catalog, start),
    }
    for pillar in usable:
        if pillar.segment:
            pools[f"product:{pillar.segment}"] = _segment_pool(catalog, pillar.segment)
    cursors = dict.fromkeys(pools, 0)

    slots: list[Slot] = []
    for index, day in enumerate(posting_dates(start, weeks, weekdays)):
        pillar = usable[index % len(usable)]
        subject = {}
        if pillar.needs:
            key = f"product:{pillar.segment}" if pillar.needs == "product" and pillar.segment else pillar.needs
            pool = pools[key]
            subject[pillar.needs] = pool[cursors[key] % len(pool)]
            cursors[key] += 1
        slots.append(Slot(scheduled_for=day, pillar=pillar, **subject))

    return slots
