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


def build_plan(
    catalog: Catalog,
    start: date,
    weeks: int = 4,
    pillars: tuple[Pillar, ...] = PILLARS,
    weekdays: tuple[int, ...] = POSTING_WEEKDAYS,
) -> list[Slot]:
    """Assign a pillar and a product to every posting date.

    Pillars rotate in order. Products round-robin independently, so a product
    only repeats once the whole catalog has been used.
    """
    if not pillars:
        raise ValueError("at least one pillar is required")
    if len(catalog) == 0:
        raise ValueError("catalog is empty")

    products = catalog.products
    slots: list[Slot] = []
    product_index = 0

    for index, day in enumerate(posting_dates(start, weeks, weekdays)):
        pillar = pillars[index % len(pillars)]
        product = None
        if pillar.needs_product:
            product = products[product_index % len(products)]
            product_index += 1
        slots.append(Slot(scheduled_for=day, pillar=pillar, product=product))

    return slots
