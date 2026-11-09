"""Collect actual on-board inference timing; never infer accuracy without labels.

The serial diagnostic stream is testing-only and is separate from the v0.2
BLE/HTTP contract. The computer parses telemetry; it does not perform inference.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import statistics
import time

PREFIX = "# INFERENCE "
STATES = ("calm", "fast", "unattached", "shaking")
KEYS = {"t_ms", "state_id", "feature_us", "predict_us", "total_us",
        "probabilities", "window_first_ms", "window_last_ms", "sample_gap_ms"}


def _constant(value):
    raise ValueError(f"Nonfinite JSON constant: {value}")


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def parse_diagnostic(line: str) -> dict | None:
    if not line.startswith(PREFIX):
        return None
    event = json.loads(line[len(PREFIX):], parse_constant=_constant, object_pairs_hook=_object)
    if not isinstance(event, dict) or set(event) != KEYS:
        raise ValueError("Unexpected inference diagnostic fields")
    for key in KEYS - {"probabilities"}:
        if type(event[key]) is not int or event[key] < 0:
            raise ValueError(f"{key} must be a nonnegative integer")
    state = event["state_id"]
    if state not in range(4):
        raise ValueError("state_id must be in0..3")
    probs = event["probabilities"]
    if not isinstance(probs, list) or len(probs) != 4 or any(
        type(p) not in (int, float) or not math.isfinite(p) or not 0 <= p <= 1
        for p in probs
    ):
        raise ValueError("Four finite probabilities in[0,1] required")
    if abs(sum(probs) - 1) > 0.001:
        raise ValueError("Probabilities do not sum to one")
    if state != max(range(4), key=lambda index: probs[index]):
        raise ValueError("state_id does not match lowest-ID argmax")
    if not event["window_first_ms"] < event["window_last_ms"] <= event["t_ms"]:
        raise ValueError("Window timestamps inconsistent with inference timestamp")
    if event["feature_us"] + event["predict_us"] > event["total_us"]:
        raise ValueError("total_us smaller than measured components")
    if event["sample_gap_ms"] <= 0:
        raise ValueError("sample_gap_ms must describe actual advancing samples")
    return event


def timing_statistics(values: list[int]) -> dict | None:
    if not values:
        return None
    ordered = sorted(values)
    return {"min": ordered[0], "median": statistics.median(ordered),
            "p95": ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)],
            "max": ordered[-1], "mean": statistics.mean(ordered)}


def summarize(events: list[dict], *, budget_us: int = 500000,
              max_sample_gap_ms: int = 80, max_event_gap_ms: int = 1000,
              expected_state: str | None = None, minimum_events: int = 3) -> dict:
    if expected_state is not None and expected_state not in STATES:
        raise ValueError("Unknown expected state")
    violations = []
    if len(events) < minimum_events:
        violations.append(f"Only{len(events)} valid events; need at least{minimum_events}")
    times = [event["t_ms"] for event in events]
    gaps = [b - a for a, b in zip(times, times[1:])]
    if any(gap <= 0 for gap in gaps):
        violations.append("Event timestamps duplicate or move backwards")
    if any(gap > max_event_gap_ms for gap in gaps):
        violations.append("Inference telemetry cadence exceeded allowed event gap")
    late = sum(event["total_us"] >= budget_us for event in events)
    stale = sum(event["sample_gap_ms"] > max_sample_gap_ms for event in events)
    if late:
        violations.append(f"{late} inference computations missed the execution budget")
    if stale:
        violations.append(f"{stale} windows contain excessive sample gaps")
    counts = {state: sum(event["state_id"] == i for event in events)
              for i, state in enumerate(STATES)}
    # An operator-supplied one-state check is not a four-class accuracy test.
    expected = None
    if expected_state is not None:
        matched = counts[expected_state]
        expected = {"operator_expected_state": expected_state, "matching_events": matched,
                    "total_events": len(events),
                    "matching_fraction": matched / len(events) if events else None,
                    "limitation": "Single operator-observed state; not independent held-out accuracy."}
    return {
        "source": "real_on_board_serial_telemetry", "valid_events": len(events),
        "execution_budget_us": budget_us, "max_allowed_sample_gap_ms": max_sample_gap_ms,
        "max_allowed_event_gap_ms": max_event_gap_ms,
        "feature_us": timing_statistics([event["feature_us"] for event in events]),
        "predict_us": timing_statistics([event["predict_us"] for event in events]),
        "total_us": timing_statistics([event["total_us"] for event in events]),
        "inference_event_interval_ms": timing_statistics(gaps) if all(gap > 0 for gap in gaps) else None,
        "observed_event_rate_hz": (1000 * (len(times) - 1) / (times[-1] - times[0])
                                   if len(times) > 1 and times[-1] > times[0] else None),
        "sample_gap_ms": timing_statistics([event["sample_gap_ms"] for event in events]),
        "state_event_counts": counts, "operator_state_check": expected,
        "violations": violations, "real_time_checks_passed": not violations,
        "limitations": ["Telemetry checks computation time and data continuity, not physical class correctness.",
                        "USB telemetry is testing-only; final demonstration firmware must disable it.",
                        "Serial transmission time is outside feature/prediction timing; event cadence is checked separately."]}


def collect(connection, *, duration: float, output: Path, clock=time.monotonic,
            expected_state: str | None = None, budget_us: int = 500000,
            max_sample_gap_ms: int = 80, max_event_gap_ms: int = 1000) -> dict:
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("duration must be finite and positive")
    output.mkdir(parents=True, exist_ok=False)
    events, rejected = [], []
    started_utc = datetime.now(timezone.utc).isoformat()
    started = clock()
    interrupted = False
    with (output / "raw_serial.log").open("xb") as raw_file, \
            (output / "events.jsonl").open("x", encoding="utf-8") as event_file:
        try:
            while clock() - started < duration:
                raw = connection.readline(4096)
                if not raw:
                    continue
                raw_file.write(raw)
                try:
                    line = raw.decode("ascii", errors="strict")
                    if line.startswith(PREFIX) and not line.endswith("\n"):
                        raise ValueError("Incomplete diagnostic line")
                    event = parse_diagnostic(line)
                    if event is None:
                        continue
                    if events and event["t_ms"] <= events[-1]["t_ms"]:
                        raise ValueError("Non-increasing diagnostic timestamps; possible board reset")
                    events.append(event)
                    event_file.write(json.dumps(event, allow_nan=False) + "\n")
                except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                    # Boot noise is preserved but only malformed diagnostic lines
                    # count against this stream's schema.
                    if raw.startswith(PREFIX.encode("ascii")):
                        rejected.append(str(exc))
        except KeyboardInterrupt:
            interrupted = True
        except OSError as exc:
            rejected.append(f"Serial I/O failure: {exc}")
    report = summarize(events, budget_us=budget_us, max_sample_gap_ms=max_sample_gap_ms,
                       max_event_gap_ms=max_event_gap_ms, expected_state=expected_state)
    report.update({"started_at_utc": started_utc,
                   "requested_duration_s": duration, "host_elapsed_s": clock() - started,
                   "interrupted": interrupted, "rejected_diagnostics": rejected})
    if rejected or interrupted:
        report["real_time_checks_passed"] = False
        report["violations"].append("Interrupted collection or malformed/reordered diagnostic records")
    (output / "report.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", required=True)
    parser.add_argument("--duration", type=float, default=15)
    parser.add_argument("--output", type=Path, required=True,
                        help="New, non-existing verification directory")
    parser.add_argument("--expected-state", choices=STATES)
    parser.add_argument("--budget-us", type=int, default=500000)
    parser.add_argument("--max-sample-gap-ms", type=int, default=80)
    parser.add_argument("--max-event-gap-ms", type=int, default=1000)
    args = parser.parse_args()
    if not math.isfinite(args.duration) or args.duration <= 0 or min(
        args.budget_us, args.max_sample_gap_ms, args.max_event_gap_ms
    ) <= 0:
        parser.error("Duration and all budgets must be positive and finite")
    import serial
    try:
        with serial.Serial(args.port, 115200, timeout=0.25) as connection:
            report = collect(connection, duration=args.duration, output=args.output,
                             expected_state=args.expected_state, budget_us=args.budget_us,
                             max_sample_gap_ms=args.max_sample_gap_ms,
                             max_event_gap_ms=args.max_event_gap_ms)
    except (OSError, ValueError, serial.SerialException) as exc:
        parser.exit(2, f"Inference verification failed: {exc}\n")
    print(json.dumps(report, indent=2, allow_nan=False))
    if not report["real_time_checks_passed"]:
        parser.exit(2, "Real-time telemetry checks did not pass; see preserved report/raw log.\n")


if __name__ == "__main__":
    main()
