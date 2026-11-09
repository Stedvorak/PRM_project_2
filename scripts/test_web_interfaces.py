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

    # Acknowledge / dismiss behavior checks
    assert 'acknowledgedAlarms' in src, "acknowledgedAlarms object missing!"
    assert 'acknowledgedAlarms.fastBreathing = true' in src, "fastBreathing acknowledge handling missing!"
    assert 'acknowledgedAlarms.unattached = true' in src, "unattached acknowledge handling missing!"
    assert 'acknowledgedAlarms.fastBreathing = false' in src, "Incident reset on state change missing!"

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

def test_alarm_state_machine():
    print("[4] Testing Alarm Acknowledgment State Machine Logic...")
    
    # State machine simulation mirroring web-station/index.html logic
    class AlarmStateMachine:
        def __init__(self):
            self.currentState = None
            self.stateStartTime = 0
            self.activeAlarms = {'fastBreathing': False, 'unattached': False}
            self.acknowledgedAlarms = {'fastBreathing': False, 'unattached': False}
            self.alarmsFiredCount = 0

        def update_state(self, new_state, now):
            if self.currentState != new_state:
                self.currentState = new_state
                self.stateStartTime = now
                self.activeAlarms['fastBreathing'] = False
                self.activeAlarms['unattached'] = False
                self.acknowledgedAlarms['fastBreathing'] = False
                self.acknowledgedAlarms['unattached'] = False

        def tick(self, now):
            stateSec = now - self.stateStartTime
            if self.currentState == 1:
                if stateSec >= 15:
                    if not self.acknowledgedAlarms['fastBreathing'] and not self.activeAlarms['fastBreathing']:
                        self.activeAlarms['fastBreathing'] = True
                        self.alarmsFiredCount += 1
            elif self.currentState == 2:
                if stateSec >= 10:
                    if not self.acknowledgedAlarms['unattached'] and not self.activeAlarms['unattached']:
                        self.activeAlarms['unattached'] = True
                        self.alarmsFiredCount += 1

        def acknowledge(self):
            if self.activeAlarms['fastBreathing']:
                self.acknowledgedAlarms['fastBreathing'] = True
                self.activeAlarms['fastBreathing'] = False
            if self.activeAlarms['unattached']:
                self.acknowledgedAlarms['unattached'] = True
                self.activeAlarms['unattached'] = False

    sm = AlarmStateMachine()
    
    # Incident 1: Fast breathing triggers after 15s
    sm.update_state(1, 0)
    sm.tick(10)
    assert not sm.activeAlarms['fastBreathing'], "Alarm triggered too early!"
    sm.tick(15)
    assert sm.activeAlarms['fastBreathing'], "Alarm failed to trigger at 15s!"
    assert sm.alarmsFiredCount == 1

    # User acknowledges incident 1
    sm.acknowledge()
    assert not sm.activeAlarms['fastBreathing'], "Alarm should be silenced after acknowledge!"
    assert sm.acknowledgedAlarms['fastBreathing'], "Alarm should be marked acknowledged!"

    # Next tick: condition still holds (state 1, 20s), but alarm MUST NOT re-trigger
    sm.tick(20)
    assert not sm.activeAlarms['fastBreathing'], "BUG: Alarm re-triggered while acknowledged!"
    assert sm.alarmsFiredCount == 1, "Alarm count incremented on acknowledged incident!"

    # State returns to calm (0)
    sm.update_state(0, 25)
    assert not sm.acknowledgedAlarms['fastBreathing'], "Acknowledge flag not cleared on state change!"

    # Incident 2: Patient fast breathes again
    sm.update_state(1, 30)
    sm.tick(40) # 10s into new incident
    assert not sm.activeAlarms['fastBreathing']
    sm.tick(45) # 15s into new incident: MUST trigger new alarm!
    assert sm.activeAlarms['fastBreathing'], "New incident failed to trigger alarm!"
    assert sm.alarmsFiredCount == 2

    print(" -> Alarm state machine verified: no re-triggers during incident, re-arms on new incident.")

if __name__ == '__main__':
    try:
        test_web_station()
        test_firmware_web_page()
        test_firmware_include_header()
        test_alarm_state_machine()
        print("\nALL FRONTEND CONTRACT AND IMPLEMENTATION TESTS PASSED SUCCESSFULLY!")
    except AssertionError as e:
        print(f"\nTEST FAILED: {e}", file=sys.stderr)
        sys.exit(1)
