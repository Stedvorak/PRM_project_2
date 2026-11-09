# Firmware setup and verification

Target: ESP32-S3 N16R8 with MPU-6050 (GY-521). Protocol is
[INTERFACES.md](INTERFACES.md) v0.2. Firmware and AI belong to Codex;
browser assets and deployment belong to Antigravity.

## Hardware assumptions: verify before powering or flashing

- Power the sensor from 3.3 V, connect common ground, SDA GPIO 8 and SCL GPIO 9
  unless the actual wiring requires different configurable pins.
- Default I2C address is 0x68 (AD0 low); use 0x69 if AD0 is high.
- RGB LED is disabled until its GPIO and type are confirmed. The implementation
  supports a WS2812/NeoPixel RGB LED; do not guess a pin or assume a discrete LED
  has the same driver. Set the configured LED pin only after checking the board.
- No connected serial port was detected during initial software preparation.
- Do not claim sensor, LED, BLE, AP, throughput or inference measurements from a
  compile or host test. All require the physical board.

## Reproduce the software build (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m platformio run -e esp32-s3
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
```

PlatformIO pins the Espressif32 platform and BLE/LED libraries. The board profile
uses 16 MB flash and octal PSRAM. Verify that this matches the supplied N16R8
board. Local build caches are ignored. No build command uploads automatically.
Use the explicit verified serial port with `platformio run -e esp32-s3 -t upload
--upload-port COMx` only after checking wiring and configuration.

The default build does not start Serial or transmit USB training data. In the
live demonstration USB is power only: acquisition, features and classification
all run on the board. Install a genuinely trained model as described in ML.md
and rebuild before expecting `ready: true`.

## Frontend handoff

Antigravity supplies static files under `firmware/data/` with an `index.html`.
Build/upload these using `platformio run -e esp32-s3 -t uploadfs --upload-port
COMx`. The firmware serves LittleFS assets without implementing another UI.
An absent filesystem/index gives an explicit unavailable response rather than a
fake dashboard. API endpoints do not depend on uploaded browser assets.

Join the configured board AP and use its address (normally 192.168.4.1).
Credentials and GPIO macros are listed in firmware/include/prm_config.h.
The GitHub Pages BLE monitor must run from HTTPS in a compatible Chrome/Edge
browser with BLE support and a user-initiated Connect action. The board's own
HTTP page uses HTTP polling, not Web Bluetooth.

## Physical acceptance checks (not yet performed)

1. Confirm MPU identity, real changing acceleration in g, 25 Hz acquisition target
   and strictly increasing timestamps. `/api/signal` has at most 100 samples.
2. Without a trained model, status is unavailable even though signal may exist.
   With a trained model, wait for a complete valid window; verify all four
   probabilities, confidence and matching IDs on HTTP and BLE.
3. Subscribe to BLE notifications and read the characteristic. Confirm one binary
   byte in 0..3, updates at least once per second even without a state change.
4. Disconnect the sensor: status becomes unavailable, signal clears, LED no
   longer shows a valid class, BLE READ is empty and notifications cease.
   Reconnect and verify warmup and recovery. Never send a sentinel as a fifth ID.
5. Exercise BLE reconnect and simultaneous Wi-Fi AP traffic; measure notification
   cadence and acquisition under load. ESP32-S3 shares its 2.4 GHz radio, so
   software compilation does not establish coexistence performance.
6. Open the real Antigravity clients. Demonstrate timeline, duration alarms for
   fast/unattached, link-loss alarm, live signal and all class probabilities.
7. Verify all four physical states and LED colours against independent labels.
   Keep genuine recording-group held-out evaluation separate from demonstrations.

Run the network validator on real hardware:

```powershell
python tools/check_contract.py --base-url http://192.168.4.1
python tools/check_contract.py --base-url http://192.168.4.1 --require-ready --require-samples
```

## Delivery safeguards

Record the actual lab start/end time. Stop experiments 30 minutes before the
end. At least three meaningful intermediate lab commits must each be pushed as
work proceeds; a final bulk push does not substitute. Verify teacher
`tomasvicar` can access the GitHub project before the lab ends. Do not confuse
the firmware branch with the integrated final deliverable or GitHub Pages repo.
Use separate branches/PRs for integration. Recheck status, tests, tracked model,
report and result paths, push, fetch, compare remote commit and document it.

Do not place a self-referential commit hash into a file and then claim it names
the commit containing that file: record the implementation/evaluation commit
explicitly and verify the final delivery commit also contains those artifacts.
Current state and outstanding evidence are recorded in CHECKLIST.md and
FINAL_METHOD.md. No algorithm is selected before actual data/evaluation.
