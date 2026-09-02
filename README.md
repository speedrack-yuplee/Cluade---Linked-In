# HOMEDANT USA — LinkedIn AI Agent

Plans, drafts and checks the LinkedIn posts for HOMEDANT USA's storage and
shelving line before anything is published.

The agent works from a catalog of real HOMEDANT listings (`src/homedant_linkedin/data/products.json`),
rotates a fixed set of content pillars across a posting calendar, renders each
slot into a post draft, and refuses to pass anything that breaks LinkedIn's
limits or makes a claim the brand cannot substantiate.

## Install

```bash
pip install -e ".[dev]"
```

Or run straight from the source tree:

```bash
PYTHONPATH=src python -m homedant_linkedin plan
```

## Commands

| Command | What it does |
| --- | --- |
| `plan` | Print the posting calendar: date, pillar, product |
| `draft` | Render every post in the plan, ready to paste |
| `validate` | Check every draft; exits `1` if any post has an issue |
| `products` | List the catalog |

Common flags: `--start YYYY-MM-DD`, `--weeks N`, `--marketplace US`,
`--catalog path/to/products.json`, and `--json` on `plan` and `draft`.

```bash
PYTHONPATH=src python -m homedant_linkedin plan --start 2026-09-08 --weeks 4
PYTHONPATH=src python -m homedant_linkedin draft --weeks 1
PYTHONPATH=src python -m homedant_linkedin validate --weeks 4
```

## Content pillars

Posts rotate through four pillars, two posts a week on Tuesday and Thursday:

- **Problem we keep hearing** — a storage problem a buyer described, and the product that answers it
- **Product spotlight** — one listing's design decisions and who it is built for
- **How it is built** — a manufacturing or design choice behind the product
- **Behind the operation** — an operating lesson from selling across Amazon marketplaces (no product)

Products round-robin independently of the pillar rotation, so a product only
repeats once the whole catalog has been used.

## Validation rules

`validate` fails a draft that:

- exceeds LinkedIn's 3,000 character body limit
- has a hook over 210 characters (it would truncate behind "…see more")
- carries fewer than 2 or more than 8 hashtags
- has no call to action
- contains an unsupportable superlative ("cheapest", "#1 on Amazon", "lifetime guarantee", …)
- names a product without linking its listing
- contains a run of blank lines

## Catalog

`products.json` holds the listings the agent may promote. Each entry needs
`asin`, `sku`, `title`, `category`, `marketplace` and `url`; `short_name`,
`highlights` and `audience` are what the post copy is actually written from.
Point `--catalog` at your own file to plan against a different set.

## Tests

```bash
PYTHONPATH=src pytest
```
