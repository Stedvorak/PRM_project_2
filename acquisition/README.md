# Real MPU-6050 acquisition at 50 Hz

This separate training-only firmware preserves the main firmware and its 25Hz
BLE/HTTP v0.2 contract. It does not drive RGB, expose fake classes, or run an ML
model. Restore the main demo firmware after collection: demonstration USB is
power only, whereas training intentionally uses USB-UART serial data.

## Wiring and detection

Use VCC **3.3V**, common GND, SDA **GPIO8**, SCL **GPIO9**. GPIO macros
`PRM_I2C_SDA`, `PRM_I2C_SCL` and preferred `PRM_MPU_ADDRESS` remain configurable.
Default address is0x68; alternate0x69 is checked. The firmware requires both ACK
and WHO_AM_I register0x75 equal0x68 before configuration or acquisition. It
reports `# DETECT PASS` followed by `# CONFIG PASS`; missing/wrong devices emit
diagnostics and no numeric rows. Retry detection is bounded and never produces
zero-vector substitutes. RGB GPIO remains entirely untouched.

MPU settings:50Hz hardware output (`SMPLRT_DIV=19`, gyro base1kHz), DLPF5/10Hz,
acceleration±2g (`raw/16384`, unitsg), gyro±250deg/s (`raw/131`). The rate/filter/
range registers are read back before `CONFIG PASS`. Data-ready polling and a
complete14-byte burst are required for each genuine timestamped row; the ignored
temperature bytes are not mistaken for gyro data. No catch-up/interpolated rows.

## Exact commands (PowerShell from repository root)

Use the existing `.venv` and pinned toolchain. Close other serial monitors first.
The acquisition build has its own project/build directory; do not change or
overwrite main firmware files. The board profile targets verified ESP32-S3
N16R8,16MB quad flash,8MB OPI PSRAM, CH343 UART0 on COM3.

```powershell
.\.venv\Scripts\python.exe -m platformio run --project-dir acquisition -e acquisition -j 4
.\.venv\Scripts\python.exe -m platformio run --project-dir acquisition -e acquisition -t upload --upload-port COM3
.\.venv\Scripts\python.exe tools/record_session.py --port COM3 --detect-only --reset
.\.venv\Scripts\python.exe tools/record_session.py --port COM3 --label calm --duration 30
```

The first command builds without flashing. Upload only after checking wiring and
board configuration. `--detect-only --reset` pulses the CH343 RTS reset circuit,
then waits for actual identity/config diagnostics; it does not assign a physical
class label or create a training recording. No sensor connection/test is claimed
until this succeeds on the actual hardware.

For other states replace `calm` with `fast`, `unattached` or `shaking`. Establish
the observed state **before** invoking the command and hold it for the entire
recording. Label is operator ground truth, never inferred by the recorder. Use
several independent sessions/takes per class. Unattached includes lying still and
held-in-hand movement. Never call an unobserved recording `calm` automatically.

An optional `--reset` before recording repeats startup detection. Port opening
itself may reset the board. Duration starts on the first valid sample; startup
and signal loss have a separate10-second no-valid-data timeout, configurable
with `--no-data-timeout`. Ctrl+C retains genuine partial rows and incomplete
metadata. A duplicate/backward timestamp/reboot ends the session rather than
silently combining different boots. Restore wiring before trying again.

## Files and quality report

Each run creates unique UTC timestamp/label/random-suffix files under
`data/raw/` (or `--output-dir`). CSV header:

```text
t_ms,ax_g,ay_g,az_g,gx_dps,gy_dps,gz_dps
```

Timestamps are integer milliseconds since ESP32 boot. The matching JSON records
units, label/provenance, firmware nominal50Hz, observed rate, diagnostics,
malformed-record rejection, gap count, estimated missing samples, session timing,
completion and errors. Malformed/nonfinite/partial lines are never converted to
measurements. Missing counts are estimates from actual timestamp gaps relative
to20ms, including rejected or missed rows. Metadata also records the nominal
duration-times50 sample target and count shortfall; no samples are filled in. Inspect the
observed rate and gaps before using a recording. A nominal50Hz setting is not a
claim that the physical board achieved it.

Original recordings are exclusively created, never overwritten. `data/` is
Git-ignored; arrange explicit dataset submission/access later. Preserve raw50Hz
files: M01v1 currently expects25Hz and must not be trained on these as though
their sample rate were25Hz. A later explicit, documented downsampling step is
required; the10Hz acquisition filter is suitable for subsequent25Hz sampling.
No existing classifier or method selection is changed by this workflow.

Software tests (synthetic serial fixtures, not hardware evidence):

```powershell
.\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider tests/test_record_session.py
```
