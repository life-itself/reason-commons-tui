"""List prices and the estimate of what a Claude request cost."""

from decimal import Decimal

from reason_commons.adapters import pricing
from reason_commons.adapters.pricing import cost, label, money, ratio, rates


def test_the_fake_servers_reply_costs_exactly_this_on_haiku_and_sonnet():
    reply = {"input": 12_000, "output": 900}
    assert cost("claude-haiku-5-5", reply) == Decimal("0.00165")
    assert cost("claude-sonnet-5-5", reply) == Decimal("0.033")


def test_a_haiku_prompt_over_100000_tokens_is_priced_whole_at_the_higher_card():
    assert cost("claude-haiku-5-5", {"input": 100_000, "output": 1_000}) == Decimal("0.0105")
    assert cost("claude-haiku-5-5", {"input": 100_001, "output": 1_000}) == Decimal("0.0525005")
    # Cache tokens are part of the prompt, so they move it over the line too.
    over = {"input": 60_000, "cache_read": 40_001, "output": 0}
    assert rates("claude-haiku-5-5", over)["input"] == Decimal("0.50")
    assert rates("claude-haiku-5-5", {"input": 60_000, "cache_read": 40_000})["input"] == Decimal("0.10")


def test_cache_writes_and_reads_have_their_own_rates():
    million = 1_000_000
    for kind, expected in (("cache_write", "0.0125"), ("cache_write_1h", "0.02"), ("cache_read", "0.001")):
        assert cost("claude-haiku-5-5", {kind: 100_000}) == Decimal(expected)
    assert cost("claude-haiku-5-5", {"cache_read": million}) == Decimal("0.05")  # over 100,000: the higher card
    assert cost("claude-sonnet-5-5", {"cache_read": million}) == Decimal("0.1")
    assert cost("claude-sonnet-5-5", {"cache_write": million, "cache_write_1h": million}) == Decimal("6.5")


def test_unknown_models_have_no_price_and_a_dated_snapshot_has_its_familys():
    assert cost("claude-unreleased-9", {"input": 10}) is None
    assert cost("local-model", {"input": 10}) is None
    assert cost("claude-haiku-4-5-20251001", {"input": 1_000_000}) == Decimal(1)
    assert pricing.known("claude-haiku-5-5-extra") is None


def test_saved_prices_override_the_list_and_fill_cache_rates_from_the_input_price():
    overrides = {"claude-haiku-5-5": {"input": "1", "output": "$2"}, "claude-unreleased-9": {"input": 3, "output": 4}}
    assert cost("claude-haiku-5-5", {"input": 1_000_000, "output": 1_000_000}, overrides) == Decimal(3)
    assert rates("claude-haiku-5-5", {}, overrides)["cache_read"] == Decimal("0.1")
    assert cost("claude-unreleased-9", {"output": 1_000_000}, overrides) == Decimal(4)
    # An unreadable override is ignored rather than guessed at.
    broken = {"claude-haiku-5-5": {"input": "cheap", "output": "1"}, "claude-sonnet-5-5": {"input": "1"}}
    assert cost("claude-haiku-5-5", {"input": 100_000}, broken) == Decimal("0.01")
    assert cost("claude-sonnet-5-5", {"input": 1_000_000}, broken) == Decimal(2)


def test_names_and_amounts_read_as_people_say_them():
    assert [label(m) for m in ("claude-haiku-5-5", "claude-sonnet-5-5", "claude-haiku-4-5-20251001",
                               "claude-opus-5", "local-model", None)] == [
        "Haiku 5.5", "Sonnet 5.5", "Haiku 4.5", "Opus 5", "local-model", "unknown model"]
    amounts = [0, 5, Decimal("1.4"), Decimal("5.2"), Decimal("0.033"), Decimal("0.00165"), Decimal("0.0049"),
               Decimal("0.00004"), None]
    assert [money(a) for a in amounts] == ["$0", "$5", "$1.40", "$5.20", "$0.03", "$0.0017", "$0.0049",
                                           "$0.00004", "unknown"]


def test_sonnet_costs_twenty_times_haiku_per_token_and_about_twelve_times_per_typical_reply():
    assert ratio("claude-haiku-5-5", "claude-sonnet-5-5", {"input": 12_000, "output": 900}) == 20
    # Haiku thinks at greater length, so a typical reply's ratio is lower (docs/validation.md: $0.0042 and $0.050).
    assert pricing.typical("claude-haiku-5-5") == Decimal("0.0042")
    assert pricing.typical("claude-sonnet-5-5") == Decimal("0.05")
    assert round(ratio("claude-haiku-5-5", "claude-sonnet-5-5")) == 12
    assert ratio("claude-haiku-5-5", "local-model") is None and pricing.typical("local-model") is None


def test_the_table_is_dated_and_sourced():
    assert pricing.AS_OF == "2026-10-08" and pricing.SOURCE.startswith("https://")
