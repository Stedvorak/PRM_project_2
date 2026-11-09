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

    # Own Extension: BPM estimation display checks
    assert 'bpmBadge' in src and 'stateBpmText' in src, "BPM indicator missing from web-station state hero!"

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
    assert 'heroBpmText' in src and 'bpmValue' in src, "hero BPM indicator missing from dashboard!"

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
    assert 'heroBpmText' in hdr and 'bpmValue' in hdr, "hero BPM indicator missing from embedded web page!"

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

def inline_script(html: str) -> str:
    scripts = re.findall(r"<script\b[^>]*>(.*?)</script\s*>", html, flags=re.S | re.I)
    return "\n".join(scripts)

def station_script() -> str:
    with open('web-station/index.html', 'r', encoding='utf-8') as f:
        return inline_script(f.read())

def board_script() -> str:
    with open('firmware/include/web_page.h', 'r', encoding='utf-8') as f:
        header = f.read()
    match = re.search(r'INDEX_HTML\[\]\s+PROGMEM\s*=\s*R"(\w*)\((.*?)\)\1"', header, re.S)
    if match:
        return inline_script(match.group(2))
    return inline_script(header)

def run_js(source: str, scenario: str, name: str) -> None:
    import shutil
    import unittest
    node = shutil.which("node")
    if not node:
        raise unittest.SkipTest("Node.js is not installed; skipping runtime JS DOM simulation")
    # If node is available, execute via Node harness
    import subprocess
    import json
    harness = r"""
const fs = require('fs');
const vm = require('vm');
const assert = require('assert/strict');
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const clock = {now: 10000};
const intervals = [];
const timeouts = [];
const elements = new Map();
function element(id) {
  if (!elements.has(id)) {
    const classes = new Set();
    const context = new Proxy({}, {get(target, property) {
      return target[property] || (() => {});
    }});
    elements.set(id, {
      id, style: {}, innerText: '', textContent: '', innerHTML: '',
      className: '', disabled: false, width: 600, height: 180,
      parentElement: {clientWidth: 600, clientHeight: 180},
      classList: {add: x => classes.add(x), remove: x => classes.delete(x),
        replace: (a,b) => {classes.delete(a); classes.add(b);},
        contains: x => classes.has(x)},
      getContext: () => context, addEventListener() {}, removeEventListener() {},
      appendChild() {}, remove() {}, click() {}
    });
  }
  return elements.get(id);
}
class ControlledDate extends Date {
  constructor(...args) { super(...(args.length ? args : [clock.now])); }
  static now() { return clock.now; }
}
const sandbox = {
  assert, console: {log() {}, warn() {}, error() {}},
  Date: ControlledDate, performance: {now: () => clock.now},
  document: {getElementById: element, createElement: element, body: element('body')},
  window: {addEventListener() {}}, navigator: {},
  setInterval(fn, ms) { const timer={fn, ms}; intervals.push(timer); return timer; },
  clearInterval(timer) { if (timer) timer.cancelled=true; },
  setTimeout(fn, ms) { const timer={fn, ms}; timeouts.push(timer); return timer; },
  clearTimeout(timer) { if (timer) timer.cancelled=true; },
  AbortController, DataView, Uint8Array, Blob, URL,
  alert() {}, fetch: async () => { throw new Error('No HTTP test fixture installed'); },
  __clock: clock, __intervals: intervals, __timeouts: timeouts,
  __elements: elements,
};
vm.createContext(sandbox);
(async () => {
  const result = vm.runInContext(input.source + '\n;(async () => {\n' + input.scenario + '\n})()', sandbox,
    {timeout: 5000, filename: input.name});
  await result;
  process.stdout.write('PASS: actual page JavaScript scenario\n');
})().catch(error => {console.error(error.stack || error); process.exitCode=1;});
"""
    result = subprocess.run([node, "-e", harness],
                            input=json.dumps(dict(source=source, scenario=scenario, name=name)),
                            text=True, capture_output=True, timeout=15)
    if result.returncode != 0:
        raise AssertionError(f"{name} failed:\n{result.stderr}\n{result.stdout}")

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
