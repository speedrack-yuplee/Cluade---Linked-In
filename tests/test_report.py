import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "report_posts.py"


def _run(posts, tmp_path):
    source = tmp_path / "posts.json"
    source.write_text(json.dumps(posts), encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--source", str(source)],
        capture_output=True,
        text=True,
    )


def test_posts_are_ranked_by_impressions(tmp_path):
    out = _run(
        [
            {"impressions": 18, "body": "hotels and residential projects"},
            {"impressions": 698, "body": "selected as a Retailers' Choice Awards Winner"},
        ],
        tmp_path,
    ).stdout
    assert out.index("698") < out.index("18")


def test_a_post_whose_impressions_could_not_be_read_is_excluded(tmp_path):
    """null is "not read", not "no reach"; averaging it in would mislead."""
    out = _run(
        [
            {"impressions": 100, "body": "shelving"},
            {"impressions": None, "body": "booth"},
        ],
        tmp_path,
    ).stdout
    assert "1개는 순위에서 제외" in out
    assert "100" in out


def test_all_zero_metrics_are_called_out_as_an_adapter_problem(tmp_path):
    """The failure the collector actually hits should name its own fix."""
    out = _run([{"impressions": None, "body": "shelving"}], tmp_path).stdout
    assert "adapter eject" in out


def test_a_missing_source_exits_three(tmp_path):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--source", str(tmp_path / "nope.json")],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 3


def test_watch_report_ranks_by_visible_engagement(tmp_path, monkeypatch):
    """Impressions belong to a post's author, so a watched post is ranked on
    what is public: reactions and comments."""
    reference = tmp_path / "content" / "reference"
    reference.mkdir(parents=True)
    (reference / "timeline.json").write_text(
        json.dumps(
            [
                {"author": "Quiet", "text": "modular storage", "reactions": 1, "comments": 0},
                {"author": "Loud", "text": "tariff and sourcing", "reactions": 40, "comments": 9},
            ]
        ),
        encoding="utf-8",
    )
    script = Path(__file__).resolve().parent.parent / "scripts" / "report_watch.py"
    out = subprocess.run(
        [sys.executable, str(script)], capture_output=True, text=True, cwd=tmp_path
    ).stdout
    assert out.index("Loud") < out.index("Quiet")
    assert "관세·소싱" in out


def test_watch_report_says_so_when_nothing_was_collected(tmp_path):
    script = Path(__file__).resolve().parent.parent / "scripts" / "report_watch.py"
    out = subprocess.run(
        [sys.executable, str(script)], capture_output=True, text=True, cwd=tmp_path
    ).stdout
    assert "collect_linkedin.ps1" in out
