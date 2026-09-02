"""Pre-publication checks. Nothing gets posted that fails these."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .models import MAX_HOOK_CHARS, MAX_POST_CHARS, PostDraft

MIN_HASHTAGS = 2
MAX_HASHTAGS = 8

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


def validate(draft: PostDraft) -> list[Issue]:
    """Every problem with ``draft``. An empty list means it is publishable."""
    issues: list[Issue] = []
    text = draft.render()

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

    if not draft.cta.strip():
        issues.append(Issue("cta", "post has no call to action"))

    lowered = text.lower()
    for claim in UNSUPPORTABLE_CLAIMS:
        if claim in lowered:
            issues.append(Issue("claims", f"unsupportable claim: {claim!r}"))

    if draft.product is not None and draft.product.url not in text:
        issues.append(Issue("link", f"product {draft.product.asin} is referenced but not linked"))

    if re.search(r"\n{3,}", text):
        issues.append(Issue("spacing", "post contains a run of blank lines"))

    return issues


def validate_all(drafts) -> dict[int, list[Issue]]:
    """Issues per draft index, omitting drafts that passed."""
    return {index: issues for index, draft in enumerate(drafts) if (issues := validate(draft))}
