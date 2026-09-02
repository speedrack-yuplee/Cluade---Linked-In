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


def test_the_footer_names_the_show_for_a_show_post(catalog, tmp_path):
    from homedant_linkedin.image import _footer_text

    drafts = compose_all(build_plan(catalog, start=date(2026, 9, 7), weeks=1), catalog)
    show_post = next(d for d in drafts if d.pillar.key == "tradeshow")
    assert "High Point Market" in _footer_text(show_post)
