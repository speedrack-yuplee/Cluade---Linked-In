"""Pre-publication checks. Nothing gets posted that fails these."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .models import MAX_HOOK_CHARS, MAX_POST_CHARS, Brand, PostDraft

MIN_HASHTAGS = 3
MAX_HASHTAGS = 10
"""The account's own award post carried eight; ten is the ceiling before a
post reads as tag stuffing."""

BRAND_HASHTAG = "HOMEDANT"

CTA_INTENTS: tuple[str, ...] = (
    "connect",
    "message me",
    "contact",
    "sample",
    "line sheet",
    "quote",
    "booth",
    "meet",
    "send",
    "ask",
)
"""A B2B post has to ask for a conversation. A link to buy is not a CTA here."""

UNSUPPORTABLE_CLAIMS: tuple[str, ...] = (
    "best in the world",
    "#1 on amazon",
    "number one on amazon",
    "guaranteed for life",
    "lifetime guarantee",
    "unbreakable",
    "cheapest",
)
"""Superlatives we cannot substantiate, and that Amazon's own policy bars."""


@dataclass(frozen=True)
class Issue:
    """One validation failure, tied to the rule that produced it."""

    rule: str
    message: str

    def __str__(self) -> str:
        return f"[{self.rule}] {self.message}"


def validate(draft: PostDraft, brand: Brand | None = None) -> list[Issue]:
    """Every problem with ``draft``. An empty list means it is publishable."""
    issues: list[Issue] = []
    text = draft.render()
    lowered = text.lower()

    if draft.char_count > MAX_POST_CHARS:
        issues.append(
            Issue("length", f"post is {draft.char_count} characters, over the {MAX_POST_CHARS} limit")
        )
    if not draft.hook.strip():
        issues.append(Issue("hook", "post has no hook"))
    elif len(draft.hook) > MAX_HOOK_CHARS:
        issues.append(
            Issue("hook", f"hook is {len(draft.hook)} characters and will truncate past {MAX_HOOK_CHARS}")
        )

    count = len(draft.hashtags)
    if count < MIN_HASHTAGS:
        issues.append(Issue("hashtags", f"{count} hashtag(s); at least {MIN_HASHTAGS} expected"))
    elif count > MAX_HASHTAGS:
        issues.append(Issue("hashtags", f"{count} hashtags; at most {MAX_HASHTAGS} allowed"))
    if BRAND_HASHTAG not in draft.hashtags:
        issues.append(Issue("hashtags", f"#{BRAND_HASHTAG} is missing"))

    if not draft.question.strip():
        issues.append(Issue("question", "post asks the reader nothing"))
    elif not draft.question.rstrip().endswith("?"):
        issues.append(Issue("question", "the closing question is not a question"))

    if not draft.cta.strip():
        issues.append(Issue("cta", "post has no call to action"))
    elif not any(intent in draft.cta.lower() for intent in CTA_INTENTS):
        issues.append(Issue("cta", "call to action does not ask for a conversation"))

    if brand is not None and brand.company.lower() not in lowered:
        issues.append(Issue("company", f"post never names {brand.company}"))

    if brand is not None:
        for term, explainers in brand.coined_terms.items():
            if term.lower() not in lowered:
                continue
            # Remove the term first: "HANDiLOCK" contains "lock", so a naive
            # search would let the name explain itself.
            rest = lowered.replace(term.lower(), " ")
            if not any(e.lower() in rest for e in explainers):
                issues.append(
                    Issue(
                        "jargon",
                        f"{term!r} is our own name and the post never says what it is; "
                        f"add one of: {', '.join(explainers)}",
                    )
                )

    for claim in UNSUPPORTABLE_CLAIMS:
        if claim in lowered:
            issues.append(Issue("claims", f"unsupportable claim: {claim!r}"))

    if "amazon.com/dp/" in lowered or "amazon.ca/dp/" in lowered:
        issues.append(Issue("channel", "a retail listing link belongs in a consumer post, not a B2B one"))

    if re.search(r"\n{3,}", text):
        issues.append(Issue("spacing", "post contains a run of blank lines"))

    return issues


def validate_all(drafts, brand: Brand | None = None) -> dict[int, list[Issue]]:
    """Issues per draft index, omitting drafts that passed."""
    return {
        index: issues for index, draft in enumerate(drafts) if (issues := validate(draft, brand))
    }
