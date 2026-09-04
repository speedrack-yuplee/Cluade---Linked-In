"""Turning a catalog and a calendar into a rotation of scheduled slots."""

from __future__ import annotations

from datetime import date, timedelta

from .catalog import Catalog
from .models import Pillar, Slot
from .pillars import PILLARS

POSTING_WEEKDAYS: tuple[int, ...] = (0, 2, 4)
"""Monday, Wednesday and Friday: three posts a week."""


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


def _feature(catalog: Catalog, day: date):
    """A product to picture on a post that is not about a product.

    Rotated by date so the same shelf does not appear on every show post.
    """
    products = catalog.products
    return products[day.toordinal() % len(products)] if products else None


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
        "installation": bool(catalog.installations),
        None: True,
    }
    return tuple(p for p in pillars if available.get(p.needs, False))


COUNTDOWN_DAYS: tuple[int, ...] = (30, 7)
"""How far ahead of a show to force a post about it.

A showroom space on an upper floor cannot rely on buyers wandering in, so the
meetings have to be booked before the show. These posts are what books them,
and they take priority over the ordinary rotation.

Two milestones, not four. Four countdowns plus a post on every day of the run
turned October into six posts about High Point Market out of thirteen — the
same show name six times, which reads as one thing repeated rather than a
company with something to say.
"""

MAX_POSTS_PER_SHOW = 4
"""Announcement, two countdowns and one from the floor. Past that a show
crowds out every other subject in the month it falls in."""


def _show_dates(shows: list, days: list[date]) -> dict[date, object]:
    """Which posting dates belong to a show, and to which show.

    Each countdown milestone claims the posting date closest to it, and every
    posting date inside the show's own run is claimed by that show.
    """
    claimed: dict[date, object] = {}
    taken: dict[str, int] = {}

    def claim(day: date, show) -> None:
        if day in claimed or taken.get(show.name, 0) >= MAX_POSTS_PER_SHOW:
            return
        claimed[day] = show
        taken[show.name] = taken.get(show.name, 0) + 1

    upcoming = [s for s in shows if days and s.start >= days[0]]
    if upcoming and days:
        # A calendar that opens with a show ahead of it opens by announcing the
        # show: that is the post the meetings get booked from.
        claim(days[0], min(upcoming, key=lambda s: s.start))

    for show in shows:
        for offset in COUNTDOWN_DAYS:
            target = show.start - timedelta(days=offset)
            free = [d for d in days if d not in claimed and d <= show.start]
            if not free:
                continue
            nearest = min(free, key=lambda d: abs((d - target).days))
            if abs((nearest - target).days) <= 3:
                claim(nearest, show)

        # One post from the floor, not one for every day of the run: the
        # remaining days of a week-long market would otherwise be the same
        # show over and over.
        running = [d for d in days if show.is_running(d)]
        if running:
            claim(running[0], show)

    return claimed


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

    profile = catalog.brand_profile
    usable = _usable_pillars(catalog, pillars, start)
    rotation = tuple(p for p in usable if p.needs != "show") or usable
    if not usable:
        raise ValueError("no pillar can be filled from this catalog and brand profile")

    pools = {
        "product": catalog.products,
        "recognition": list(profile.recognitions),
        "show": _upcoming_shows(catalog, start),
        "installation": catalog.installations,
    }
    for pillar in usable:
        if pillar.segment:
            pools[f"product:{pillar.segment}"] = _segment_pool(catalog, pillar.segment)
    cursors = dict.fromkeys(pools, 0)

    days = [d for d in posting_dates(start, weeks, weekdays) if d not in profile.blackout_dates]
    show_pillar = next((p for p in usable if p.needs == "show"), None)
    claimed = _show_dates(pools["show"], days) if show_pillar else {}

    slots: list[Slot] = []
    index = 0
    for day in days:
        if day in claimed:
            slots.append(
                Slot(
                    scheduled_for=day,
                    pillar=show_pillar,
                    show=claimed[day],
                    feature=_feature(catalog, day),
                )
            )
            continue
        in_season = [p for p in rotation if not p.months or day.month in p.months]
        pillar = in_season[index % len(in_season)]
        index += 1
        subject = {}
        if pillar.needs:
            key = f"product:{pillar.segment}" if pillar.needs == "product" and pillar.segment else pillar.needs
            pool = pools[key]
            subject[pillar.needs] = pool[cursors[key] % len(pool)]
            cursors[key] += 1
        if pillar.needs != "product":
            subject["feature"] = _feature(catalog, day)
        slots.append(Slot(scheduled_for=day, pillar=pillar, **subject))

    return slots
