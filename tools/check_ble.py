"""Observe actual v0.2 BLE READ/NOTIFY traffic; never infer physical accuracy."""
from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import statistics
import time

DEVICE_NAME = "PRM-Project-2"
SERVICE_UUID = "7c2f1000-73ad-4a0d-9ec4-10cc7ea46a10"
STATE_UUID = "7c2f1001-73ad-4a0d-9ec4-10cc7ea46a10"
STATES = ("calm", "fast", "unattached", "shaking")


def decode_state(payload: bytes | bytearray, *, allow_unavailable: bool = False) -> int | None:
    """Only an empty READ may represent unavailable; notifications are one byte."""
    if not isinstance(payload, (bytes, bytearray)):
        raise ValueError("BLE payload must be bytes")
    if len(payload) == 0 and allow_unavailable:
        return None
    if len(payload) != 1 or payload[0] > 3:
        raise ValueError("Expected exactly one binary unsigned state byte0..3")
    return payload[0]


def notification_record(payload: bytes | bytearray, arrived_s: float) -> dict:
    if not math.isfinite(arrived_s) or arrived_s < 0:
        raise ValueError("Arrival time must be nonnegative and finite")
    state = decode_state(payload)
    return {"arrival_s": arrived_s, "payload_hex": bytes(payload).hex(),
            "length": len(payload), "state_id": state, "state": STATES[state]}


def summarize_notifications(records: list[dict], *, initial_state: int | None,
                            duration_s: float, require_ready: bool,
                            initial_read_arrival_s: float = 0,
                            maximum_interval_s: float = 1.3) -> dict:
    times = [record["arrival_s"] for record in records]
    gaps = [b - a for a, b in zip(times, times[1:])]
    violations = []
    if any(gap <= 0 for gap in gaps):
        violations.append("Notification arrival timestamps did not increase")
    if any(gap > maximum_interval_s for gap in gaps):
        violations.append("Notification interval exceeded1s plus0.3s host tolerance")
    if initial_state is not None and not records:
        violations.append("A valid initial READ had no subsequent state notifications")
    if initial_state is not None and records and times[0] - initial_read_arrival_s > maximum_interval_s:
        violations.append("First valid notification arrived too late after a valid READ")
    if require_ready and len(records) < 2:
        violations.append("Ready check requires at least two valid notifications")
    if records and duration_s - times[-1] > maximum_interval_s:
        violations.append("Notification stream became stale before collection ended")
    repeated = sum(a["state_id"] == b["state_id"] for a, b in zip(records, records[1:]))
    return {
        "valid_notifications": len(records), "state_event_counts": {
            name: sum(record["state_id"] == i for record in records)
            for i, name in enumerate(STATES)},
        "ready_observed": initial_state is not None or bool(records),
        "observed_consecutive_unchanged_notifications": repeated,
        "unchanged_state_repeat_observed": repeated > 0,
        "first_notification_delay_s": times[0] if times else None,
        "notification_interval_s": {"min": min(gaps), "median": statistics.median(gaps),
                                     "max": max(gaps)} if gaps else None,
        "allowed_max_notification_interval_s": maximum_interval_s,
        "violations": violations, "checks_passed": not violations,
        "limitations": [
            "Arrival timing includes operating-system/BLE scheduling;0.3s tolerance is explicit.",
            "Repeated unchanged packets are observed when available, not forced or fabricated.",
            "No physical state label or classifier accuracy is established by BLE telemetry.",
            "An unavailable empty READ with no notifications is legal unless --require-ready is used."]}


