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

    drafts = compose_all(build_plan(catalog, start=date(2026, 9, 7), weeks=3), catalog)
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

    drafts = compose_all(build_plan(catalog, start=date(2026, 9, 7), weeks=3), catalog)
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


def test_a_show_post_always_renders_its_own_countdown(catalog, tmp_path):
    """No stock picture can state how many days are left, so the show layout
    draws the number itself."""
    from PIL import Image as PILImage

    from homedant_linkedin import image as image_module

    drafts = compose_all(build_plan(catalog, start=date(2026, 9, 7), weeks=6), catalog)
    show = next(d for d in drafts if d.pillar.key == "tradeshow")
    path = image_module.render(show, tmp_path / "show.png", photo=image_module.photo_for(show))
    with PILImage.open(path) as art:
        ground = art.convert("RGB").getpixel((10, 10))
    assert ground == image_module.SHOW_GROUND, "the show card lost its steel ground"


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


def test_the_high_point_logo_is_the_horizontal_lockup(catalog):
    """The brand guide asks for a lockup, not the icon or wordmark alone, and
    the slot is wide, so the horizontal one is the only correct file."""
    from PIL import Image as PILImage

    from homedant_linkedin.image import asset_path

    path = asset_path("shows", "High Point Market")
    assert path.exists(), "the show logo has not been supplied"
    with PILImage.open(path) as logo:
        assert logo.mode == "RGBA", "the logo needs its transparency"
        assert logo.width / logo.height > 2, "that is not the horizontal lockup"


def test_an_award_badge_and_the_product_both_survive(catalog, tmp_path, monkeypatch):
    """The badge says someone vouched for the product; the photograph says what
    they vouched for. Neither may paint over the other, and the panel is opaque
    so the badge has to be drawn after it."""
    from PIL import Image as PILImage

    from homedant_linkedin import image as image_module

    badge = PILImage.new("RGBA", (300, 300), (255, 0, 255, 255))
    monkeypatch.setattr(
        image_module, "load_asset", lambda path: badge if "awards" in str(path) else None
    )

    drafts = compose_all(build_plan(catalog, start=date(2026, 9, 2), weeks=1), catalog)
    award = next(d for d in drafts if d.pillar.key == "recognition")
    photo = PILImage.new("RGB", (700, 1200), (0, 255, 0))
    path = image_module.render(award, tmp_path / "award.png", photo=photo, use_creatives=False)

    with PILImage.open(path) as rendered:
        present = {colour for _, colour in rendered.convert("RGB").getcolors(maxcolors=1_000_000)}
    assert (255, 0, 255) in present, "the badge was painted over"
    assert (0, 255, 0) in present, "the badge displaced the product photo"


