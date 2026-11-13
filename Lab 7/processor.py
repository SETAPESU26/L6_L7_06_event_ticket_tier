"""
Lab 7 - Fuzz Testing with Hypothesis (FIXED processor)
Name : P T Mounika
SRN  : PES1UG24CS311
Repo : L6_L7_06_event_ticket_tier

Every function validates its input and returns an "Invalid ..." message
instead of raising an exception when it gets None, non-strings, empty
strings, missing/extra fields, non-numeric numbers or out-of-range values.
"""

TIER_RATES = {
    "VIP": 150.0,
    "PREMIUM": 90.0,
    "GENERAL": 45.0,
}

MAX_INPUT_LENGTH = 200   # guards against huge inputs (DoS-style)
MAX_ROW = 1000
MAX_AGE = 130


def _to_int(text):
    """Convert text to int only if it is a plain ASCII number, else None."""
    text = text.strip()
    sign = ""
    if text[:1] in ("+", "-"):
        sign, text = text[0], text[1:]
    if not text or not text.isascii() or not text.isdigit():
        return None
    return int(sign + text)


def decode_promo_voucher(voucher_code):
    if not isinstance(voucher_code, str):
        return "Invalid voucher: input must be a string"
    if len(voucher_code) > MAX_INPUT_LENGTH:
        return "Invalid voucher: input too long"

    code = voucher_code.strip()
    if not code:
        return "Invalid voucher: empty input"

    parts = code.split('-')
    if len(parts) != 2:
        return "Invalid voucher: expected format PREFIX-PERCENT (e.g. EARLY-20)"

    prefix, pct_str = parts[0].strip(), parts[1].strip()
    if not prefix or not prefix.isalnum():
        return "Invalid voucher: prefix must be letters/digits"

    percentage = _to_int(pct_str)
    if percentage is None:
        return "Invalid voucher: percentage must be a whole number"
    if not 1 <= percentage <= 100:
        return "Invalid voucher: percentage must be between 1 and 100"

    return f"Valid {prefix.upper()}: {percentage}% OFF"


def calculate_seat_tier_price(tier_spec):
    if not isinstance(tier_spec, str):
        return "Invalid tier spec: input must be a string"
    if len(tier_spec) > MAX_INPUT_LENGTH:
        return "Invalid tier spec: input too long"

    parts = tier_spec.split('@')
    if len(parts) != 2:
        return "Invalid tier spec: expected format TIER@ROW (e.g. VIP@4)"

    tier = parts[0].strip().upper()
    if tier not in TIER_RATES:
        return f"Invalid tier spec: tier must be one of {', '.join(TIER_RATES)}"

    row = _to_int(parts[1])
    if row is None:
        return "Invalid tier spec: row must be a whole number"
    if not 1 <= row <= MAX_ROW:
        return f"Invalid tier spec: row must be between 1 and {MAX_ROW}"

    base = TIER_RATES[tier]
    return base + (row * 2.0)


def parse_attendee_badge(badge_csv):
    if not isinstance(badge_csv, str):
        return "Invalid badge: input must be a string"
    if len(badge_csv) > MAX_INPUT_LENGTH:
        return "Invalid badge: input too long"

    tokens = badge_csv.split(',')
    if len(tokens) != 3:
        return "Invalid badge: expected format Name,Age,Seat"

    name = tokens[0].strip()
    seat = tokens[2].strip()
    if not name:
        return "Invalid badge: name is missing"
    if not seat:
        return "Invalid badge: seat is missing"

    age = _to_int(tokens[1])
    if age is None:
        return "Invalid badge: age must be a whole number"
    if not 0 <= age <= MAX_AGE:
        return f"Invalid badge: age must be between 0 and {MAX_AGE}"

    category = "Child" if age < 18 else "Adult"
    return f"{name} [{category}] - Seat {seat}"


def _safe_input(prompt):
    try:
        return input(prompt)
    except EOFError:
        return None


def main():
    print("==== Running decode_promo_voucher ====")
    v_input = _safe_input("Enter voucher (e.g. EARLY-20): ")
    print("Voucher:", decode_promo_voucher(v_input))

    print("\n==== Running calculate_seat_tier_price ====")
    t_input = _safe_input("Enter tier spec (e.g. VIP@4): ")
    print("Seat Price: $", calculate_seat_tier_price(t_input))

    print("\n==== Running parse_attendee_badge ====")
    b_input = _safe_input("Enter badge CSV (Name,Age,Seat): ")
    print("Badge:", parse_attendee_badge(b_input))


if __name__ == "__main__":
    main()
