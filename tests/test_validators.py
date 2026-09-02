from dataclasses import replace
from datetime import date

from homedant_linkedin.composer import compose, compose_all
from homedant_linkedin.models import Slot
from homedant_linkedin.pillars import get_pillar
from homedant_linkedin.planner import build_plan
from homedant_linkedin.validators import validate, validate_all

PLAN_START = date(2026, 9, 1)


def _draft(catalog):
    product = catalog.by_asin("B09NLRKRYT")
    return compose(Slot(PLAN_START, get_pillar("retail"), product=product), catalog)


def test_every_generated_post_passes_validation(catalog):
    drafts = compose_all(build_plan(catalog, start=PLAN_START, weeks=12), catalog)
    assert validate_all(drafts, catalog.brand_profile) == {}


def test_an_over_long_post_is_flagged(catalog):
    assert any(i.rule == "length" for i in validate(replace(_draft(catalog), body="x" * 4000)))


def test_an_over_long_hook_is_flagged(catalog):
    assert any(i.rule == "hook" for i in validate(replace(_draft(catalog), hook="x" * 300)))


def test_an_unsupportable_claim_is_flagged(catalog):
    draft = replace(_draft(catalog), body="This is the cheapest shelving anywhere.")
    assert any(i.rule == "claims" for i in validate(draft))


def test_a_post_that_never_names_the_company_is_flagged(catalog):
    draft = replace(_draft(catalog), body="Steel shelving, built well.")
    assert any(i.rule == "company" for i in validate(draft, catalog.brand_profile))


def test_the_company_rule_is_skipped_when_no_brand_is_given(catalog):
    draft = replace(_draft(catalog), body="Steel shelving, built well.")
    assert not any(i.rule == "company" for i in validate(draft))


def test_a_retail_listing_link_is_flagged(catalog):
    draft = replace(_draft(catalog), cta="Buy it at https://www.amazon.com/dp/B09NLRKRYT")
    assert any(i.rule == "channel" for i in validate(draft))


def test_a_cta_that_does_not_ask_for_a_conversation_is_flagged(catalog):
    assert any(i.rule == "cta" for i in validate(replace(_draft(catalog), cta="Thanks for reading.")))


def test_a_missing_brand_hashtag_is_flagged(catalog):
    draft = replace(_draft(catalog), hashtags=("RetailBuyers", "SteelShelving", "B2B"))
    assert any(i.rule == "hashtags" and "HOMEDANT" in i.message for i in validate(draft))


def test_too_few_hashtags_is_flagged(catalog):
    assert any(i.rule == "hashtags" for i in validate(replace(_draft(catalog), hashtags=("HOMEDANT",))))


def test_too_many_hashtags_is_flagged(catalog):
    draft = replace(_draft(catalog), hashtags=tuple(["HOMEDANT"] + [f"Tag{n}" for n in range(12)]))
    assert any(i.rule == "hashtags" and "at most" in i.message for i in validate(draft))


def test_a_run_of_blank_lines_is_flagged(catalog):
    assert any(i.rule == "spacing" for i in validate(replace(_draft(catalog), body="a\n\n\n\nb")))
