from datetime import date

from homedant_linkedin.composer import compose_all
from homedant_linkedin.image import SIZE, render
from homedant_linkedin.planner import build_plan

try:
    from PIL import Image
except ImportError:  # pragma: no cover - Pillow is a declared dependency
    Image = None


def test_every_post_in_a_plan_renders_a_square_image(catalog, tmp_path):
    """Panels and drawn layouts alike come out at LinkedIn's square size."""
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
    with_photo = render(product_post, tmp_path / "with.png", photo=photo, use_creatives=False)
    without = render(product_post, tmp_path / "without.png", use_creatives=False)
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


def test_a_ready_made_panel_is_used_for_a_product_pillar(catalog, tmp_path):
    """The brand's own A+ content beats anything the layout can draw."""
    from homedant_linkedin.image import creative_for

    drafts = compose_all(build_plan(catalog, start=date(2026, 9, 7), weeks=6), catalog)
    retail = next(d for d in drafts if d.pillar.key == "retail")
    panel = creative_for(retail)
    assert panel is not None and panel.parent.name == "retail"


def test_a_show_post_always_renders_its_own_countdown(catalog):
    """No fixed panel can state how many days are left."""
    from homedant_linkedin.image import creative_for

    drafts = compose_all(build_plan(catalog, start=date(2026, 9, 7), weeks=6), catalog)
    show = next(d for d in drafts if d.pillar.key == "tradeshow")
    award = next(d for d in drafts if d.pillar.key == "recognition")
    assert creative_for(show) is None
    assert creative_for(award) is None


def test_use_creatives_can_be_turned_off(catalog, tmp_path):
    drafts = compose_all(build_plan(catalog, start=date(2026, 9, 7), weeks=6), catalog)
    retail = next(d for d in drafts if d.pillar.key == "retail")
    drawn = render(retail, tmp_path / "drawn.png", use_creatives=False)
    panel = render(retail, tmp_path / "panel.png")
    assert drawn.read_bytes() != panel.read_bytes()


def test_a_supplied_photo_stands_in_when_the_listing_image_is_unreachable(catalog):
    """A show post keeps its picture even when that day's product has no file."""
    from homedant_linkedin.image import photo_for

    drafts = compose_all(build_plan(catalog, start=date(2026, 9, 2), weeks=1), catalog)
    show = next(d for d in drafts if d.pillar.key == "tradeshow")
    assert photo_for(show, timeout=2) is not None


def test_a_show_logo_survives_the_photo_panel(catalog, tmp_path, monkeypatch):
    """The panel is opaque, so a logo drawn before it would be painted over."""
    from PIL import Image as PILImage

    from homedant_linkedin import image as image_module

    mark = PILImage.new("RGBA", (300, 100), (255, 0, 255, 255))
    monkeypatch.setattr(image_module, "load_asset", lambda path: mark if "shows" in str(path) else None)

    drafts = compose_all(build_plan(catalog, start=date(2026, 9, 2), weeks=1), catalog)
    show = next(d for d in drafts if d.pillar.key == "tradeshow")
    photo = PILImage.new("RGB", (700, 1200), (240, 240, 240))
    path = image_module.render(show, tmp_path / "show.png", photo=photo)

    with PILImage.open(path) as rendered:
        assert (255, 0, 255) in rendered.convert("RGB").getcolors(maxcolors=1_000_000)[0][1:] or any(
            colour == (255, 0, 255) for _, colour in rendered.convert("RGB").getcolors(maxcolors=1_000_000)
        )
