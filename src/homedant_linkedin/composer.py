"""Rendering a scheduled slot into a LinkedIn post draft.

The templates follow the account's own posts, which run as prose rather than
bullet lists: a hook that states the news or asks the reader's question, a
paragraph giving it meaning, a paragraph on what the shelving does, an
invitation to connect, and a thank-you where a third party is involved.

The three lines the image carries are composed here too, so the picture argues
what the post argues rather than restating the same brand facts under a
different headline every week.
"""

from __future__ import annotations

from .catalog import Catalog
from .models import PostDraft, Slot

CONNECT_CTA = (
    "We look forward to connecting with {audiences} who are looking for practical and "
    "dependable storage solutions."
)


def _paragraphs(*blocks: str) -> str:
    """Join blocks with a blank line, dropping the ones that came out empty.

    A composer that skips an optional line must not leave a gap behind it.
    """
    return "\n\n".join(block.strip() for block in blocks if block and block.strip())


def _sentence(text: str) -> str:
    """``text`` with its first letter raised and the rest left alone.

    str.capitalize lowercases everything after the first character, which turns
    "a university in Korea" into "a university in korea".
    """
    return text[:1].upper() + text[1:]


def _and_list(items: list[str]) -> str:
    if len(items) < 2:
        return items[0] if items else ""
    if len(items) == 2:
        return " and ".join(items)
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def _load_clause(product) -> str:
    """The unit's own load rating, where the catalog states one.

    Ratings differ by model and by whether a LiftBeam is fitted, so a post
    never carries a figure that was not recorded for the product it is about.
    """
    if not product or not product.load_per_tier:
        return ""
    total = f" and {product.load_total}" if product.load_total else ""
    return f", and it still carries {product.load_per_tier} on a tier{total}"


# One line, answerable from the reader's own desk, and worth reading when it
# is answered. "What do you think?" is none of those.
QUESTIONS: dict[str, tuple[str, ...]] = {
    "recognition": (
        "Which of these decides it in your category: the load rating, the assembly time, or the finish?",
        "What is the first spec you check when a new shelving supplier reaches out?",
    ),
    "tradeshow": (
        "Which day are you walking the floor?",
        "What are you sourcing at this one?",
        "Who else should we be talking to while we are there?",
    ),
    "reference": (
        "Where does the storage go in your buildings when there is no room left for it?",
        "What is the longest you have waited on a fit-out that should have taken an afternoon?",
    ),
    "project": (
        "Where does storage run out first in your units: the entry, the bathroom, or the closet?",
        "How far ahead of handover do you specify storage?",
    ),
    "retail": (
        "How many facings does storage get in a four foot bay in your stores?",
        "What box size breaks your current shelving?",
    ),
    "manufacturing": (
        "Boltless or bolted, which comes back to you less often?",
        "How much of an assembly complaint is the instructions rather than the product?",
    ),
    "seasonal": (
        "When does your Q4 storage set go on the floor?",
        "Does holiday storage sit in seasonal or in home organization for you?",
    ),
    "supply": (
        "Where is your sourcing concentrated right now?",
        "How far out are you quoting lead times this quarter?",
    ),
}


def _question(slot: Slot) -> str:
    options = QUESTIONS.get(slot.pillar.key, ())
    return _variant(slot, options) if options else ""


def _variant(slot: Slot, options: tuple[str, ...]) -> str:
    """One of several openings, rotated by the date itself.

    A hook that repeats stops being read, so each pillar keeps a small set. The
    week was the wrong counter, and so was the date: posting days sit two and
    three days apart, so any modulo of either eventually lands two neighbours
    on the same line. Counting the pillar's own turns cannot.
    """
    return options[slot.turn % len(options)]


def _points(slot: Slot, options: tuple[tuple[str, ...], ...]) -> tuple[str, ...]:
    """The image's three lines, rotated in step with the hook.

    Passed the same number of options as the hook has, so the picture and the
    opening line are always the same argument.
    """
    return _variant(slot, options)


