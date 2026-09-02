"""Command line entry point: plan, draft, validate, products."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path

from .catalog import Catalog
from .composer import compose_all
from .planner import build_plan
from .schedule import anchor_for, due_on
from .validators import validate


def parse_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise argparse.ArgumentTypeError(f"expected YYYY-MM-DD, got {value!r}") from None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="homedant_linkedin",
        description="Plan, draft and check HOMEDANT USA's LinkedIn posts.",
    )
    parser.add_argument("--catalog", help="path to a products.json (defaults to the bundled catalog)")
    parser.add_argument("--marketplace", help="restrict to one marketplace, e.g. US")
    sub = parser.add_subparsers(dest="command", required=True)

    for name, help_text in (
        ("plan", "show the posting calendar"),
        ("draft", "render every post in the plan"),
        ("validate", "check every drafted post, exit 1 on any issue"),
    ):
        sp = sub.add_parser(name, help=help_text)
        sp.add_argument("--start", type=parse_date, help="first posting date (YYYY-MM-DD)")
        sp.add_argument("--weeks", type=int, default=4, help="how many weeks to plan (default 4)")
        if name != "validate":
            sp.add_argument("--json", action="store_true", help="emit JSON instead of text")

    sub.add_parser("products", help="list the catalog")

    cal = sub.add_parser("calendar", help="the whole plan up to an end date")
    cal.add_argument("--until", type=parse_date, required=True, help="last date to plan (YYYY-MM-DD)")
    cal.add_argument("--json", action="store_true", help="emit JSON instead of text")

    nxt = sub.add_parser(
        "next",
        help="write today's post and image for an unattended run",
    )
    nxt.add_argument("--date", type=parse_date, help="the day to post for (default today)")
    nxt.add_argument("--out", default="out", help="directory to write post.txt and post.png into")
    nxt.add_argument(
        "--require-slot",
        action="store_true",
        help="exit 3 when nothing is scheduled, instead of exiting 0 quietly",
    )
    return parser


def _slots(args, catalog: Catalog):
    """The plan the commands show.

    Without an explicit --start this is the same calendar the unattended run
    posts from, so `plan` and `next` can never disagree about which post falls
    on which day.
    """
    start = args.start or anchor_for(catalog, date.today())
    return build_plan(catalog, start=start, weeks=args.weeks)


def _cmd_plan(args, catalog: Catalog, out) -> int:
    slots = _slots(args, catalog)
    if getattr(args, "json", False):
        print(
            json.dumps(
                [
                    {
                        "date": s.scheduled_for.isoformat(),
                        "pillar": s.pillar.key,
                        "asin": s.product.asin if s.product else None,
                    }
                    for s in slots
                ],
                indent=2,
            ),
            file=out,
        )
        return 0
    print(f"{catalog.company} — {len(slots)} posts over {args.weeks} week(s)\n", file=out)
    for slot in slots:
        subject = slot.subject
        print(
            f"{slot.scheduled_for:%Y-%m-%d %a}  {slot.pillar.name:<26}  {subject}",
            file=out,
        )
    return 0


def _cmd_draft(args, catalog: Catalog, out) -> int:
    drafts = compose_all(_slots(args, catalog), catalog)
    if getattr(args, "json", False):
        print(
            json.dumps(
                [
                    {
                        "date": d.scheduled_for.isoformat(),
                        "pillar": d.pillar.key,
                        "text": d.render(),
                        "chars": d.char_count,
                    }
                    for d in drafts
                ],
                indent=2,
            ),
            file=out,
        )
        return 0
    for draft in drafts:
        print(f"=== {draft.scheduled_for:%Y-%m-%d} · {draft.pillar.name} · {draft.char_count} chars ===", file=out)
        print(draft.render(), file=out)
        print(file=out)
    return 0


def _cmd_validate(args, catalog: Catalog, out) -> int:
    drafts = compose_all(_slots(args, catalog), catalog)
    failures = 0
    for draft in drafts:
        issues = validate(draft, catalog.brand_profile)
        label = f"{draft.scheduled_for:%Y-%m-%d} {draft.pillar.key}"
        if issues:
            failures += 1
            print(f"FAIL {label}", file=out)
            for issue in issues:
                print(f"     {issue}", file=out)
        else:
            print(f"OK   {label}", file=out)
    print(f"\n{len(drafts) - failures}/{len(drafts)} posts ready to publish", file=out)
    return 1 if failures else 0


def _cmd_products(args, catalog: Catalog, out) -> int:
    print(f"{catalog.brand}: {len(catalog)} products across {len(catalog.categories)} categories\n", file=out)
    for product in catalog:
        print(f"{product.asin}  {product.marketplace}  {product.category:<18}  {product.short_title}", file=out)
    return 0


def _cmd_calendar(args, catalog: Catalog, out) -> int:
    """Every post from the anchor to --until, grouped by month."""
    start = anchor_for(catalog, date.today())
    weeks = ((args.until - start).days // 7) + 2
    slots = [s for s in build_plan(catalog, start=start, weeks=weeks) if s.scheduled_for <= args.until]
    drafts = compose_all(slots, catalog)

    if args.json:
        print(
            json.dumps(
                [
                    {
                        "date": d.scheduled_for.isoformat(),
                        "pillar": d.pillar.key,
                        "pillar_name": d.pillar.name,
                        "subject": d.slot.subject,
                        "hook": d.hook,
                        "asin": d.product.asin if d.product else None,
                        "chars": d.char_count,
                    }
                    for d in drafts
                ],
                indent=2,
                ensure_ascii=False,
            ),
            file=out,
        )
        return 0

    month = None
    for draft in drafts:
        if draft.scheduled_for.strftime("%Y-%m") != month:
            month = draft.scheduled_for.strftime("%Y-%m")
            print(f"\n{draft.scheduled_for:%B %Y}", file=out)
            print("-" * 78, file=out)
        print(
            f"{draft.scheduled_for:%m-%d %a}  {draft.pillar.name:<24}  {draft.hook[:44]}",
            file=out,
        )
    print(f"\n{len(drafts)} posts to {args.until:%Y-%m-%d}", file=out)
    return 0


def _cmd_next(args, catalog: Catalog, out) -> int:
    """Write the post due today, or say that nothing is due.

    Exit codes: 0 wrote a post (or nothing was due), 2 the post failed
    validation and must not be sent, 3 nothing was due and the caller asked to
    be told about it.
    """
    day = args.date or date.today()
    draft = due_on(catalog, day)
    if draft is None:
        print(f"nothing scheduled for {day:%Y-%m-%d}", file=out)
        return 3 if args.require_slot else 0

    issues = validate(draft, catalog.brand_profile)
    if issues:
        print(f"{day:%Y-%m-%d} {draft.pillar.key} failed validation:", file=out)
        for issue in issues:
            print(f"  {issue}", file=out)
        return 2

    directory = Path(args.out)
    directory.mkdir(parents=True, exist_ok=True)
    text_path = directory / "post.txt"
    text_path.write_text(draft.render() + "\n", encoding="utf-8")

    from .image import fetch_product_image, render  # late import: only this command needs Pillow

    product = draft.product
    photo = fetch_product_image(product.image_url) if product else None
    if product and photo is None and product.image_url:
        print("note: product photo unavailable, using the type-only layout", file=out)
    image_path = render(draft, directory / "post.png", photo=photo)
    (directory / "post.json").write_text(
        json.dumps(
            {
                "date": draft.scheduled_for.isoformat(),
                "pillar": draft.pillar.key,
                "pillar_name": draft.pillar.name,
                "subject": draft.slot.subject,
                "chars": draft.char_count,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"{day:%Y-%m-%d} {draft.pillar.name}: {draft.slot.subject}", file=out)
    print(f"wrote {text_path} and {image_path}", file=out)
    return 0


COMMANDS = {
    "plan": _cmd_plan,
    "draft": _cmd_draft,
    "validate": _cmd_validate,
    "products": _cmd_products,
    "next": _cmd_next,
    "calendar": _cmd_calendar,
}


def main(argv: list[str] | None = None, out=None) -> int:
    out = out or sys.stdout
    args = build_parser().parse_args(argv)
    catalog = Catalog.load(args.catalog)
    if args.marketplace:
        catalog = catalog.filter(marketplace=args.marketplace)
        if len(catalog) == 0:
            print(f"no products in marketplace {args.marketplace}", file=out)
            return 1
    return COMMANDS[args.command](args, catalog, out)
