"""The trade press reader, exercised without touching the network."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from homedant_linkedin import feeds
from homedant_linkedin.cli import main


def rss(items: str) -> bytes:
    return f"<rss version='2.0'><channel><title>T</title>{items}</channel></rss>".encode()


def item(title: str, description: str = "", when: datetime | None = None) -> str:
    stamp = f"<pubDate>{when.strftime('%a, %d %b %Y %H:%M:%S +0000')}</pubDate>" if when else ""
    return f"<item><title>{title}</title><description>{description}</description><link>https://x/1</link>{stamp}</item>"


FRESH = datetime.now(timezone.utc) - timedelta(days=2)
STALE = datetime.now(timezone.utc) - timedelta(days=400)


def test_bundled_feed_list_loads():
    feed_list, watch = feeds.load_feeds()
    assert feed_list and watch
    assert all(f.url.startswith("https://") for f in feed_list)
    assert all(f.segment for f in feed_list)


def test_parses_rss_items():
    feed = feeds.Feed(name="Trade Weekly", url="https://x/feed", segment="retail")
    entries = feeds.parse_feed(rss(item("Modular casegoods", "FSC certified", FRESH)), feed)
    assert len(entries) == 1
    assert entries[0].title == "Modular casegoods"
    assert entries[0].feed == "Trade Weekly"
    assert entries[0].segment == "retail"
    assert entries[0].published is not None


def test_parses_atom_entries():
    feed = feeds.Feed(name="Atom Daily", url="https://x/atom")
    payload = (
        "<feed xmlns='http://www.w3.org/2005/Atom'><entry>"
        "<title>BIFMA update</title><summary>New test report</summary>"
        "<link href='https://x/2'/><updated>2026-08-01T10:00:00Z</updated>"
        "</entry></feed>"
    ).encode()
    entries = feeds.parse_feed(payload, feed)
    assert entries[0].title == "BIFMA update"
    assert entries[0].link == "https://x/2"
    assert entries[0].published.year == 2026


def test_summary_html_is_stripped():
    feed = feeds.Feed(name="F", url="https://x")
    entries = feeds.parse_feed(rss(item("T", "&lt;p&gt;low-VOC   finishes&lt;/p&gt;")), feed)
    assert entries[0].summary == "low-VOC finishes"


def test_unparseable_feed_is_reported_not_raised():
    feed = feeds.Feed(name="Broken", url="https://x")
    entries, errors = feeds.collect((feed,), fetcher=lambda f, t: b"not xml at all")
    assert entries == ()
    assert errors and errors[0][0] == "Broken"


def test_network_failure_is_reported_not_raised():
    feed = feeds.Feed(name="Down", url="https://x")

    def boom(f, t):
        raise OSError("connection refused")

    entries, errors = feeds.collect((feed,), fetcher=boom)
    assert entries == ()
    assert "connection refused" in errors[0][1]


def test_stale_entries_fall_outside_the_window():
    feed = feeds.Feed(name="F", url="https://x")
    payload = rss(item("New", "modular", FRESH) + item("Old", "modular", STALE))
    entries, _ = feeds.collect((feed,), days=30, fetcher=lambda f, t: payload)
    assert [e.title for e in entries] == ["New"]


def test_undated_entries_survive_the_window():
    """We cannot prove an undated story is stale, so it stays in the count."""
    feed = feeds.Feed(name="F", url="https://x")
    entries, _ = feeds.collect((feed,), days=30, fetcher=lambda f, t: rss(item("No date", "modular")))
    assert [e.title for e in entries] == ["No date"]


def test_rank_counts_entries_not_repetitions():
    entries = (
        feeds.Entry(feed="A", segment="", title="modular modular modular", summary="modular", link=""),
        feeds.Entry(feed="B", segment="", title="FSC timber", summary="", link=""),
    )
    hits = feeds.rank(entries, {"modularity": ("modular",), "sustainability": ("FSC",)})
    counts = {h.term: h.count for h in hits}
    assert counts == {"modular": 1, "FSC": 1}


def test_rank_is_case_insensitive_and_sorted_by_count():
    entries = (
        feeds.Entry(feed="A", segment="", title="Modular", summary="", link=""),
        feeds.Entry(feed="B", segment="", title="modular", summary="", link=""),
        feeds.Entry(feed="C", segment="", title="fsc", summary="", link=""),
    )
    hits = feeds.rank(entries, {"m": ("modular",), "s": ("FSC",)})
    assert [h.term for h in hits] == ["modular", "FSC"]
    assert hits[0].feeds == ("A", "B")


def test_rank_skips_terms_nobody_mentioned():
    entries = (feeds.Entry(feed="A", segment="", title="tariffs", summary="", link=""),)
    assert feeds.rank(entries, {"x": ("nearshoring",)}) == ()


def test_feed_requires_name_and_url():
    with pytest.raises(ValueError):
        feeds.Feed.from_dict({"name": "no url"})


def test_feed_list_without_feeds_is_rejected(tmp_path):
    path = tmp_path / "feeds.json"
    path.write_text(json.dumps({"feeds": [], "watch": {"a": ["b"]}}), encoding="utf-8")
    with pytest.raises(ValueError):
        feeds.load_feeds(path)


def test_feed_list_without_watch_terms_is_rejected(tmp_path):
    path = tmp_path / "feeds.json"
    path.write_text(json.dumps({"feeds": [{"name": "a", "url": "https://x"}], "watch": {}}), encoding="utf-8")
    with pytest.raises(ValueError):
        feeds.load_feeds(path)


def _stub(monkeypatch, payload: bytes):
    monkeypatch.setattr(feeds, "fetch", lambda feed, timeout: payload)


def test_cli_trends_lists_terms(monkeypatch, capsys, tmp_path):
    path = tmp_path / "feeds.json"
    path.write_text(
        json.dumps(
            {
                "feeds": [{"name": "Trade Weekly", "url": "https://x/feed", "segment": "retail"}],
                "watch": {"modularity": ["modular"]},
            }
        ),
        encoding="utf-8",
    )
    _stub(monkeypatch, rss(item("Modular casegoods win", "", FRESH)))
    assert main(["trends", "--feeds", str(path)]) == 0
    out = capsys.readouterr().out
    assert "modular" in out
    assert "Trade Weekly" in out


def test_cli_trends_json(monkeypatch, capsys, tmp_path):
    path = tmp_path / "feeds.json"
    path.write_text(
        json.dumps({"feeds": [{"name": "F", "url": "https://x"}], "watch": {"m": ["modular"]}}),
        encoding="utf-8",
    )
    _stub(monkeypatch, rss(item("Modular", "", FRESH)))
    assert main(["trends", "--feeds", str(path), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["entries"] == 1
    assert payload["terms"][0]["term"] == "modular"


def test_cli_trends_exits_1_when_no_feed_answers(monkeypatch, capsys, tmp_path):
    path = tmp_path / "feeds.json"
    path.write_text(
        json.dumps({"feeds": [{"name": "F", "url": "https://x"}], "watch": {"m": ["modular"]}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(feeds, "fetch", lambda feed, timeout: (_ for _ in ()).throw(OSError("no route")))
    assert main(["trends", "--feeds", str(path)]) == 1
    assert "no feed answered" in capsys.readouterr().out