def _hashtags(slot: Slot, extra: tuple[str, ...] = ()) -> tuple[str, ...]:
    """Pillar hashtags plus any the subject carries, in order, without repeats."""
    seen: dict[str, None] = {}
    for tag in (*extra, *slot.pillar.hashtags):
        seen.setdefault(tag, None)
    return tuple(seen)


def _next_show(catalog: Catalog, after):
    """The next show that has not finished, or None."""
    upcoming = [s for s in catalog.brand_profile.trade_shows if s.end >= after]
    return min(upcoming, key=lambda s: s.start) if upcoming else None


def _compose_recognition(slot: Slot, catalog: Catalog) -> PostDraft:
    award = slot.recognition
    profile = catalog.brand_profile

    if award.posted_on:
        # Already announced. Repeating the announcement would duplicate a post
        # that is still live, so the award is used as the reason for what is
        # next instead.
        show = _next_show(catalog, slot.scheduled_for)
        where = f" at {show.name}" if show else ""
        return PostDraft(
            slot=slot,
            hook=(
                f"What does a {award.award or award.name} actually change? "
                "It changes who picks up the phone."
            ),
            body=_paragraphs(
                f"Since {profile.company} was recognised at the {award.date.year} {award.event}, "
                "the conversations have started with the product rather than with an introduction. "
                "That is the whole value of it.",
                profile.capability,
                f"You can see the range for yourself{where}."
                if show
                else "The range is the same one the judges looked at.",
            ),
            cta=CONNECT_CTA.format(audiences=profile.audience_phrase),
            question=_question(slot),
            hashtags=_hashtags(slot, award.hashtags),
            points=(
                f"{award.award or award.name}, {award.event} {award.date.year}",
                f"Selected by {award.org}",
                f"The same range on the floor at {show.name}"
                if show
                else "The same range the judges looked at",
            ),
        )

    where = f" in {award.city}" if award.city else ""
    return PostDraft(
        slot=slot,
        hook=(
            f"We are proud to share that {profile.brand} has been selected as a "
            f"{award.award or award.name} at the {award.date.year} {award.event}{where}! \U0001f389"
        ),
        body=_paragraphs(
            f"This recognition is a meaningful milestone for {profile.company} as we continue "
            f"introducing {profile.positioning}.",
            profile.capability,
        ),
        cta=CONNECT_CTA.format(audiences=profile.audience_phrase),
        closing=(
            f"Thank you to {_and_list(list(award.thanks))} for this recognition."
            if award.thanks
            else f"Thank you to {award.org} for this recognition."
        ),
        question=_question(slot),
        hashtags=_hashtags(slot, award.hashtags),
        points=(
            award.award or award.name,
            f"{award.event}, {award.date.year}" + (f", {award.city}" if award.city else ""),
            profile.proof_points[0],
        ),
    )


def _show_hook(show, day, brand: str, turn: int = 0) -> str:
    """The opening line, in the register the account already uses.

    The countdown form ("2 Days to Go") is copied from the NY NOW post; the
    closer the show, the more urgent the ask to book a meeting.
    """
    days = show.days_until(day)
    where = f", {show.location}" if show.booth else ""
    if show.is_running(day):
        return f"We are on the floor at {show.name}{where}. Come and find us."
    if days <= 7:
        nights = "1 Day" if days == 1 else f"{days} Days"
        return f"\u23f3 {nights} to Go \u2014 see you at {show.name}{where}!"
    if days <= 20:
        stand = f" We are at {show.location}." if show.booth else ""
        return f"Two weeks out from {show.name}, and the calendar is filling up.{stand}"
    far = (
        f"{brand} is coming to {show.name}{where}!",
        f"We are taking the full boltless range to {show.name}{where}. "
        "The calendar opens now.",
    )
    return far[turn % len(far)]