async def observe(*, duration: float, output: Path, scan_timeout: float,
                  require_ready: bool) -> dict:
    """Only this function scans actual hardware; tests exercise pure helpers."""
    output.mkdir(parents=True, exist_ok=False)
    report = {"source": "actual_ble_discovery_and_gatt", "device_name": DEVICE_NAME,
              "service_uuid": SERVICE_UUID, "characteristic_uuid": STATE_UUID,
              "started_at_utc": datetime.now(timezone.utc).isoformat(),
              "requested_duration_s": duration, "connection_established": False,
              "checks_passed": False, "error": None}
    records, rejected = [], []
    initial_state = None
    try:
        from bleak import BleakClient, BleakScanner
        discoveries = await BleakScanner.discover(timeout=scan_timeout, return_adv=True)
        candidates = []
        names_seen = []
        for device, advertisement in discoveries.values():
            name = advertisement.local_name or device.name
            if name:
                names_seen.append(name)
            if name == DEVICE_NAME:
                services = [uuid.lower() for uuid in (advertisement.service_uuids or [])]
                if SERVICE_UUID in services:
                    candidates.append(device)
        report["matching_devices"] = [{"name": device.name, "address": device.address}
                                      for device in candidates]
        report["target_name_observed"] = DEVICE_NAME in names_seen
        if len(candidates) != 1:
            raise RuntimeError(f"Expected one exact-name/service device; found{len(candidates)}")
        device = candidates[0]
        async with BleakClient(device, timeout=15) as client:
            report["connection_established"] = bool(client.is_connected)
            service = client.services.get_service(SERVICE_UUID)
            if service is None:
                raise RuntimeError("Required service was not discovered")
            characteristic = service.get_characteristic(STATE_UUID)
            if characteristic is None:
                raise RuntimeError("Required state characteristic was not discovered")
            properties = {prop.lower() for prop in characteristic.properties}
            report["properties"] = sorted(properties)
            if not {"read", "notify"}.issubset(properties):
                raise RuntimeError("State characteristic must support READ and NOTIFY")
            origin = time.monotonic()
            with (output / "notifications.jsonl").open("x", encoding="utf-8") as stream:
                def receive(_sender, data):
                    arrived = time.monotonic() - origin
                    raw = {"arrival_s": arrived, "payload_hex": bytes(data).hex(), "length": len(data)}
                    try:
                        record = notification_record(data, arrived)
                        records.append(record)
                        raw.update(record)
                    except ValueError as exc:
                        raw["error"] = str(exc)
                        rejected.append(str(exc))
                    stream.write(json.dumps(raw, allow_nan=False) + "\n")
                    stream.flush()
                # Subscribe before READ so an update cannot be lost between them.
                await client.start_notify(characteristic, receive)
                initial_bytes = bytes(await client.read_gatt_char(characteristic))
                read_arrival_s = time.monotonic() - origin
                report["initial_read_hex"] = initial_bytes.hex()
                report["initial_read_length"] = len(initial_bytes)
                report["initial_read_arrival_s"] = read_arrival_s
                initial_state = decode_state(initial_bytes, allow_unavailable=True)
                report["initial_state_id"] = initial_state
                await asyncio.sleep(duration)
                report["connected_at_end"] = bool(client.is_connected)
                actual_elapsed = time.monotonic() - origin
                if client.is_connected:
                    await client.stop_notify(characteristic)
                summary = summarize_notifications(records, initial_state=initial_state,
                    duration_s=actual_elapsed, require_ready=require_ready,
                    initial_read_arrival_s=read_arrival_s)
                report.update(summary)
                report["observed_duration_s"] = actual_elapsed
                if not report["connected_at_end"]:
                    report["violations"].append("GATT disconnected during collection")
                if rejected:
                    report["violations"].append("Malformed state notification payloads observed")
                report["checks_passed"] = not report["violations"]
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
        report["checks_passed"] = False
    report["rejected_notifications"] = rejected
    report["raw_valid_notification_count"] = len(records)
    (output / "report.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--duration", type=float, default=10)
    parser.add_argument("--scan-timeout", type=float, default=8)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()
    if not all(math.isfinite(value) and value > 0 for value in (args.duration, args.scan_timeout)):
        parser.error("Duration and scan timeout must be finite and positive")
    try:
        report = asyncio.run(observe(duration=args.duration, output=args.output,
            scan_timeout=args.scan_timeout, require_ready=args.require_ready))
    except (OSError, ValueError) as exc:
        parser.exit(2, f"BLE check could not start: {exc}\n")
    print(json.dumps(report, indent=2, allow_nan=False))
    if not report["checks_passed"]:
        parser.exit(2, "BLE checks not verified; see actual error/report.\n")


if __name__ == "__main__":
    main()
