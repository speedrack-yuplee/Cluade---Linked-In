"""report_performance.py joins three files that share no ID column, so what
it gets *wrong* matters more than what it gets right: a bad match reports a
working layout as failing or a failing one as fine."""

import importlib.util
import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "report_performance.py"
spec = importlib.util.spec_from_file_location("report_performance", SCRIPT)
report_performance = importlib.util.module_from_spec(spec)
sys.modules["report_performance"] = spec.loader.exec_module(report_performance) or sys.modules.get(
    "report_performance", report_performance
)
spec.loader.exec_module(report_performance)


def test_a_published_record_matches_the_same_day_post_by_hook():
    published = {"date": "2026-09-01", "hook": "The frame locks together by hand."}
    posts = [
        {"posted_at": "2026-09-01", "url": "a", "hook": "Something else entirely."},
        {"posted_at": "2026-09-01", "url": "b", "hook": "The frame locks together by hand, no tools."},
    ]
    matched = report_performance._match_post(published, posts)
    assert matched["url"] == "b"


def test_an_unrelated_same_day_post_is_not_matched_on_date_alone():
    """Two posts on the same day with no hook overlap must not guess."""
    published = {"date": "2026-09-01", "hook": "The frame locks together by hand."}
    posts = [
        {"posted_at": "2026-09-01", "url": "a", "hook": "Booth 4512, three days to go."},
        {"posted_at": "2026-09-01", "url": "b", "hook": "Proud to be a Retailers' Choice winner."},
    ]
    assert report_performance._match_post(published, posts) is None


def test_a_single_same_day_post_matches_without_needing_the_hook():
    published = {"date": "2026-09-01", "hook": "anything"}
    posts = [{"posted_at": "2026-09-01T08:00:00", "url": "only-one"}]
    assert report_performance._match_post(published, posts)["url"] == "only-one"


def test_velocity_is_impressions_per_hour_between_first_and_last_snapshot():
    snapshots = [
        {"checked_at": "2026-09-01T00:00:00Z", "posts": [{"url": "x", "impressions": 100}]},
        {"checked_at": "2026-09-01T04:00:00Z", "posts": [{"url": "x", "impressions": 500}]},
    ]
    latest, per_hour = report_performance._velocity(snapshots, "x")
    assert latest == 500
    assert per_hour == 100.0


def test_a_url_with_one_snapshot_has_no_velocity_but_still_has_a_count():
    snapshots = [{"checked_at": "2026-09-01T00:00:00Z", "posts": [{"url": "x", "impressions": 42}]}]
    latest, per_hour = report_performance._velocity(snapshots, "x")
    assert latest == 42
    assert per_hour is None


def test_the_report_reaches_the_target_line_when_impressions_clear_it(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    ref = tmp_path / "content" / "reference"
    ref.mkdir(parents=True)
    (ref / "published.json").write_text(json.dumps([
        {"date": "2026-09-01", "pillar": "manufacturing", "pillar_name": "제조", "layout": "detail",
         "hook": "The frame locks together by hand."},
    ]))
    (ref / "posts.json").write_text(json.dumps([
        {"posted_at": "2026-09-01", "url": "a", "impressions": 1200,
         "hook": "The frame locks together by hand."},
    ]))
    (ref / "impressions_log.jsonl").write_text("")

    monkeypatch.setattr(report_performance, "REFERENCE", ref)
    text = report_performance.report(target=1000)
    assert "✅ 목표 달성" in text


def test_the_report_says_when_nothing_has_been_published_yet(tmp_path, monkeypatch):
    monkeypatch.setattr(report_performance, "REFERENCE", tmp_path / "content" / "reference")
    text = report_performance.report()
    assert "published.json" in text