def _compose_tradeshow(slot: Slot, catalog: Catalog) -> PostDraft:
    show = slot.show
    profile = catalog.brand_profile
    day = slot.scheduled_for
    running = show.is_running(day)

    if running:
        second = (
            "We are showing our full boltless steel shelving range, and there is a table free for "
            "anyone who wants to sit down with dimensions and a pack spec."
        )
        cta = f"Message me and I will come and meet you at the entrance. \u2014 {profile.author}"
        points = (
            "The full boltless steel shelving range is up on the stand",
            "A table free for anyone who wants to sit down with dimensions and a pack spec",
            f"Message {profile.author} and we will meet you at the entrance",
        )
    else:
        second = (
            "Bring the dimensions you are working with and we will tell you on the spot whether we "
            "already have a unit that fits, or whether it is a tooling change."
        )
        cta = (
            "If you are attending, message me and we will book a time before the calendar fills. "
            f"\u2014 {profile.author}"
        )
        points = (
            "Bring your dimensions and we will tell you on the spot whether a unit fits",
            "Boltless steel shelving, assembled by hand in about ten minutes",
            f"Meetings are booking now \u2014 message {profile.author} to hold a time",
        )

    return PostDraft(
        slot=slot,
        hook=_show_hook(show, day, profile.brand, slot.turn),
        body=_paragraphs(
            f"{profile.company} is at {show.venue}, {show.dates}, with our {profile.offer}.",
            profile.capability,
            second,
        ),
        cta=cta,
        closing=f"We also showed at {profile.show_history} this year."
        if profile.exhibited_at and not running
        else "",
        question=_question(slot),
        hashtags=_hashtags(slot, show.hashtags),
        points=points,
    )


def _compose_reference(slot: Slot, catalog: Catalog) -> PostDraft:
    """A room it went into, and what the install actually took.

    The photograph does the arguing, so the text stays out of its way: what the
    building needed, what went in, and the one thing about it a specifier would
    not have expected.
    """
    site = slot.installation
    profile = catalog.brand_profile

    return PostDraft(
        slot=slot,
        hook=_variant(
            slot,
            (
                f"This is {site.room} at {site.subject}. The shelving went up by hand, "
                "in an afternoon.",
                f"{_sentence(site.subject)} needed {site.room} to hold more, "
                "without a contractor and without touching the building.",
            ),
        ),
        body=_paragraphs(
            site.situation,
            "So the frame goes together by hand. HANDiLOCK joints lock the uprights to the "
            "beams with no bolts and no tools, which means no drilling, no noise and nothing "
            "to lose on the floor. Tier heights move afterwards, in 1.18 inch steps, as what "
            "the room holds changes.",
            f"{profile.company} has been making steel shelving in its own Korean factory "
            f"since {profile.founded}. Rooms like this one are where it ends up.",
        ),
        cta=(
            "Send me the room dimensions and what has to go in it, and I will come back with "
            f"a layout and a quote. \u2014 {profile.author}"
        ),
        question=_question(slot),
        hashtags=_hashtags(slot, site.hashtags),
        points=(
            _sentence(site.room),
            "Assembled by hand, no bolts and no drilling",
            "Tier heights adjust in 1.18 inch steps",
        ),
    )


def _compose_project(slot: Slot, catalog: Catalog) -> PostDraft:
    product = slot.product
    profile = catalog.brand_profile
    return PostDraft(
        slot=slot,
        hook=_variant(
            slot,
            (
                "How can hotels and residential projects provide more storage without making "
                "rooms feel crowded?",
                "The storage in a guest room is decided long before the guest arrives. Usually "
                "by whoever signed off the millwork budget.",
                "Every multifamily unit has a corner nobody specified. That is where the "
                "complaints come from.",
            ),
        ),
        body=_paragraphs(
            f"At {profile.company}, we build for the room as it already is. "
            f"{product.sentence_name} was designed for {product.audience}, and it goes in without "
            "construction work, without a contractor, and without touching the finishes.",
            f"{_and_list(list(product.highlights))}.".capitalize(),
            product.retail_fit and f"For specifiers: {product.retail_fit}.",
        ),
        cta="Send me your floor plan and unit count and we will come back with a layout and a quote.",
        question=_question(slot),
        hashtags=_hashtags(slot),
        points=(
            "Goes in with no construction work and no damage to the finishes",
            *product.highlights[:2],
        ),
    )


