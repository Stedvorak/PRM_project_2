# Shared interfaces - Draft v0.1

Both agents must use the same state encoding.

| Code | State |
|------|-------|
| 0 | calm |
| 1 | fast |
| 2 | unattached |
| 3 | shaking |

## BLE

Device name: PRM-Project-2

Proposed service UUID:
7c2f1000-73ad-4a0d-9ec4-10cc7ea46a10

Proposed state characteristic UUID:
7c2f1001-73ad-4a0d-9ec4-10cc7ea46a10

Notification payload:
One unsigned byte containing state code (0-3).

## HTTP API

Endpoint: GET /api/status

Proposed JSON response:

{
  "state": "calm",
  "state_id": 0,
  "breaths_per_min": null,
  "confidence": null,
  "probabilities": null
}

Null means unavailable, not zero.

## Integration rules

- Codex implements BLE and HTTP endpoints.
- Antigravity implements browser clients.
- Both use exactly the same UUIDs and state IDs.
- Mock data must be clearly identified.
- This contract must be confirmed by both agents.
- Any changes must be committed and communicated.
