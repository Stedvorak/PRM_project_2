# Frontend Interfaces Documentation

This document describes the two client interfaces developed by **ANTIGRAVITY** for the Real-Time AI project.

## 1. Web Bluetooth Bedside Monitor (`web-station/index.html`)

### Architecture
- **Environment**: Client-side single page app (SPA) deployed to GitHub Pages or static host.
- **Protocol**: Web Bluetooth API (GATT Client over BLE).
- **Communication Flow**:
  1. User triggers device discovery via `navigator.bluetooth.requestDevice({ filters: [{ name: 'PRM-Project-2' }], optionalServices: ['7c2f1000-73ad-4a0d-9ec4-10cc7ea46a10'] })`.
  2. Subscribes to notifications on characteristic `7c2f1001-73ad-4a0d-9ec4-10cc7ea46a10`.
  3. Every notification delivers 1 unsigned byte: `dataView.getUint8(0)`.
  4. Decodes byte into state 0 (calm), 1 (fast), 2 (unattached), 3 (shaking).

### Alarm Thresholds & Acknowledgment Lifecycle
- **Fast Breathing Alarm**: Triggers when State 1 lasts continuously for more than **15.0 seconds**.
- **Unattached Sensor Alarm**: Triggers when State 2 lasts continuously for more than **10.0 seconds**.
- **Connection Lost Alarm**: Triggers upon event `gattserverdisconnected`.
- **Audio Feedback**: Synthesized multi-frequency alarms generated using `AudioContext` and `OscillatorNode`.
- **Incident Acknowledgment**: When the user clicks the "Acknowledge / Silence" button:
  1. The audio alarm is immediately stopped and visual flashing banner is dismissed.
  2. The active incident is marked acknowledged (`acknowledgedAlarms`), preventing immediate re-triggering while remaining in that state.
  3. When the state changes or returns to normal (e.g. State 0 Calm), the acknowledgment flag clears.
  4. Subsequent occurrences (new incidents) will trigger alarms again after exceeding their duration threshold.
- **Telemetry & Logging**: Records state transitions with duration and raised alarms, exportable as CSV.

---

## 2. ESP32 Wi-Fi AP Dashboard (`firmware/data/index.html` & `firmware/include/web_page.h`)

### Architecture
- **Environment**: Hosted on ESP32 web server (IP e.g. `192.168.4.1`) when running in SoftAP mode.
- **Protocol**: HTTP REST API.
- **Communication Flow**:
  1. Client polls `GET /api/status` at 500ms intervals.
  2. Receives JSON payload:
     ```json
     {
       "state": "calm",
       "state_id": 0,
       "breaths_per_min": null,
       "confidence": null,
       "probabilities": null
     }
     ```
  3. Respects `null` values as unavailable data rather than zero.
  4. Renders live state, breaths per minute (BPM), classifier confidence, and horizontal probability distributions.

### Firmware Integration
Two formats are provided for the firmware developer (CODEX):
1. **SPIFFS/LittleFS File**: `firmware/data/index.html` can be uploaded directly to flash storage.
2. **C++ Header**: `firmware/include/web_page.h` contains `INDEX_HTML` in `PROGMEM`, allowing direct serving via:
   ```cpp
   #include "web_page.h"
   server.on("/", HTTP_GET, [](AsyncWebServerRequest *request){
       request->send_P(200, "text/html", INDEX_HTML);
   });
   ```

---

## 3. Verification & Testing

Run the automated contract test script:
```bash
python3 scripts/test_web_interfaces.py
```
Outputs verify zero schema discrepancies, correct UUID matching, and functional alarm thresholds.
