"""Validate the v0.2 HTTP interface; this does not verify sensor authenticity or BLE.

Usage: python tools/check_contract.py --base-url http://192.168.4.1
Add --require-ready --require-samples for a live, trained-device demonstration.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


STATES = ("calm", "fast", "unattached", "shaking")
STATUS_KEYS = {"ready", "timestamp_ms", "state", "state_id", "probabilities",
               "confidence", "breaths_per_min"}
SIGNAL_KEYS = {"sample_rate_hz", "unit", "samples"}
SAMPLE_KEYS = {"t_ms", "ax_g", "ay_g", "az_g"}


class ContractError(ValueError):
    """A response violates the agreed wire contract."""


def _check(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def _keys(value: object, expected: set[str], context: str) -> None:
    _check(type(value) is dict, f"{context} must be an object")
    _check(set(value) == expected, f"{context} keys must be {sorted(expected)}")


def _number(value: object) -> bool:
    # JSON booleans must not pass Python's bool-is-an-int relationship.
    if type(value) not in (int, float):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def _timestamp(value: object) -> bool:
    return type(value) is int and value >= 0


def validate_status(status: object, *, require_ready: bool = False) -> None:
    """Raise ContractError for a malformed status, including invalid null states."""
    _keys(status, STATUS_KEYS, "status")
    _check(type(status["ready"]) is bool, "ready must be a boolean")
    _check(_timestamp(status["timestamp_ms"]), "timestamp_ms must be a nonnegative integer")
    if not status["ready"]:
        _check(all(status[key] is None for key in (
            "state", "state_id", "probabilities", "confidence", "breaths_per_min"
        )), "unavailable status must have null prediction and rate fields")
        _check(not require_ready, "device is unavailable (--require-ready)")
        return

    state_id = status["state_id"]
    _check(type(state_id) is int and 0 <= state_id <= 3,
           "ready state_id must be an integer from 0 to 3")
    _check(status["state"] == STATES[state_id], "state must match state_id")
    probabilities = status["probabilities"]
    _keys(probabilities, set(STATES), "probabilities")
    values = [probabilities[state] for state in STATES]
    _check(all(_number(value) and 0 <= value <= 1 for value in values),
           "probabilities must be finite numbers in [0,1]")
    _check(abs(sum(values) - 1.0) <= 0.001 + 1e-12,
           "probabilities must sum to 1 within 0.001")
    winner = max(range(4), key=lambda index: values[index])
    _check(state_id == winner, "state_id must identify the maximum probability (lowest ID wins ties)")
    confidence = status["confidence"]
    _check(_number(confidence) and abs(confidence - max(values)) <= 1e-6,
           "confidence must equal the maximum probability")
    rate = status["breaths_per_min"]
    _check(rate is None or (_number(rate) and rate >= 0),
           "breaths_per_min must be null or a finite nonnegative number")


def validate_signal(signal: object, *, require_samples: bool = False) -> None:
    """Validate signal shape/timing; this cannot establish that samples are real."""
    _keys(signal, SIGNAL_KEYS, "signal")
    _check(_number(signal["sample_rate_hz"]) and signal["sample_rate_hz"] == 25,
           "sample_rate_hz must be 25")
    _check(signal["unit"] == "g", 'unit must be "g"')
    samples = signal["samples"]
    _check(type(samples) is list and len(samples) <= 100,
           "samples must be an array of at most 100 samples")
    _check(not require_samples or len(samples) > 0,
           "device returned no samples (--require-samples)")
    previous = -1
    for index, sample in enumerate(samples):
        _keys(sample, SAMPLE_KEYS, f"samples[{index}]")
        timestamp = sample["t_ms"]
        _check(_timestamp(timestamp), f"samples[{index}].t_ms must be a nonnegative integer")
        _check(timestamp > previous, "sample timestamps must be strictly increasing")
        previous = timestamp
        _check(all(_number(sample[axis]) for axis in ("ax_g", "ay_g", "az_g")),
               f"samples[{index}] acceleration values must be finite numbers")


def _unique_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        _check(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ContractError(f"non-JSON numeric constant: {value}")


def fetch_json(url: str, timeout: float = 5.0) -> object:
    request = Request(url, headers={"Accept": "application/json", "Cache-Control": "no-cache"})
    with urlopen(request, timeout=timeout) as response:
        _check(response.status == 200, f"{url}: expected HTTP 200")
        content_type = response.headers.get_content_type()
        _check(content_type == "application/json", f"{url}: expected application/json")
        cache_tokens = {token.strip().lower() for token in response.headers.get("Cache-Control", "").split(",")}
        _check("no-store" in cache_tokens, f"{url}: Cache-Control must include no-store")
        payload = response.read(131073)
        _check(len(payload) <= 131072, f"{url}: response exceeds 128 KiB limit")
    return json.loads(payload.decode("utf-8"), object_pairs_hook=_unique_object,
                      parse_constant=_reject_constant)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://192.168.4.1")
    parser.add_argument("--require-ready", action="store_true")
    parser.add_argument("--require-samples", action="store_true")
    parser.add_argument("--timeout", type=float, default=5.0)
    args = parser.parse_args(argv)
    if args.timeout <= 0 or not math.isfinite(args.timeout):
        parser.error("--timeout must be finite and positive")
    base = args.base_url.rstrip("/")
    try:
        status = fetch_json(base + "/api/status", args.timeout)
        validate_status(status, require_ready=args.require_ready)
        signal = fetch_json(base + "/api/signal", args.timeout)
        validate_signal(signal, require_samples=args.require_samples)
    except (ContractError, HTTPError, URLError, TimeoutError, OSError,
            UnicodeError, json.JSONDecodeError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(f"PASS: HTTP v0.2 shape and headers; ready={status['ready']}, samples={len(signal['samples'])}")
    print("This check does not verify measurement authenticity, classification quality, or BLE behavior.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
