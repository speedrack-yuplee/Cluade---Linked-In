from dataclasses import replace
from datetime import date

from homedant_linkedin.composer import compose, compose_all
from homedant_linkedin.models import Slot
from homedant_linkedin.pillars import get_pillar
from homedant_linkedin.planner import build_plan
from homedant_linkedin.validators import validate, validate_all


def _draft(catalog):
    product = catalog.by_asin("B09NLRKRYT")
    return compose(Slot(date(2026, 9, 1), get_pillar("spotlight"), product), catalog)


def test_every_generated_post_passes_validation(catalog):
    drafts = compose_all(build_plan(catalog, start=date(2026, 9, 1), weeks=12), catalog)
    assert validate_all(drafts) == {}


def test_an_over_long_post_is_flagged(catalog):
    draft = replace(_draft(catalog), body="x" * 4000)
    assert any(issue.rule == "length" for issue in validate(draft))


def test_an_over_long_hook_is_flagged(catalog):
    draft = replace(_draft(catalog), hook="x" * 300)
    assert any(issue.rule == "hook" for issue in validate(draft))


def test_an_unsupportable_claim_is_flagged(catalog):
    draft = replace(_draft(catalog), body="This is the cheapest shelving anywhere.")
    assert any(issue.rule == "claims" for issue in validate(draft))


def test_a_product_post_without_its_link_is_flagged(catalog):
    draft = replace(_draft(catalog), cta="Thanks for reading.")
    assert any(issue.rule == "link" for issue in validate(draft))


def test_too_few_hashtags_is_flagged(catalog):
    draft = replace(_draft(catalog), hashtags=("HOMEDANT",))
    assert any(issue.rule == "hashtags" for issue in validate(draft))
