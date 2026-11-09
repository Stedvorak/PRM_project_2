"""Record actual 50Hz MPU-6050 serial samples; never generate missing readings."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re
import time
import uuid

LABELS = ("calm", "fast", "unattached", "shaking")
COLUMNS = ("t_ms", "ax_g", "ay_g", "az_g", "gx_dps", "gy_dps", "gz_dps")
RATE_HZ = 50
PERIOD_MS = 20


def probe_stream(connection, *, timeout: float = 10, clock=time.monotonic) -> dict:
    """Observe actual firmware identity/config diagnostics without assigning a class."""
    started = clock()
    address = None
    configured = False
    lines = []
    while clock() - started < timeout:
        raw = connection.readline(512)
        if not raw:
            continue
        line = raw.decode("ascii", errors="replace").strip()
        if line.startswith("#"):
            lines.append(line)
            print(line)
        match = re.fullmatch(r"# DETECT PASS address=0x(68|69) who_am_i=0x68", line)
        if match:
            address = "0x" + match.group(1)
        if line.startswith("# CONFIG PASS rate_hz=50 "):
            configured = True
        if address is not None and configured:
            return {"verified": True, "address": address, "diagnostics": lines}
    return {"verified": False, "address": address, "diagnostics": lines}


def parse_record(line: str) -> tuple[int, float, float, float, float, float, float]:
    """Reject malformed data instead of replacing any field with zero."""
    parts = line.strip().split(",")
    if len(parts) != 7:
        raise ValueError("expected seven CSV fields")
    try:
        stamp = int(parts[0])
        axes = tuple(float(value) for value in parts[1:])
    except ValueError as exc:
        raise ValueError("nonnumeric sample") from exc
    if stamp < 0 or not all(math.isfinite(value) for value in axes):
        raise ValueError("invalid timestamp or nonfinite axes")
    return (stamp, *axes)


def unique_paths(output_dir: Path, label: str) -> tuple[Path, Path]:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
    base = f"{stamp}_{label}_{uuid.uuid4().hex[:8]}"
    return output_dir / f"{base}.csv", output_dir / f"{base}.json"


def record_stream(connection, csv_path: Path, metadata_path: Path, *, label: str,
                  duration: float, no_data_timeout: float = 10,
                  clock=time.monotonic) -> dict:
    """Preserve received rows and finalize metadata even on interrupted sessions.

    connection must provide readline(size). Tests pass explicit synthetic serial
    fixtures; this function does not construct or fill any sensor measurements.
    """
    if label not in LABELS or not math.isfinite(duration) or duration <= 0:
        raise ValueError("valid label and positive finite duration required")
    if not math.isfinite(no_data_timeout) or no_data_timeout <= 0:
        raise ValueError("no-data-timeout must be positive and finite")
    if csv_path.exists() or metadata_path.exists():
        raise FileExistsError("refusing to overwrite session files")
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    started_utc = datetime.now(timezone.utc).isoformat()
    count = malformed = line_count = missing = gaps = diagnostics_count = 0
    first_t = previous_t = None
    largest_gap = 0
    diagnostics = []
    detection_seen = configuration_seen = False
    error = None
    complete = False
    opened_at = last_received_at = clock()
    sample_started_at = None
    # Exclusive creation protects originals, including timestamp collisions.
    with csv_path.open("x", newline="", encoding="utf-8") as csv_file, \
            metadata_path.open("x", encoding="utf-8") as metadata_file:
        writer = csv.writer(csv_file)
        writer.writerow(COLUMNS)
        try:
            while True:
                now = clock()
                if sample_started_at is not None and now - sample_started_at >= duration:
                    complete = True
                    break
                if now - last_received_at >= no_data_timeout:
                    error = "no valid sensor samples within timeout"
                    break
                raw = connection.readline(512)
                if not raw:
                    continue
                line_count += 1
                try:
                    line = raw.decode("ascii", errors="strict")
                except UnicodeDecodeError:
                    malformed += 1
                    continue
                if line.startswith("#"):
                    diagnostics_count += 1
                    if len(diagnostics) < 100:
                        diagnostics.append(line.strip())
                    if line.startswith("# DETECT PASS "):
                        detection_seen = True
                    if line.startswith("# CONFIG PASS rate_hz=50 "):
                        configuration_seen = True
                    continue
                if line.strip() == ",".join(COLUMNS):
                    continue
                if not line.endswith("\n"):
                    malformed += 1
                    continue
                try:
                    sample = parse_record(line)
                except ValueError:
                    malformed += 1
                    continue
                stamp = sample[0]
                if previous_t is not None:
                    delta = stamp - previous_t
                    if delta <= 0:
                        error = "timestamp reset, backward timestamp or duplicate; stopped session"
                        break
                    largest_gap = max(largest_gap, delta)
                    estimated = max(0, int(math.floor(delta / PERIOD_MS + 0.5)) - 1)
                    if estimated:
                        gaps += 1
                        missing += estimated
                else:
                    first_t = stamp
                    sample_started_at = clock()
                writer.writerow(sample)
                previous_t = stamp
                count += 1
                last_received_at = clock()
        except KeyboardInterrupt:
            error = "operator interrupted recording; genuine partial rows preserved"
        except (OSError, RuntimeError) as exc:
            error = f"serial recording failed: {exc}"
        finally:
            csv_file.flush()
            elapsed = clock() - opened_at
            span_ms = previous_t - first_t if first_t is not None and count > 1 else 0
            metadata = {
                "source": "real_sensor",
                "label_source": "operator observation; software cannot establish ground truth",
                "label": label,
                "recording_id": csv_path.stem,
                "csv_file": csv_path.name,
                "started_at_utc": started_utc,
                "requested_duration_s": duration,
                "host_elapsed_s": elapsed,
                "sample_rate_hz": RATE_HZ,
                "observed_sample_rate_hz": 1000 * (count - 1) / span_ms if span_ms else None,
                "units": {"t_ms": "ms since ESP32 boot", "ax_g": "g", "ay_g": "g",
                          "az_g": "g", "gx_dps": "deg/s", "gy_dps": "deg/s", "gz_dps": "deg/s"},
                "sensor_settings": {"accel_range_g": 2, "gyro_range_dps": 250,
                                    "dlpf_hz": 10, "sda_gpio": 8, "scl_gpio": 9,
                                    "settings_source": "acquisition firmware defaults; inspect diagnostics for overrides"},
                "valid_samples": count,
                "nominal_expected_samples": int(round(duration * RATE_HZ)),
                "nominal_count_shortfall": max(0, int(round(duration * RATE_HZ)) - count),
                "received_lines": line_count,
                "malformed_records_rejected": malformed,
                "diagnostic_lines": diagnostics_count,
                "diagnostics": diagnostics,
                "detection_pass_observed": detection_seen,
                "configuration_pass_observed": configuration_seen,
                "estimated_missing_samples": missing,
                "gap_events": gaps,
                "max_gap_ms": largest_gap if count > 1 else None,
                "missing_estimate_method": "max(0, round-half-up(delta_ms/20)-1); includes rejected/missed rows, no interpolation",
                "first_t_ms": first_t,
                "last_t_ms": previous_t,
                "complete": complete and count >= 2,
                "error": error,
                "training_note": "50Hz raw recording; M01 v1 expects25Hz. Preserve raw data and explicitly downsample before training.",
            }
            json.dump(metadata, metadata_file, indent=2, allow_nan=False)
            metadata_file.write("\n")
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", required=True)
    parser.add_argument("--label", choices=LABELS)
    parser.add_argument("--detect-only", action="store_true",
                        help="Read WHO_AM_I/config diagnostics without labeling or saving a recording")
    parser.add_argument("--reset", action="store_true",
                        help="Reset board through CH343 RTS before reading startup diagnostics")
    parser.add_argument("--duration", type=float, default=30)
    parser.add_argument("--output-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--no-data-timeout", type=float, default=10)
    args = parser.parse_args()
    if not math.isfinite(args.duration) or args.duration <= 0:
        parser.error("duration must be positive and finite")
    if not math.isfinite(args.no_data_timeout) or args.no_data_timeout <= 0:
        parser.error("no-data-timeout must be positive and finite")
    if not args.detect_only and args.label is None:
        parser.error("--label is required when recording")
    import serial
    if not args.detect_only:
        csv_path, metadata_path = unique_paths(args.output_dir, args.label)
        print(f"REAL acquisition: hold label '{args.label}' before opening the port and throughout recording.")
    print("Port opening may reset the board. Duration starts at the first valid sample; no-data timeout is separate.")
    try:
        with serial.Serial(args.port, 115200, timeout=0.25) as connection:
            if args.reset:
                # CH343 ESP32 auto-reset circuit: GPIO0 high, pulse EN low, release.
                connection.dtr = False
                connection.rts = True
                time.sleep(0.1)
                connection.rts = False
                time.sleep(0.1)
            if args.detect_only:
                result = probe_stream(connection, timeout=args.no_data_timeout)
                if not result["verified"]:
                    parser.exit(2, "Sensor detection/configuration not verified; inspect wiring and flash the acquisition firmware.\n")
                print(f"Observed genuine firmware WHO_AM_I/config test PASS at {result['address']}; no label or training file assigned.")
                return
            result = record_stream(connection, csv_path, metadata_path, label=args.label,
                                   duration=args.duration, no_data_timeout=args.no_data_timeout)
    except (OSError, serial.SerialException, ValueError) as exc:
        parser.exit(2, f"Recording failed: {exc}\n")
    print(f"Saved {result['valid_samples']} real samples: {csv_path}")
    print(f"Metadata: {metadata_path}")
    print(f"Rejected malformed: {result['malformed_records_rejected']}; estimated missing: {result['estimated_missing_samples']}; gaps: {result['gap_events']}")
    print(f"Nominal count target: {result['nominal_expected_samples']}; count shortfall: {result['nominal_count_shortfall']} (not interpolated)")
    print(f"Observed rate: {result['observed_sample_rate_hz']} Hz (target50Hz)")
    if not result["complete"]:
        parser.exit(2, f"Session incomplete: {result['error'] or 'insufficient samples'}. Partial real data preserved.\n")


if __name__ == "__main__":
    main()
