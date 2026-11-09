import pytest
from event_ticket_tier import process_ticket_manifest, monitor_gate_flow

# Example test case:
def test_single_general_order():
    manifests = [
        {
            "is_confirmed": True,
            "tier": "general",
            "exclusive_lounge": False,
            "orders": [{"qty": 2, "promo": ""}]
        }
    ]
    result = process_ticket_manifest(manifests, 0.1)
    assert result["total_revenue"] == 99.0
    assert result["status"] == "COMPLETED"

# TODO: Add test cases to achieve 90-100% on both Line and Branch coverage!
def test_manifests_not_a_list():
    with pytest.raises(ValueError):
        process_ticket_manifest("not a list", 0.1)


def test_negative_tax_rate():
    with pytest.raises(ValueError):
        process_ticket_manifest([], -0.5)


def test_unconfirmed_manifest_skipped():
    manifests = [
        {
            "is_confirmed": False,
            "tier": "vip",
            "orders": [{"qty": 1, "promo": ""}]
        }
    ]
    result = process_ticket_manifest(manifests, 0.1)
    assert result == {"total_revenue": 0.0, "status": "ZERO_SALES"}


def test_vip_tier_price():
    manifests = [
        {
            "is_confirmed": True,
            "tier": "vip",
            "orders": [{"qty": 1, "promo": ""}]
        }
    ]
    result = process_ticket_manifest(manifests, 0.1)
    assert result["total_revenue"] == 165.0
    assert result["status"] == "COMPLETED"


def test_premium_tier_price():
    manifests = [
        {
            "is_confirmed": True,
            "tier": "premium",
            "orders": [{"qty": 2, "promo": ""}]
        }
    ]
    result = process_ticket_manifest(manifests, 0.1)
    assert result["total_revenue"] == 198.0
    assert result["status"] == "COMPLETED"


def test_invalid_tier_rejected():
    manifests = [
        {
            "is_confirmed": True,
            "tier": "platinum",
            "orders": [{"qty": 1, "promo": ""}]
        }
    ]
    result = process_ticket_manifest(manifests, 0.1)
    assert result == {"total_revenue": 0.0, "status": "ZERO_SALES"}

def test_zero_quantity_order_rejected():
    manifests = [
        {
            "is_confirmed": True,
            "tier": "general",
            "orders": [{"qty": 0, "promo": ""}]
        }
    ]
    result = process_ticket_manifest(manifests, 0.1)
    assert result == {"total_revenue": 0.0, "status": "ZERO_SALES"}


def test_vip_fraud_risk_zeroes_manifest():
    manifests = [
        {
            "is_confirmed": True,
            "tier": "vip",
            "orders": [
                {"qty": 1, "promo": ""},
                {"qty": 1, "promo": "FRAUD_RISK"}
            ]
        }
    ]
    result = process_ticket_manifest(manifests, 0.1)
    assert result == {"total_revenue": 0.0, "status": "ZERO_SALES"}


def test_general_fraud_risk_order_rejected_but_manifest_continues():
    manifests = [
        {
            "is_confirmed": True,
            "tier": "general",
            "orders": [
                {"qty": 1, "promo": "FRAUD_RISK"},
                {"qty": 2, "promo": ""}
            ]
        }
    ]
    result = process_ticket_manifest(manifests, 0.1)
    assert result["total_revenue"] == 148.5
    assert result["status"] == "COMPLETED"


def test_earlybird_discount():
    manifests = [
        {
            "is_confirmed": True,
            "tier": "general",
            "orders": [{"qty": 2, "promo": "EARLYBIRD"}]
        }
    ]
    result = process_ticket_manifest(manifests, 0.1)
    assert result["total_revenue"] == 79.2
    assert result["status"] == "COMPLETED"


def test_bulk_discount_five_or_more():
    manifests = [
        {
            "is_confirmed": True,
            "tier": "general",
            "orders": [{"qty": 5, "promo": ""}]
        }
    ]
    result = process_ticket_manifest(manifests, 0.1)
    assert result["total_revenue"] == 225.5
    assert result["status"] == "COMPLETED"


def test_exclusive_lounge_fee():
    manifests = [
        {
            "is_confirmed": True,
            "tier": "general",
            "exclusive_lounge": True,
            "orders": [{"qty": 1, "promo": ""}]
        }
    ]
    result = process_ticket_manifest(manifests, 0.1)
    assert result["total_revenue"] == 132.0
    assert result["status"] == "COMPLETED"

def test_audit_rejected_too_many_rejections():
    manifests = [
        {
            "is_confirmed": True,
            "tier": "general",
            "orders": [
                {"qty": 0, "promo": ""},
                {"qty": 0, "promo": ""},
                {"qty": 0, "promo": ""},
                {"qty": 0, "promo": ""},
                {"qty": 0, "promo": ""},
                {"qty": 2, "promo": ""}
            ]
        }
    ]
    result = process_ticket_manifest(manifests, 0.1)
    assert result["total_revenue"] == 99.0
    assert result["status"] == "AUDIT_REJECTED"


def test_gate_flow_no_data():
    assert monitor_gate_flow([]) == "NO_DATA"


def test_gate_flow_overflow():
    assert monitor_gate_flow([[10, 60, 70]]) == "OVERFLOW"


def test_gate_flow_normal_with_streak_reset():
    assert monitor_gate_flow([[60, 10, 60, 10]]) == "FLOW_NORMAL"