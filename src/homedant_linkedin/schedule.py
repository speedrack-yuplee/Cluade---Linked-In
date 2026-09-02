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
    """The Monday the rotation counts from."""
    anchor = catalog.brand_profile.plan_anchor
    if anchor and anchor <= today:
        return anchor
    return today - timedelta(days=today.weekday())


def due_on(catalog: Catalog, day: date) -> PostDraft | None:
    """The post scheduled for ``day``, or None if ``day`` is not a posting day."""
    anchor = anchor_for(catalog, day)
    weeks = min(((day - anchor).days // 7) + 2, HORIZON_WEEKS)
    for slot in build_plan(catalog, start=anchor, weeks=weeks):
        if slot.scheduled_for == day:
            return compose(slot, catalog)
    return None
