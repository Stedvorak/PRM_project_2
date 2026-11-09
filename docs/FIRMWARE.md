# Firmware setup and verification

Target: ESP32-S3 N16R8 with optional/pending MPU-6050 (GY-521). Protocol is
[INTERFACES.md](INTERFACES.md) v0.2. Firmware and AI belong to Codex;
browser assets and deployment belong to Antigravity.

## Hardware assumptions: verify before powering or flashing

- User-confirmed wiring configuration: sensor VCC to 3.3 V, common GND,
  SDA GPIO8 and SCL GPIO9. GPIO macros remain configurable.
- Before acquisition, an explicit I2C detection test requires an address ACK and
  MPU-6050 WHO_AM_I=0x68. Prefer configured address0x68 (AD0 low); if absent,
  automatically test0x69 (AD0 high). The fallback is configurable. An unrelated
  acknowledging I2C device is not sufficient evidence of the correct sensor.
- Detection failure keeps status unavailable and the signal buffer empty;
  recovery retries detection before sensor configuration/acquisition. Physical
  sensor connection is not assumed. Capture builds report detection diagnostics
  before measurements; demo builds keep application USB serial silent.
- The operator visually verified the WS2812/NeoPixel-compatible RGB LED onGPIO48
  with red, green, blue and magenta. PRM_RGB_PIN defaults to48 and remains
  configurable. Diagnostic cycling is disabled; runtime colors follow the model.
- COM3 was verified as ESP32-S3 revision 0.2 using esptool; flash_id detected
  16MB quad flash. The user verified 8MB PSRAM, dual-core 240MHz and CH343.
  The carrier's GPIO wiring/LED remains unconfirmed. The capture environment uses UART0
  (`ARDUINO_USB_CDC_ON_BOOT=0`) for this kind of adapter. For the board's native
  USB connector instead, explicitly set that macro to 1 and choose its port.
- Do not claim sensor, LED, BLE, AP, throughput or inference measurements from a
  compile or host test. All require the physical board.

## Reproduce the software build (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m platformio run -e esp32-s3
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
```

PlatformIO pins the Espressif32 platform, Arduino framework and BLE/LED libraries.
The explicit boards/prm-esp32s3-n16r8.json profile uses ESP32-S3 at 240MHz,
16MB quad flash at80MHz, 8MB octal PSRAM (qio_opi), and the default_16MB
partition table. Its final partition ends exactly at16MB. This matches verified
chip/flash and user-reported PSRAM; it does not identify a carrier pinout.
Local build caches are ignored. Run builds serially, especially after changing
platformio.ini, because PlatformIO can invalidate the shared build cache.
No build command uploads automatically.
Use the explicit verified serial port with `platformio run -e esp32-s3 -t upload
--upload-port COMx` only after checking wiring and configuration.

The default build does not start Serial or transmit USB training data. In the
live demonstration USB is power only: acquisition, features and classification
all run on the board. Install a genuinely trained model as described in ML.md
and rebuild before expecting `ready: true`.

## Frontend handoff

Antigravity's embedded page is integrated from commit
`2064cf89be4e8724d09fb92b444be87c03e5a893` and adapted to v0.2 in
`firmware/include/web_page.h`. Arduino WebServer 2.0.0 provides the exact
`send_P(int, PGM_P, PGM_P)` overload; `/` and `/index.html` serve its `INDEX_HTML`
PROGMEM constant. No separate filesystem upload is needed for this page.
LittleFS remains available for additional assets, mounted without automatic
formatting. If Antigravity supplies such files under `firmware/data/`, upload
using `platformio run -e esp32-s3 -t uploadfs --upload-port COMx`. The embedded
header is the authoritative page; do not deploy an obsolete alternate copy.

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
