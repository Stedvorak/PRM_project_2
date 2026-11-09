"""Synthetic serial fixtures only; no hardware/data-collection claims."""
import csv
import json

import pytest

from tools.record_session import parse_record, probe_stream, record_stream, unique_paths


class Clock:
    def __init__(self):
        self.value = 0.0

    def __call__(self):
        return self.value


class SyntheticSerial:
    def __init__(self, lines, clock):
        self.lines = iter(lines)
        self.clock = clock

    def readline(self, size):
        self.clock.value += 0.02
        return next(self.lines, b"")


@pytest.mark.parametrize("line", ["", "1,2", "1,nan,0,0,0,0,0", "-1,0,0,0,0,0,0",
                                 "1,inf,0,0,0,0,0", "1.5,0,0,0,0,0,0"])
def test_malformed_sample_rejected_without_substitution(line):
    with pytest.raises(ValueError):
        parse_record(line)


def test_sample_parse_preserves_actual_numeric_values():
    assert parse_record("20,0.1,-0.2,1,2,3,-4\n") == (20, 0.1, -0.2, 1, 2, 3, -4)


def test_unique_timestamped_files(tmp_path):
    first = unique_paths(tmp_path, "calm")
    second = unique_paths(tmp_path, "calm")
    assert first != second
    assert "_calm_" in first[0].stem
    assert first[0].suffix == ".csv" and first[1].suffix == ".json"


def test_rejected_rows_and_timestamp_reset_keep_real_partial(tmp_path):
    clock = Clock()
    connection = SyntheticSerial([
        b"# DETECT PASS address=0x68 who_am_i=0x68\n",
        b"# CONFIG PASS rate_hz=50 accel_unit=g gyro_unit=deg/s\n",
        b"t_ms,ax_g,ay_g,az_g,gx_dps,gy_dps,gz_dps\n",
        b"malformed\n", b"40,nan,0,0,0,0,0\n", b"40,0,0,1,0,0,0",
        b"40,0,0,1,0,0,0\n", b"60,0.1,0,1,1,0,0\n",
        b"40,0,0,1,0,0,0\n",
    ], clock)
    csv_path, metadata_path = tmp_path / "partial.csv", tmp_path / "partial.json"
    result = record_stream(connection, csv_path, metadata_path, label="calm", duration=30, clock=clock)
    assert result["valid_samples"] == 2
    assert result["malformed_records_rejected"] == 3
    assert not result["complete"]
    assert "timestamp reset" in result["error"]
    assert result["detection_pass_observed"] and result["configuration_pass_observed"]
    saved = list(csv.DictReader(csv_path.open()))
    assert [row["t_ms"] for row in saved] == ["40", "60"]
    assert json.loads(metadata_path.read_text())["valid_samples"] == 2


def test_gap_reports_missing_samples_without_inventing_rows(tmp_path):
    clock = Clock()
    lines = [f"{t},0,0,1,0,0,0\n".encode() for t in [0, 20, 80, 100, 120, 140, 160, 180]]
    csv_path, metadata_path = tmp_path / "gaps.csv", tmp_path / "gaps.json"
    result = record_stream(SyntheticSerial(lines, clock), csv_path, metadata_path,
                           label="fast", duration=0.12, clock=clock)
    assert result["complete"]
    assert result["estimated_missing_samples"] == 2
    assert result["gap_events"] == 1
    assert result["max_gap_ms"] == 60
    assert len(list(csv.DictReader(csv_path.open()))) == result["valid_samples"]
    assert result["units"]["gx_dps"] == "deg/s"
    assert result["sample_rate_hz"] == 50


def test_missing_sensor_times_out_without_numeric_samples(tmp_path):
    clock = Clock()
    connection = SyntheticSerial([b"# DETECT FAIL no verified MPU-6050\n"] * 20, clock)
    result = record_stream(connection, tmp_path / "none.csv", tmp_path / "none.json",
                           label="unattached", duration=30, no_data_timeout=0.1, clock=clock)
    assert not result["complete"]
    assert result["valid_samples"] == 0
    assert result["observed_sample_rate_hz"] is None
    assert result["first_t_ms"] is None
    assert "no valid sensor" in result["error"]


def test_original_recordings_cannot_be_overwritten(tmp_path):
    csv_path = tmp_path / "original.csv"
    csv_path.write_text("original\n")
    with pytest.raises(FileExistsError):
        record_stream(None, csv_path, tmp_path / "meta.json", label="calm", duration=1)
    assert csv_path.read_text() == "original\n"


def test_probe_requires_real_identity_and_configuration_diagnostics():
    clock = Clock()
    result = probe_stream(SyntheticSerial([
        b"# DETECT candidate=0x68 ack=1 who_am_i=0x12 rejected\n",
        b"# DETECT PASS address=0x69 who_am_i=0x68\n",
        b"# CONFIG PASS rate_hz=50 accel_unit=g gyro_unit=deg/s\n",
    ], clock), clock=clock)
    assert result["verified"] and result["address"] == "0x69"


def test_probe_ack_alone_never_verifies_sensor():
    clock = Clock()
    result = probe_stream(SyntheticSerial([
        b"# DETECT candidate=0x68 ack=1 who_am_i=0x12 rejected\n",
    ], clock), timeout=0.1, clock=clock)
    assert not result["verified"]
