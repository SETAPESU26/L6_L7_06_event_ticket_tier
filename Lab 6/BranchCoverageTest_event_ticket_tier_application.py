"""
Lab 6 - Branch coverage tests for event_ticket_tier.py
Student: M DEVASHRUTH (PES1UG24CS251)

Run:
    coverage run --branch -m pytest BranchCoverageTest_event_ticket_tier_application.py
    coverage report -m
"""
import pytest
from event_ticket_tier import process_ticket_manifest, monitor_gate_flow


def make_manifest(tier="general", orders=None, confirmed=True, lounge=False):
    return {
        "is_confirmed": confirmed,
        "tier": tier,
        "exclusive_lounge": lounge,
        "orders": orders if orders is not None else [],
    }


# ===========================================================================
# process_ticket_manifest - input validation (both halves of the `or`)
# ===========================================================================
def test_single_general_order():
    manifests = [make_manifest("general", [{"qty": 2, "promo": ""}])]
    result = process_ticket_manifest(manifests, 0.1)
    assert result["total_revenue"] == 99.0
    assert result["status"] == "COMPLETED"


def test_non_list_manifests_raises():
    with pytest.raises(ValueError):
        process_ticket_manifest("not-a-list", 0.1)


def test_tuple_manifests_raises():
    with pytest.raises(ValueError):
        process_ticket_manifest((make_manifest(),), 0.1)


def test_negative_tax_rate_raises():
    with pytest.raises(ValueError):
        process_ticket_manifest([make_manifest()], -0.01)


def test_zero_tax_rate_is_valid():
    result = process_ticket_manifest([make_manifest("general", [{"qty": 1}])], 0.0)
    assert result["total_revenue"] == 45.0


def test_empty_manifest_list_is_zero_sales():
    assert process_ticket_manifest([], 0.1) == {"total_revenue": 0.0, "status": "ZERO_SALES"}


# ===========================================================================
# is_confirmed True / False
# ===========================================================================
def test_unconfirmed_manifest_is_skipped():
    manifests = [make_manifest("vip", [{"qty": 3, "promo": ""}], confirmed=False)]
    assert process_ticket_manifest(manifests, 0.1) == {"total_revenue": 0.0, "status": "ZERO_SALES"}


def test_missing_is_confirmed_defaults_to_unconfirmed():
    manifests = [{"tier": "vip", "orders": [{"qty": 1}]}]
    assert process_ticket_manifest(manifests, 0.1)["status"] == "ZERO_SALES"


def test_confirmed_and_unconfirmed_mixed():
    manifests = [
        make_manifest("vip", [{"qty": 1}], confirmed=False),
        make_manifest("general", [{"qty": 1}], confirmed=True),
    ]
    assert process_ticket_manifest(manifests, 0.0)["total_revenue"] == 45.0


# ===========================================================================
# tier selection: vip / premium / general / unknown / default
# ===========================================================================
def test_vip_tier_price():
    result = process_ticket_manifest([make_manifest("vip", [{"qty": 1}])], 0.0)
    assert result["total_revenue"] == 150.0


def test_premium_tier_price():
    result = process_ticket_manifest([make_manifest("premium", [{"qty": 1}])], 0.0)
    assert result["total_revenue"] == 90.0


def test_general_tier_price():
    result = process_ticket_manifest([make_manifest("general", [{"qty": 1}])], 0.0)
    assert result["total_revenue"] == 45.0


def test_missing_tier_defaults_to_general():
    manifests = [{"is_confirmed": True, "orders": [{"qty": 1}]}]
    assert process_ticket_manifest(manifests, 0.0)["total_revenue"] == 45.0


def test_unknown_tier_is_rejected_and_skipped():
    manifests = [make_manifest("backstage", [{"qty": 2}])]
    assert process_ticket_manifest(manifests, 0.1) == {"total_revenue": 0.0, "status": "ZERO_SALES"}


# ===========================================================================
# per-order quantity check
# ===========================================================================
def test_zero_quantity_rejected():
    result = process_ticket_manifest([make_manifest("general", [{"qty": 0}])], 0.1)
    assert result["status"] == "ZERO_SALES"


def test_negative_quantity_rejected():
    result = process_ticket_manifest([make_manifest("general", [{"qty": -3}])], 0.1)
    assert result["status"] == "ZERO_SALES"


def test_missing_quantity_defaults_to_zero_and_is_rejected():
    result = process_ticket_manifest([make_manifest("general", [{"promo": ""}])], 0.1)
    assert result["status"] == "ZERO_SALES"


def test_manifest_without_orders_key():
    manifests = [{"is_confirmed": True, "tier": "general"}]
    assert process_ticket_manifest(manifests, 0.1)["status"] == "ZERO_SALES"


def test_manifest_with_empty_orders():
    assert process_ticket_manifest([make_manifest("general", [])], 0.1)["status"] == "ZERO_SALES"


# ===========================================================================
# promo handling: FRAUD_RISK (vip vs non-vip) / EARLYBIRD / none (bulk or not)
# ===========================================================================
def test_vip_fraud_risk_voids_manifest_and_stops_processing():
    orders = [
        {"qty": 2, "promo": ""},            # 300 counted, then wiped by the fraud order
        {"qty": 1, "promo": "FRAUD_RISK"},   # voids VIP manifest, break
        {"qty": 9, "promo": ""},            # never reached
    ]
    result = process_ticket_manifest([make_manifest("vip", orders)], 0.1)
    assert result == {"total_revenue": 0.0, "status": "ZERO_SALES"}


