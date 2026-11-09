"""Synthetic software fixtures, never hardware timing or accuracy evidence."""
import copy
import json

import pytest

from tools.check_inference import PREFIX, collect, parse_diagnostic, summarize, timing_statistics


def event(offset=0):
    return {"t_ms": 10000 + offset, "state_id": 2,
            "feature_us": 20, "predict_us": 5, "total_us": 30,
            "probabilities": [0.1, 0.2, 0.6, 0.1],
            "window_first_ms": 6000 + offset, "window_last_ms": 9960 + offset,
            "sample_gap_ms": 40}


def line(item):
    return PREFIX + json.dumps(item) + "\n"


def test_valid_diagnostic_and_non_diagnostic_lines():
    assert parse_diagnostic(line(event())) == event()
    assert parse_diagnostic("# Boot ready\n") is None
    assert parse_diagnostic("500,0,0,1,0,0,0\n") is None


@pytest.mark.parametrize("field,value", [
    ("state_id", 4), ("state_id", True), ("feature_us", -1),
    ("predict_us", 1.5), ("total_us", 24), ("sample_gap_ms", 0),
    ("window_first_ms", 11000), ("window_last_ms", 11000),
    ("probabilities", [0.1, 0.2, 0.7]),
    ("probabilities", [0.1, 0.2, 0.6, 0.2]),
    ("probabilities", [0.1, 0.8, 0.1, 0.0]),
    ("probabilities", [0.1, 0.2, float("nan"), 0.7]),
])
def test_malformed_or_inconsistent_event_rejected(field, value):
    item = event()
    item[field] = value
    with pytest.raises(ValueError):
        parse_diagnostic(line(item))


def test_duplicate_json_keys_and_unexpected_fields_rejected():
    with pytest.raises(ValueError, match="Duplicate"):
        parse_diagnostic(PREFIX + '{"t_ms":0,"t_ms":1}')
    item = event()
    item["extra"] = 1
    with pytest.raises(ValueError, match="fields"):
        parse_diagnostic(line(item))


def test_argmax_tie_requires_lowest_id():
    item = event()
    item["probabilities"] = [0.5, 0.5, 0, 0]
    item["state_id"] = 0
    assert parse_diagnostic(line(item))["state_id"] == 0
    item["state_id"] = 1
    with pytest.raises(ValueError, match="argmax"):
        parse_diagnostic(line(item))


def test_timing_statistics_and_real_time_summary():
    events = [event(offset) for offset in (0, 500, 1000)]
    report = summarize(events)
    assert report["real_time_checks_passed"]
    assert report["observed_event_rate_hz"] == 2
    assert report["inference_event_interval_ms"]["median"] == 500
    assert report["total_us"]["p95"] == 30
    assert report["operator_state_check"] is None
    assert report["state_event_counts"]["unattached"] == 3
    assert timing_statistics([4, 1, 2, 3])["median"] == 2.5
    assert timing_statistics([]) is None


def test_summary_rejects_deadline_continuity_and_cadence_failures():
    events = [event(offset) for offset in (0, 1500, 3000)]
    events[0]["total_us"] = 500000
    events[1]["sample_gap_ms"] = 81
    report = summarize(events)
    assert not report["real_time_checks_passed"]
    assert len(report["violations"]) == 3
    assert not summarize([])["real_time_checks_passed"]
    assert not summarize([event(), event(), event()])["real_time_checks_passed"]


def test_operator_state_check_is_explicit_and_separate():
    report = summarize([event(i * 500) for i in range(3)], expected_state="unattached")
    assert report["operator_state_check"]["matching_fraction"] == 1
    assert "not independent" in report["operator_state_check"]["limitation"]
    with pytest.raises(ValueError, match="Unknown"):
        summarize([], expected_state="invented")


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


class SyntheticSerial:
    def __init__(self, lines, clock):
        self.lines = iter(lines)
        self.clock = clock

    def readline(self, size):
        self.clock.now += 0.5
        return next(self.lines, b"")


def test_collect_preserves_actual_received_bytes_and_exclusive_outputs(tmp_path):
    fixture = [line(event(i * 500)).encode("ascii") for i in range(3)]
    clock = FakeClock()
    destination = tmp_path / "software_only"
    report = collect(SyntheticSerial(fixture, clock), duration=2,
                     output=destination, clock=clock)
    assert report["real_time_checks_passed"]
    assert (destination / "raw_serial.log").read_bytes() == b"".join(fixture)
    assert len((destination / "events.jsonl").read_text().splitlines()) == 3
    assert json.loads((destination / "report.json").read_text())["valid_events"] == 3
    with pytest.raises(FileExistsError):
        collect(SyntheticSerial([], clock), duration=2, output=destination, clock=clock)


def test_collect_reports_reordered_and_malformed_data_without_fabrication(tmp_path):
    fixture = [line(event()).encode("ascii"), line(event()).encode("ascii"),
               b'# INFERENCE {"incomplete":1}', b"boot noise\n"]
    clock = FakeClock()
    report = collect(SyntheticSerial(fixture, clock), duration=3,
                     output=tmp_path / "bad_software_fixture", clock=clock)
    assert report["valid_events"] == 1
    assert len(report["rejected_diagnostics"]) == 2
    assert not report["real_time_checks_passed"]
