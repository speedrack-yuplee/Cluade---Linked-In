from datetime import date

import pytest

from homedant_linkedin.pillars import PILLARS, get_pillar
from homedant_linkedin.planner import build_plan, posting_dates

PLAN_START = date(2026, 9, 1)


def test_posting_dates_land_on_tuesday_and_thursday():
    assert [d.weekday() for d in posting_dates(PLAN_START, weeks=2)] == [1, 3, 1, 3]


def test_posting_dates_never_precede_the_start_date():
    assert posting_dates(date(2026, 9, 3), weeks=1) == [date(2026, 9, 3)]


def test_posting_dates_rejects_zero_weeks():
    with pytest.raises(ValueError, match="at least 1"):
        posting_dates(PLAN_START, weeks=0)


def test_plan_assigns_a_pillar_to_every_slot(catalog):
    slots = build_plan(catalog, start=PLAN_START, weeks=4)
    assert len(slots) == 8
    assert all(slot.pillar in PILLARS for slot in slots)


def test_recognition_leads_the_rotation(catalog):
    """The award post outperformed product posts by more than an order of
    magnitude, so it opens every cycle."""
    slots = build_plan(catalog, start=PLAN_START, weeks=4)
    assert slots[0].pillar.key == "recognition"
    assert slots[0].recognition is not None


def test_a_show_that_has_already_closed_is_never_scheduled(catalog):
    """Both shows on file ended before this plan starts."""
    slots = build_plan(catalog, start=PLAN_START, weeks=6)
    assert all(slot.pillar.key != "tradeshow" for slot in slots)


def test_an_upcoming_show_is_scheduled(catalog):
    """The same plan, dated before the shows closed, does use them."""
    slots = build_plan(catalog, start=date(2026, 3, 2), weeks=4)
    shows = [slot for slot in slots if slot.pillar.key == "tradeshow"]
    assert shows and all(slot.show.end >= date(2026, 3, 2) for slot in shows)


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
    slots = build_plan(catalog, start=PLAN_START, weeks=12)
    used = [s.product.asin for s in slots if s.pillar.key == "retail"]
    pool_size = len([p for p in catalog if "retail" in p.segments])
    assert len(set(used[:pool_size])) == len(used[:pool_size])


def test_slot_subject_labels_whatever_the_slot_carries(catalog):
    slots = build_plan(catalog, start=PLAN_START, weeks=4)
    assert slots[0].subject == "Retailers' Choice Awards Winner"
    assert next(s for s in slots if s.pillar.key == "supply").subject == "(brand)"


def test_plan_rejects_an_empty_catalog(catalog):
    with pytest.raises(ValueError, match="empty"):
        build_plan(catalog.filter(marketplace="JP"), start=PLAN_START)


def test_get_pillar_raises_with_a_helpful_message():
    with pytest.raises(KeyError, match="known pillars"):
        get_pillar("nope")
