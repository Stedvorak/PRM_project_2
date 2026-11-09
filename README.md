# Real-Time AI Bedside Monitor (MPA-PRM)

Real-time embedded monitoring system using an **ESP32-S3 N16R8** development board and an **MPU-6050** (GY-521) 6-DOF IMU sensor. The device classifies breathing and motion states directly on-chip and streams telemetry via Bluetooth Low Energy (BLE) and a local Wi-Fi access point.

## Team Members
- David Bártek
- Štěpán Dvořák

## Live Monitoring Station
- **BLE Bedside Monitor (GitHub Pages):** [https://Stedvorak.github.io/PRM_project_2/](https://Stedvorak.github.io/PRM_project_2/)
- Compatible with Chrome/Edge on desktop/Android supporting the Web Bluetooth API.

## Hardware Wiring
The sensor communicates with the ESP32-S3 via I2C at 3.3V:

| MPU-6050 Pin | ESP32-S3 Pin | Function |
| :--- | :--- | :--- |
| **VCC** | **3V3** | Power supply (3.3V) |
| **GND** | **GND** | Ground |
| **SCL** | **GPIO 9** | I2C Clock |
| **SDA** | **GPIO 8** | I2C Data |
| **AD0** | **GND** | I2C Address `0x68` |

*(Wiring diagram and photo available in `docs/wiring.jpg`)*

## State Definitions & RGB LED Indication
The classifier runs on the microcontroller with no computer tether (USB only supplies power):

| State Code | State Name | RGB LED Color | Description |
| :---: | :--- | :---: | :--- |
| `0` | `calm` | **Green** | Calm regular breathing (sensor against chest) |
| `1` | `fast` | **Red** | Fast/shallow breathing (sensor against chest) |
| `2` | `unattached` | **Blue** | Device held still in hand or placed on table |
| `3` | `shaking` | **Magenta** | Active shaking or vigorous motion |

## Machine Learning Pipeline
1. **Data Acquisition:** 6-axis acceleration and angular velocity recorded at 50 Hz.
2. **Feature Extraction:** Sliding window of 2.0 s (100 samples) with 0.5 s step. Computed features include standard deviation, range, axis variance, magnitude energy, and log-transformed variance.
3. **On-Chip Inference:** Compact decision tree / random forest compiled directly to native C++ functions (`firmware/include/model.h`) for sub-millisecond execution without external neural network runtime overhead.

## Interfaces & Connectivity
- **BLE GATT Service:** `7c2f1000-73ad-4a0d-9ec4-10cc7ea46a10`
  - **State Characteristic:** `7c2f1001-73ad-4a0d-9ec4-10cc7ea46a10` (Notification with 1-byte state code `0`–`3`).
  - Alarm triggers on Web Station: Fast breathing > 15 s, Unattached > 10 s, or connection loss.
- **ESP32 Wi-Fi AP:** Serves real-time telemetry and state probabilities over `GET /api/status`.

## Own Extension: Real-Time Respiratory Rate (BPM) Estimation (1.5 pts)
In addition to 4-state classification, the ESP32-S3 firmware performs real-time respiratory rate estimation in **Breaths Per Minute (BPM)**:
- **Method:**
  1. **Low-Pass Filtering:** Applies a moving-average filter to the dominant chest-displacement axis ($a_z$) to eliminate high-frequency IMU jitter and tremor.
  2. **Baseline Detrending:** Subtracts a moving baseline average to center respiratory waveforms symmetrically around zero.
  3. **Peak & Zero-Crossing Detection:** Detects breath cycle transitions via refractory local maxima and upward zero-crossings, measuring cycle duration $T_{resp}$ (s) to obtain respiratory frequency $f_{resp} = 1 / T_{resp}$ (Hz).
  4. **Rate Scaling:** Converts respiratory frequency to breaths per minute ($\text{BPM} = f_{resp} \times 60$).
- **Window Length:** Evaluated over a 2.0-second sliding window (100 samples at 50 Hz, updated every 500 ms inference step).
- **Physiological Bounds & Contract:**
  - Active States `0` (calm) and `1` (fast) compute and return rates strictly bounded to physiological limits: **[8.0, 40.0] BPM**.
  - Active States `2` (unattached) and `3` (shaking) return `-1.0f` (mapping to JSON `null` in `/api/status` and `--` on dashboards).
  - Populates `"breaths_per_min"` in `/api/status` and renders live numerical indicators alongside the state badges in both the GitHub Pages Web Station and the ESP32 AP web dashboard.

## AI Tools Usage
In accordance with BUT AI guidelines, artificial intelligence tools were used as follows:
- **Codex / Antigravity / Gemini:** Architecture contract specification (`docs/INTERFACES.md`), Web Bluetooth interface scaffolding (`web-station/index.html`), and C++ inference conversion routines. All generated code was verified and adapted by team members.
