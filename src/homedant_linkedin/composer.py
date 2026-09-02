"""Rendering a scheduled slot into a LinkedIn post draft.

The templates follow the account's own posts, which run as prose rather than
bullet lists: a hook that states the news or asks the reader's question, a
paragraph giving it meaning, a paragraph on what the shelving does, an
invitation to connect, and a thank-you where a third party is involved. Proof
points are carried separately for the image, which does use a list.
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


def _variant(slot: Slot, options: tuple[str, ...]) -> str:
    """One of several openings, rotated by ISO week.

    A hook that repeats every fortnight stops being read, so each pillar keeps
    a small set and the week decides which one runs.
    """
    return options[slot.scheduled_for.isocalendar()[1] % len(options)]


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
            hashtags=_hashtags(slot, award.hashtags),
            points=profile.proof_points[:3],
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
        hashtags=_hashtags(slot, award.hashtags),
        points=profile.proof_points[:3],
    )


def _show_hook(show, day, brand: str) -> str:
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
    return f"{brand} is coming to {show.name}{where}! \U0001f1f0\U0001f1f7"


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
    else:
        second = (
            "Bring the dimensions you are working with and we will tell you on the spot whether we "
            "already have a unit that fits, or whether it is a tooling change."
        )
        cta = (
            "If you are attending, message me and we will book a time before the calendar fills. "
            f"\u2014 {profile.author}"
        )

    return PostDraft(
        slot=slot,
        hook=_show_hook(show, day, profile.brand),
        body=_paragraphs(
            f"{profile.company} is at {show.venue}, {show.dates}, with our {profile.offer}.",
            profile.capability,
            second,
        ),
        cta=cta,
        hashtags=_hashtags(slot, show.hashtags),
        points=profile.proof_points[:3],
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
        hashtags=_hashtags(slot),
        points=product.highlights[:3],
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
        hashtags=_hashtags(slot),
        points=product.highlights[:3],
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
        hashtags=_hashtags(slot),
        points=profile.proof_points[:3],
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
            profile.capability,
        ),
        cta=CONNECT_CTA.format(audiences=profile.audience_phrase),
        hashtags=_hashtags(slot),
        points=profile.proof_points[-3:],
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
        hashtags=_hashtags(slot),
        points=product.highlights[:3],
    )


_COMPOSERS = {
    "recognition": _compose_recognition,
    "tradeshow": _compose_tradeshow,
    "project": _compose_project,
    "retail": _compose_retail,
    "manufacturing": _compose_manufacturing,
    "seasonal": _compose_seasonal,
    "supply": _compose_supply,
}

_SUBJECT_ATTR = {"product": "product", "recognition": "recognition", "show": "show"}


def compose(slot: Slot, catalog: Catalog) -> PostDraft:
    """Render one slot. Raises for a pillar with no composer or no subject."""
    try:
        composer = _COMPOSERS[slot.pillar.key]
    except KeyError:
        raise KeyError(f"no composer registered for pillar {slot.pillar.key!r}") from None
    needs = slot.pillar.needs
    if needs and getattr(slot, _SUBJECT_ATTR[needs]) is None:
        raise ValueError(f"pillar {slot.pillar.key!r} requires a {needs} but the slot has none")
    return composer(slot, catalog)


def compose_all(slots, catalog: Catalog) -> list[PostDraft]:
    return [compose(slot, catalog) for slot in slots]