def test_the_retailers_choice_badge_is_cut_out_but_not_altered():
    """Keying every white pixel would have taken the rules inside the disc with
    it and let the ivory ground through, which alters someone else's mark. The
    sheet behind the badge is what had to go, and only that."""
    from PIL import Image as PILImage

    from homedant_linkedin.image import asset_path

    path = asset_path("awards", "Retailers' Choice Awards Winner")
    assert path.exists(), "the NHPA winner badge has not been supplied"
    with PILImage.open(path) as badge:
        assert badge.mode == "RGBA", "the badge needs its transparency"
        pixels = badge.convert("RGBA").load()
        assert pixels[0, 0][3] == 0, "the page behind the badge is still there"
        white_inside = sum(
            1
            for x in range(badge.width // 3, 2 * badge.width // 3)
            for y in range(badge.height // 3, 2 * badge.height // 3)
            if pixels[x, y][3] == 255 and min(pixels[x, y][:3]) > 240
        )
        assert white_inside > 500, "the white rules inside the disc were keyed out too"


def test_a_reference_image_is_the_photograph(catalog, tmp_path):
    """The room is the argument, so nothing is painted over it but the words at
    the bottom. A panel or a studio cut-out here would contradict the post."""
    from PIL import Image as PILImage

    from homedant_linkedin import image as image_module

    drafts = compose_all(build_plan(catalog, start=date(2026, 9, 7), weeks=4), catalog)
    reference = next(d for d in drafts if d.pillar.key == "reference")
    assert reference.slot.pictured is None, "a studio product crept onto an installation post"

    photo = image_module.photo_for(reference)
    assert photo is not None, "the installation photograph is not in the repository"

    path = image_module.render(reference, tmp_path / "ref.png", photo=photo, use_creatives=False)
    with PILImage.open(path) as rendered:
        assert rendered.size == (image_module.SIZE, image_module.SIZE)
        # The top half is the room, untouched: a solid ground would leave far
        # fewer distinct colours than a photograph does.
        top = rendered.convert("RGB").crop((0, 200, image_module.SIZE, 480))
        assert len(top.getcolors(maxcolors=1_000_000)) > 2_000


def test_no_two_posts_in_a_row_carry_the_same_picture(catalog):
    """Seasonal and supply each had exactly one ready-made panel, so every
    seasonal post went out with the same image as the last one. A feed learns
    to scroll past that."""
    from homedant_linkedin.image import photo_pool, pooled_photo

    assert len(photo_pool()) > 20, "the working copy of the library is not in place"
    drafts = compose_all(build_plan(catalog, start=date(2026, 9, 7), weeks=16), catalog)
    chosen = [
        pooled_photo(d.scheduled_for)
        for d in drafts
        if not (d.slot.show or d.slot.recognition or d.slot.installation)
    ]
    assert len(chosen) > 20
    for earlier, later in zip(chosen, chosen[1:]):
        assert earlier != later, "two posts running on the same photograph"
    # Over a quarter the pool should be walked, not circled in a tight loop.
    assert len(set(chosen)) >= len(chosen) * 0.8


def test_the_masthead_uses_the_supplied_wordmark_on_both_grounds():
    """A dark show card cannot carry the black-on-white logo."""
    from PIL import Image as PILImage

    from homedant_linkedin.image import ASSET_DIR

    for name in ("logo.png", "logo-light.png"):
        path = ASSET_DIR / name
        assert path.exists(), f"{name} has not been supplied"
        with PILImage.open(path) as art:
            assert art.mode == "RGBA", f"{name} needs its transparency"
            assert art.convert("RGBA").load()[0, 0][3] == 0, f"{name} still has its background"


def test_no_bullet_is_painted_over_by_the_footer_band():
    """A supply post's third point ran one line too long and the band covered
    it, so the reader saw half a sentence."""
    from PIL import Image as PILImage, ImageDraw

    from homedant_linkedin import image as image_module

    canvas = PILImage.new("RGB", (image_module.SIZE, image_module.SIZE), image_module.GROUND)
    draw = ImageDraw.Draw(canvas)
    long_points = (
        "CA and GA warehouses, so a domestic order does not wait on an ocean container",
        "Our own Korean factory since 1979, where a specification change is a phone call",
        "A specification change is a conversation with the plant rather than a negotiation "
        "with a contract manufacturer somewhere else",
    )
    for top in (400, 560, 700, 820):
        end = image_module._bullets(
            canvas, draw, long_points, top, image_module.SIZE - 2 * image_module.MARGIN,
            image_module.INK, image_module.ACCENT,
        )
        assert end <= image_module.BULLET_FLOOR + image_module.BULLET_GAP, (
            f"bullets starting at {top} reach {end}, past the band at {image_module.BULLET_FLOOR}"
        )


def test_the_opening_fortnight_is_not_one_template_five_times(catalog):
    """Every pillar starts at turn zero, so without an offset the first post of
    each came out on the same layout and the feed opened with one post
    repeated."""
    from homedant_linkedin import image as image_module

    drafts = compose_all(build_plan(catalog, start=date(2026, 9, 7), weeks=5), catalog)
    plain = [
        image_module._layout_key(d)
        for d in drafts
        if not (d.slot.show or d.slot.recognition or d.slot.installation)
    ]
    assert len(plain) >= 5
    assert len(set(plain)) == len(image_module.LAYOUT_CYCLE), (
        "the first weeks of ordinary posts never reach every template"
    )
    for earlier, later in zip(plain, plain[1:]):
        assert earlier != later, "two ordinary posts running on the same template"
