#!/usr/bin/env python3
"""Run software-only frontend integration tests against the actual served pages.

The board page is extracted from firmware/include/web_page.h (PROGMEM), not a
nonexistent firmware/data/index.html. Node executes actual inline JavaScript
with explicit test-only DOM, clock and BLE/HTTP doubles. No hardware is implied.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def inline_script(html: str) -> str:
    scripts = re.findall(r"<script\b[^>]*>(.*?)</script\s*>", html, flags=re.S | re.I)
    if not scripts:
        raise AssertionError("No inline JavaScript found in actual page")
    return "\n".join(scripts)


def station_script() -> str:
    return inline_script((ROOT / "web-station/index.html").read_text(encoding="utf-8-sig"))


def board_script() -> str:
    header = (ROOT / "firmware/include/web_page.h").read_text(encoding="utf-8-sig")
    match = re.search(r'INDEX_HTML\[\]\s+PROGMEM\s*=\s*R"(\w*)\((.*?)\)\1"', header, re.S)
    if not match:
        raise AssertionError("Cannot extract actual INDEX_HTML PROGMEM raw literal")
    return inline_script(match.group(2))


# Explicit test doubles. Timers are controlled by scenarios; they never connect
# to physical devices, serve measurements, or substitute data into product code.
NODE_HARNESS = r"""
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


def run_js(source: str, scenario: str, name: str) -> None:
    node = shutil.which("node")
    if not node:
        raise RuntimeError("Node.js is required for runtime frontend integration tests")
    result = subprocess.run([node, "-e", NODE_HARNESS],
                            input=json.dumps(dict(source=source, scenario=scenario, name=name)),
                            text=True, capture_output=True, timeout=15, cwd=ROOT)
    if result.returncode:
        raise AssertionError(f"{name} failed:\n{result.stderr}\n{result.stdout}")
    if "PASS:" not in result.stdout:
        raise AssertionError(f"{name} did not finish its JavaScript assertions")


def main() -> int:
    print("Software-only tests: actual BLE station and embedded PROGMEM page JavaScript.", flush=True)
    return subprocess.call([sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests",
                            "-p", "test_frontend_integration.py", "-v"], cwd=ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
