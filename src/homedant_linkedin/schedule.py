"""Finding the single post that is due on a given day.

The unattended run has to land on the same slot the calendar shows, so the
rotation is always counted from the anchor Monday in the brand profile rather
than from whenever the job happened to start.
"""

from __future__ import annotations

from datetime import date, timedelta

from .catalog import Catalog
from .composer import compose
from .models import PostDraft
from .planner import build_plan

HORIZON_WEEKS = 52


def anchor_for(catalog: Catalog, today: date) -> date:
    """The day the rotation counts from: the brand profile's, else this Monday."""
    anchor = catalog.brand_profile.plan_anchor
    if anchor:
        return anchor
    return today - timedelta(days=today.weekday())


def due_on(catalog: Catalog, day: date) -> PostDraft | None:
    """The post scheduled for ``day``.

    None when ``day`` is not a posting day, and also when it falls before the
    anchor: the calendar has not started, so an early run must post nothing
    rather than post the first slot ahead of time.
    """
    anchor = anchor_for(catalog, day)
    if day < anchor:
        return None
    weeks = min(((day - anchor).days // 7) + 2, HORIZON_WEEKS)
    for slot in build_plan(catalog, start=anchor, weeks=weeks):
        if slot.scheduled_for == day:
            return compose(slot, catalog)
    return None
