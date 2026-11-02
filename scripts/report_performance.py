#!/usr/bin/env python3
"""Say whether recent posts are on track for 1,000 impressions, and why not.

Joins three things that each answer half a question on their own:

  content/reference/published.json   what we actually posted: pillar, layout, hook
  content/reference/posts.json       the latest snapshot opencli read off LinkedIn
  content/reference/impressions_log.jsonl   the same snapshot, once per collection run

published.json says what we chose; the log says how it performed and how fast.
Neither alone can say "the figure-card layout is underperforming its hook" —
that needs both, joined by date, since opencli's own JSON carries no reference
back to which draft a post came from.

    python scripts/report_performance.py --out performance.txt
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REFERENCE = Path("content/reference")
TARGET = 1000
"""The early goal Leo set. Not a ceiling — once posts clear it routinely this
number stops being the interesting question."""


def _load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig", errors="replace"), strict=False)
    except json.JSONDecodeError as exc:
        print(f"{path}: unreadable ({exc})", file=sys.stderr)
        return default


def _load_log(path: Path) -> list[dict]:
    """impressions_log.jsonl: one JSON object per line, oldest first."""
    if not path.exists():
        return []
    snapshots = []
    for line in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            snapshots.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return snapshots


def _norm(text: str) -> str:
    """Lowercase, collapsed whitespace, punctuation stripped.

    The drafted hook and the text opencli scrapes back off a rendered page
    are the same words but not always the same characters — a smart quote,
    a trailing period a wrap dropped, LinkedIn's own "...more" truncation.
    Comparing on words alone is what makes the match survive that."""
    text = re.sub(r"\s+", " ", (text or "")).strip().lower()
    return re.sub(r"[^\w ]", "", text)


def _match_post(published: dict, posts: list[dict]) -> dict | None:
    """The collected post this published record is probably about.

    opencli's rows carry no ID that traces back to a draft, so this matches on
    date and, where that alone is ambiguous, the opening words of the hook. A
    post the day's own hook does not appear in is not matched at all — a wrong
    match would misreport a working layout as failing, or the reverse.
    """
    same_day = [p for p in posts if (p.get("posted_at") or "")[:10] == published["date"]]
    if len(same_day) == 1:
        return same_day[0]
    if not same_day:
        return None
    hook = _norm(published.get("hook"))[:40]
    for p in same_day:
        if hook and hook in _norm(p.get("hook") or p.get("body")):
            return p
    return None


def _velocity(snapshots: list[dict], url: str) -> tuple[int | None, float | None]:
    """Latest impression count for ``url``, and impressions per hour since the
    first snapshot that saw it — the number that says whether a post is still
    climbing or has already levelled off short of the target."""
    seen = []
    for snap in snapshots:
        checked_at = snap.get("checked_at")
        for p in snap.get("posts", []):
            if p.get("url") == url and isinstance(p.get("impressions"), int):
                seen.append((checked_at, p["impressions"]))
    if not seen:
        return None, None
    seen.sort()
    latest = seen[-1][1]
    if len(seen) < 2:
        return latest, None
    try:
        first_time = datetime.fromisoformat(seen[0][0].replace("Z", "+00:00"))
        last_time = datetime.fromisoformat(seen[-1][0].replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return latest, None
    hours = max((last_time - first_time).total_seconds() / 3600, 0.5)
    return latest, round((seen[-1][1] - seen[0][1]) / hours, 1)


LAYOUT_ADVICE = {
    "plain": "사진이 없는 판형입니다. 다음 이 필러 차례엔 사진이 있는 판형이 먼저 걸리게 되어 있습니다.",
    "product": "제품 사진 + 불릿 판형입니다. 반응이 약하면 다음 회차는 full-bleed 사진으로 자동 전환됩니다.",
    "full": "사진 전체 판형입니다. 사진 자체가 약할 수 있습니다 — 다음 회차엔 부품 근접(detail)으로 넘어갑니다.",
    "figure": "숫자 카드 판형입니다. 숫자가 안 와닿으면 문구를 바꿔야 합니다 — 판형 문제가 아닐 수 있습니다.",
    "detail": "부품 근접 판형입니다. 주장이 구체적일수록 반응이 좋은 편이니, 캡션이 막연하지 않은지 보세요.",
    "reference": "실제 설치 사진입니다. 지금 가진 판형 중 가장 신뢰를 주는 편이라, 약하면 문구 쪽을 먼저 의심하세요.",
    "show": "전시회 카운트다운입니다. 날짜가 코앞이 아니면 원래도 약하게 나옵니다.",
    "award": "수상 인증입니다. 반복 억제가 걸려 있어 자주 나오지 않습니다.",
}


def report(target: int = TARGET) -> str:
    published = _load_json(REFERENCE / "published.json", [])
    posts = _load_json(REFERENCE / "posts.json", [])
    snapshots = _load_log(REFERENCE / "impressions_log.jsonl")

    lines = [f"LinkedIn 성과 점검 — 목표 노출 {target:,}"]
    if not published:
        lines.append("")
        lines.append("published.json 이 없습니다. 아직 이 시스템으로 나간 게시글이 없거나,")
        lines.append("linkedin-draft.yml 워크플로가 한 번도 안 돌았습니다.")
        return "\n".join(lines)
    if not posts:
        lines.append("")
        lines.append("posts.json 이 없습니다. collect_linkedin.ps1 을 아직 못 돌렸습니다.")
        return "\n".join(lines)

    lines.append(f"(기록된 초안 {len(published)}건 · 수집 스냅샷 {len(snapshots)}회)")
    lines.append("")

    matched = 0
    for record in sorted(published, key=lambda r: r["date"], reverse=True)[:12]:
        post = _match_post(record, posts)
        header = f"{record['date']}  {record.get('pillar_name', record['pillar'])}  [{record.get('layout', '?')}]"
        if post is None:
            lines.append(f"{header}  — 아직 실제 게시글과 매칭 안 됨 (수집 필요)")
            continue
        matched += 1
        impressions = post.get("impressions")
        url = post.get("url")
        latest, per_hour = (impressions, None) if not url else _velocity(snapshots, url)
        latest = latest if latest is not None else impressions

        if latest is None:
            lines.append(f"{header}  — 노출 수치 없음")
            continue

        pct = round(100 * latest / target)
        status = "✅ 목표 달성" if latest >= target else f"{pct}% 진행"
        speed = f", 시간당 +{per_hour}" if per_hour is not None else ""
        lines.append(f"{header}  — 노출 {latest:,} ({status}{speed})")

        if latest < target * 0.5 and per_hour is not None and per_hour < 5:
            advice = LAYOUT_ADVICE.get(record.get("layout", ""), "")
            if advice:
                lines.append(f"   → {advice}")

    if matched == 0:
        lines.append("")
        lines.append("실제 게시글과 매칭된 초안이 없습니다. 날짜/훅이 다르면 매칭이 안 됩니다.")

    # Layout-level averages, once enough posts exist to say anything.
    by_layout: dict[str, list[int]] = {}
    for record in published:
        post = _match_post(record, posts)
        if post and isinstance(post.get("impressions"), int):
            by_layout.setdefault(record.get("layout", "?"), []).append(post["impressions"])
    scored = {k: v for k, v in by_layout.items() if len(v) >= 2}
    if scored:
        lines += ["", "[판형별 평균 노출] (2건 이상)"]
        for layout, values in sorted(scored.items(), key=lambda kv: -sum(kv[1]) / len(kv[1])):
            avg = round(sum(values) / len(values))
            lines.append(f"  {layout:<10} 평균 {avg:,}  (n={len(values)})")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=int, default=TARGET)
    parser.add_argument("--out", type=Path, help="write to a file instead of stdout")
    arguments = parser.parse_args()

    text = report(arguments.target)
    if arguments.out:
        arguments.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
