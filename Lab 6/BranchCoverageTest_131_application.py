import pytest

from event_ticket_tier import process_ticket_manifest, monitor_gate_flow


# Input validation: exercise both sides of the validation condition.
def test_invalid_manifest_type():
    with pytest.raises(ValueError):
        process_ticket_manifest("invalid", 0.1)


def test_negative_tax_rate():
    with pytest.raises(ValueError):
        process_ticket_manifest([], -0.1)


def test_valid_input_with_zero_tax():
    result = process_ticket_manifest(
        [{"is_confirmed": True, "tier": "general",
          "orders": [{"qty": 1, "promo": ""}]}],
        0.0,
    )
    assert result == {"total_revenue": 45.0, "status": "COMPLETED"}


# Manifest confirmation and all tier-selection branches.
def test_unconfirmed_manifest_is_skipped():
    result = process_ticket_manifest(
        [{"is_confirmed": False, "tier": "vip",
          "orders": [{"qty": 1, "promo": ""}]}],
        0.0,
    )
    assert result == {"total_revenue": 0.0, "status": "ZERO_SALES"}


@pytest.mark.parametrize(
    ("tier", "price"),
    [("vip", 150.0), ("premium", 90.0), ("general", 45.0)],
)
def test_each_supported_tier(tier, price):
    result = process_ticket_manifest(
        [{"is_confirmed": True, "tier": tier,
          "orders": [{"qty": 1, "promo": ""}]}],
        0.0,
    )
    assert result == {"total_revenue": price, "status": "COMPLETED"}


def test_unknown_tier_increments_rejections():
    result = process_ticket_manifest(
        [{"is_confirmed": True, "tier": "student", "orders": []}],
        0.0,
    )
    assert result == {"total_revenue": 0.0, "status": "ZERO_SALES"}


# Quantity and promotional-code branches.
@pytest.mark.parametrize("qty", [0, -1])
def test_non_positive_quantity_is_rejected(qty):
    result = process_ticket_manifest(
        [{"is_confirmed": True, "tier": "general",
          "orders": [{"qty": qty, "promo": ""}]}],
        0.0,
    )
    assert result == {"total_revenue": 0.0, "status": "ZERO_SALES"}


def test_earlybird_discount():
    result = process_ticket_manifest(
        [{"is_confirmed": True, "tier": "premium",
          "orders": [{"qty": 2, "promo": "EARLYBIRD"}]}],
        0.0,
    )
    assert result == {"total_revenue": 144.0, "status": "COMPLETED"}


def test_quantity_five_or_more_gets_discount():
    result = process_ticket_manifest(
        [{"is_confirmed": True, "tier": "general",
          "orders": [{"qty": 5, "promo": ""}]}],
        0.0,
    )
    assert result == {"total_revenue": 205.0, "status": "COMPLETED"}


def test_quantity_below_five_gets_no_quantity_discount():
    result = process_ticket_manifest(
        [{"is_confirmed": True, "tier": "general",
          "orders": [{"qty": 4, "promo": ""}]}],
        0.0,
    )
    assert result == {"total_revenue": 180.0, "status": "COMPLETED"}


def test_fraud_risk_for_non_vip_counts_rejection_but_keeps_price():
    result = process_ticket_manifest(
        [{"is_confirmed": True, "tier": "general",
          "orders": [{"qty": 2, "promo": "FRAUD_RISK"}]}],
        0.0,
    )
    assert result == {"total_revenue": 90.0, "status": "COMPLETED"}


def test_vip_fraud_resets_total_and_breaks_order_loop():
    result = process_ticket_manifest(
        [{"is_confirmed": True, "tier": "vip",
          "orders": [{"qty": 1, "promo": ""},
                     {"qty": 1, "promo": "FRAUD_RISK"},
                     {"qty": 2, "promo": ""}]}],
        0.0,
    )
    assert result == {"total_revenue": 0.0, "status": "ZERO_SALES"}


# Lounge, audit, zero-sales and completed-result branches.
def test_exclusive_lounge_adds_fee():
    result = process_ticket_manifest(
        [{"is_confirmed": True, "tier": "general",
          "exclusive_lounge": True,
          "orders": [{"qty": 1, "promo": ""}]}],
        0.0,
    )
    assert result == {"total_revenue": 120.0, "status": "COMPLETED"}


def test_more_than_four_rejections_causes_audit_rejection():
    manifests = [
        {"is_confirmed": True, "tier": "unknown", "orders": []}
        for _ in range(5)
    ]
    result = process_ticket_manifest(manifests, 0.0)
    assert result == {"total_revenue": 0.0, "status": "AUDIT_REJECTED"}


def test_four_rejections_do_not_trigger_audit():
    manifests = [
        {"is_confirmed": True, "tier": "unknown", "orders": []}
        for _ in range(4)
    ]
    result = process_ticket_manifest(manifests, 0.0)
    assert result == {"total_revenue": 0.0, "status": "ZERO_SALES"}


def test_tax_is_applied():
    result = process_ticket_manifest(
        [{"is_confirmed": True, "tier": "general",
          "orders": [{"qty": 2, "promo": ""}]}],
        0.1,
    )
    assert result == {"total_revenue": 99.0, "status": "COMPLETED"}


# Gate-flow branches: empty input, high/low rate, streak and reset.
def test_gate_flow_empty_input():
    assert monitor_gate_flow([]) == "NO_DATA"


def test_gate_flow_normal_rate():
    assert monitor_gate_flow([[20, 30, 40]]) == "FLOW_NORMAL"


def test_gate_flow_one_high_rate_is_not_overflow():
    assert monitor_gate_flow([[51]]) == "FLOW_NORMAL"


def test_gate_flow_two_consecutive_high_rates_overflow():
    assert monitor_gate_flow([[51, 60]]) == "OVERFLOW"


def test_gate_flow_normal_rate_resets_high_rate_streak():
    assert monitor_gate_flow([[51, 40, 51]]) == "FLOW_NORMAL"
