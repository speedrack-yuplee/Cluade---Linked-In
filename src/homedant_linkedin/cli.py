"""Command line entry point: plan, draft, validate, products."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta

from .catalog import Catalog
from .composer import compose_all
from .planner import build_plan
from .validators import validate


def next_monday(today: date | None = None) -> date:
    today = today or date.today()
    return today + timedelta(days=(7 - today.weekday()) % 7 or 7)


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
    return parser


def _slots(args, catalog: Catalog):
    return build_plan(catalog, start=args.start or next_monday(), weeks=args.weeks)


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
        subject = slot.product.short_title if slot.product else "(no product)"
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
        issues = validate(draft)
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


COMMANDS = {"plan": _cmd_plan, "draft": _cmd_draft, "validate": _cmd_validate, "products": _cmd_products}


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
