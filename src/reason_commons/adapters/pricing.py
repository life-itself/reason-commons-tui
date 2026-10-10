"""Anthropic's list prices, to estimate what a Claude reply cost from its token counts.

An estimate only: Anthropic bills from its own records, and the Anthropic Console is the
authority on what was charged. Prices are dollars per million tokens, as Decimals, so sums
are exact. Nothing here reads or writes a commons.
"""

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
import re

# The day the table below was checked against the live pricing page, and where.
AS_OF = "2026-10-08"
SOURCE = "https://platform.claude.com/docs/en/about-claude/pricing"
# The kinds of token a reply's usage reports, in the order a rate card lists their prices.
TOKEN_KINDS = ("input", "output", "cache_write", "cache_write_1h", "cache_read")
MILLION = Decimal(1_000_000)


def _card(*prices):
    return dict(zip(TOKEN_KINDS, (Decimal(price) for price in prices)))


# Per model, its rate cards from the shortest prompt up: (the longest prompt the card covers, or None
# for any length; the card). A prompt is the input and cache tokens of one request, and its card
# prices the whole request, output included.
PRICES = {
    "claude-haiku-5-5": ((100_000, _card("0.10", "0.50", "0.125", "0.20", "0.01")),
                         (None, _card("0.50", "2.50", "0.625", "1", "0.05"))),
    "claude-sonnet-5-5": ((None, _card("2", "10", "2.50", "4", "0.10")),),
    "claude-opus-5-5": ((None, _card("4", "20", "5", "8", "0.20")),),
    "claude-haiku-4-5": ((None, _card("1", "5", "1.25", "2", "0.10")),),
}
# Without an explicit price, a cache write or read costs this many times the input price.
CACHE_MULTIPLIERS = {"cache_write": Decimal("1.25"), "cache_write_1h": Decimal(2), "cache_read": Decimal("0.1")}


def parse_amount(value):
    """A non-negative Decimal from a number or a string such as "5", "$5" or "5.50"; None otherwise."""
    if isinstance(value, bool) or not isinstance(value, (int, float, str, Decimal)):
        return None
    try:
        amount = Decimal(str(value).strip().lstrip("$").strip())
    except InvalidOperation:
        return None
    return amount if amount.is_finite() and amount >= 0 else None


def _override(prices):
    """One rate card from a ``usage.prices.<model>`` setting; it needs at least the input and output prices."""
    if not isinstance(prices, dict):
        return None
    card = {kind: parse_amount(prices[kind]) for kind in TOKEN_KINDS if kind in prices}
    if card.get("input") is None or card.get("output") is None or None in card.values():
        return None
    for kind, multiplier in CACHE_MULTIPLIERS.items():
        card.setdefault(kind, card["input"] * multiplier)
    return card


def known(model):
    """The table's name for a model, allowing a dated snapshot (claude-haiku-4-5-20251001); None if unknown."""
    if not isinstance(model, str):
        return None
    return next((name for name in PRICES if model == name or re.fullmatch(re.escape(name) + r"-\d{8}", model)), None)


def prompt_tokens(tokens):
    return sum(int(tokens.get(kind) or 0) for kind in TOKEN_KINDS if kind != "output")


def rates(model, tokens, overrides=None):
    """The rate card that prices this request, or None for a model with no known price."""
    override = _override((overrides or {}).get(model))
    if override is not None:
        return override
    name = known(model)
    if name is None:
        return None
    size = prompt_tokens(tokens)
    return next(card for longest, card in PRICES[name] if longest is None or size <= longest)


def cost(model, tokens, overrides=None):
    """Dollars for one request at list price, exactly; None when the model's price is not known."""
    card = rates(model, tokens, overrides)
    if card is None:
        return None
    return sum((Decimal(int(tokens.get(kind) or 0)) * card[kind] for kind in TOKEN_KINDS), Decimal(0)) / MILLION


def label(model):
    """A model's everyday name: "claude-haiku-5-5" is "Haiku 5.5". Anything else stays as it is."""
    found = re.fullmatch(r"claude-([a-z]+)-(\d+)(?:-(\d{1,2}))?(?:-\d{8})?", model or "")
    if not found:
        return model or "unknown model"
    family, major, minor = found.groups()
    return f"{family.capitalize()} {major}" + (f".{minor}" if minor else "")


def money(value):
    """Dollars as people read them: "$5", "$1.40", "$0.05", and two significant figures below a cent
    ("$0.0049"), so a cheap reply never shows as "$0.00"."""
    if value is None:
        return "unknown"
    value = Decimal(value)
    if value == 0:
        return "$0"
    if value >= 1 and value == value.to_integral_value():
        return f"${value:.0f}"
    if value >= Decimal("0.01"):
        return f"${value.quantize(Decimal('0.01'), ROUND_HALF_UP)}"
    places = Decimal(1).scaleb(value.adjusted() - 1)  # two significant figures
    return f"${value.quantize(places, ROUND_HALF_UP).normalize():f}"


# A typical consultation's tokens, as measured in the billed runs of 2026-10-08 (docs/validation.md): about
# 17,000 in, and out about 5,000 for Haiku 5.5, which thinks at length, and 1,600 for Sonnet 5.5. Used to
# estimate a reply before the usage log has enough of a model's own replies.
TYPICAL_REPLY = {"claude-haiku-5-5": {"input": 17_000, "output": 5_000},
                 "claude-sonnet-5-5": {"input": 17_000, "output": 1_600}}
OTHER_REPLY = {"input": 17_000, "output": 2_000}


def typical(model, overrides=None):
    """A typical consultation's estimated cost on this model at list price; None when its price is unknown."""
    return cost(model, TYPICAL_REPLY.get(known(model), OTHER_REPLY), overrides)


def ratio(cheaper, dearer, tokens=None, overrides=None):
    """How many times the dearer model costs the cheaper one: for these tokens on both, or by default for a
    typical consultation on each. None when either price is unknown."""
    if tokens is None:
        low, high = typical(cheaper, overrides), typical(dearer, overrides)
    else:
        low, high = cost(cheaper, tokens, overrides), cost(dearer, tokens, overrides)
    if not low or high is None:
        return None
    return high / low
