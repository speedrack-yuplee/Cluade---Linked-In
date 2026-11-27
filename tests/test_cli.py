import io
from datetime import date

from homedant_linkedin.cli import main


def _run(argv):
    out = io.StringIO()
    code = main(argv, out=out)
    return code, out.getvalue()


def test_plan_defaults_to_the_same_calendar_the_scheduled_run_posts_from():
    """`plan` and `next` must never disagree about which post falls on a day."""
    import json as _json

    from homedant_linkedin.catalog import Catalog
    from homedant_linkedin.schedule import due_on

    _, output = _run(["plan", "--json", "--weeks", "3"])
    catalog = Catalog.load()
    for row in _json.loads(output):
        day = date.fromisoformat(row["date"])
        assert due_on(catalog, day).pillar.key == row["pillar"]


def test_plan_leads_with_the_show_announcement():
    code, output = _run(["plan", "--start", "2026-09-01", "--weeks", "1"])
    assert code == 0
    assert "Trade show" in output.splitlines()[2]


def test_plan_prints_one_line_per_post():
    """Four, not six: Labor Day falls on the Monday of the second week and
    nothing goes out on a US federal holiday."""
    code, output = _run(["plan", "--start", "2026-09-01", "--weeks", "2"])
    assert code == 0
    assert output.count("2026-") == 4
    assert "2026-09-07" not in output


def test_plan_json_is_machine_readable():
    import json

    code, output = _run(["plan", "--json", "--start", "2026-09-01", "--weeks", "1"])
    assert code == 0
    assert [row["pillar"] for row in json.loads(output)] == ["tradeshow", "recognition"]


def test_draft_renders_full_post_text():
    code, output = _run(["draft", "--start", "2026-09-01", "--weeks", "1"])
    assert code == 0
    assert "Homedant USA Inc" in output
    assert "#HOMEDANT" in output


def test_validate_passes_on_the_bundled_catalog():
    code, output = _run(["validate", "--start", "2026-09-01", "--weeks", "4"])
    assert code == 0
    assert "FAIL" not in output


def test_products_lists_the_catalog():
    code, output = _run(["products"])
    assert code == 0
    assert "B0GWGZF1F3" in output


def test_an_unknown_marketplace_exits_nonzero():
    code, output = _run(["--marketplace", "JP", "plan"])
    assert code == 1
    assert "no products" in output


def test_next_writes_the_post_and_the_image(tmp_path):
    code, output = _run(["next", "--date", "2026-09-04", "--out", str(tmp_path)])
    assert code == 0
    assert (tmp_path / "post.txt").exists()
    assert (tmp_path / "post.png").exists()
    assert "Homedant USA Inc" in (tmp_path / "post.txt").read_text()
    assert "Third-party recognition" in output


def test_next_is_quiet_on_a_day_with_nothing_scheduled(tmp_path):
    code, output = _run(["next", "--date", "2026-09-08", "--out", str(tmp_path)])
    assert code == 0
    assert not (tmp_path / "post.txt").exists()
    assert "nothing scheduled" in output


def test_next_can_report_an_empty_day_as_an_error(tmp_path):
    code, _ = _run(["next", "--date", "2026-09-08", "--out", str(tmp_path), "--require-slot"])
    assert code == 3