def _compose_retail(slot: Slot, catalog: Catalog) -> PostDraft:
    product = slot.product
    profile = catalog.brand_profile
    return PostDraft(
        slot=slot,
        hook=_variant(
            slot,
            (
                "Ever struggled to fit diverse inventory perfectly onto your shelves?",
                "A shelf that only fits one box size is a planogram problem waiting to happen.",
                "Buyers do not ask how strong the shelf is. They ask how many of them fit on a "
                "pallet.",
            ),
        ),
        body=_paragraphs(
            f"At {profile.company}, we understand that every product has its own dimensions. "
            f"{product.sentence_name} adjusts to them rather than the other way round, and it was "
            f"built for {product.audience}.",
            f"{_and_list(list(product.highlights))}.".capitalize(),
            product.retail_fit and f"On the floor: {product.retail_fit}.",
        ),
        cta="Message me for a line sheet, case pack and pallet configuration.",
        question=_question(slot),
        hashtags=_hashtags(slot),
        points=(
            "Shelf height adjusts in 1.18 inch intervals, so the shelf fits the box",
            *product.highlights[:2],
        ),
    )


def _compose_manufacturing(slot: Slot, catalog: Catalog) -> PostDraft:
    product = slot.product
    profile = catalog.brand_profile
    return PostDraft(
        slot=slot,
        hook=_variant(
            slot,
            (
                "A boltless frame sounds like a shortcut. It is the harder engineering choice.",
                "The fastest way to lose a customer is an assembly step they cannot finish.",
                "We own the factory. That is not a marketing line, it is why a spec change takes "
                "a phone call.",
                "Turn the board over and the shelf changes colour. One SKU, two rooms it belongs in.",
            ),
        ),
        body=_paragraphs(
            "Every fastener you remove is a tolerance you now have to hold in the steel itself, "
            "because the joint has to carry the load the bolt used to carry.",
            f"Ours is called HANDiLOCK. It goes together by hand in about ten minutes, with no "
            f"tools, no drilling and no noise{_load_clause(product)}, and it is engineered and "
            f"inspected in {profile.company}'s own Korean factory rather than bought in. We have "
            f"been making steel shelving since {profile.founded}, and that joint is the part we "
            "have spent the longest getting right.",
            profile.capability,
        ),
        cta="If you are evaluating a supplier, ask me for our test reports. We will send them.",
        question=_question(slot),
        hashtags=_hashtags(slot),
        points=_points(
            slot,
            (
                (
                    "HANDiLOCK joints carry the load the bolt used to carry",
                    product.highlights[0],
                    "Engineered and inspected in our own Korean factory",
                ),
                (
                    "Assembled by hand in about ten minutes",
                    "No tools, no drilling and no noise",
                    "Fewer parts is fewer ways to get it wrong",
                ),
                (
                    f"Our own factory in Korea since {profile.founded}",
                    "A specification change is a phone call, not a negotiation",
                    "Engineered and inspected in-house rather than bought in",
                ),
                (
                    "Reversible board: light wood on one face, soft white on the other",
                    "One SKU, two rooms it belongs in",
                    "Laminated on all six sides, anti-scratch and waterproof",
                ),
            ),
        ),
    )


