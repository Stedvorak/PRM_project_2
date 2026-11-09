"""Capture one genuinely observed labeled MPU-6050 recording over USB serial.

USB data is allowed for acquisition/training, not for the independent live demo.
Run a data-collection firmware build; demo builds must emit no serial data.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import time


STATES = ("calm", "fast", "unattached", "shaking")
COLUMNS = ("t_ms", "ax_g", "ay_g", "az_g", "gx_dps", "gy_dps", "gz_dps")


def parse_sample(line: str) -> list[int | float] | None:
    """Ignore boot/log lines, but never convert them into measured samples."""
    parts = line.strip().split(",")
    if len(parts) != 7:
        return None
    try:
        timestamp = int(parts[0])
        values = [float(value) for value in parts[1:]]
    except ValueError:
        return None
    if timestamp < 0 or not all(math.isfinite(value) for value in values):
        return None
    return [timestamp, *values]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", required=True, help="For example COM5")
    parser.add_argument("--state", choices=STATES, required=True)
    parser.add_argument("--recording-id", required=True,
                        help="Unique session/take identifier, not a reused label")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seconds", type=float, default=30)
    parser.add_argument("--baud", type=int, default=115200)
    args = parser.parse_args()
    if not math.isfinite(args.seconds) or args.seconds < 4:
        parser.error("Capture duration must be at least four seconds")
    if not args.recording_id.strip():
        parser.error("recording-id cannot be empty")
    metadata_path = args.output.with_suffix(args.output.suffix + ".json")
    if args.output.exists() or metadata_path.exists():
        parser.error("Refusing to overwrite a recording or its metadata")
    try:
        import serial
    except ImportError:
        parser.exit(2, "pyserial is required for real acquisition: python -m pip install pyserial==3.5\n")
    count, previous = 0, None
    gaps = []
    args.output.parent.mkdir(parents=True, exist_ok=True)
    print(f"Capture REAL {args.state}: maintain this state for {args.seconds:g} seconds.")
    print("Do not change the label during this recording. Ctrl+C ends capture.")
    try:
        with serial.Serial(args.port, args.baud, timeout=0.25) as connection:
            # Many boards reset upon serial opening; wait for boot, then discard
            # buffered boot lines so capture reflects the requested labeled interval.
            time.sleep(2)
            connection.reset_input_buffer()
            started = time.monotonic()
            with args.output.open("x", newline="", encoding="utf-8") as stream:
                writer = csv.writer(stream)
                writer.writerow(COLUMNS)
                try:
                    while time.monotonic() - started < args.seconds:
                        sample = parse_sample(connection.readline().decode("ascii", errors="replace"))
                        if sample is None:
                            continue
                        timestamp = int(sample[0])
                        if previous is not None:
                            if timestamp <= previous:
                                raise ValueError("Timestamp reset/duplicate: recording stopped; do not train on it")
                            gaps.append(timestamp - previous)
                        writer.writerow(sample)
                        count += 1
                        previous = timestamp
                except KeyboardInterrupt:
                    print("Capture interrupted; retained only samples actually received.")
    except (OSError, serial.SerialException, ValueError) as exc:
        parser.exit(2, f"Capture failed: {exc}. Inspect any partial CSV before use.\n")
    metadata = {"source": "real_sensor", "sample_rate_hz": 25,
        "recording_id": args.recording_id, "state": args.state,
        "path": args.output.name, "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "samples": count, "complete_window_available": count >= 100,
        "max_gap_ms": max(gaps) if gaps else None,
        "observed_sample_rate_hz": (1000 * len(gaps) / sum(gaps)) if gaps else None}
    with metadata_path.open("x", encoding="utf-8") as stream:
        json.dump(metadata, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(f"Saved {count} real samples to {args.output}; metadata: {metadata_path}")
    if count < 100:
        parser.exit(2, "Insufficient samples for a four-second window; record again to a NEW file.\n")


if __name__ == "__main__":
    main()
