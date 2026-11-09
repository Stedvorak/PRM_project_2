"""Synthetic BLE payload/timing fixtures only; no hardware scan is performed."""
import pytest

from tools.check_ble import decode_state, notification_record, summarize_notifications


def test_empty_read_is_unavailable_but_notification_must_be_one_byte():
    assert decode_state(b"", allow_unavailable=True) is None
    with pytest.raises(ValueError):
        decode_state(b"")
    for state in range(4):
        assert decode_state(bytes([state])) == state


@pytest.mark.parametrize("payload", [b"\x04", b"0", b"\xff", b"\x00\x01", "0", [0]])
def test_invalid_payloads_never_become_classes(payload):
    with pytest.raises(ValueError):
        decode_state(payload)


def test_unchanged_valid_heartbeats_are_observed():
    records = [notification_record(b"\x02", when) for when in (0.1, 0.9, 1.7, 2.5)]
    report = summarize_notifications(records, initial_state=2, duration_s=3,
                                    require_ready=True)
    assert report["checks_passed"]
    assert report["observed_consecutive_unchanged_notifications"] == 3
    assert report["notification_interval_s"]["max"] == pytest.approx(0.8)
    assert report["state_event_counts"]["unattached"] == 4


def test_unavailable_is_legal_only_when_readiness_is_not_required():
    assert summarize_notifications([], initial_state=None, duration_s=10,
                                   require_ready=False)["checks_passed"]
    assert not summarize_notifications([], initial_state=None, duration_s=10,
                                       require_ready=True)["checks_passed"]
    assert not summarize_notifications([], initial_state=0, duration_s=10,
                                       require_ready=False)["checks_passed"]


def test_stale_or_reordered_arrivals_fail():
    records = [notification_record(b"\x00", when) for when in (0.1, 2.0)]
    assert not summarize_notifications(records, initial_state=0, duration_s=2.5,
                                       require_ready=True)["checks_passed"]
    assert not summarize_notifications(records, initial_state=0, duration_s=10,
                                       require_ready=True)["checks_passed"]
    records = [notification_record(b"\x00", when) for when in (1.0, 0.5)]
    assert not summarize_notifications(records, initial_state=0, duration_s=1.5,
                                       require_ready=True)["checks_passed"]


def test_first_heartbeat_deadline_starts_at_valid_read():
    records = [notification_record(b"\x00", when) for when in (3.0, 3.8)]
    assert not summarize_notifications(records, initial_state=0, duration_s=4,
                                       require_ready=True)["checks_passed"]
    assert summarize_notifications(records, initial_state=0, duration_s=4,
                                   initial_read_arrival_s=2.8,
                                   require_ready=True)["checks_passed"]


@pytest.mark.parametrize("when", [-1, float("nan"), float("inf")])
def test_invalid_arrival_times_rejected(when):
    with pytest.raises(ValueError):
        notification_record(b"\x00", when)
