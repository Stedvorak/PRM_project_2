# Shared interfaces - v0.2

User-approved shared contract for Codex firmware and Antigravity browser clients.

| Code | State | LED |
|------|-------|-----|
| 0 | calm | green |
| 1 | fast | red |
| 2 | unattached | blue |
| 3 | shaking | magenta |

## BLE

- Device name: `PRM-Project-2`
- Service UUID: `7c2f1000-73ad-4a0d-9ec4-10cc7ea46a10`
- State characteristic UUID: `7c2f1001-73ad-4a0d-9ec4-10cc7ea46a10`
- Properties: READ and NOTIFY.
- Valid read and notification payload: exactly one binary unsigned byte (0-3),
  not an ASCII digit or JSON. UUIDs and state IDs are unchanged from v0.1.
- While subscribed and ready, send the current valid state at least once per
  second, including when unchanged.
- Startup, sensor failure, stale acquisition or unavailable inference must never
  be encoded as a valid class. Clear the readable characteristic to zero bytes
  and suppress notifications while unavailable. A zero-length READ means
  unavailable; every notification remains exactly one valid byte. No fifth ID
  or sentinel byte is introduced. Do not resend a stale prediction after failure.
- Clients invalidate predictions when notifications become stale, and distinguish
  a stale stream from a GATT disconnection event.

## HTTP API

Responses: `Content-Type: application/json`, `Cache-Control: no-store`.
Timestamps: nonnegative integer milliseconds since boot, from a monotonic clock.
Frontend polling target: approximately 2 Hz (500 ms per endpoint).
The board-hosted page uses same-origin HTTP; GitHub Pages uses BLE.

### GET /api/status

All fields are always present. Unavailable response example (not a measurement):

```json
{
  "ready": false,
  "timestamp_ms": 0,
  "state": null,
  "state_id": null,
  "probabilities": null,
  "confidence": null,
  "breaths_per_min": null
}
```

| Field | Type and meaning |
|-------|------------------|
| ready | boolean; true only with healthy current acquisition and a valid prediction |
| timestamp_ms | integer milliseconds since boot at response snapshot |
| state | calm, fast, unattached, shaking, or null |
| state_id | integer 0, 1, 2, 3, or null; must match state |
| probabilities | object with exactly calm, fast, unattached, shaking; each a finite number in [0,1], sum within 0.001 of 1; null only while unavailable |
| confidence | maximum of the four probabilities, or null |
| breaths_per_min | finite nonnegative number, or null if no genuine estimate exists |

When ready is false, state, state_id, probabilities, confidence and
breaths_per_min are null. When ready is true, all except breaths_per_min are
non-null. State and state_id identify the maximum-probability class; ties use the
lowest ID. All fields describe one consistent snapshot. Null means unavailable,
not zero. A missing model is unavailable inference, never a fabricated prediction.

### GET /api/signal

```json
{
  "sample_rate_hz": 25,
  "unit": "g",
  "samples": []
}
```

- sample_rate_hz: number 25, the acquisition target, not a measured-rate claim.
- unit: string "g" (standard gravity).
- samples: array of 0 to 100 most recent real samples, oldest first.
- Each sample has exactly t_ms (integer milliseconds since boot), ax_g, ay_g,
  az_g (finite acceleration values in g).
- Sample timestamps are strictly increasing within each response. Polls may
  overlap because this is a rolling buffer. Never interpolate missing samples.
- At startup or sensor failure return an empty samples array. Clear the buffer
  on failure; resume only with real readings. Never fabricate measurements or
  replace missing readings with zero vectors.

## Integration rules

- Codex owns firmware, BLE and HTTP endpoint implementation.
- Antigravity owns browser clients and the board-hosted web frontend.
- Both developers use exactly these UUIDs, state IDs and JSON fields.
- Mock data must be clearly identified and never exposed as real measurements.
- Version 0.2 is approved by the user for both developers. Any subsequent change
  requires agreement before implementation and must be committed and communicated.
- AP credentials, GPIO wiring and frontend asset packaging are deployment
  configuration, not a change to this protocol; document them in firmware setup.
