"""Software-only contract fixtures: these are not hardware measurements."""

from email.message import Message
import importlib.util
import io
from pathlib import Path
import unittest
from unittest.mock import patch


_spec = importlib.util.spec_from_file_location(
    "check_contract", Path(__file__).parents[1] / "tools" / "check_contract.py"
)
contract = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(contract)


def unavailable():
    return dict(ready=False, timestamp_ms=0, state=None, state_id=None,
                probabilities=None, confidence=None, breaths_per_min=None)


def available():
    return dict(ready=True, timestamp_ms=4400, state="fast", state_id=1,
                probabilities=dict(calm=0.1, fast=0.7, unattached=0.1, shaking=0.1),
                confidence=0.7, breaths_per_min=None)


def signal():
    return dict(sample_rate_hz=25, unit="g", samples=[
        dict(t_ms=0, ax_g=0.0, ay_g=0.0, az_g=1.0),
        dict(t_ms=40, ax_g=0.1, ay_g=-0.1, az_g=0.9),
    ])


class StatusContractTests(unittest.TestCase):
    def test_unavailable_is_valid_but_fails_ready_requirement(self):
        contract.validate_status(unavailable())
        with self.assertRaises(contract.ContractError):
            contract.validate_status(unavailable(), require_ready=True)

    def test_available_prediction_and_optional_rate(self):
        status = available()
        contract.validate_status(status, require_ready=True)
        status["breaths_per_min"] = 23.5
        contract.validate_status(status)

    def test_wrong_or_missing_keys(self):
        for key in available():
            status = available()
            del status[key]
            with self.subTest(missing=key), self.assertRaises(contract.ContractError):
                contract.validate_status(status)
        status = available()
        status["debug"] = True
        with self.assertRaises(contract.ContractError):
            contract.validate_status(status)

    def test_unavailable_never_exposes_old_prediction(self):
        for key, value in available().items():
            if key in ("ready", "timestamp_ms", "breaths_per_min"):
                continue
            status = unavailable()
            status[key] = value
            with self.subTest(key=key), self.assertRaises(contract.ContractError):
                contract.validate_status(status)

    def test_types_ranges_mapping_and_finiteness(self):
        changes = [
            ("ready", 1), ("timestamp_ms", True), ("timestamp_ms", 1.0),
            ("timestamp_ms", -1), ("state_id", True), ("state_id", 4),
            ("state_id", 1.0), ("state", "calm"), ("state", None),
            ("confidence", None), ("confidence", True), ("confidence", 0.6),
            ("confidence", float("nan")), ("breaths_per_min", -1),
            ("breaths_per_min", True), ("breaths_per_min", float("inf")),
        ]
        for key, value in changes:
            status = available()
            status[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(contract.ContractError):
                contract.validate_status(status)

    def test_bad_probabilities(self):
        options = [None, [], dict(calm=0.1, fast=0.9),
                   dict(calm=-0.1, fast=0.9, unattached=0.1, shaking=0.1),
                   dict(calm=0.1, fast=0.8, unattached=0.1, shaking=0.1),
                   dict(calm=True, fast=0, unattached=0, shaking=0),
                   dict(calm=0.1, fast=float("nan"), unattached=0.1, shaking=0.1)]
        for probabilities in options:
            status = available()
            status["probabilities"] = probabilities
            with self.subTest(probabilities=probabilities), self.assertRaises(contract.ContractError):
                contract.validate_status(status)

    def test_ties_choose_lowest_state_id(self):
        status = available()
        status.update(state="calm", state_id=0, confidence=0.5,
                      probabilities=dict(calm=0.5, fast=0.5, unattached=0, shaking=0))
        contract.validate_status(status)
        status.update(state="fast", state_id=1)
        with self.assertRaises(contract.ContractError):
            contract.validate_status(status)


class SignalContractTests(unittest.TestCase):
    def test_valid_and_empty_buffer(self):
        contract.validate_signal(signal(), require_samples=True)
        empty = dict(sample_rate_hz=25, unit="g", samples=[])
        contract.validate_signal(empty)
        with self.assertRaises(contract.ContractError):
            contract.validate_signal(empty, require_samples=True)

    def test_duplicate_or_decreasing_times(self):
        for timestamp in (0, -1, True, 40.0):
            data = signal()
            data["samples"][1]["t_ms"] = timestamp
            with self.subTest(timestamp=timestamp), self.assertRaises(contract.ContractError):
                contract.validate_signal(data)

    def test_signal_shape_units_capacity_and_numbers(self):
        cases = []
        for field, value in (("sample_rate_hz", True), ("sample_rate_hz", 50),
                             ("unit", "m/s2"), ("samples", {})):
            data = signal()
            data[field] = value
            cases.append(data)
        data = signal()
        data["samples"] = [dict(t_ms=i, ax_g=0, ay_g=0, az_g=1) for i in range(101)]
        cases.append(data)
        for value in (True, None, "0.1", float("inf"), float("nan")):
            data = signal()
            data["samples"][0]["ax_g"] = value
            cases.append(data)
        data = signal()
        data["samples"][0]["gx_dps"] = 1
        cases.append(data)
        for data in cases:
            with self.subTest(data=data), self.assertRaises(contract.ContractError):
                contract.validate_signal(data)


class FetchAndCliTests(unittest.TestCase):
    def test_duplicate_json_keys_rejected(self):
        with self.assertRaises(contract.ContractError):
            contract._unique_object([("ready", True), ("ready", False)])

    def test_json_and_headers_are_checked_on_fetch(self):
        def response(body, content_type="application/json", cache_control="no-store"):
            stream = io.BytesIO(body)
            stream.status = 200
            stream.headers = Message()
            stream.headers["Content-Type"] = content_type
            stream.headers["Cache-Control"] = cache_control
            return stream

        with patch.object(contract, "urlopen", return_value=response(b'{"ready":false}')):
            self.assertEqual(contract.fetch_json("http://test.invalid/api/status"), {"ready": False})
        malformed = [
            (b'{"x":NaN}', "application/json", "no-store"),
            (b'{"x":Infinity}', "application/json", "no-store"),
            (b'{"x":1,"x":2}', "application/json", "no-store"),
            (b'{}', "text/html", "no-store"),
            (b'{}', "application/json", "max-age=60"),
            (b' ' * 131073, "application/json", "no-store"),
        ]
        for body, content_type, cache_control in malformed:
            with self.subTest(body=body[:30], content_type=content_type, cache_control=cache_control):
                with patch.object(contract, "urlopen", return_value=response(body, content_type, cache_control)):
                    with self.assertRaises(contract.ContractError):
                        contract.fetch_json("http://test.invalid/api/status")

    def test_extreme_integer_is_rejected_as_nonfinite_numeric_field(self):
        data = signal()
        data["samples"][0]["ax_g"] = 10 ** 1000
        with self.assertRaises(contract.ContractError):
            contract.validate_signal(data)

    def test_success_is_explicitly_limited_to_contract_validation(self):
        with patch.object(contract, "fetch_json", side_effect=[unavailable(), signal()]):
            self.assertEqual(contract.main(["--base-url", "http://test.invalid"]), 0)

    def test_cli_ready_failure(self):
        with patch.object(contract, "fetch_json", return_value=unavailable()):
            self.assertEqual(contract.main(["--require-ready"]), 1)


if __name__ == "__main__":
    unittest.main()
