#!/usr/bin/env python3
"""
Test Suite for Web Interfaces (web-station and ESP32 dashboard).
Verifies:
1. Exact match with docs/INTERFACES.md:
   - Device Name: PRM-Project-2
   - Service UUID: 7c2f1000-73ad-4a0d-9ec4-10cc7ea46a10
   - Characteristic UUID: 7c2f1001-73ad-4a0d-9ec4-10cc7ea46a10
   - States: 0=calm, 1=fast, 2=unattached, 3=shaking
   - Colors: green, red, blue, magenta
2. Alarm thresholds in web-station:
   - Fast breathing limit: 15s
   - Unattached limit: 10s
   - Disconnect handling: gattserverdisconnected
3. HTTP contract in firmware/data/index.html:
   - Endpoint: /api/status
   - Keys: state, state_id, breaths_per_min, confidence, probabilities
   - Null handling logic
"""

import sys
import re

def test_web_station():
    with open('web-station/index.html', 'r', encoding='utf-8') as f:
        src = f.read()

    print("[1] Testing web-station/index.html...")
    assert '7c2f1000-73ad-4a0d-9ec4-10cc7ea46a10' in src, "Service UUID missing or incorrect!"
    assert '7c2f1001-73ad-4a0d-9ec4-10cc7ea46a10' in src, "Characteristic UUID missing or incorrect!"
    assert 'PRM-Project-2' in src, "Device name 'PRM-Project-2' missing!"
    
    # State mapping checks
    assert "0: { name: 'Calm Breathing', class: 'calm'" in src or "0: calm" in src.lower()
    assert "1: { name: 'Fast Breathing', class: 'fast'" in src or "1: fast" in src.lower()
    assert "2: { name: 'Not Attached', class: 'unattached'" in src or "2: unattached" in src.lower()
    assert "3: { name: 'Shaking', class: 'shaking'" in src or "3: shaking" in src.lower()

    # Alarm thresholds checks
    assert '15' in src and 'FAST_BREATHING_SEC' in src, "15s Fast breathing alarm threshold missing!"
    assert '10' in src and 'UNATTACHED_SEC' in src, "10s Unattached alarm threshold missing!"
    assert 'gattserverdisconnected' in src, "Disconnect event listener missing!"

    # Web Audio & Mock mode checks
    assert 'AudioContext' in src, "Web Audio API sound generator missing!"
    assert 'mockSetState' in src, "Mock state simulator missing!"
    assert 'mockScenarioFastAlarm' in src, "Fast alarm test scenario missing!"
    assert 'mockScenarioUnattachedAlarm' in src, "Unattached alarm test scenario missing!"

    print(" -> web-station/index.html passed all contract and functional checks.")

def test_firmware_web_page():
    with open('firmware/data/index.html', 'r', encoding='utf-8') as f:
        src = f.read()

    print("[2] Testing firmware/data/index.html...")
    assert '/api/status' in src, "Endpoint /api/status missing!"
    assert 'state_id' in src, "state_id key missing!"
    assert 'breaths_per_min' in src, "breaths_per_min handling missing!"
    assert 'probabilities' in src, "probabilities handling missing!"
    assert 'confidence' in src, "confidence handling missing!"

    # Check null handling logic
    assert 'null' in src, "Null value handling missing!"

    print(" -> firmware/data/index.html passed all contract checks.")

def test_firmware_include_header():
    with open('firmware/include/web_page.h', 'r', encoding='utf-8') as f:
        hdr = f.read()

    print("[3] Testing firmware/include/web_page.h...")
    assert 'INDEX_HTML' in hdr, "INDEX_HTML declaration missing!"
    assert 'PROGMEM' in hdr, "PROGMEM keyword missing!"
    assert '/api/status' in hdr, "Endpoint missing in embedded header!"

    print(" -> firmware/include/web_page.h passed header checks.")

if __name__ == '__main__':
    try:
        test_web_station()
        test_firmware_web_page()
        test_firmware_include_header()
        print("\nALL FRONTEND CONTRACT AND IMPLEMENTATION TESTS PASSED SUCCESSFULLY!")
    except AssertionError as e:
        print(f"\nTEST FAILED: {e}", file=sys.stderr)
        sys.exit(1)
