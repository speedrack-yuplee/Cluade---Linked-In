#!/usr/bin/env python3
"""Read what other accounts are posting, and say what it suggests writing about.

Reads content/reference/timeline.json and watched.json — the feed and the
named profiles the collector picked up — and reports which posts drew a
response and which subjects keep coming back.

Impressions belong to a post's author, so nothing here ranks by reach. What
is visible is reactions and comments, and what people wrote about.

    python scripts/report_watch.py --out watch.txt
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

REFERENCE = Path("content/reference")

# Terms worth noticing in someone else's post because HOMEDANT can answer
# them: they name a buyer's problem this brand already has a fact about.
WATCHED_TERMS: dict[str, tuple[str, ...]] = {
    "관세·소싱": ("tariff", "duty", "sourcing", "nearshor", "lead time", "landed cost", "container"),
    "지속가능성": ("sustainab", "fsc", "recycled", "low-voc", "carbon"),
    "모듈·다용도": ("modular", "reconfigur", "multi-use", "flexible space", "adaptive"),
    "규격·인증": ("bifma", "ada", "certif", "test report", "compliance", "load rating"),
    "채널·조달": ("ff&e", "procurement", "specifier", "planogram", "reset", "build-to-rent"),
    "전시회": ("market", "show", "booth", "neocon", "hpmkt", "expo"),
    "한국·제조": ("korea", "made in", "factory", "manufactur"),
}

STOP = set("""a an the and or but of in on for to with from at by as is are was were be been
this that these those we our you your they their it its will can has have had more most than
about into over under after before new now just our us""".split())


def load(name: str) -> list[dict]:
    path = REFERENCE / name
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig", errors="replace"), strict=False)
    except json.JSONDecodeError as exc:
        print(f"{path}: unreadable ({exc})", file=sys.stderr)
        return []
    if isinstance(data, dict):
        data = [data]
    posts: list[dict] = []
    for entry in data:
        # watched.json nests posts under each profile; timeline.json is flat.
        if isinstance(entry, dict) and isinstance(entry.get("posts"), list):
            for post in entry["posts"]:
                posts.append({**post, "author": post.get("author") or entry.get("name")})
        else:
            posts.append(entry)
    return posts


def engagement(post: dict) -> int:
    return sum(post.get(k) or 0 for k in ("reactions", "comments") if isinstance(post.get(k), int))


def text_of(post: dict) -> str:
    return " ".join(f"{post.get('text') or ''} {post.get('body') or ''}".split())


def report(posts: list[dict]) -> str:
    if not posts:
        return (
            "읽을 게시글이 없습니다.\n"
            "content/reference/timeline.json 또는 watched.json 이 아직 수집되지 않았습니다.\n"
            "scripts/collect_linkedin.ps1 을 PC에서 실행하세요."
        )

    lines = [f"다른 계정 게시글 {len(posts)}개"]

    ranked = sorted(posts, key=engagement, reverse=True)
    lines += ["", "[반응이 붙은 글]"]
    for post in ranked[:6]:
        if not engagement(post):
            break
        counts = " · ".join(
            f"{label} {post[key]}"
            for key, label in (("reactions", "반응"), ("comments", "댓글"))
            if isinstance(post.get(key), int) and post[key]
        )
        lines.append(f"{post.get('author') or '(작성자 미상)'} — {counts}")
        lines.append(f"  {text_of(post)[:78]}")

    corpus = " ".join(text_of(p) for p in posts).lower()
    hits = {
        name: sum(corpus.count(w) for w in words)
        for name, words in WATCHED_TERMS.items()
    }
    live = {k: v for k, v in hits.items() if v}
    if live:
        lines += ["", "[이번 수집에서 자주 나온 주제]"]
        for name, n in sorted(live.items(), key=lambda kv: -kv[1]):
            lines.append(f"{name:<12} {n:>3}회")

    words = Counter(
        w for w in re.findall(r"[a-z][a-z'-]{3,}", corpus) if w not in STOP
    )
    lines += ["", "[자주 쓰인 단어]", "  " + ", ".join(w for w, _ in words.most_common(12))]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    text = report(load("timeline.json") + load("watched.json"))
    print(text)
    if args.out:
        args.out.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
