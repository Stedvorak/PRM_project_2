# Firmware/frontend integration provenance

The teammate's commit `2064cf89be4e8724d09fb92b444be87c03e5a893` was verified
with `git ls-remote` at `refs/heads/antigravity`. The reported branch name
`antigravity/web` did not exist on the remote at verification time.

No blind merge, reset, force-push or overwrite of firmware/ML work was used.
The imported files were checked not to exist locally, then copied byte-for-byte
from that exact commit before the authorized v0.2 adaptations:

- firmware/include/web_page.h — embedded ESP32 PROGMEM dashboard.
- web-station/index.html and README.md — Web Bluetooth station.
- docs/FRONTEND.md — frontend handoff documentation.
- scripts/test_web_interfaces.py — frontend verification entry point.

The teammate's older shared instructions, interface draft, method registry,
checklist, task list and ignore rules were not imported. Method M01 v1 and its
unavailable-model guard are preserved. No genuine model has been selected.

## Serving and data path

This firmware uses Arduino WebServer, not AsyncWebServer. The pinned framework's
WebServer.h declares `send_P(int code, PGM_P content_type, PGM_P content)`.
The root and /index.html routes serve INDEX_HTML directly from flash; no separate
LittleFS upload is required. Optional additional assets can still use LittleFS.

The dashboard consumes v0.2 /api/status and /api/signal. Status comes only from
the on-board sensor/model pipeline; signal comes from a bounded buffer of actual
MPU-6050 samples. No UI animation or simulated state is a measurement. Missing
sensor/model means explicitly unavailable data. The default guard means live
probabilities cannot exist until real recordings have been trained and reviewed.

BLE service/characteristic UUIDs remain respectively
7c2f1000-73ad-4a0d-9ec4-10cc7ea46a10 and
7c2f1001-73ad-4a0d-9ec4-10cc7ea46a10. State IDs remain 0 calm, 1 fast,
2 unattached, 3 shaking, sent as one binary unsigned byte. Unavailable READ is
empty and notifications cease; client stale detection must invalidate old state.

## Evidence boundaries

Build output, Python environment and host test results are stored under
outputs/verification/. Synthetic test fixtures exercise software behavior only.
No reported static linker size is a runtime hardware measurement. Flashing,
actual acquisition, BLE delivery/coexistence, LED wiring, browser/device pairing,
model accuracy, deployment and teacher live demonstrations remain separate checks.
