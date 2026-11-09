# PRM-Project-2 Web Station (GitHub Pages)

Standalone Web Bluetooth Bedside Monitor for real-time movement and breathing classification.

## Live Deployment Instructions

This station is designed with zero dependencies (vanilla HTML5, CSS3, ES6 JavaScript) and runs directly from GitHub Pages or any local static web server.

### Deploying on GitHub Pages:
1. Push `web-station/index.html` to your GitHub repository (or dedicated public repository).
2. Go to **Settings** → **Pages**.
3. Under **Build and deployment**:
   - Source: **Deploy from a branch**
   - Branch: `main` (or active branch), folder: `/ (root)` or `/web-station`.
4. Save and open the generated HTTPS URL.

> **Note on Web Bluetooth Security Context:**
> Web Bluetooth requires a secure context (`https://` or `http://localhost`). Browsers will not permit Bluetooth access over insecure plain HTTP.

## Browser Compatibility

- **Google Chrome** (macOS, Windows, Android)
- **Microsoft Edge** (macOS, Windows)
- **Opera** (macOS, Windows)

*Note: Safari and iOS browsers do not currently support the Web Bluetooth API. Use the built-in Mock Testing Suite on unsupported platforms.*

## Contract Specification Compliance

- **Device Name**: `PRM-Project-2`
- **Service UUID**: `7c2f1000-73ad-4a0d-9ec4-10cc7ea46a10`
- **State Characteristic UUID**: `7c2f1001-73ad-4a0d-9ec4-10cc7ea46a10`
- **State Mappings**:
  - `0`: **Calm Breathing** (Green `#10b981`)
  - `1`: **Fast Breathing** (Red `#ef4444`)
  - `2`: **Not Attached** (Blue `#3b82f6`)
  - `3`: **Shaking** (Magenta `#d946ef`)

## Alarms and Thresholds

| Alarm | Condition | Action |
|-------|-----------|--------|
| **Fast Breathing** | State 1 persists for **> 15 seconds** | Flashing red banner + rapid high-pitch medical audio alert |
| **Not Attached** | State 2 persists for **> 10 seconds** | Pulsing warning banner + two-tone chime alert |
| **Connection Drop** | BLE GATT disconnected (`gattserverdisconnected`) | Critical alert banner + alert siren |

All audio alerts are synthesized on-the-fly using the Web Audio API without requiring any external audio files. A mute/unmute button and an acknowledge button are provided in the UI.

## Mock Testing Suite

The page includes a built-in mock control panel:
- **Manual State Overrides**: Click State 0, 1, 2, or 3 to test UI updates immediately.
- **Automated Scenario 1**: Fast breathing alarm demonstration (triggers State 1 and runs a live 15s countdown to alarm).
- **Automated Scenario 2**: Unattached alarm demonstration (triggers State 2 and runs a live 10s countdown to alarm).
- **Automated Scenario 3**: Simulated GATT connection drop.
- **Auto-Cycle**: Continuously cycles through states every 5 seconds.
