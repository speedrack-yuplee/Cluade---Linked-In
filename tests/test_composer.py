from dataclasses import replace
from datetime import date

import pytest

from homedant_linkedin.composer import compose, compose_all
from homedant_linkedin.models import Pillar, Slot
from homedant_linkedin.pillars import get_pillar
from homedant_linkedin.planner import build_plan

PLAN_START = date(2026, 9, 7)  # a Monday, so every week contributes three slots


def test_every_slot_in_a_plan_composes(catalog):
    drafts = compose_all(build_plan(catalog, start=PLAN_START, weeks=6), catalog)
    assert len(drafts) == 18
    assert all(draft.render().strip() for draft in drafts)


def _unposted(award):
    """The same award as it would have been before it went out."""
    return replace(award, posted_on=None)


def test_the_award_post_thanks_the_organisations_by_name(catalog):
    award = _unposted(catalog.brand_profile.recognitions[0])
    text = compose(Slot(PLAN_START, get_pillar("recognition"), recognition=award), catalog).render()
    assert "Thank you to Hardlines Supplier Event and North American Hardware" in text
    assert "#RetailersChoice" in text


def test_an_award_that_is_already_live_is_not_announced_again(catalog):
    """Repeating the announcement would duplicate a post that is still up."""
    award = catalog.brand_profile.recognitions[0]
    assert award.posted_on is not None
    text = compose(Slot(PLAN_START, get_pillar("recognition"), recognition=award), catalog).render()
    assert "We are proud to share" not in text
    assert "Thank you to" not in text
    assert award.event in text


def test_the_show_post_names_the_booth_and_the_dates(catalog):
    show = next(s for s in catalog.brand_profile.trade_shows if s.booth)
    text = compose(Slot(PLAN_START, get_pillar("tradeshow"), show=show), catalog).render()
    assert "Booth #372" in text
    assert "August 2-6, 2026" in text


def test_the_high_point_post_carries_the_dates_from_the_booth_memo(catalog):
    show = next(s for s in catalog.brand_profile.trade_shows if s.name == "High Point Market")
    text = compose(Slot(PLAN_START, get_pillar("tradeshow"), show=show), catalog).render()
    assert "October 16-21, 2026" in text
    assert "Suites at Market Square" in text
    assert "Space M-1007" in text
    assert "Booth" not in text, "High Point numbers showroom spaces, not booths"


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
    assert "The 24-inch pegboard storage rack adjusts to them" in text


def test_no_post_renders_a_bullet_list(catalog):
    """The account's own posts run as prose; the bullets belong to the image."""
    drafts = compose_all(build_plan(catalog, start=PLAN_START, weeks=6), catalog)
    assert not any(line.startswith("- ") for d in drafts for line in d.render().split("\n"))


def test_proof_points_are_carried_for_the_image_but_not_the_text(catalog):
    drafts = compose_all(build_plan(catalog, start=PLAN_START, weeks=2), catalog)
    assert all(draft.points for draft in drafts)


def test_the_award_post_matches_the_structure_of_the_real_one(catalog):
    """Hook, milestone, capability, invitation, thanks - in that order."""
    award = _unposted(catalog.brand_profile.recognitions[0])
    text = compose(Slot(PLAN_START, get_pillar("recognition"), recognition=award), catalog).render()
    order = [
        "We are proud to share that HOMEDANT",
        "meaningful milestone for Homedant USA Inc",
        "Our shelving systems are designed to support",
        "We look forward to connecting with",
        "Thank you to",
        "#HOMEDANT",
    ]
    positions = [text.index(fragment) for fragment in order]
    assert positions == sorted(positions)


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


def test_the_show_history_reads_as_a_sentence(catalog):
    assert catalog.brand_profile.show_history.endswith("NY NOW and DESIGN TOKYO")


def test_a_show_post_carries_the_year_s_other_shows(catalog):
    """A buyer meeting the brand at one show should know it stands at others."""
    show = next(s for s in catalog.brand_profile.trade_shows if s.name == "High Point Market")
    text = compose(Slot(PLAN_START, get_pillar("tradeshow"), show=show), catalog).render()
    assert "NeoCon" in text and "National Hardware Show" in text