def test_non_vip_fraud_risk_is_counted_as_rejected_but_still_billed():
    # Documents the module's CURRENT behaviour: for non-VIP tiers the FRAUD_RISK
    # order increments rejected_orders but does not break, so it is still added.
    orders = [{"qty": 2, "promo": "FRAUD_RISK"}]
    result = process_ticket_manifest([make_manifest("premium", orders)], 0.0)
    assert result["total_revenue"] == 180.0
    assert result["status"] == "COMPLETED"


def test_earlybird_discount():
    result = process_ticket_manifest([make_manifest("premium", [{"qty": 2, "promo": "EARLYBIRD"}])], 0.0)
    assert result["total_revenue"] == pytest.approx(144.0)


def test_earlybird_with_large_quantity_gets_no_bulk_discount():
    # 5 * 45 = 225 * 0.8 = 180 (the bulk -20 only applies in the "no promo" branch)
    result = process_ticket_manifest([make_manifest("general", [{"qty": 5, "promo": "EARLYBIRD"}])], 0.0)
    assert result["total_revenue"] == pytest.approx(180.0)


def test_bulk_discount_at_exactly_five_tickets():
    result = process_ticket_manifest([make_manifest("general", [{"qty": 5}])], 0.0)
    assert result["total_revenue"] == 205.0


def test_no_bulk_discount_at_four_tickets():
    result = process_ticket_manifest([make_manifest("general", [{"qty": 4}])], 0.0)
    assert result["total_revenue"] == 180.0


def test_unrecognised_promo_code_behaves_like_no_promo():
    result = process_ticket_manifest([make_manifest("general", [{"qty": 5, "promo": "SAVE50"}])], 0.0)
    assert result["total_revenue"] == 205.0


# ===========================================================================
# exclusive lounge True / False
# ===========================================================================
def test_exclusive_lounge_surcharge_added():
    manifests = [make_manifest("general", [{"qty": 1}], lounge=True)]
    assert process_ticket_manifest(manifests, 0.0)["total_revenue"] == 120.0


def test_lounge_only_manifest_still_earns_surcharge():
    manifests = [make_manifest("general", [], lounge=True)]
    result = process_ticket_manifest(manifests, 0.0)
    assert result == {"total_revenue": 75.0, "status": "COMPLETED"}


# ===========================================================================
# final status: AUDIT_REJECTED / ZERO_SALES / COMPLETED (boundary at 4 / 5)
# ===========================================================================
def test_four_rejections_is_not_an_audit_failure():
    orders = [{"qty": 0} for _ in range(4)] + [{"qty": 1}]
    result = process_ticket_manifest([make_manifest("general", orders)], 0.0)
    assert result == {"total_revenue": 45.0, "status": "COMPLETED"}


def test_five_rejections_triggers_audit_rejected():
    orders = [{"qty": 0} for _ in range(5)] + [{"qty": 1}]
    result = process_ticket_manifest([make_manifest("general", orders)], 0.0)
    assert result == {"total_revenue": 45.0, "status": "AUDIT_REJECTED"}


def test_rejections_accumulate_across_manifests():
    manifests = [
        make_manifest("backstage", [{"qty": 1}]),          # +1 (unknown tier)
        make_manifest("general", [{"qty": 0}] * 3),        # +3
        make_manifest("vip", [{"qty": 1, "promo": "FRAUD_RISK"}]),  # +1 -> 5 total
    ]
    assert process_ticket_manifest(manifests, 0.1)["status"] == "AUDIT_REJECTED"


def test_tax_is_applied_and_rounded():
    # 3 * 45 = 135 * 1.075 = 145.125 -> 145.12 (round-half-even on the float)
    result = process_ticket_manifest([make_manifest("general", [{"qty": 3}])], 0.075)
    assert result["total_revenue"] == pytest.approx(145.12, abs=0.01)
    assert result["status"] == "COMPLETED"


# ===========================================================================
# monitor_gate_flow
# ===========================================================================
def test_gate_flow_no_data_empty_list():
    assert monitor_gate_flow([]) == "NO_DATA"


def test_gate_flow_no_data_none():
    assert monitor_gate_flow(None) == "NO_DATA"


def test_gate_flow_overflow_on_two_consecutive_high_rates():
    assert monitor_gate_flow([[10, 60, 70]]) == "OVERFLOW"


def test_gate_flow_single_spike_is_normal():
    assert monitor_gate_flow([[10, 60, 20]]) == "FLOW_NORMAL"


def test_gate_flow_streak_resets_after_normal_reading():
    assert monitor_gate_flow([[60, 10, 60, 10, 60]]) == "FLOW_NORMAL"


def test_gate_flow_threshold_is_strictly_greater_than_50():
    assert monitor_gate_flow([[50, 50, 50]]) == "FLOW_NORMAL"


def test_gate_flow_streak_does_not_carry_across_streams():
    assert monitor_gate_flow([[60], [60]]) == "FLOW_NORMAL"


def test_gate_flow_overflow_found_in_later_stream():
    assert monitor_gate_flow([[10, 20], [60, 70]]) == "OVERFLOW"


def test_gate_flow_empty_stream_is_normal():
    assert monitor_gate_flow([[]]) == "FLOW_NORMAL"
