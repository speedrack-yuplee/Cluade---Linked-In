#!/usr/bin/env python3
"""Rank collected LinkedIn posts and say what the numbers support.

Reads content/reference/posts.json — whatever opencli produced, in the shape
content/reference/README.md documents — and writes a short digest.

    python scripts/report_posts.py --out digest.txt
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_SOURCE = Path("content/reference/posts.json")

# What a post is about, judged from its own words. The collector does not
# label posts, and a label guessed here is better than no grouping at all.
TOPICS: dict[str, tuple[str, ...]] = {
    "수상·인증": ("award", "winner", "recognized", "recognition", "selected for"),
    "전시회": ("booth", "market", "show", "neocon", "days to go", "see you at", "live at"),
    "프로젝트": ("hotel", "residential", "condominium", "multifamily", "project"),
    "제품·리테일": ("shelving", "shelves", "storage", "boltless", "tier", "inventory"),
    "회사 소식": ("website", "renewed", "pleased to share", "team"),
}


def load(path: Path) -> list[dict]:
    raw = path.read_text(encoding="utf-8-sig", errors="replace")
    try:
        data = json.loads(raw, strict=False)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{path} is not readable as JSON: {exc}")
    return data if isinstance(data, list) else [data]


def topic_of(post: dict) -> str:
    text = f"{post.get('body') or ''} {post.get('raw_text') or ''}".lower()
    for name, words in TOPICS.items():
        if any(w in text for w in words):
            return name
    return "기타"


def first_line(post: dict, width: int = 58) -> str:
    text = (post.get("body") or post.get("raw_text") or "").strip()
    text = re.sub(r"\s+", " ", text)
    return text[:width] + ("…" if len(text) > width else "")


def report(posts: list[dict]) -> str:
    measured = [p for p in posts if isinstance(p.get("impressions"), int)]
    unmeasured = len(posts) - len(measured)

    lines = [f"LinkedIn 게시글 성과 — 수집 {len(posts)}개"]
    if unmeasured:
        lines.append(f"(노출을 읽지 못한 {unmeasured}개는 순위에서 제외)")
    if not measured:
        lines.append("")
        lines.append("노출 수치가 하나도 없습니다. 어댑터가 그 영역을 못 읽고")
        lines.append("있을 수 있습니다: opencli adapter eject linkedin")
        return "\n".join(lines)

    ranked = sorted(measured, key=lambda p: p["impressions"], reverse=True)
    lines += ["", "[상위 5개]"]
    for i, p in enumerate(ranked[:5], 1):
        counts = f"노출 {p['impressions']}"
        for key, label in (("reactions", "반응"), ("comments", "댓글"), ("reposts", "퍼감")):
            if isinstance(p.get(key), int):
                counts += f" · {label} {p[key]}"
        lines.append(f"{i}. {counts}")
        lines.append(f"   {topic_of(p)} | {first_line(p)}")

    groups: dict[str, list[int]] = {}
    for p in measured:
        groups.setdefault(topic_of(p), []).append(p["impressions"])
    lines += ["", "[주제별 평균 노출]"]
    for name, values in sorted(groups.items(), key=lambda kv: -sum(kv[1]) / len(kv[1])):
        lines.append(f"{name:<10} {sum(values) // len(values):>5}  (n={len(values)})")

    best, worst = ranked[0]["impressions"], ranked[-1]["impressions"]
    if worst:
        lines += ["", f"최고와 최저의 차이: {best / worst:.0f}배"]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--out", type=Path, help="write here as well as to stdout")
    args = parser.parse_args()

    if not args.source.exists():
        print(f"{args.source} does not exist yet", file=sys.stderr)
        return 3

    text = report(load(args.source))
    print(text)
    if args.out:
        args.out.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
