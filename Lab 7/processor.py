"""
Lab 7 - hardened version of processor.py
Student: M DEVASHRUTH (PES1UG24CS251)

Every function now validates its input and returns a clear "Invalid ..."
result (or None for the price) instead of raising an exception.
"""

TIER_RATES = {
    "VIP": 150.0,
    "PREMIUM": 90.0,
    "GENERAL": 45.0,
}
MAX_ROW = 1000        # sanity limit on seat row numbers
MAX_AGE = 120         # sanity limit on attendee age


def _is_plain_number(text, max_len=6):
    """True only for non-empty strings of ASCII digits 0-9 (no signs, spaces,
    underscores, Unicode digits, or absurdly long numbers)."""
    return (
        isinstance(text, str)
        and 0 < len(text) <= max_len
        and all(ch in "0123456789" for ch in text)
    )


def decode_promo_voucher(voucher_code):
    if not isinstance(voucher_code, str):
        return "Invalid voucher: input must be text"

    code = voucher_code.strip()
    parts = code.split("-")
    if len(parts) != 2:
        return "Invalid voucher: expected format PREFIX-PERCENT"

    prefix, pct_str = parts[0].strip(), parts[1].strip()
    if not prefix or not (prefix.isascii() and prefix.isalnum()):
        return "Invalid voucher: prefix must be letters/digits"
    if not _is_plain_number(pct_str):
        return "Invalid voucher: percentage must be a whole number"

    percentage = int(pct_str)
    if not 0 <= percentage <= 100:
        return "Invalid voucher: percentage must be between 0 and 100"

    return f"Valid {prefix.upper()}: {percentage}% OFF"


def calculate_seat_tier_price(tier_spec):
    if not isinstance(tier_spec, str):
        return None

    parts = tier_spec.split("@")
    if len(parts) != 2:
        return None

    tier = parts[0].strip().upper()
    row_str = parts[1].strip()
    if tier not in TIER_RATES or not _is_plain_number(row_str):
        return None

    row = int(row_str)
    if row > MAX_ROW:
        return None

    return TIER_RATES[tier] + (row * 2.0)


def parse_attendee_badge(badge_csv):
    if not isinstance(badge_csv, str):
        return "Invalid badge: input must be text"

    tokens = badge_csv.split(",")
    if len(tokens) != 3:
        return "Invalid badge: expected Name,Age,Seat"

    name, age_str, seat = tokens[0].strip(), tokens[1].strip(), tokens[2].strip()
    if not name or not seat:
        return "Invalid badge: name and seat cannot be empty"
    if not _is_plain_number(age_str, max_len=3):
        return "Invalid badge: age must be a whole number"

    age = int(age_str)
    if age > MAX_AGE:
        return "Invalid badge: age out of range"

    category = "Child" if age < 18 else "Adult"
    return f"{name} [{category}] - Seat {seat}"


def main():
    print("==== Running decode_promo_voucher ====")
    v_input = input("Enter voucher (e.g. EARLY-20): ")
    print("Voucher:", decode_promo_voucher(v_input))

    print("\n==== Running calculate_seat_tier_price ====")
    t_input = input("Enter tier spec (e.g. VIP@4): ")
    price = calculate_seat_tier_price(t_input)
    if price is None:
        print("Seat Price: Invalid tier spec (expected TIER@ROW, e.g. VIP@4)")
    else:
        print("Seat Price: $", price)

    print("\n==== Running parse_attendee_badge ====")
    b_input = input("Enter badge CSV (Name,Age,Seat): ")
    print("Badge:", parse_attendee_badge(b_input))


if __name__ == "__main__":
    main()
