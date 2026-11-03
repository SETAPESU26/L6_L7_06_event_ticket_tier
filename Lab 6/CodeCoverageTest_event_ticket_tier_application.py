"""
Lab 6 - Code (line) coverage tests for event_ticket_tier.py
Student: M DEVASHRUTH (PES1UG24CS251)

Run:
    coverage run -m pytest CodeCoverageTest_event_ticket_tier_application.py
    coverage report -m
"""
import pytest
from event_ticket_tier import process_ticket_manifest, monitor_gate_flow


def make_manifest(tier="general", orders=None, confirmed=True, lounge=False):
    """Small helper to keep the test bodies short and readable."""
    return {
        "is_confirmed": confirmed,
        "tier": tier,
        "exclusive_lounge": lounge,
        "orders": orders if orders is not None else [],
    }


# ---------------------------------------------------------------------------
# process_ticket_manifest
# ---------------------------------------------------------------------------
def test_single_general_order():
    # starter example: 2 * 45 = 90, +10% tax = 99.0
    manifests = [make_manifest("general", [{"qty": 2, "promo": ""}])]
    result = process_ticket_manifest(manifests, 0.1)
    assert result["total_revenue"] == 99.0
    assert result["status"] == "COMPLETED"


def test_invalid_manifests_type_raises():
    with pytest.raises(ValueError):
        process_ticket_manifest("not-a-list", 0.1)


def test_unconfirmed_manifest_is_skipped():
    manifests = [make_manifest("vip", [{"qty": 3, "promo": ""}], confirmed=False)]
    result = process_ticket_manifest(manifests, 0.1)
    assert result == {"total_revenue": 0.0, "status": "ZERO_SALES"}


def test_vip_tier_price():
    # 1 * 150 = 150, no tax
    manifests = [make_manifest("vip", [{"qty": 1, "promo": ""}])]
    result = process_ticket_manifest(manifests, 0.0)
    assert result["total_revenue"] == 150.0
    assert result["status"] == "COMPLETED"


def test_premium_tier_with_earlybird_discount():
    # 2 * 90 = 180, EARLYBIRD -> 144, no tax
    manifests = [make_manifest("premium", [{"qty": 2, "promo": "EARLYBIRD"}])]
    result = process_ticket_manifest(manifests, 0.0)
    assert result["total_revenue"] == pytest.approx(144.0)
    assert result["status"] == "COMPLETED"


def test_bulk_discount_for_five_or_more_tickets():
    # 5 * 45 = 225, bulk -20 = 205, no tax
    manifests = [make_manifest("general", [{"qty": 5, "promo": ""}])]
    result = process_ticket_manifest(manifests, 0.0)
    assert result["total_revenue"] == 205.0


def test_unknown_tier_is_rejected():
    manifests = [make_manifest("backstage", [{"qty": 2, "promo": ""}])]
    result = process_ticket_manifest(manifests, 0.1)
    assert result == {"total_revenue": 0.0, "status": "ZERO_SALES"}


def test_zero_quantity_order_is_rejected():
    manifests = [make_manifest("general", [{"qty": 0, "promo": ""}])]
    result = process_ticket_manifest(manifests, 0.1)
    assert result["status"] == "ZERO_SALES"


def test_vip_fraud_risk_voids_manifest():
    orders = [
        {"qty": 2, "promo": ""},           # 300, added before the fraud order
        {"qty": 1, "promo": "FRAUD_RISK"},  # voids the whole VIP manifest
        {"qty": 9, "promo": ""},           # never reached (break)
    ]
    result = process_ticket_manifest([make_manifest("vip", orders)], 0.1)
    assert result == {"total_revenue": 0.0, "status": "ZERO_SALES"}


def test_exclusive_lounge_surcharge():
    # 1 * 45 = 45 + 75 lounge = 120, no tax
    manifests = [make_manifest("general", [{"qty": 1, "promo": ""}], lounge=True)]
    result = process_ticket_manifest(manifests, 0.0)
    assert result["total_revenue"] == 120.0


def test_audit_rejected_when_more_than_four_rejections():
    bad_orders = [{"qty": 0, "promo": ""} for _ in range(5)]
    good_orders = [{"qty": 1, "promo": ""}]
    manifests = [make_manifest("general", bad_orders + good_orders)]
    result = process_ticket_manifest(manifests, 0.0)
    assert result["status"] == "AUDIT_REJECTED"
    assert result["total_revenue"] == 45.0


# ---------------------------------------------------------------------------
# monitor_gate_flow
# ---------------------------------------------------------------------------
def test_gate_flow_no_data():
    assert monitor_gate_flow([]) == "NO_DATA"


def test_gate_flow_overflow_on_consecutive_high_rates():
    assert monitor_gate_flow([[10, 60, 70]]) == "OVERFLOW"


def test_gate_flow_normal():
    assert monitor_gate_flow([[10, 60, 20, 55, 5]]) == "FLOW_NORMAL"
