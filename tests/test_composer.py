from datetime import date

import pytest

from homedant_linkedin.composer import compose, compose_all
from homedant_linkedin.models import Pillar, Slot
from homedant_linkedin.pillars import get_pillar
from homedant_linkedin.planner import build_plan


def test_every_slot_in_a_plan_composes(catalog):
    drafts = compose_all(build_plan(catalog, start=date(2026, 9, 1), weeks=4), catalog)
    assert len(drafts) == 8
    assert all(draft.render().strip() for draft in drafts)


def test_a_product_post_links_the_listing(catalog):
    product = catalog.by_asin("B0GWGZF1F3")
    slot = Slot(date(2026, 9, 1), get_pillar("spotlight"), product)
    assert product.url in compose(slot, catalog).render()


def test_the_operations_post_signs_off_as_the_author(catalog):
    slot = Slot(date(2026, 9, 1), get_pillar("operations"))
    assert "Leo Lee" in compose(slot, catalog).render()


def test_compose_rejects_a_product_pillar_with_no_product(catalog):
    slot = Slot(date(2026, 9, 1), get_pillar("spotlight"))
    with pytest.raises(ValueError, match="requires a product"):
        compose(slot, catalog)


def test_compose_rejects_a_pillar_with_no_composer(catalog):
    slot = Slot(date(2026, 9, 1), Pillar("unknown", "Unknown", "", ("Tag",)))
    with pytest.raises(KeyError, match="no composer"):
        compose(slot, catalog)


def test_render_puts_the_hook_first_and_hashtags_last(catalog):
    product = catalog.by_asin("B0D8VQS2BK")
    draft = compose(Slot(date(2026, 9, 1), get_pillar("problem"), product), catalog)
    rendered = draft.render()
    assert rendered.startswith(draft.hook)
    assert rendered.rstrip().endswith(f"#{draft.hashtags[-1]}")
