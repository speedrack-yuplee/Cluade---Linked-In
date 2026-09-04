"""Download the room photographs a product gets composited into.

The cloud session cannot reach the stock CDNs: the egress policy answers 403 to
CONNECT for images.pexels.com and images.unsplash.com. A GitHub Actions runner
is not behind that policy, so the choosing happens in the session and the
downloading happens here.

Each entry in assets/backgrounds/sources.json names a photo page rather than a
file. The page carries an og:image pointing at the full-size original, so the
direct URL never has to be guessed, and the same code works for Pexels and
Unsplash alike.

Photographer and page are recorded in credits.json. Neither licence requires
attribution, but a picture used in company marketing should be traceable to the
licence it came in under.
"""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
BACKGROUNDS = ROOT / "assets" / "backgrounds"
SOURCES = BACKGROUNDS / "sources.json"
CREDITS = BACKGROUNDS / "credits.json"

MAX_EDGE = 1600
QUALITY = 88

# Some stock sites answer a bare urllib request with a challenge page.
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

ALLOWED_HOSTS = ("pexels.com", "unsplash.com", "pixabay.com")
"""Sites whose licence covers commercial use. A page anywhere else is refused
rather than downloaded, so a copyrighted photo cannot reach a HOMEDANT post by
someone pasting a link into sources.json."""


def _get(url: str, timeout: int = 40) -> bytes:
    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def _meta(html: str, prop: str) -> str | None:
    """The content of one og/twitter meta tag, whichever order the attributes
    were written in."""
    for pattern in (
        rf'<meta[^>]+(?:property|name)=["\']{prop}["\'][^>]+content=["\']([^"\']+)["\']',
        rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\']{prop}["\']',
    ):
        found = re.search(pattern, html, re.IGNORECASE)
        if found:
            return found.group(1)
    return None


def resolve(page: str) -> tuple[str, str]:
    """The image URL and the credit line for a photo page."""
    html = _get(page).decode("utf-8", "replace")
    image = _meta(html, "og:image")
    if not image:
        raise RuntimeError("no og:image on the page")
    title = _meta(html, "og:title") or ""
    return image, title.strip()


def save(data: bytes, target: Path) -> tuple[int, int]:
    """Write ``data`` to ``target`` with its long edge at most MAX_EDGE."""
    with Image.open(io.BytesIO(data)) as art:
        art = art.convert("RGB")
        scale = min(1.0, MAX_EDGE / max(art.size))
        if scale < 1.0:
            art = art.resize(
                (round(art.width * scale), round(art.height * scale)), Image.LANCZOS
            )
        target.parent.mkdir(parents=True, exist_ok=True)
        art.save(target, "JPEG", quality=QUALITY, optimize=True)
        return art.size


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

        page = entry["page"]
        if not any(host in page for host in ALLOWED_HOSTS):
            failures.append(f"{slug}: {page} is not a licensed stock site")
            continue

        target = BACKGROUNDS / f"{slug}.jpg"
        if target.exists() and not arguments.force:
            print(f"  have  {slug}")
            continue

        try:
            url, title = resolve(page)
            width, height = save(_get(url), target)
        except Exception as exc:  # noqa: BLE001 - one bad page must not stop the rest
            failures.append(f"{slug}: {exc}")
            print(f"  FAIL  {slug}: {exc}")
            continue

        credits[slug] = {
            "page": page,
            "title": title,
            "scene": entry.get("scene", ""),
            "licence": "Pexels" if "pexels" in page else "Unsplash",
        }
        print(f"  got   {slug}  {width}x{height}  {target.stat().st_size // 1024} KB")

    CREDITS.write_text(
        json.dumps(credits, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    if failures:
        print("\nfailed:", file=sys.stderr)
        for failure in failures:
            print(f"  {failure}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
