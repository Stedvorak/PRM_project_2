# Frontend integration and interface v0.2

The shared contract is `docs/INTERFACES.md` v0.2. Firmware and both browser
clients must use its unchanged four states and BLE UUIDs. Frontend visuals were
provided by Antigravity; the integration adapts their data handling to v0.2.

## ESP32 Wi-Fi dashboard

The authoritative integrated page is `firmware/include/web_page.h`:
`INDEX_HTML` remains a `PROGMEM` raw string, served directly from the firmware
using Arduino `WebServer::send_P(200, "text/html", INDEX_HTML)`. No external CDN,
script, font or network service is required. Open the board's own AP address
from a browser connected to that AP. This HTTP page does not use Web Bluetooth.

No `firmware/data/index.html` is present in either integrated branch. The
PROGMEM header is the supplied and authoritative embedded dashboard.

The integrated page polls both `/api/status` and `/api/signal` approximately twice
per second. There is one guarded polling cycle with two endpoint requests, a
1.8-second request timeout and no overlapping cycles. A manual Poll Now button
uses the same guard. Slow requests reduce the rate instead of accumulating work.
Network or contract errors invalidate the affected view; no mock fallback exists.

Status handling requires `ready` and `timestamp_ms`, exact state/state_id mapping,
four named probability keys with values in [0,1] and approximately unit sum,
confidence equal to the maximum, and an optional nonnegative breathing estimate.
`ready=false` requires null predictions and displays PREDICTION UNAVAILABLE.
`null` is never coerced into state zero. All probability bars clear to N/A when
unavailable. A valid breathing estimate is displayed only when supplied by the
firmware; it is not derived from the class label or guessed in JavaScript.

The acceleration chart uses only the latest `/api/signal` response, with up to
100 real samples at the 25 Hz acquisition target. The three lines display ax_g,
ay_g and az_g in g, positioned using their actual increasing boot timestamps.
The chart scales its axis to the received data and breaks lines at gaps above
80 ms; it does not generate missing samples. An empty array clears the chart.
Overlapping poll buffers replace the previous buffer, so samples are not duplicated.
The page reports received sample count, elapsed signal span and latest device
sample timestamp. The configured 25 Hz target is not advertised as a measured rate.

A two-second watchdog invalidates stale status responses and signal responses.
Additional timestamp-progress checks invalidate status snapshots or signals that
keep returning unchanged device timestamps. A decreasing status boot timestamp clears old signal
state for a restarted board. A sensor may provide real signal while no trained
classifier is installed; that signal remains visible while prediction is
explicitly unavailable. All ESP-page simulation controls were removed.

## GitHub Pages Web Bluetooth station

Source: `web-station/index.html`. This is a separate HTTPS monitoring client,
not the page served by the ESP32 AP. Device selection must follow a user click.
The shared service is `7c2f1000-73ad-4a0d-9ec4-10cc7ea46a10`; the READ/NOTIFY
characteristic is `7c2f1001-73ad-4a0d-9ec4-10cc7ea46a10`; device name is
`PRM-Project-2`. A valid notification is exactly one unsigned binary byte:
0 calm, 1 fast, 2 unattached, 3 shaking. A zero-length read means unavailable.
The firmware sends unchanged valid states as well, at least once per second.

The station must clear stale predictions when notifications stop, distinguish
that condition from a GATT disconnection, and never treat unavailable readings
as calm. Alarm limits are fast breathing over 15 seconds and unattached over
10 seconds, with a separate connection-lost alarm. The station integration and
its explicit simulation controls are verified separately from the ESP page;
simulation must be visibly identified and isolated from device measurements.

## Verification status and required live checks

Automated checks are software evidence only. See the current test output/report
for exactly which Node/DOM and Python contract checks were actually executed.
Static string assertions cannot demonstrate a real browser connection, working
alarms or functional hardware. This documentation does not claim those results.

Before demonstration, verify on physical hardware and a supported browser:

- A board without a trained model shows unavailable prediction while genuine
  sensor samples can still plot.
- A trained board shows matching LED, BLE state and HTTP probabilities.
- Startup and sensor disconnection never produce a guessed class or fake signal.
- Both HTTP endpoints refresh and remain responsive with concurrent BLE use.
- The GitHub Pages client connects in a secure context, displays the timeline,
  and demonstrates both duration alarms and connection-lost/stale alarms.
- The page works with no Internet connection while connected to the board AP.

Record actual browser/device versions, observations and failures; do not replace
these live checks with simulated data or report unperformed runtime tests.
