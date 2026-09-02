from datetime import date

from homedant_linkedin.schedule import anchor_for, due_on


def test_nothing_is_due_on_a_day_that_is_not_a_posting_day(catalog):
    assert due_on(catalog, date(2026, 9, 8)) is None  # a Tuesday


def test_the_post_due_on_a_posting_day_matches_the_calendar(catalog):
    draft = due_on(catalog, date(2026, 9, 7))
    assert draft is not None
    assert draft.pillar.key == "recognition"
    assert draft.scheduled_for == date(2026, 9, 7)


def test_the_rotation_is_counted_from_the_anchor_not_from_today(catalog):
    """A run three weeks late still lands on that week's slot, not on the
    first slot of the rotation."""
    assert anchor_for(catalog, date(2026, 9, 30)) == catalog.brand_profile.plan_anchor
    assert due_on(catalog, date(2026, 9, 30)).pillar.key != "recognition"


def test_an_anchor_in_the_future_falls_back_to_this_week(catalog):
    day = date(2026, 8, 5)  # before the anchor
    assert anchor_for(catalog, day) == date(2026, 8, 3)
    assert due_on(catalog, day) is not None
