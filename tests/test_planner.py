from datetime import date

import pytest

from homedant_linkedin.pillars import PILLARS, get_pillar
from homedant_linkedin.planner import build_plan, posting_dates


def test_posting_dates_land_on_tuesday_and_thursday():
    days = posting_dates(date(2026, 9, 1), weeks=2)
    assert [d.weekday() for d in days] == [1, 3, 1, 3]


def test_posting_dates_never_precede_the_start_date():
    start = date(2026, 9, 3)  # a Thursday
    days = posting_dates(start, weeks=1)
    assert days == [date(2026, 9, 3)]


def test_posting_dates_rejects_zero_weeks():
    with pytest.raises(ValueError, match="at least 1"):
        posting_dates(date(2026, 9, 1), weeks=0)


def test_plan_assigns_a_pillar_to_every_slot(catalog):
    slots = build_plan(catalog, start=date(2026, 9, 1), weeks=4)
    assert len(slots) == 8
    assert all(slot.pillar in PILLARS for slot in slots)


def test_plan_rotates_pillars_in_order(catalog):
    slots = build_plan(catalog, start=date(2026, 9, 1), weeks=4)
    assert [s.pillar.key for s in slots[:4]] == [p.key for p in PILLARS]


def test_operations_slots_carry_no_product(catalog):
    slots = build_plan(catalog, start=date(2026, 9, 1), weeks=4)
    operations = [s for s in slots if s.pillar.key == "operations"]
    assert operations and all(s.product is None for s in operations)


def test_products_do_not_repeat_before_the_catalog_is_exhausted(catalog):
    slots = build_plan(catalog, start=date(2026, 9, 1), weeks=10)
    used = [s.product.asin for s in slots if s.product]
    first_pass = used[: len(catalog)]
    assert len(set(first_pass)) == len(first_pass)


def test_plan_rejects_an_empty_catalog(catalog):
    empty = catalog.filter(marketplace="JP")
    with pytest.raises(ValueError, match="empty"):
        build_plan(empty, start=date(2026, 9, 1))


def test_get_pillar_raises_with_a_helpful_message():
    with pytest.raises(KeyError, match="known pillars"):
        get_pillar("nope")
