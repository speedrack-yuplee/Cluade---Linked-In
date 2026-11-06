"""Pull product photography off HOMEDANT's own websites into the photo pool.

These are our sites. homedant.com is the US storefront and speedrack.kr the
Korean one, and both carry finished product photography that nobody has to
export from the design library by hand — which makes them the one source of
new pictures that needs no work from Leo at all.

Neither is reachable from the cloud session: the organisation's egress policy
answers 403 to CONNECT for both, and routing around that policy is not on the
table. So this runs in one of two places, and the code is the same in both:

  - a GitHub Actions runner, which is not behind that policy, via
    .github/workflows/site-photos.yml; or
  - the cloud session itself, once the environment's network policy is widened
    to allow homedant.com and speedrack.kr.

What comes down is downscaled to the same 1600 px / quality 82 the OneDrive
sync writes, so a picture from the web and a picture from the design library
are interchangeable to the pool. Everything lands in assets/library/web/<site>.

Only images the pages themselves reference are taken, and only from our own
two domains: a photograph hotlinked from somewhere else is somebody else's to
license, and a LinkedIn post is not the place to find that out.
"""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "assets" / "library" / "web"

SITES = {
    "homedant": "https://homedant.com",
    "speedrack": "https://speedrack.kr",
}

MAX_EDGE = 1600
QUALITY = 82
MIN_EDGE = 700
"""Below this a picture is a thumbnail, an icon or a badge. The finished post
image is 1200 px, and a photograph that has to be blown up to fill it looks
exactly like a photograph that was blown up to fill it."""

MAX_PAGES = 40
MAX_IMAGES = 400

SKIP = re.compile(
    r"(logo|icon|favicon|sprite|banner|btn|button|arrow|bullet|blank|spacer|loading)",
    re.I,
)
"""Furniture, not photography. The wordmark is already in assets/ as a
transparent PNG and a second copy scraped off a page header would only end up
composited on top of itself."""

HEADERS = {
    "User-Agent": "homedant-linkedin/1.0 (+https://github.com/speedrack-yuplee)",
    "Accept": "text/html,image/*,*/*",
}


def get(url: str, timeout: int = 30) -> bytes:
    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def links(html: str, base: str) -> set[str]:
    """Same-site pages worth crawling for more photographs."""
    host = urllib.parse.urlparse(base).netloc
    found = set()
    for href in re.findall(r'href=["\']([^"\']+)["\']', html, re.I):
        absolute = urllib.parse.urljoin(base, href)
        parts = urllib.parse.urlparse(absolute)
        if parts.netloc != host or parts.scheme not in ("http", "https"):
            continue
        if re.search(r"\.(pdf|zip|jpg|png|mp4|css|js)$", parts.path, re.I):
            continue
        found.add(parts._replace(fragment="", query="").geturl())
    return found


def images(html: str, base: str) -> list[str]:
    """Image URLs the page references, from src, data-src and srcset alike.

    Korean commerce templates lazy-load almost everything, so a crawler that
    only reads src comes home with the header and nothing else.
    """
    host = urllib.parse.urlparse(base).netloc
    found: list[str] = []
    patterns = (
        r'<img[^>]+src=["\']([^"\']+)["\']',
        r'data-(?:src|original|lazy)=["\']([^"\']+)["\']',
        r'srcset=["\']([^"\']+)["\']',
    )
    for pattern in patterns:
        for raw in re.findall(pattern, html, re.I):
            for candidate in raw.split(","):
                url = candidate.strip().split(" ")[0]
                if not url or url.startswith("data:"):
                    continue
                absolute = urllib.parse.urljoin(base, url)
                if urllib.parse.urlparse(absolute).netloc != host:
                    continue
                if SKIP.search(absolute):
                    continue
                if absolute not in found:
                    found.append(absolute)
    return found


def save(data: bytes, target: Path) -> tuple[int, int]:
    with Image.open(io.BytesIO(data)) as art:
        art = art.convert("RGB")
        if min(art.size) < MIN_EDGE:
            raise RuntimeError(f"{art.width}x{art.height} — too small")
        scale = min(1.0, MAX_EDGE / max(art.size))
        if scale < 1.0:
            art = art.resize(
                (round(art.width * scale), round(art.height * scale)), Image.LANCZOS
            )
        target.parent.mkdir(parents=True, exist_ok=True)
        art.save(target, "JPEG", quality=QUALITY, optimize=True)
        return art.size


def crawl(site: str, root: str, limit: int) -> list[dict]:
    """Walk the site breadth-first and keep every photograph big enough."""
    seen_pages: set[str] = set()
    queue = [root]
    seen_images: set[str] = set()
    kept: list[dict] = []

    while queue and len(seen_pages) < MAX_PAGES and len(kept) < limit:
        page = queue.pop(0)
        if page in seen_pages:
            continue
        seen_pages.add(page)

        try:
            html = get(page).decode("utf-8", "replace")
        except Exception as exc:  # noqa: BLE001 - one dead page must not stop the crawl
            print(f"  skip  {page}: {exc}")
            continue

        for url in images(html, page):
            if url in seen_images or len(kept) >= limit:
                continue
            seen_images.add(url)
            name = Path(urllib.parse.urlparse(url).path).stem or "image"
            slug = re.sub(r"[^A-Za-z0-9_-]+", "-", name).strip("-").lower()[:60]
            target = TARGET / site / f"{slug or 'image'}-{len(kept):03d}.jpg"
            try:
                width, height = save(get(url), target)
            except Exception as exc:  # noqa: BLE001 - try the next picture
                continue
            kept.append(
                {
                    "file": str(target.relative_to(ROOT)).replace("\\", "/"),
                    "source": url,
                    "page": page,
                    "size": f"{width}x{height}",
                }
            )
            print(f"  got   {target.name}  {width}x{height}")

        queue.extend(sorted(links(html, page) - seen_pages))

    return kept


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", choices=sorted(SITES), help="just this site")
    parser.add_argument("--limit", type=int, default=MAX_IMAGES, help="per site")
    arguments = parser.parse_args()

    manifest: dict[str, list[dict]] = {}
    blocked: list[str] = []

    for site, root in SITES.items():
        if arguments.only and site != arguments.only:
            continue
        print(f"[{site}] {root}")
        try:
            manifest[site] = crawl(site, root, arguments.limit)
        except Exception as exc:  # noqa: BLE001 - report, do not retry a policy denial
            blocked.append(f"{site}: {exc}")
            print(f"  FAIL  {site}: {exc}", file=sys.stderr)

    if manifest:
        TARGET.mkdir(parents=True, exist_ok=True)
        (TARGET / "index.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        total = sum(len(v) for v in manifest.values())
        print(f"\n{total} photographs into {TARGET.relative_to(ROOT)}")

    if blocked:
        print("\nunreachable:", file=sys.stderr)
        for line in blocked:
            print(f"  {line}", file=sys.stderr)
        print(
            "\nIf this is the cloud session, that is the egress policy, not the site.\n"
            "Widen the environment's network policy, or run "
            ".github/workflows/site-photos.yml instead.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
