"""Download the room photographs a product gets composited into.

The cloud session cannot reach the stock CDNs: the egress policy answers 403 to
CONNECT for images.pexels.com and images.unsplash.com. A GitHub Actions runner
is not behind that policy — but Pexels and Unsplash answer 403 to a runner too,
because they turn away datacenter addresses. So neither end can fetch from them
and the source has to be one that serves machines.

Openverse does. It indexes openly licensed photography across Flickr, Wikimedia
and others, needs no API key, and states each result's licence in the response
rather than leaving it to be inferred. Only CC0 and public-domain results are
kept, so a picture in a HOMEDANT post never carries an attribution obligation
that a LinkedIn caption would have to satisfy.

Entries in sources.json name a search, not a file, because which photograph is
available under those terms is not knowable from here. What actually came down
is written to credits.json with its licence and landing page, for review.
"""

from __future__ import annotations

import argparse
import io
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
BACKGROUNDS = ROOT / "assets" / "backgrounds"
SOURCES = BACKGROUNDS / "sources.json"
CREDITS = BACKGROUNDS / "credits.json"

API = "https://api.openverse.org/v1/images/"
MAX_EDGE = 1600
QUALITY = 88
MIN_WIDTH = 1200
"""A background is composited into and then cropped, so anything narrower than
the finished 1200 px post image is no use."""

FREE_LICENCES = {"cc0", "pdm"}
"""Licences that carry no attribution condition. Everything else is skipped:
a CC BY photo is free to use but obliges a credit line, and a caption that has
to carry one is a caption that will eventually go out without it."""

HEADERS = {"User-Agent": "homedant-linkedin/1.0 (+https://github.com/speedrack-yuplee)"}


def _get(url: str, timeout: int = 40) -> bytes:
    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def search(query: str, wanted: int = 40) -> list[dict]:
    """Openverse results for ``query`` that are usable without attribution."""
    parameters = urllib.parse.urlencode(
        {
            "q": query,
            "license": ",".join(sorted(FREE_LICENCES)),
            "license_type": "commercial,modification",
            "size": "large",
            "page_size": wanted,
            "mature": "false",
        }
    )
    payload = json.loads(_get(f"{API}?{parameters}").decode("utf-8"))
    return payload.get("results", [])


def save(data: bytes, target: Path) -> tuple[int, int]:
    """Write ``data`` to ``target`` with its long edge at most MAX_EDGE."""
    with Image.open(io.BytesIO(data)) as art:
        art = art.convert("RGB")
        if art.width < MIN_WIDTH:
            raise RuntimeError(f"only {art.width}px wide")
        scale = min(1.0, MAX_EDGE / max(art.size))
        if scale < 1.0:
            art = art.resize(
                (round(art.width * scale), round(art.height * scale)), Image.LANCZOS
            )
        target.parent.mkdir(parents=True, exist_ok=True)
        art.save(target, "JPEG", quality=QUALITY, optimize=True)
        return art.size


def fetch(entry: dict) -> dict:
    """The first result for this entry that downloads and is big enough.

    Openverse indexes other people's servers, so a result can be gone, be a
    thumbnail, or not be an image at all. Working down the list rather than
    trusting the first hit is what makes the run finish.
    """
    slug = entry["slug"]
    target = BACKGROUNDS / f"{slug}.jpg"
    problems: list[str] = []

    for candidate in search(entry["query"]):
        licence = (candidate.get("license") or "").lower()
        if licence not in FREE_LICENCES:
            continue
        url = candidate.get("url")
        if not url:
            continue
        try:
            width, height = save(_get(url), target)
        except Exception as exc:  # noqa: BLE001 - try the next candidate
            problems.append(f"{url}: {exc}")
            continue
        return {
            "slug": slug,
            "scene": entry.get("scene", ""),
            "size": f"{width}x{height}",
            "licence": f"{licence} {candidate.get('license_version', '')}".strip(),
            "creator": candidate.get("creator") or "",
            "title": candidate.get("title") or "",
            "landing": candidate.get("foreign_landing_url") or "",
            "source": candidate.get("source") or "",
        }

    raise RuntimeError(
        f"no usable result for {entry['query']!r}"
        + (f" (tried {len(problems)})" if problems else "")
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="re-download what is already here")
    parser.add_argument("--only", help="just this slug")
    arguments = parser.parse_args()

    entries = json.loads(SOURCES.read_text(encoding="utf-8"))["backgrounds"]
    credits = json.loads(CREDITS.read_text(encoding="utf-8")) if CREDITS.exists() else {}
    failures: list[str] = []

    for entry in entries:
        slug = entry["slug"]
        if arguments.only and slug != arguments.only:
            continue
        if (BACKGROUNDS / f"{slug}.jpg").exists() and not arguments.force:
            print(f"  have  {slug}")
            continue

        try:
            credit = fetch(entry)
        except Exception as exc:  # noqa: BLE001 - one bad query must not stop the rest
            failures.append(f"{slug}: {exc}")
            print(f"  FAIL  {slug}: {exc}")
            continue

        credits[slug] = credit
        print(f"  got   {slug}  {credit['size']}  {credit['licence']}  {credit['landing']}")

    CREDITS.write_text(
        json.dumps(credits, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    if failures:
        print("\nfailed:", file=sys.stderr)
        for failure in failures:
            print(f"  {failure}", file=sys.stderr)
        # A partial run is still worth committing, so the caller decides.
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
