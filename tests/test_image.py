from datetime import date

from homedant_linkedin.composer import compose_all
from homedant_linkedin.image import SIZE, render
from homedant_linkedin.planner import build_plan

try:
    from PIL import Image
except ImportError:  # pragma: no cover - Pillow is a declared dependency
    Image = None


def test_every_post_in_a_plan_renders_a_square_image(catalog, tmp_path):
    drafts = compose_all(build_plan(catalog, start=date(2026, 9, 7), weeks=2), catalog)
    for index, draft in enumerate(drafts):
        path = render(draft, tmp_path / f"{index}.png")
        assert path.exists() and path.stat().st_size > 0
        with Image.open(path) as image:
            assert image.size == (SIZE, SIZE)


def test_a_product_photo_narrows_the_text_column_without_failing(catalog, tmp_path):
    """A post renders with or without a photo; the CDN is not always reachable."""
    from PIL import Image as PILImage

    drafts = compose_all(build_plan(catalog, start=date(2026, 9, 7), weeks=1), catalog)
    product_post = next(d for d in drafts if d.product)
    photo = PILImage.new("RGB", (600, 600), (200, 200, 200))
    with_photo = render(product_post, tmp_path / "with.png", photo=photo)
    without = render(product_post, tmp_path / "without.png")
    assert with_photo.read_bytes() != without.read_bytes()


def test_fetching_a_photo_returns_none_rather_than_raising():
    from homedant_linkedin.image import fetch_product_image

    assert fetch_product_image("") is None
    assert fetch_product_image("https://example.invalid/nope.jpg", timeout=3) is None


def test_the_band_names_the_venue_and_the_space_for_a_show_post(catalog):
    from homedant_linkedin.image import _footer_text

    drafts = compose_all(build_plan(catalog, start=date(2026, 9, 7), weeks=4), catalog)
    show_post = next(d for d in drafts if d.pillar.key == "tradeshow")
    band = _footer_text(show_post)
    assert "Suites at Market Square" in band
    assert "Space M-1007" in band


def test_the_band_names_the_product_without_the_asin(catalog):
    """The ASIN means nothing to a buyer reading the feed."""
    from homedant_linkedin.image import _footer_text

    drafts = compose_all(build_plan(catalog, start=date(2026, 9, 7), weeks=2), catalog)
    product_post = next(d for d in drafts if d.product)
    band = _footer_text(product_post)
    assert product_post.product.short_title in band
    assert product_post.product.asin not in band


def test_an_asset_slug_is_derived_from_the_name():
    from homedant_linkedin.image import asset_path, slug

    assert slug("High Point Market") == "high-point-market"
    assert slug("Retailers' Choice Awards Winner") == "retailers-choice-awards-winner"
    assert asset_path("shows", "NY NOW Summer 2026").name == "ny-now-summer-2026.png"


def test_a_missing_asset_is_none_rather_than_an_error(tmp_path):
    from homedant_linkedin.image import load_asset

    assert load_asset(tmp_path / "nothing.png") is None
