# HOMEDANT USA — LinkedIn AI Agent

Plans, drafts and checks the LinkedIn posts for Homedant USA Inc before
anything is published.

The account sells **B2B**: retail buyers, distributors, hospitality specifiers
and multifamily developers. Posts are written for those readers, not for the
Amazon shopper, and they close by asking for a conversation rather than
linking a listing.

The agent works from a brand profile (`src/homedant_linkedin/data/brand.json`)
and a product catalog (`src/homedant_linkedin/data/products.json`), rotates a
set of content pillars across a posting calendar, renders each slot into a post
draft, and refuses to pass anything that breaks LinkedIn's limits or makes a
claim the brand cannot substantiate.

## What the account's own history says

| Post | Impressions | Reactions |
| --- | ---: | ---: |
| Retailers' Choice Awards win at the National Hardware Show | **698** | 10 |
| RangeMe Award Winner Collection | 42 | 1 |
| Open wardrobe system for hotel and residential projects | 18 | — |

Third-party recognition outperformed product-led posts by 15 to 35 times, so
the plan leads every cycle with it. See `content/posts/` for the source.

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
| `next` | Write today's post and image into `out/` for an unattended run |

Common flags: `--start YYYY-MM-DD`, `--weeks N`, `--marketplace US`,
`--catalog path/to/products.json`, and `--json` on `plan` and `draft`.

```bash
PYTHONPATH=src python -m homedant_linkedin plan --start 2026-09-08 --weeks 4
PYTHONPATH=src python -m homedant_linkedin draft --weeks 1
PYTHONPATH=src python -m homedant_linkedin validate --weeks 4
```

## Content pillars

Posts rotate through six pillars, two posts a week on Tuesday and Thursday:

| Pillar | Subject | Notes |
| --- | --- | --- |
| Third-party recognition | An award on file | Leads the rotation |
| Trade show | An upcoming show | Dropped once the show has closed |
| Project solution | A project-tagged product | Hospitality and multifamily |
| Retail fit | A retail-tagged product | Merchandising, case pack, planogram |
| Made in Korea | Any product | Manufacturing and design control |
| Supply and logistics | — | Warehousing and lead time |

Each subject pool round-robins on its own counter, so a subject only repeats
once its pool is exhausted. Product pillars draw only from products tagged for
that segment — a hospitality hook over a pallet-configuration product reads as
a mismatch.

**Trade shows must be kept current.** A show whose end date has passed is
dropped from the rotation and the pillar falls out until an upcoming show is
added to `brand.json`. Both shows currently on file (NY NOW Summer 2026,
National Hardware Show 2026) have closed.

## Validation rules

`validate` fails a draft that:

- exceeds LinkedIn's 3,000 character body limit
- has a hook over 210 characters (it would truncate behind "…see more")
- carries fewer than 3 or more than 10 hashtags, or omits `#HOMEDANT`
- has no call to action, or a call to action that does not ask for a conversation
- never names Homedant USA Inc (every real post tags the company)
- links a retail listing — that is a consumer CTA, not a B2B one
- contains an unsupportable superlative ("cheapest", "#1 on Amazon", "lifetime guarantee", …)
- contains a run of blank lines

## Data

`brand.json` holds who is posting and the facts every post can draw on: the
company name as it is tagged on LinkedIn, the audiences, the proof points, and
the recognitions and trade shows the plan schedules against. **Add each new
award and each upcoming show here** — that is what keeps the top-performing
pillar supplied.

`products.json` holds the products the agent may promote. Each entry needs
`asin`, `sku`, `title`, `category`, `marketplace` and `url`; `short_name`,
`highlights`, `audience`, `retail_fit` and `segments` are what the post copy is
actually written from. Point `--catalog` at your own file to plan against a
different set.

## Weekly automation

`.github/workflows/linkedin-draft.yml` runs three times a week — Monday,
Wednesday and Friday at 09:00 KST — and sends that day's post and image to
Telegram. Nothing is published automatically; the draft arrives in the chat and
a person posts it.

The run is a straight line: `next` builds the post from the calendar, validates
it, renders the image, and `scripts/send_telegram.py` delivers both. A post that
fails validation exits non-zero and is never sent.

The rotation is counted from `plan_anchor` in `brand.json`, not from the day the
job happens to run, so a missed or re-run job lands on the same slot the
calendar shows.

### Setting it up

Add two repository secrets under **Settings → Secrets and variables → Actions**:

| Secret | Where it comes from |
| --- | --- |
| `TELEGRAM_BOT_TOKEN` | BotFather, when the bot was created |
| `TELEGRAM_CHAT_ID` | `https://api.telegram.org/bot<token>/getUpdates` after messaging the bot |

Secrets are not readable from the repository, so a public repository is fine.
Then run the workflow once by hand (**Actions → LinkedIn draft → Run
workflow**) to confirm the message arrives.

## Images

`image.py` renders each post into a 1200x1200 PNG from the same draft the text
comes from: the HOMEDANT wordmark over its tagline rule, the hook as the
headline, up to three proof points, and a footer band carrying the show or the
award. No external service is involved.

## Existing posts

`content/posts/` holds the LinkedIn posts that have already been published.
Drop them in as markdown files and the drafts can be written to match that
voice rather than the default template voice. See
[`content/posts/README.md`](content/posts/README.md) for the file format and
for how to add one from the GitHub web UI.

## Tests

```bash
PYTHONPATH=src pytest
```
