"""
Lab 7 - Fuzz Testing with Hypothesis
Name : P T Mounika
SRN  : PES1UG24CS311
Repo : L6_L7_06_event_ticket_tier

Property-based fuzz tests for processor.py.
Each function is fed random / malformed input (random text, None, and
"almost valid" structured strings) and must never raise an exception.
Extra property tests check that valid inputs still give the right result.
"""

from hypothesis import given, settings, strategies as st
from processor import decode_promo_voucher, calculate_seat_tier_price, parse_attendee_badge


# ---------------------------------------------------------------------------
# Strategies that build "almost valid" inputs so the fuzzer reaches deeper
# code paths than pure random text would.
# ---------------------------------------------------------------------------
voucher_like = st.builds(
    lambda prefix, sep, pct: f"{prefix}{sep}{pct}",
    st.text(max_size=10),
    st.sampled_from(["-", "--", "", " - ", "-x-"]),
    st.one_of(st.integers(), st.text(max_size=5)),
)

tier_like = st.builds(
    lambda tier, sep, row: f"{tier}{sep}{row}",
    st.one_of(st.sampled_from(["VIP", "premium", " General ", "GOLD", ""]), st.text(max_size=8)),
    st.sampled_from(["@", "@@", "", " @ "]),
    st.one_of(st.integers(), st.text(max_size=5)),
)

badge_like = st.builds(
    lambda name, age, seat, extra: ",".join([name, str(age), seat] + extra),
    st.text(max_size=10),
    st.one_of(st.integers(), st.text(max_size=4)),
    st.text(max_size=5),
    st.lists(st.text(max_size=3), max_size=2),
) | st.builds(lambda parts: ",".join(parts), st.lists(st.text(max_size=6), max_size=4))


# ---------------------------------------------------------------------------
# 1. decode_promo_voucher
# ---------------------------------------------------------------------------
@settings(max_examples=300)
@given(st.text() | st.none() | voucher_like)
def test_decode_promo_voucher_no_crash(s):
    try:
        result = decode_promo_voucher(s)
        assert isinstance(result, str)
    except Exception as e:
        assert False, f"decode_promo_voucher crashed on {s!r} with: {type(e).__name__}: {e}"


@given(st.from_regex(r"[A-Za-z]{1,10}", fullmatch=True), st.integers(min_value=1, max_value=100))
def test_decode_promo_voucher_valid(prefix, pct):
    assert decode_promo_voucher(f"{prefix}-{pct}") == f"Valid {prefix.upper()}: {pct}% OFF"


# ---------------------------------------------------------------------------
# 2. calculate_seat_tier_price
# ---------------------------------------------------------------------------
@settings(max_examples=300)
@given(st.text() | st.none() | tier_like)
def test_calculate_seat_tier_price_safe(s):
    try:
        result = calculate_seat_tier_price(s)
        assert isinstance(result, (float, str))
        if isinstance(result, float):
            assert result >= 0, "price must never be negative"
    except Exception as e:
        assert False, f"calculate_seat_tier_price crashed on {s!r} with: {type(e).__name__}: {e}"


@given(st.sampled_from([("VIP", 150.0), ("PREMIUM", 90.0), ("GENERAL", 45.0)]),
       st.integers(min_value=1, max_value=500))
def test_calculate_seat_tier_price_valid(tier_rate, row):
    tier, rate = tier_rate
    assert calculate_seat_tier_price(f"{tier.lower()}@{row}") == rate + row * 2.0


# ---------------------------------------------------------------------------
# 3. parse_attendee_badge
# ---------------------------------------------------------------------------
@settings(max_examples=300)
@given(st.text() | st.none() | badge_like)
def test_parse_attendee_badge_safe(s):
    try:
        result = parse_attendee_badge(s)
        assert isinstance(result, str)
    except Exception as e:
        assert False, f"parse_attendee_badge crashed on {s!r} with: {type(e).__name__}: {e}"


@given(st.from_regex(r"[A-Za-z]{1,12}", fullmatch=True),
       st.integers(min_value=0, max_value=120),
       st.from_regex(r"[A-Z][0-9]{1,3}", fullmatch=True))
def test_parse_attendee_badge_valid(name, age, seat):
    category = "Child" if age < 18 else "Adult"
    assert parse_attendee_badge(f"{name},{age},{seat}") == f"{name} [{category}] - Seat {seat}"