def _compose_supply(slot: Slot, catalog: Catalog) -> PostDraft:
    profile = catalog.brand_profile
    return PostDraft(
        slot=slot,
        hook=_variant(
            slot,
            (
                "Buyers ask about the product first and the supply chain second. The second "
                "answer decides it.",
                "A reset date does not move because a vessel did. That is what domestic stock "
                "is for.",
                "The hardest question in a vendor meeting is not about the product. It is "
                "\u201ccan you actually ship it?\u201d",
            ),
        ),
        body=_paragraphs(
            f"{profile.company} holds stock in CA and GA warehouses, so a domestic order does not "
            "wait on an ocean container, and a reset date does not move because a vessel did.",
            "Manufacturing sits in our own Korean factory, which means a specification change is a "
            "conversation with the plant rather than a negotiation with a contract manufacturer.",
            f"We showed at {profile.show_history} this year, and the questions were the same at "
            "every one of them.",
            profile.capability,
        ),
        cta=CONNECT_CTA.format(audiences=profile.audience_phrase),
        question=_question(slot),
        hashtags=_hashtags(slot),
        points=(
            "CA and GA warehouses, so a domestic order does not wait on a container",
            f"Our own Korean factory since {profile.founded}",
            "A specification change is a conversation with the plant",
        ),
    )


def _compose_seasonal(slot: Slot, catalog: Catalog) -> PostDraft:
    product = slot.product
    profile = catalog.brand_profile
    return PostDraft(
        slot=slot,
        hook=_variant(
            slot,
            (
                "Holiday decor is a storage category. It just does not look like one on the "
                "planogram.",
                "The same shelving unit sells twice a year: once to put the decorations up, "
                "once to put them away.",
                "Garages fill up in November and get sorted out in January. Both are shelving "
                "moments.",
            ),
        ),
        body=_paragraphs(
            f"At {profile.company}, we see the same pattern every year. Storage is the demand "
            "holiday decor creates, and the buy that serves it happens months earlier.",
            f"{product.sentence_name} carries the load either way, and it was built for "
            f"{product.audience}.",
            product.retail_fit and f"On the floor: {product.retail_fit}.",
        ),
        cta="Message me for a line sheet if you are still building your Q4 storage set.",
        question=_question(slot),
        hashtags=_hashtags(slot),
        points=(
            "The same unit sells twice a year: decorations up, decorations away",
            *product.highlights[:2],
        ),
    )


_COMPOSERS = {
    "recognition": _compose_recognition,
    "reference": _compose_reference,
    "tradeshow": _compose_tradeshow,
    "project": _compose_project,
    "retail": _compose_retail,
    "manufacturing": _compose_manufacturing,
    "seasonal": _compose_seasonal,
    "supply": _compose_supply,
}

_SUBJECT_ATTR = {
    "product": "product",
    "recognition": "recognition",
    "show": "show",
    "installation": "installation",
}


def _timed_to_moment(draft: PostDraft) -> PostDraft:
    """Re-open ``draft`` on the US date it was timed to.

    The pillar still decides what the post is about; the moment decides how it
    walks in. Our own hook is not thrown away — it becomes the paragraph after,
    which is where the argument was going to start anyway.
    """
    from dataclasses import replace

    moment = draft.slot.moment
    if moment is None or not moment.angle:
        return draft
    return replace(
        draft,
        hook=moment.angle,
        body=_paragraphs(draft.hook, draft.body),
    )


def compose(slot: Slot, catalog: Catalog) -> PostDraft:
    """Render one slot. Raises for a pillar with no composer or no subject."""
    try:
        composer = _COMPOSERS[slot.pillar.key]
    except KeyError:
        raise KeyError(f"no composer registered for pillar {slot.pillar.key!r}") from None
    needs = slot.pillar.needs
    if needs and getattr(slot, _SUBJECT_ATTR[needs]) is None:
        raise ValueError(f"pillar {slot.pillar.key!r} requires a {needs} but the slot has none")
    return _timed_to_moment(composer(slot, catalog))


def compose_all(slots, catalog: Catalog) -> list[PostDraft]:
    return [compose(slot, catalog) for slot in slots]
