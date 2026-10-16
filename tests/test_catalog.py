import json

import pytest

from homedant_linkedin.catalog import Catalog
from homedant_linkedin.models import Product


def test_bundled_catalog_loads_every_product(catalog):
    assert len(catalog) == 11
    assert catalog.brand == "HOMEDANT"
    assert catalog.company == "Homedant USA Inc"
    assert catalog.author == "Leo Lee"


def test_brand_profile_carries_the_award_and_show_history(catalog):
    profile = catalog.brand_profile
    assert any("Retailers' Choice" in r.name for r in profile.recognitions)
    assert any(s.booth == "372" for s in profile.trade_shows)


def test_audience_phrase_reads_as_a_sentence(catalog):
    phrase = catalog.brand_profile.audience_phrase
    assert phrase.startswith("retail buyers")
    assert phrase.endswith("and multifamily developers")


def test_by_asin_is_case_insensitive(catalog):
    assert catalog.by_asin("b0gwgzf1f3").sku == "HS604015HP-5W-2Pack"


def test_by_asin_raises_for_unknown(catalog):
    with pytest.raises(KeyError):
        catalog.by_asin("B000000000")


def test_filter_by_marketplace_keeps_only_that_marketplace(catalog):
    canadian = catalog.filter(marketplace="CA")
    assert len(canadian) == 1
    assert {p.marketplace for p in canadian} == {"CA"}


def test_filter_by_category_narrows_the_catalog(catalog):
    racks = catalog.filter(category="garment-rack")
    assert {p.category for p in racks} == {"garment-rack"}
    assert len(racks) < len(catalog)


def test_every_product_is_tagged_for_at_least_one_segment(catalog):
    assert all(product.segments for product in catalog)


def test_short_title_prefers_the_hand_written_short_name(catalog):
    assert catalog.by_asin("B0BTYD4L7Y").short_title == "the over-the-toilet storage cabinet"


def test_sentence_name_capitalises_for_the_start_of_a_sentence(catalog):
    assert catalog.by_asin("B0BTYD4L7Y").sentence_name == "The over-the-toilet storage cabinet"


def test_short_title_falls_back_to_the_trimmed_listing_title():
    product = Product.from_dict(
        {
            "asin": "B0TEST0000",
            "sku": "TEST",
            "title": 'HOMEDANT - Over The Toilet Storage Cabinet 24.5" W x 8.6" D',
            "category": "bathroom-storage",
            "marketplace": "US",
            "url": "https://example.com/dp/B0TEST0000",
        }
    )
    assert product.short_title == "Over The Toilet Storage Cabinet"


def test_product_from_dict_rejects_missing_fields():
    with pytest.raises(ValueError, match="missing required field"):
        Product.from_dict({"asin": "B0", "sku": "S"})


def test_load_rejects_a_catalog_with_no_products(tmp_path):
    path = tmp_path / "empty.json"
    path.write_text(json.dumps({"products": []}), encoding="utf-8")
    with pytest.raises(ValueError, match="no products"):
        Catalog.load(path)
