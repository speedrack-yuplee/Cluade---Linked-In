#!/usr/bin/env python3
"""Render the content calendar as a standalone HTML page.

The page is generated from the catalog and brand profile, so adding a show, an
award or a product and re-running this reflects the change everywhere: the
calendar, the counts, and the source panel that says what it was built from.

    python scripts/build_calendar_page.py --until 2026-12-31 --out calendar.html
"""

from __future__ import annotations

import argparse
import html
import sys
from collections import Counter
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from homedant_linkedin.catalog import Catalog  # noqa: E402
from homedant_linkedin.composer import compose_all  # noqa: E402
from homedant_linkedin.planner import build_plan  # noqa: E402
from homedant_linkedin.schedule import anchor_for  # noqa: E402

PILLAR_TONE = {
    "tradeshow": "show",
    "recognition": "award",
    "seasonal": "season",
}

STYLE = """
:root {
  --ground: #F7F4EE;
  --surface: #FFFDF9;
  --edge: #E2DBCF;
  --ink: #221E1B;
  --muted: #6E645C;
  --accent: #9E1B22;
  --show: #2F4858;
  --season: #8A6A22;
  --shadow: 0 1px 2px rgba(34, 30, 27, .06);
  color-scheme: light dark;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --ground: #17150F;
    --surface: #201D17;
    --edge: #37322A;
    --ink: #F1EBE0;
    --muted: #A2988B;
    --accent: #E2686F;
    --show: #8FB6CC;
    --season: #D8B463;
    --shadow: none;
  }
}
:root[data-theme="dark"] {
  --ground: #17150F;
  --surface: #201D17;
  --edge: #37322A;
  --ink: #F1EBE0;
  --muted: #A2988B;
  --accent: #E2686F;
  --show: #8FB6CC;
  --season: #D8B463;
  --shadow: none;
}

body {
  margin: 0;
  background: var(--ground);
  color: var(--ink);
  font-family: "Source Sans 3", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: 16px;
  line-height: 1.55;
}
.wrap { max-width: 1020px; margin: 0 auto; padding: 56px 24px 96px; }

h1, h2, h3 { font-family: Archivo, "Helvetica Neue", Arial, sans-serif; text-wrap: balance; margin: 0; }
h1 { font-size: 2.45rem; font-weight: 700; letter-spacing: -.022em; line-height: 1.1; }
h2 { font-size: 1.05rem; font-weight: 600; letter-spacing: .07em; text-transform: uppercase; }
.lede { color: var(--muted); max-width: 62ch; margin: 14px 0 0; font-size: 1.05rem; }

.eyebrow {
  font-family: "IBM Plex Mono", ui-monospace, monospace;
  font-size: .74rem; letter-spacing: .16em; text-transform: uppercase; color: var(--accent);
  margin: 0 0 14px;
}

.summary {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(148px, 1fr));
  gap: 1px; background: var(--edge); border: 1px solid var(--edge);
  margin: 40px 0 12px;
}
.stat { background: var(--surface); padding: 16px 18px; }
.stat b {
  display: block; font-family: Archivo, sans-serif; font-size: 1.85rem; font-weight: 700;
  letter-spacing: -.02em; font-variant-numeric: tabular-nums;
}
.stat span { color: var(--muted); font-size: .82rem; }

.panels { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 22px; margin: 44px 0 8px; }
.panel h2 { margin-bottom: 12px; color: var(--muted); font-size: .8rem; }
.panel ul { margin: 0; padding: 0; list-style: none; }
.panel li { padding: 9px 0; border-top: 1px solid var(--edge); display: flex; gap: 12px; align-items: baseline; }
.panel li:last-child { border-bottom: 1px solid var(--edge); }
.panel .k { font-family: "IBM Plex Mono", monospace; font-size: .78rem; color: var(--muted); white-space: nowrap; }
.panel .v { flex: 1; }
.note { color: var(--muted); font-size: .9rem; margin: 14px 0 0; }

.month { margin: 52px 0 0; }
.month > h2 { padding-bottom: 10px; border-bottom: 2px solid var(--ink); }
.rows { display: grid; }
.row {
  display: grid; grid-template-columns: 92px 150px 1fr; gap: 18px;
  padding: 13px 0; border-bottom: 1px solid var(--edge); align-items: baseline;
}
.row .when {
  font-family: "IBM Plex Mono", monospace; font-size: .82rem; color: var(--muted);
  font-variant-numeric: tabular-nums; white-space: nowrap;
}
.tag {
  font-family: "IBM Plex Mono", monospace; font-size: .7rem; letter-spacing: .06em;
  text-transform: uppercase; color: var(--muted);
}
.row.show .tag, .row.show .hook { color: var(--show); }
.row.show .hook { font-weight: 600; }
.row.award .tag { color: var(--accent); }
.row.season .tag { color: var(--season); }
.hook { }
.subject { display: block; color: var(--muted); font-size: .86rem; margin-top: 2px; }
.dcount {
  font-family: "IBM Plex Mono", monospace; font-size: .7rem; color: var(--show);
  border: 1px solid currentColor; padding: 1px 5px; margin-left: 8px; white-space: nowrap;
}

@media (max-width: 640px) {
  .row { grid-template-columns: 78px 1fr; }
  .row .tag { grid-column: 2; margin-bottom: -8px; }
  h1 { font-size: 1.9rem; }
}
"""


