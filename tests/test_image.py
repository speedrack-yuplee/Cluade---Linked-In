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


def test_the_footer_names_the_show_for_a_show_post(catalog, tmp_path):
    from homedant_linkedin.image import _footer_text

    drafts = compose_all(build_plan(catalog, start=date(2026, 9, 7), weeks=4), catalog)
    show_post = next(d for d in drafts if d.pillar.key == "tradeshow")
    assert "High Point Market" in _footer_text(show_post)
