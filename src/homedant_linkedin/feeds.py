"""Reading the trade press, so a post can answer what buyers are reading.

The agent has no view of LinkedIn's own trending list; LinkedIn does not
publish one. What it can see is the trade press those buyers read, so this
module pulls a set of industry feeds and counts how often the terms we care
about show up. That is a reading list, not a ranking of LinkedIn itself.

Deliberately dependency-free: `urllib` fetches and `ElementTree` parses, so
adding this costs the project nothing at install time.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from xml.etree import ElementTree

DATA_DIR = Path(__file__).parent / "data"
DEFAULT_FEEDS_PATH = DATA_DIR / "feeds.json"

USER_AGENT = "homedant-linkedin/0.1 (+trade press reader)"
"""Several trade publishers refuse a request with no user agent at all."""

DEFAULT_TIMEOUT = 20.0
DEFAULT_DAYS = 30

ATOM = "{http://www.w3.org/2005/Atom}"

_TAGS = re.compile(r"<[^>]+>")
_SPACE = re.compile(r"\s+")


@dataclass(frozen=True)
class Feed:
    """One publication the buyers we sell to actually read."""

    name: str
    url: str
    segment: str = ""

    @classmethod
    def from_dict(cls, raw: dict) -> "Feed":
        missing = [k for k in ("name", "url") if not raw.get(k)]
        if missing:
            raise ValueError(f"feed is missing required field(s): {', '.join(missing)}")
        return cls(name=raw["name"], url=raw["url"], segment=raw.get("segment", ""))


@dataclass(frozen=True)
class Entry:
    """One story, flattened to the parts a keyword count needs."""

    feed: str
    segment: str
    title: str
    summary: str
    link: str
    published: datetime | None = None

    @property
    def text(self) -> str:
        return f"{self.title} {self.summary}"


@dataclass(frozen=True)
class Hit:
    """One watched term, and how much of the last N days mentioned it."""

    theme: str
    term: str
    count: int
    feeds: tuple[str, ...]
    example: str = ""


@dataclass(frozen=True)
class Report:
    """What one `trends` run saw, including the feeds that would not answer."""

    entries: tuple[Entry, ...]
    hits: tuple[Hit, ...]
    errors: tuple[tuple[str, str], ...] = ()
    days: int = DEFAULT_DAYS


def load_feeds(path: str | Path | None = None) -> tuple[tuple[Feed, ...], dict[str, tuple[str, ...]]]:
    """Read the feed list and the watched terms, grouped by theme."""
    path = Path(path) if path else DEFAULT_FEEDS_PATH
    raw = json.loads(path.read_text(encoding="utf-8"))
    feeds = tuple(Feed.from_dict(item) for item in raw.get("feeds", []))
    if not feeds:
        raise ValueError(f"feed list at {path} contains no feeds")
    watch = {theme: tuple(terms) for theme, terms in raw.get("watch", {}).items() if terms}
    if not watch:
        raise ValueError(f"feed list at {path} contains no watched terms")
    return feeds, watch


def clean(value: str | None) -> str:
    """Feed summaries arrive as HTML. We only ever count words in them."""
    if not value:
        return ""
    return _SPACE.sub(" ", _TAGS.sub(" ", value)).strip()


def parse_date(value: str | None) -> datetime | None:
    """RSS dates are RFC 822, Atom dates are ISO 8601. Accept either."""
    if not value:
        return None
    text = value.strip()
    try:
        parsed = parsedate_to_datetime(text)
    except (TypeError, ValueError):
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None
    if parsed is None:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def parse_feed(payload: bytes | str, feed: Feed) -> tuple[Entry, ...]:
    """Turn one feed document into entries, whether it is RSS or Atom."""
    try:
        root = ElementTree.fromstring(payload)
    except ElementTree.ParseError as exc:
        raise ValueError(f"{feed.name}: not parseable as XML ({exc})") from exc

    entries: list[Entry] = []
    for item in root.iter():
        if item.tag == "item":
            title = item.findtext("title")
            summary = item.findtext("description")
            link = item.findtext("link") or ""
            when = parse_date(item.findtext("pubDate") or item.findtext("date"))
        elif item.tag == f"{ATOM}entry":
            title = item.findtext(f"{ATOM}title")
            summary = item.findtext(f"{ATOM}summary") or item.findtext(f"{ATOM}content")
            anchor = item.find(f"{ATOM}link")
            link = anchor.get("href", "") if anchor is not None else ""
            when = parse_date(item.findtext(f"{ATOM}updated") or item.findtext(f"{ATOM}published"))
        else:
            continue
        entries.append(
            Entry(
                feed=feed.name,
                segment=feed.segment,
                title=clean(title),
                summary=clean(summary),
                link=link.strip(),
                published=when,
            )
        )
    return tuple(entries)


def fetch(feed: Feed, timeout: float = DEFAULT_TIMEOUT) -> bytes:
    """Fetch one feed. Raises on anything that is not a readable response."""
    request = urllib.request.Request(feed.url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def collect(
    feeds: tuple[Feed, ...],
    days: int = DEFAULT_DAYS,
    timeout: float = DEFAULT_TIMEOUT,
    fetcher=None,
) -> tuple[tuple[Entry, ...], tuple[tuple[str, str], ...]]:
    """Read every feed in parallel. A feed that fails is reported, not fatal.

    `fetcher` resolves at call time rather than as a default, so a test (or a
    caller with its own cache) can swap the network out.

    An entry with no date survives the window: we cannot prove it is stale,
    and dropping it would quietly bias the count toward tidier publishers.
    """
    read_one = fetcher or fetch
    cutoff = datetime.now(timezone.utc) - timedelta(days=days) if days else None

    def read(feed: Feed) -> tuple[tuple[Entry, ...], tuple[str, str] | None]:
        try:
            return parse_feed(read_one(feed, timeout), feed), None
        except (urllib.error.URLError, OSError, ValueError) as exc:
            return (), (feed.name, str(exc))

    entries: list[Entry] = []
    errors: list[tuple[str, str]] = []
    with ThreadPoolExecutor(max_workers=min(8, len(feeds))) as pool:
        for found, error in pool.map(read, feeds):
            if error:
                errors.append(error)
            entries.extend(e for e in found if cutoff is None or e.published is None or e.published >= cutoff)

    entries.sort(key=lambda e: (e.published is not None, e.published or datetime.min.replace(tzinfo=timezone.utc)), reverse=True)
    return tuple(entries), tuple(errors)


def rank(entries: tuple[Entry, ...], watch: dict[str, tuple[str, ...]]) -> tuple[Hit, ...]:
    """Count the entries mentioning each watched term, busiest term first.

    One entry counts once per term however often it repeats it, so a single
    long article cannot manufacture a trend on its own.
    """
    hits: list[Hit] = []
    for theme, terms in watch.items():
        for term in terms:
            needle = term.lower()
            matched = [e for e in entries if needle in e.text.lower()]
            if not matched:
                continue
            hits.append(
                Hit(
                    theme=theme,
                    term=term,
                    count=len(matched),
                    feeds=tuple(sorted({e.feed for e in matched})),
                    example=matched[0].title,
                )
            )
    hits.sort(key=lambda h: (-h.count, h.theme, h.term))
    return tuple(hits)


def report(
    path: str | Path | None = None,
    days: int = DEFAULT_DAYS,
    timeout: float = DEFAULT_TIMEOUT,
    fetcher=None,
) -> Report:
    """Read every feed and rank the watched terms across what came back."""
    feeds, watch = load_feeds(path)
    entries, errors = collect(feeds, days=days, timeout=timeout, fetcher=fetcher)
    return Report(entries=entries, hits=rank(entries, watch), errors=errors, days=days)
