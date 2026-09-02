from datetime import date

import pytest

from homedant_linkedin.composer import compose, compose_all
from homedant_linkedin.models import Pillar, Slot
from homedant_linkedin.pillars import get_pillar
from homedant_linkedin.planner import build_plan

PLAN_START = date(2026, 9, 1)


def test_every_slot_in_a_plan_composes(catalog):
    drafts = compose_all(build_plan(catalog, start=PLAN_START, weeks=6), catalog)
    assert len(drafts) == 12
    assert all(draft.render().strip() for draft in drafts)


def test_the_award_post_thanks_the_organisations_by_name(catalog):
    award = catalog.brand_profile.recognitions[0]
    text = compose(Slot(PLAN_START, get_pillar("recognition"), recognition=award), catalog).render()
    assert "Thank you to Hardlines Supplier Event and North American Hardware" in text
    assert "#RetailersChoice" in text


def test_the_show_post_names_the_booth_and_the_dates(catalog):
    show = catalog.brand_profile.trade_shows[0]
    text = compose(Slot(PLAN_START, get_pillar("tradeshow"), show=show), catalog).render()
    assert "Booth #372" in text
    assert "August 2-6, 2026" in text


def test_a_show_without_a_booth_omits_the_booth_line(catalog):
    show = next(s for s in catalog.brand_profile.trade_shows if s.booth is None)
    assert "Booth" not in compose(Slot(PLAN_START, get_pillar("tradeshow"), show=show), catalog).render()


def test_no_post_links_a_retail_listing(catalog):
    """A B2B post asks for a conversation; a listing link is a consumer CTA."""
    drafts = compose_all(build_plan(catalog, start=PLAN_START, weeks=6), catalog)
    assert not any("amazon.com/dp/" in draft.render() for draft in drafts)


def test_a_product_name_opening_a_sentence_is_capitalised(catalog):
    product = catalog.by_asin("B0GWGZF1F3")
    text = compose(Slot(PLAN_START, get_pillar("retail"), product=product), catalog).render()
    assert "The 24-inch pegboard storage rack was built for" in text


def test_a_merchandising_note_that_repeats_a_bullet_is_dropped(catalog):
    product = catalog.by_asin("B0F629W2DT")
    text = compose(Slot(PLAN_START, get_pillar("project"), product=product), catalog).render()
    assert text.count("ships in a two pack") == 1


def test_compose_rejects_a_pillar_whose_subject_is_missing(catalog):
    with pytest.raises(ValueError, match="requires a product"):
        compose(Slot(PLAN_START, get_pillar("retail")), catalog)
    with pytest.raises(ValueError, match="requires a recognition"):
        compose(Slot(PLAN_START, get_pillar("recognition")), catalog)


def test_compose_rejects_a_pillar_with_no_composer(catalog):
    slot = Slot(PLAN_START, Pillar("unknown", "Unknown", "", ("Tag",), needs=None))
    with pytest.raises(KeyError, match="no composer"):
        compose(slot, catalog)


def test_render_puts_the_hook_first_and_hashtags_last(catalog):
    product = catalog.by_asin("B0D8VQS2BK")
    draft = compose(Slot(PLAN_START, get_pillar("project"), product=product), catalog)
    rendered = draft.render()
    assert rendered.startswith(draft.hook)
    assert rendered.rstrip().endswith(f"#{draft.hashtags[-1]}")
