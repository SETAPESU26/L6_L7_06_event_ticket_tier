"""
Lab 7 - Fuzz testing with Hypothesis
Student: M DEVASHRUTH (PES1UG24CS251)

Run:
    pytest test_processor.py
    python -m pytest test_processor.py
"""
from hypothesis import given, example, strategies as st
from processor import (
    decode_promo_voucher,
    calculate_seat_tier_price,
    parse_attendee_badge,
)

# Text without commas, used to build well-formed badge CSV strings.
no_comma_text = st.text(alphabet=st.characters(blacklist_characters=","))


# ---------------------------------------------------------------------------
# Part A - "must never crash" fuzz tests (arbitrary text or None)
# ---------------------------------------------------------------------------
@given(st.text() | st.none())
@example(None)
@example("EARLY20")
@example("EARLY-abc")
def test_decode_promo_voucher_no_crash(s):
    try:
        decode_promo_voucher(s)
    except Exception as e:
        assert False, f"decode_promo_voucher crashed with: {e!r} on input {s!r}"


@given(st.text() | st.none())
@example(None)
@example("VIP4")
@example("GOLD@3")
def test_calculate_seat_tier_price_safe(s):
    try:
        calculate_seat_tier_price(s)
    except Exception as e:
        assert False, f"calculate_seat_tier_price crashed with: {e!r} on input {s!r}"


@given(st.text() | st.none())
@example(None)
@example("Asha,abc,A12")
@example("Asha,20")
def test_parse_attendee_badge_safe(s):
    try:
        parse_attendee_badge(s)
    except Exception as e:
        assert False, f"parse_attendee_badge crashed with: {e!r} on input {s!r}"


# ---------------------------------------------------------------------------
# Part B - structured fuzzing: well-formed-looking inputs with extreme values.
# Random text almost never looks like "NAME-20", so these reach the logic
# that sits behind the parsing and check that the *results* make sense.
# ---------------------------------------------------------------------------
@given(
    st.text(alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")), min_size=1),
    st.integers(),
)
def test_decode_promo_voucher_percentage_in_range(prefix, pct):
    code = f"{prefix}-{pct}"
    try:
        result = decode_promo_voucher(code)
    except Exception as e:
        assert False, f"decode_promo_voucher crashed with: {e!r} on input {code!r}"
    assert isinstance(result, str)
    if result.startswith("Valid"):
        assert 0 <= pct <= 100, f"accepted impossible discount {pct}% from {code!r}"


@given(
    st.sampled_from(["VIP", "PREMIUM", "GENERAL", "vip", " Premium ", "BRONZE", ""]),
    st.integers(),
)
def test_calculate_seat_tier_price_sensible(tier, row):
    spec = f"{tier}@{row}"
    try:
        price = calculate_seat_tier_price(spec)
    except Exception as e:
        assert False, f"calculate_seat_tier_price crashed with: {e!r} on input {spec!r}"
    if price is not None:
        assert isinstance(price, float)
        assert price >= 45.0, f"price {price} is below the cheapest base rate for {spec!r}"
        assert price < 10_000, f"absurd price {price} for {spec!r}"


@given(no_comma_text, st.integers(), no_comma_text)
def test_parse_attendee_badge_age_in_range(name, age, seat):
    badge = f"{name},{age},{seat}"
    try:
        result = parse_attendee_badge(badge)
    except Exception as e:
        assert False, f"parse_attendee_badge crashed with: {e!r} on input {badge!r}"
    assert isinstance(result, str)
    if not result.startswith("Invalid"):
        assert 0 <= age <= 120, f"accepted impossible age {age} from {badge!r}"
