# PRM Project 2 — Real-time AI

ESP32-S3 N16R8 + MPU-6050 real-time four-state classifier and monitoring
interfaces. [Assignment](https://tomasvicar.github.io/AUI-public/labs/real-time-ai.html).

## Current status

Firmware and a real-recording training pipeline are implemented for testing.
There is no trained model or genuine classifier evaluation yet. The checked-in
model deliberately returns unavailable; no mock prediction is exposed as real.
Physical wiring, flashing, sensor acquisition, LED and BLE/AP demonstrations
remain to be verified. This repository is not yet a complete lab submission.

- [Shared BLE/HTTP interface v0.2](docs/INTERFACES.md)
- [Build, wiring assumptions and hardware acceptance checks](docs/FIRMWARE.md)
- [Collect real recordings, train, evaluate and export a model](docs/ML.md)
- [Method registry](docs/METHODS.md) and [final method status](docs/FINAL_METHOD.md)
- [Submission checklist](docs/CHECKLIST.md)

## Quick start (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
.\.venv\Scripts\python.exe -m platformio run -e esp32-s3
```

See FIRMWARE.md before uploading. Pins are provisional, RGB defaults disabled,
and the capture build is training-only. Default demo firmware does not transmit
USB serial data. The board performs acquisition/features/inference independently.

Codex owns firmware and AI. Antigravity owns the BLE monitoring station and
board-hosted frontend. Integrate through separate branches and PRs. No frontend
assets are replaced by the firmware work. `/data/` holds ignored original
recordings; `firmware/data/` is reserved for tracked LittleFS frontend assets.

## Required submission details still pending

- Actual group member names.
- A photo of the actual wiring and confirmed pin mapping.
- Deployed GitHub Pages monitoring URL.
- Real recordings, labels, held-out evaluation and installed model identity.
- All live demonstrations, chosen extension evidence and final remote commit.

The proposed own extension is explicit sensor-fault/unavailable detection and
recovery. It must be demonstrated on hardware before claiming completion.
Teacher account `tomasvicar` was verified to have write access during preparation;
recheck at delivery. Three intermediate commits must be pushed during the lab.

## AI tools

OpenAI Codex and native subagents were used for interface validation, firmware,
data-collection/training tools, software tests and documentation. Antigravity
develops the web clients separately; its exact tool/model disclosure belongs in
the integrated report. Every group member must understand and explain the code.
Synthetic software fixtures are never presented as real sensor measurements or
model evaluation.
