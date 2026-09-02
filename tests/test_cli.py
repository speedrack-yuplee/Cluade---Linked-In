import io
from datetime import date

from homedant_linkedin.cli import main, next_monday


def _run(argv):
    out = io.StringIO()
    code = main(argv, out=out)
    return code, out.getvalue()


def test_next_monday_always_moves_forward():
    assert next_monday(date(2026, 9, 2)).weekday() == 0
    assert next_monday(date(2026, 8, 31)) == date(2026, 9, 7)


def test_plan_leads_with_the_award_post():
    code, output = _run(["plan", "--start", "2026-09-01", "--weeks", "1"])
    assert code == 0
    assert "Third-party recognition" in output.splitlines()[2]


def test_plan_prints_one_line_per_post():
    code, output = _run(["plan", "--start", "2026-09-01", "--weeks", "2"])
    assert code == 0
    assert output.count("2026-") == 4


def test_plan_json_is_machine_readable():
    import json

    code, output = _run(["plan", "--json", "--start", "2026-09-01", "--weeks", "1"])
    assert code == 0
    assert [row["pillar"] for row in json.loads(output)] == ["recognition", "project"]


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
