# PRM-Project-2 Web Station

The standalone BLE monitoring page uses the shared v0.2 contract in
`docs/INTERFACES.md`. Serve it over HTTPS (GitHub Pages) or localhost and open it
in a browser with Web Bluetooth support, such as Chrome on Windows/Android or
Edge on Windows. It does not connect through the board's plain HTTP page.

## Deployment

This folder has no build dependencies. For a dedicated public Pages repository,
copy `index.html` to its root and publish that repository's root. Alternatively,
publish the project root and open `/PRM_project_2/web-station/` under the resulting
Pages URL, or use a Pages Actions workflow that uploads `web-station/` as the site
artifact. GitHub's branch-based Pages picker supports root or `/docs`, not an
arbitrary `/web-station` source folder. Verify the actual HTTPS URL after deployment.
No deployment is claimed by these files.

## BLE contract

- Device name: `PRM-Project-2`.
- Service: `7c2f1000-73ad-4a0d-9ec4-10cc7ea46a10`.
- READ + NOTIFY characteristic: `7c2f1001-73ad-4a0d-9ec4-10cc7ea46a10`.
- Exactly one binary unsigned byte: 0 calm (green), 1 fast (red),
  2 unattached (blue), 3 shaking (magenta).
- The listener is registered before notifications start. An initial read displays
  the current state; a zero-length read means unavailable. Invalid lengths or
  values clear the displayed prediction and never become calm by default.
- Repeated valid notifications preserve the state's duration. After more than
  3 seconds without a valid notification, the page clears the prediction and
  raises **data stale/unavailable** while GATT may still be connected. A GATT
  disconnect raises a distinct **connection lost** alarm.
- State recovery clears stale status and begins a new state interval; duration
  alarms never span an unavailable gap. The timeline leaves such gaps uncolored.

## Alarms

- Fast breathing: continuously observed state 1 for 15 seconds.
- Unattached: continuously observed state 2 for 10 seconds.
- Stale stream: no valid notification for more than 3 seconds after connection
  or the last valid notification.
- Connection lost: an unexpected `gattserverdisconnected` event.

The mute and acknowledge buttons control synthesized Web Audio alerts. An
intentional Disconnect clears the current prediction without a connection-loss
alarm. Audio availability depends on browser policy and user interaction.

Acknowledgment silences the current incident instead of re-firing on the next
timer tick. Duration alarms re-arm after a state change or unavailable gap;
stale-data alarms re-arm after a valid notification or reconnection; a new
unexpected disconnect after reconnection starts a new connection-loss incident.
Acknowledging unavailable data preserves the explicit unavailable display.

The incident-scoped acknowledgment behavior adapts Antigravity commit
`8f5a9bb`, extended to the v0.2 stale-data alarm while preserving the current
payload validation, unavailable-state handling and mock isolation.

## Explicit mock testing

Mock mode is enabled only by its controls, never by BLE failure. Its connection
badge and state hero visibly say MOCK. Switching between mock and real operation
resets histories/statistics so simulated and received states are not mixed.
Mock controls exercise UI alarms and are not device measurements or classifier
quality evidence.

## Software verification

Run `python -B scripts/test_web_interfaces.py` or
`python -B -m pytest -q -p no:cacheprovider tests/test_frontend_integration.py`.
These execute the actual page JavaScript in Node with a mocked DOM and mocked
BLE/HTTP inputs. They verify client behavior, not physical Bluetooth, sensor
measurements, GitHub Pages deployment, or end-to-end hardware operation.
