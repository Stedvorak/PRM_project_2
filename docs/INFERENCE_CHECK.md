# Actual on-board inference verification

This testing-only telemetry is independent of the v0.2 BLE/HTTP contract. It
does not add fields, state IDs or UUIDs. The final demonstration firmware must
disable it because USB is power only during the demonstration.

## Firmware integration

Include `prm_diagnostics.h`. `PRM_INFERENCE_DIAGNOSTICS` defaults to0; the helper
is a no-op and does not include Arduino/Serial when disabled. For a separate
diagnostics build, set the macro to1 and start Serial at115200. Instrument actual
on-board feature extraction and model prediction with the ESP32 monotonic
microsecond timer, outside state spinlocks. The total must include feature,
prediction and validation work. Invoke only for a valid current prediction:

```cpp
prm::emitInferenceDiagnostic(timestamp_ms, state, probabilities,
    feature_us, predict_us, total_us,
    window_first_ms, window_last_ms, maximum_sample_gap_ms);
```

The exact argument types are uint64_t, uint8_t, const float*, uint32_t,
uint32_t, uint32_t, uint64_t, uint64_t, uint64_t. Class probability order is
calm, fast, unattached, shaking. The caller retains the existing maximum2Hz
inference schedule and never emits a fabricated prediction when unavailable.
The helper emits a `# INFERENCE ` prefix followed by one JSON object, with
fields t_ms, state_id, feature_us, predict_us, total_us, probabilities (array of4),
window_first_ms, window_last_ms and sample_gap_ms. No host-side inference is used.

## Collect from actual hardware

After flashing a genuinely trained diagnostics build and establishing a healthy
sensor, close other COM3 monitors and run from the repository root:

```powershell
.\.venv\Scripts\python.exe tools/check_inference.py --port COM3 --duration 15 --output outputs/verification/H01_inference
```

The output directory must not already exist. It preserves raw serial bytes,
validated events.jsonl and report.json. The checker validates finite normalized
probabilities/argmax, timestamps, execution under500ms, maximum sample gap80ms
and maximum telemetry gap1000ms. It reports min/median/p95/max computation
timings and actual inference event rate. Malformed or reordered diagnostics,
interruption, fewer than3 events or violated budgets cause a nonzero exit.

Only when the operator has explicitly established the physical state, add e.g.
`--expected-state unattached`. The resulting match fraction is a single-state
observation, never four-class held-out accuracy. Serial printing happens after
the measured computation; actual event cadence is checked separately.

The Python host only collects/checks board telemetry. A passing compile or
synthetic software test is not hardware inference evidence. Preserve each
hardware run separately, report failures honestly, and finally restore/rebuild
the silent demo build with the same selected model. BLE/AP/LED and full
four-state physical demonstrations remain separate verification tasks.

Software tests use clearly synthetic temporary fixtures:

```powershell
.\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider tests/test_inference_diagnostics.py
```
