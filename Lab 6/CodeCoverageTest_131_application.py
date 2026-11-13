import pytest

from event_ticket_tier import process_ticket_manifest, monitor_gate_flow


def test_invalid_manifest_input():
    with pytest.raises(ValueError):
        process_ticket_manifest("not-a-list", 0.1)


def test_negative_tax_rate():
    with pytest.raises(ValueError):
        process_ticket_manifest([], -0.1)


def test_unconfirmed_manifest_is_skipped():
    result = process_ticket_manifest(
        [{"is_confirmed": False, "tier": "vip", "orders": [{"qty": 2}]}],
        0.1
    )
    assert result == {"total_revenue": 0.0, "status": "ZERO_SALES"}


def test_all_ticket_tiers_and_lounge():
    manifests = [
        {
            "is_confirmed": True,
            "tier": "vip",
            "exclusive_lounge": True,
            "orders": [{"qty": 1, "promo": ""}]
        },
        {
            "is_confirmed": True,
            "tier": "premium",
            "orders": [{"qty": 1, "promo": ""}]
        },
        {
            "is_confirmed": True,
            "tier": "general",
            "orders": [{"qty": 1, "promo": ""}]
        }
    ]

    result = process_ticket_manifest(manifests, 0.0)
    assert result == {"total_revenue": 360.0, "status": "COMPLETED"}


def test_unknown_tier_is_rejected():
    result = process_ticket_manifest(
        [{"is_confirmed": True, "tier": "student", "orders": []}],
        0.0
    )
    assert result == {"total_revenue": 0.0, "status": "ZERO_SALES"}


def test_non_positive_quantity_is_rejected():
    result = process_ticket_manifest(
        [{
            "is_confirmed": True,
            "tier": "general",
            "orders": [{"qty": 0}, {"qty": -2}]
        }],
        0.0
    )
    assert result == {"total_revenue": 0.0, "status": "ZERO_SALES"}


def test_earlybird_discount():
    result = process_ticket_manifest(
        [{
            "is_confirmed": True,
            "tier": "premium",
            "orders": [{"qty": 2, "promo": "EARLYBIRD"}]
        }],
        0.0
    )
    assert result == {"total_revenue": 144.0, "status": "COMPLETED"}


def test_quantity_discount_for_five_or_more():
    result = process_ticket_manifest(
        [{
            "is_confirmed": True,
            "tier": "general",
            "orders": [{"qty": 5, "promo": ""}]
        }],
        0.0
    )
    assert result == {"total_revenue": 205.0, "status": "COMPLETED"}


def test_fraud_risk_order_is_rejected_for_general_tier():
    result = process_ticket_manifest(
        [{
            "is_confirmed": True,
            "tier": "general",
            "orders": [{"qty": 2, "promo": "FRAUD_RISK"}]
        }],
        0.0
    )
    assert result == {"total_revenue": 90.0, "status": "COMPLETED"}


def test_vip_fraud_resets_manifest_total_and_stops_processing():
    result = process_ticket_manifest(
        [{
            "is_confirmed": True,
            "tier": "vip",
            "orders": [
                {"qty": 1, "promo": ""},
                {"qty": 1, "promo": "FRAUD_RISK"},
                {"qty": 2, "promo": ""}
            ]
        }],
        0.0
    )
    assert result == {"total_revenue": 0.0, "status": "ZERO_SALES"}


def test_audit_rejected_after_more_than_four_rejections():
    manifests = [
        {"is_confirmed": True, "tier": "unknown", "orders": []}
        for _ in range(5)
    ]

    result = process_ticket_manifest(manifests, 0.1)
    assert result == {"total_revenue": 0.0, "status": "AUDIT_REJECTED"}


def test_tax_is_applied_and_revenue_is_rounded():
    result = process_ticket_manifest(
        [{
            "is_confirmed": True,
            "tier": "general",
            "orders": [{"qty": 2, "promo": ""}]
        }],
        0.1
    )
    assert result == {"total_revenue": 99.0, "status": "COMPLETED"}


def test_monitor_gate_flow_with_no_data():
    assert monitor_gate_flow([]) == "NO_DATA"


def test_monitor_gate_flow_detects_two_consecutive_high_rates():
    assert monitor_gate_flow([[20, 51, 60]]) == "OVERFLOW"


def test_monitor_gate_flow_resets_streak_after_normal_rate():
    assert monitor_gate_flow([[51, 40, 51]]) == "FLOW_NORMAL"