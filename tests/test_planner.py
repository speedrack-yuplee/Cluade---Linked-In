from datetime import date

import pytest

from homedant_linkedin.pillars import PILLARS, get_pillar
from homedant_linkedin.planner import build_plan, posting_dates

PLAN_START = date(2026, 9, 7)  # a Monday, so every week contributes three slots


def test_posting_dates_land_on_monday_wednesday_and_friday():
    assert [d.weekday() for d in posting_dates(PLAN_START, weeks=2)] == [0, 2, 4, 0, 2, 4]


def test_posting_dates_never_precede_the_start_date():
    """A plan starting Thursday skips that week's Monday and Wednesday."""
    assert posting_dates(date(2026, 9, 3), weeks=1) == [date(2026, 9, 4)]


def test_posting_dates_rejects_zero_weeks():
    with pytest.raises(ValueError, match="at least 1"):
        posting_dates(PLAN_START, weeks=0)


def test_plan_assigns_a_pillar_to_every_slot(catalog):
    slots = build_plan(catalog, start=PLAN_START, weeks=4)
    assert len(slots) == 12
    assert all(slot.pillar in PILLARS for slot in slots)


def test_a_calendar_opens_by_announcing_the_next_show(catalog):
    """The show post is what books the meetings, so it goes first."""
    slots = build_plan(catalog, start=PLAN_START, weeks=4)
    assert slots[0].pillar.key == "tradeshow"
    assert slots[0].show.name == "High Point Market"


def test_recognition_leads_the_rotation_behind_the_show(catalog):
    """The award post outperformed product posts by more than an order of
    magnitude, so it opens the rotation proper."""
    slots = build_plan(catalog, start=PLAN_START, weeks=4)
    rotation = [s for s in slots if s.pillar.key != "tradeshow"]
    assert rotation[0].pillar.key == "recognition"
    assert rotation[0].recognition is not None


def test_a_show_that_has_already_closed_is_never_scheduled(catalog):
    """By November every show on file has ended, so the pillar drops out."""
    slots = build_plan(catalog, start=date(2026, 11, 2), weeks=6)
    assert all(slot.pillar.key != "tradeshow" for slot in slots)


def test_an_upcoming_show_is_scheduled(catalog):
    """High Point Market opens in October, so a September plan uses it."""
    slots = build_plan(catalog, start=PLAN_START, weeks=4)
    shows = [slot for slot in slots if slot.pillar.key == "tradeshow"]
    assert shows and all(slot.show.end >= PLAN_START for slot in shows)
    assert any(slot.show.name == "High Point Market" for slot in shows)


def test_the_project_pillar_only_draws_project_products(catalog):
    slots = build_plan(catalog, start=PLAN_START, weeks=10)
    project = [slot for slot in slots if slot.pillar.key == "project"]
    assert project and all("project" in slot.product.segments for slot in project)


def test_the_retail_pillar_only_draws_retail_products(catalog):
    slots = build_plan(catalog, start=PLAN_START, weeks=10)
    retail = [slot for slot in slots if slot.pillar.key == "retail"]
    assert retail and all("retail" in slot.product.segments for slot in retail)


def test_the_supply_pillar_carries_no_subject(catalog):
    slots = build_plan(catalog, start=PLAN_START, weeks=4)
    supply = [slot for slot in slots if slot.pillar.key == "supply"]
    assert supply and all(slot.product is None and slot.show is None for slot in supply)


def test_products_do_not_repeat_before_their_pool_is_exhausted(catalog):
    """Pillars sharing a segment share its pool, so no product comes round
    again until every product in that segment has been used."""
    slots = build_plan(catalog, start=PLAN_START, weeks=12)
    used = [s.product.asin for s in slots if s.pillar.segment == "retail" and s.product]
    pool_size = len([p for p in catalog if "retail" in p.segments])
    first_pass = used[:pool_size]
    assert len(set(first_pass)) == len(first_pass)


def test_nothing_is_scheduled_on_a_blackout_date(catalog):
    """Christmas Day is a posting weekday, and no B2B feed is being read."""
    slots = build_plan(catalog, start=PLAN_START, weeks=20)
    assert date(2026, 12, 25) not in {slot.scheduled_for for slot in slots}


def test_a_seasonal_pillar_only_runs_in_its_own_months(catalog):
    slots = build_plan(catalog, start=PLAN_START, weeks=20)
    seasonal = [s for s in slots if s.pillar.key == "seasonal"]
    assert seasonal and all(s.scheduled_for.month in (10, 11, 12) for s in seasonal)


def test_slot_subject_labels_whatever_the_slot_carries(catalog):
    slots = build_plan(catalog, start=PLAN_START, weeks=4)
    assert slots[0].subject == "High Point Market"
    assert next(s for s in slots if s.pillar.key == "supply").subject == "(brand)"


def test_plan_rejects_an_empty_catalog(catalog):
    with pytest.raises(ValueError, match="empty"):
        build_plan(catalog.filter(marketplace="JP"), start=PLAN_START)


def test_get_pillar_raises_with_a_helpful_message():
    with pytest.raises(KeyError, match="known pillars"):
        get_pillar("nope")
