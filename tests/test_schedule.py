from datetime import date

from homedant_linkedin.planner import build_plan
from homedant_linkedin.schedule import anchor_for, due_on


def test_nothing_is_due_on_a_day_that_is_not_a_posting_day(catalog):
    assert due_on(catalog, date(2026, 9, 8)) is None  # a Tuesday


def test_the_calendar_opens_on_the_anchor(catalog):
    draft = due_on(catalog, catalog.brand_profile.plan_anchor)
    assert draft is not None
    assert draft.pillar.key == "tradeshow"


def test_the_post_due_on_a_posting_day_matches_the_calendar(catalog):
    draft = due_on(catalog, date(2026, 9, 9))
    assert draft is not None
    assert draft.scheduled_for == date(2026, 9, 9)


def test_nothing_is_due_on_a_us_federal_holiday(catalog):
    """7 September 2026 is a Monday and Labor Day."""
    assert due_on(catalog, date(2026, 9, 7)) is None


def test_the_rotation_is_counted_from_the_anchor_not_from_today(catalog):
    """A run weeks into the calendar lands on that day's slot, not on the
    first slot of the rotation."""
    anchor = catalog.brand_profile.plan_anchor
    assert anchor_for(catalog, date(2026, 9, 30)) == anchor

    plan = {slot.scheduled_for: slot for slot in build_plan(catalog, start=anchor, weeks=6)}
    for day in (date(2026, 9, 30), date(2026, 10, 9)):
        assert due_on(catalog, day).pillar.key == plan[day].pillar.key


def test_nothing_is_due_before_the_anchor(catalog):
    """A run that fires early must post nothing, not the first slot early."""
    assert due_on(catalog, date(2026, 8, 5)) is None
    assert due_on(catalog, date(2026, 8, 31)) is None