def _row(draft, show_start: date | None) -> str:
    tone = PILLAR_TONE.get(draft["pillar"], "")
    day = date.fromisoformat(draft["date"])
    badge = ""
    if draft["pillar"] == "tradeshow" and show_start:
        gap = (show_start - day).days
        badge = f'<span class="dcount">{"D-" + str(gap) if gap > 0 else "ON FLOOR"}</span>'
    subject = ""
    if draft["subject"] not in ("(brand)", draft["pillar_name"]):
        subject = f'<span class="subject">{html.escape(draft["subject"])}</span>'
    return (
        f'<div class="row {tone}">'
        f'<div class="when">{day:%d %a}</div>'
        f'<div class="tag">{html.escape(draft["pillar_name"])}</div>'
        f'<div><span class="hook">{html.escape(draft["hook"])}</span>{badge}{subject}</div>'
        "</div>"
    )


def build(catalog: Catalog, until: date) -> str:
    start = anchor_for(catalog, date.today())
    weeks = ((until - start).days // 7) + 2
    slots = [s for s in build_plan(catalog, start=start, weeks=weeks) if s.scheduled_for <= until]
    drafts = compose_all(slots, catalog)
    rows = [
        {
            "date": d.scheduled_for.isoformat(),
            "pillar": d.pillar.key,
            "pillar_name": d.pillar.name,
            "subject": d.slot.subject,
            "hook": d.hook,
        }
        for d in drafts
    ]

    profile = catalog.brand_profile
    show = next((s for s in profile.trade_shows if s.end >= start), None)
    counts = Counter(r["pillar_name"] for r in rows)

    months: list[str] = []
    current = None
    for row in rows:
        day = date.fromisoformat(row["date"])
        key = day.strftime("%Y-%m")
        if key != current:
            if current:
                months.append("</div></section>")
            current = key
            months.append(f'<section class="month"><h2>{day:%B %Y}</h2><div class="rows">')
        months.append(_row(row, show.start if show else None))
    if current:
        months.append("</div></section>")

    pillars = "".join(
        f'<li><span class="v">{html.escape(name)}</span>'
        f'<span class="k">{count}</span></li>'
        for name, count in counts.most_common()
    )
    sources = "".join(
        f'<li><span class="k">{k}</span><span class="v">{html.escape(v)}</span></li>'
        for k, v in (
            ("products", f"{len(catalog)} listings across {len(catalog.categories)} categories"),
            ("awards", ", ".join(r.name for r in profile.recognitions) or "none on file"),
            (
                "shows",
                ", ".join(f"{s.name} ({s.dates})" for s in profile.trade_shows if s.end >= start)
                or "none upcoming",
            ),
            ("proof", f"{len(profile.proof_points)} brand proof points"),
        )
    )

    generated = datetime.now().strftime("%d %B %Y")
    return f"""<title>HOMEDANT Content Calendar</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@600;700&family=IBM+Plex+Mono:wght@400;500&family=Source+Sans+3:wght@400;600&display=swap">
<style>{STYLE}</style>
<div class="wrap">
  <p class="eyebrow">Homedant USA Inc &middot; LinkedIn &middot; generated {generated}</p>
  <h1>Three posts a week to the end of 2026</h1>
  <p class="lede">Every post between {date.fromisoformat(rows[0]['date']):%d %B} and
  {until:%d %B}, drafted and checked before it is sent. The calendar is built from the product
  catalog and the brand profile, so it changes when they do.</p>

  <div class="summary">
    <div class="stat"><b>{len(rows)}</b><span>posts scheduled</span></div>
    <div class="stat"><b>{len(counts)}</b><span>content pillars</span></div>
    <div class="stat"><b>{counts.get('Trade show', 0)}</b><span>High Point posts</span></div>
    <div class="stat"><b>698</b><span>best post to date</span></div>
  </div>
  <p class="note">The award post drew 698 impressions against 18&ndash;42 for product posts, so
  recognition and the show lead the rotation.</p>

  <div class="panels">
    <div class="panel">
      <h2>Pillar mix</h2>
      <ul>{pillars}</ul>
    </div>
    <div class="panel">
      <h2>Built from</h2>
      <ul>{sources}</ul>
      <p class="note">Add a show, an award or a product and the calendar rebuilds around it.</p>
    </div>
  </div>

  {''.join(months)}
</div>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--until", required=True, help="last date to plan (YYYY-MM-DD)")
    parser.add_argument("--out", default="calendar.html")
    args = parser.parse_args()

    page = build(Catalog.load(), date.fromisoformat(args.until))
    Path(args.out).write_text(page, encoding="utf-8")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
