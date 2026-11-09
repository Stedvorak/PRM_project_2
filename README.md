# PRM Project 2 — Real-time AI

ESP32-S3 N16R8 + MPU-6050 real-time four-state classifier and monitoring
interfaces. [Assignment](https://tomasvicar.github.io/AUI-public/labs/real-time-ai.html).

Group members: **David Bártek** and **Štěpán Dvořák**.
Live BLE station: [Open the monitoring page](https://stedvorak.github.io/PRM_project_2/web-station/).

## Current status

Trained M01 v1 monitoring firmware is now flashed to COM3. It detected the
MPU-6050 at0x68 and produced22 real on-device predictions at2Hz. Measured
feature+prediction computation was2.377–2.458ms against a500ms update budget.
This is timing evidence, not a physically labeled accuracy demonstration.

All12 real recordings (17993 samples, four classes) are preserved under data/raw/.
Six candidates were evaluated with two whole collection-round folds. Selected
M01 pooled held-out accuracy83.64%, mean-fold balanced accuracy86.11%, macroF1
0.8351. Placement dependence and unattached recall53.09% limit generalization.
See docs/RESULTS.md and docs/FINAL_METHOD.md for exact evidence and versions.

The trained monitoring image includes BLE, AP, HTTP and the embedded webpage.
GPIO48 WS2812/NeoPixel colors were visually confirmed by the operator; the LED
now follows real states (calm green, fast red, unattached blue, shaking magenta).
The PC joined the ESP32 AP: both real JSON APIs passed v0.2 checks with a ready
prediction and100 sensor samples; the embedded page returned HTTP200.
PC BLE verification is blocked by Windows reporting its adapter not ready.
The user reports teacher acceptance of grading sections1 and2. David prepared
sections4 and5; their existing frontend implementation is preserved.

- [Shared BLE/HTTP interface v0.2](docs/INTERFACES.md)
- [Build, wiring assumptions and hardware acceptance checks](docs/FIRMWARE.md)
- [Collect real recordings, train, evaluate and export a model](docs/ML.md)
- [Separate 50 Hz USB acquisition and timestamped session recorder](acquisition/README.md)
- [Method registry](docs/METHODS.md) and [final method status](docs/FINAL_METHOD.md)
- [Submission checklist](docs/CHECKLIST.md)

## Quick start (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
.\.venv\Scripts\python.exe -m platformio run -e esp32-s3
```

See FIRMWARE.md before uploading. Sensor pins are SDA8/SCL9; verified RGB is GPIO48,
and the capture build is training-only. Default demo firmware does not transmit
USB serial data. The board performs acquisition/features/inference independently.

Codex owns firmware and AI. Antigravity owns the BLE monitoring station and
board-hosted frontend. Integrate through separate branches and PRs. No frontend
assets are replaced by the firmware work. `/data/` holds ignored original
recordings; `firmware/data/` is reserved for tracked LittleFS frontend assets.

## Required submission details still pending

- A photo of the actual wiring and confirmed pin mapping.
- Live BLE connection, timeline and alarm demonstration on a supported device.
- David's sections4/5 demonstration and final teacher/submission confirmation.

The separate acquisition project records all six real axes at50Hz over CH343
COM3, with identity/configuration tests and a Python recorder. Its raw files must
be explicitly downsampled before using M01's25Hz training pipeline. Acquisition
does not change the agreed25Hz live signal API or install a classifier.
The board now runs trained monitoring firmware, replacing acquisition firmware.
The inference-check build emits testing-only USB diagnostics; the esp32-s3
build disables this stream for the required power-only USB demonstration.

David owns the prepared section5 extension; preserve his implementation and
coordinate its demonstration. Sensor-fault/unavailable guards are implemented
in firmware and must not be confused with a completed teacher demonstration.
Teacher account `tomasvicar` was verified to have write access during preparation;
recheck at delivery. Three intermediate commits must be pushed during the lab.

## AI tools

OpenAI Codex and native subagents were used for interface validation, firmware,
data-collection/training tools, software tests and documentation. Antigravity
developed the web clients using Antigravity/Gemini, as disclosed in the teammate
README. Every group member must understand and explain the code.
Synthetic software fixtures are never presented as real sensor measurements or
model evaluation.
