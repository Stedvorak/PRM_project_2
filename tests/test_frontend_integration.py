"""Actual client JS behavior under controlled software-only inputs, not hardware."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

_spec = importlib.util.spec_from_file_location(
    "web_test_runner", Path(__file__).parents[1] / "scripts/test_web_interfaces.py")
runner = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(runner)

BLE_FIXTURE = r"""
const calls = [];
const characteristic = {
  properties: {read: true, notify: true},
  value: new DataView(new ArrayBuffer(0)),
  addEventListener(type, handler) { calls.push('listener'); this.listener=handler; },
  removeEventListener() { this.listener=null; },
  async startNotifications() { calls.push('start'); return this; },
  async readValue() { calls.push('read'); return this.value; }
};
const service = {async getCharacteristic(uuid) {
  assert.equal(uuid, '7c2f1001-73ad-4a0d-9ec4-10cc7ea46a10'); return characteristic;
}};
const server = {async getPrimaryService(uuid) {
  assert.equal(uuid, '7c2f1000-73ad-4a0d-9ec4-10cc7ea46a10'); return service;
}};
const device = {
  name: 'PRM-Project-2',
  addEventListener(type, handler) { this.disconnected=handler; },
  removeEventListener() { this.disconnected=null; },
  gatt: {connected: false,
    async connect() {this.connected=true; return server;},
    disconnect() {this.connected=false; if(device.disconnected) device.disconnected({target:device});}
  }
};
navigator.bluetooth = {async requestDevice(options) {
  assert.equal(options.filters[0].name, 'PRM-Project-2');
  assert.equal(options.optionalServices[0], '7c2f1000-73ad-4a0d-9ec4-10cc7ea46a10');
  return device;
}};
function packet(bytes) {
  characteristic.value = new DataView(Uint8Array.from(bytes).buffer);
  characteristic.listener({target:characteristic});
}
function timerTick() { __intervals.find(timer=>timer.ms===100).fn(); }
"""

STATUS_FIXTURE = r"""
const goodStatus = {
  ready: true, timestamp_ms: 5000, state: 'fast', state_id: 1,
  probabilities: {calm:0.1,fast:0.7,unattached:0.1,shaking:0.1},
  confidence:0.7,breaths_per_min:null
};
const noStatus = {
  ready:false,timestamp_ms:5001,state:null,state_id:null,
  probabilities:null,confidence:null,breaths_per_min:null
};
const goodSignal = {sample_rate_hz:25,unit:'g',samples:[
  {t_ms:4960,ax_g:0.1,ay_g:-0.2,az_g:1},
  {t_ms:5000,ax_g:0.15,ay_g:-0.1,az_g:0.95}
]};
"""


class BleStationRuntimeTests(unittest.TestCase):
    def run_scenario(self, scenario):
        runner.run_js(runner.station_script(), BLE_FIXTURE + scenario, self.id())

    def test_connect_subscribes_before_initial_read_empty_means_unavailable(self):
        self.run_scenario(r"""
await connectBLE();
assert.deepEqual(calls, ['listener','start','read']);
assert.equal(isConnected, true);
assert.equal(currentState, null);
assert.equal(el.stateClass.innerText, 'Unavailable');
assert.equal(isMockMode, false);
assert.equal(activeAlarms.disconnect, false);
""")

    def test_only_exact_binary_state_values_are_accepted(self):
        self.run_scenario(r"""
await connectBLE();
for (const code of [0,1,2,3]) { packet([code]); assert.equal(currentState,code); }
assert.equal(stats.packetCount,4);
for (const invalid of [[], [0,1], [4], [48], [255]]) {
  packet(invalid); assert.equal(currentState,null);
  assert.equal(stats.packetCount,4);
}
assert.equal(isMockMode,false);
""")

    def test_stale_state_and_disconnect_are_distinct_and_recovery_restarts_duration(self):
        self.run_scenario(r"""
await connectBLE(); packet([1]);
const start = stateStartTime;
__clock.now += 3101; timerTick();
assert.equal(currentState,null); assert.equal(isConnected,true);
assert.equal(activeAlarms.stale,true); assert.equal(activeAlarms.disconnect,false);
assert.equal(activeAlarms.fastBreathing,false);
assert.ok(timelineData.some(item=>item.state===null));
packet([1]); assert.equal(currentState,1);
assert.ok(stateStartTime>start); assert.equal(activeAlarms.stale,false);
device.gatt.disconnect();
assert.equal(isConnected,false); assert.equal(currentState,null);
assert.equal(activeAlarms.disconnect,true); assert.equal(activeAlarms.stale,false);
""")

    def test_unavailable_initial_stream_stales_without_a_false_class(self):
        self.run_scenario(r"""
await connectBLE(); __clock.now += 3101; timerTick();
assert.equal(currentState,null); assert.equal(activeAlarms.stale,true);
assert.equal(stats.packetCount,0); assert.equal(stats.transitions,0);
""")

    def test_duration_alarms_need_continuous_real_notifications(self):
        self.run_scenario(r"""
await connectBLE(); packet([1]);
for(let i=0;i<15;i++) { __clock.now+=1000; packet([1]); timerTick(); }
assert.equal(activeAlarms.fastBreathing,true);
packet([2]);
assert.equal(activeAlarms.fastBreathing,false);
for(let i=0;i<10;i++) { __clock.now+=1000; packet([2]); timerTick(); }
assert.equal(activeAlarms.unattached,true);
packet([]); assert.equal(currentState,null);
assert.equal(activeAlarms.unattached,false);
__clock.now+=20000; timerTick();
assert.equal(activeAlarms.fastBreathing,false);
assert.equal(activeAlarms.unattached,false);
""")

    def test_explicit_disconnect_and_mock_mode_do_not_mix_with_live_history(self):
        self.run_scenario(r"""
await connectBLE(); packet([3]); await disconnectBLE();
assert.equal(activeAlarms.disconnect,false); assert.equal(currentState,null);
toggleMockMode();
assert.equal(isMockMode,true); assert.ok(el.stateName.innerText.startsWith('MOCK:'));
assert.equal(timelineData.length,1);
window.mockSetState(2); assert.equal(currentState,2);
toggleMockMode(); assert.equal(isMockMode,false); assert.equal(currentState,null);
assert.equal(timelineData.length,0); assert.equal(stateLog.length,0);
""")

    def test_failed_connection_never_enables_mock_and_wrong_properties_rejected(self):
        self.run_scenario(r"""
characteristic.properties.notify=false;
await connectBLE();
assert.equal(isConnected,false); assert.equal(isMockMode,false);
assert.equal(currentState,null); assert.equal(calls.includes('start'),false);
navigator.bluetooth.requestDevice=async()=>{throw new Error('BLE radio unavailable');};
await connectBLE(); assert.equal(isMockMode,false); assert.equal(currentState,null);
""")

    def test_initial_read_cannot_overwrite_a_newer_notification(self):
        self.run_scenario(r"""
characteristic.readValue=async()=>{
  packet([3]);
  return new DataView(Uint8Array.from([0]).buffer);
};
await connectBLE(); assert.equal(currentState,3);
""")

    def test_duration_acknowledgment_persists_until_state_recovery(self):
        for code, seconds, key in ((1, 15, "fastBreathing"), (2, 10, "unattached")):
            with self.subTest(state=code):
                self.run_scenario(r"""
const code = CODE, limit = LIMIT, key = 'KEY';
await connectBLE(); packet([code]);
for(let i=0;i<limit;i++) { __clock.now+=1000; packet([code]); timerTick(); }
assert.equal(activeAlarms[key],true);
const alarmCount=stats.alarmCount;
silenceAlarms();
assert.equal(acknowledgedAlarms[key],true);
assert.equal(activeAlarms[key],false);
assert.ok(el.stateHero.className.includes('acknowledged'));
for(let i=0;i<5;i++) { __clock.now+=1000; packet([code]); timerTick(); }
assert.equal(activeAlarms[key],false);
assert.equal(stats.alarmCount,alarmCount);
assert.ok((code===1 ? el.fastStatusLabel : el.unattachedStatusLabel).innerText.includes('Acknowledged'));
packet([0]);
assert.equal(acknowledgedAlarms[key],false);
packet([code]);
for(let i=0;i<limit;i++) { __clock.now+=1000; packet([code]); timerTick(); }
assert.equal(activeAlarms[key],true);
assert.equal(stats.alarmCount,alarmCount+1);
""".replace("CODE", str(code)).replace("LIMIT", str(seconds)).replace("KEY", key))

    def test_duration_acknowledgment_rearms_after_unavailable_gap(self):
        self.run_scenario(r"""
await connectBLE(); packet([1]);
for(let i=0;i<15;i++) { __clock.now+=1000; packet([1]); timerTick(); }
silenceAlarms();
packet([]);
assert.equal(acknowledgedAlarms.fastBreathing,false);
const unavailableTitle=el.stateName.innerText;
silenceAlarms();
assert.equal(currentState,null);
assert.equal(el.stateName.innerText,unavailableTitle);
assert.equal(el.stateClass.innerText,'Unavailable');
packet([1]);
for(let i=0;i<15;i++) { __clock.now+=1000; packet([1]); timerTick(); }
assert.equal(activeAlarms.fastBreathing,true);
""")

    def test_stale_acknowledgment_persists_and_rearms_on_valid_notification(self):
        self.run_scenario(r"""
await connectBLE(); packet([0]);
__clock.now+=3101; timerTick();
assert.equal(activeAlarms.stale,true);
const unavailableTitle=el.stateName.innerText;
const alarmCount=stats.alarmCount;
silenceAlarms();
assert.equal(acknowledgedAlarms.stale,true);
assert.equal(el.stateName.innerText,unavailableTitle);
assert.equal(el.stateClass.innerText,'Unavailable');
for(let i=0;i<5;i++) { __clock.now+=100; timerTick(); }
packet([]); __clock.now+=100; timerTick();
assert.equal(activeAlarms.stale,false);
assert.equal(stats.alarmCount,alarmCount);
assert.equal(currentState,null);
packet([0]);
assert.equal(acknowledgedAlarms.stale,false);
__clock.now+=3101; timerTick();
assert.equal(activeAlarms.stale,true);
assert.equal(stats.alarmCount,alarmCount+1);
""")

    def test_disconnect_acknowledgment_persists_until_a_new_connection_incident(self):
        self.run_scenario(r"""
await connectBLE(); packet([0]); device.gatt.disconnect();
assert.equal(activeAlarms.disconnect,true);
const alarmCount=stats.alarmCount;
const unavailableTitle=el.stateName.innerText;
silenceAlarms();
assert.equal(acknowledgedAlarms.disconnect,true);
assert.equal(el.stateName.innerText,unavailableTitle);
assert.equal(el.stateCode.innerText,'-');
assert.equal(el.stateClass.innerText,'Unavailable');
packet([0]); // A queued old notification cannot revive a disconnected device.
assert.equal(currentState,null);
assert.equal(el.stateName.innerText,unavailableTitle);
device.gatt.disconnect();
__clock.now+=500; timerTick();
assert.equal(activeAlarms.disconnect,false);
assert.equal(stats.alarmCount,alarmCount);
await connectBLE(); packet([0]);
assert.equal(acknowledgedAlarms.disconnect,false);
device.gatt.disconnect();
assert.equal(activeAlarms.disconnect,true);
assert.equal(stats.alarmCount,1); // Reconnection starts a fresh statistics session.
""")


class EmbeddedDashboardRuntimeTests(unittest.TestCase):
    def run_scenario(self, scenario):
        runner.run_js(runner.board_script(), STATUS_FIXTURE + scenario, self.id())

    def test_live_prediction_renders_probability_object_and_null_rate(self):
        self.run_scenario(r"""
updateUI(goodStatus);
assert.equal(stateIdText.textContent,'1');
assert.equal(probBars.fast.val.textContent,'70.0%');
assert.equal(bpmValue.textContent,'N/A');
updateUI(noStatus);
assert.equal(stateIdText.textContent,'-');
assert.equal(confValue.textContent,'N/A');
assert.equal(probBars.fast.val.textContent,'N/A');
""")

    def test_malformed_status_never_passes_client_validation(self):
        self.run_scenario(r"""
for(const patch of [
  {ready:1}, {timestamp_ms:-1}, {state_id:null}, {state:'calm'},
  {confidence:0.2}, {breaths_per_min:-1},
  {probabilities:[0.1,0.7,0.1,0.1]},
  {probabilities:{calm:0,fast:0.8,unattached:0,shaking:0}},
]) { assert.throws(()=>validateStatus({...goodStatus,...patch})); }
assert.throws(()=>validateStatus({...noStatus,state:'calm',state_id:0}));
""")

    def test_signal_uses_real_samples_with_strict_timestamps_and_failure_clears(self):
        self.run_scenario(r"""
renderSignal(goodSignal);
assert.equal(latestSignalSamples.length,2);
assert.equal(latestSignalSamples[1].ax_g,0.15);
assert.throws(()=>validateSignal({...goodSignal,unit:'m/s2'}));
assert.throws(()=>validateSignal({...goodSignal,samples:[goodSignal.samples[0],goodSignal.samples[0]]}));
assert.throws(()=>validateSignal({...goodSignal,samples:[{...goodSignal.samples[0],ax_g:null}]}));
assert.throws(()=>validateSignal({...goodSignal,samples:Array(101).fill(goodSignal.samples[0])}));
renderSignal({sample_rate_hz:25,unit:'g',samples:[]});
assert.equal(latestSignalSamples.length,0);
""")

    def test_cached_nonadvancing_status_and_signal_become_unavailable(self):
        self.run_scenario(r"""
updateUI(goodStatus); renderSignal(goodSignal);
__clock.now+=2101;
assert.throws(()=>updateUI(goodStatus));
renderSignal(goodSignal);
assert.equal(latestSignalSamples.length,0);
assert.ok(signalStatus.textContent.toLowerCase().includes('stale'));
""")

    def test_poll_requests_both_actual_endpoints_without_overlapping_cycles(self):
        self.run_scenario(r"""
const urls=[];
let resolveStatus;
fetch=async endpoint=>{
  urls.push(endpoint);
  if(endpoint==='/api/status') return await new Promise(resolve=>{resolveStatus=resolve;});
  return {ok:true,json:async()=>goodSignal};
};
const first=pollEndpoints();
await pollEndpoints();
assert.deepEqual(urls,['/api/status','/api/signal']);
resolveStatus({ok:true,json:async()=>goodStatus});
await first;
assert.equal(pollInFlight,false);
assert.equal(stateIdText.textContent,'1');
assert.equal(latestSignalSamples.length,2);
assert.ok(__timeouts.some(timer=>timer.fn===pollEndpoints && timer.ms===500));
fetch=async()=>{throw new Error('AP connection lost');};
await pollEndpoints();
assert.equal(stateIdText.textContent,'-');
assert.equal(latestSignalSamples.length,0);
""")

    def test_watchdog_clears_transport_staleness_and_device_restart(self):
        self.run_scenario(r"""
updateUI(goodStatus); renderSignal(goodSignal);
lastStatusReceivedAt=performance.now(); lastSignalReceivedAt=performance.now();
__clock.now+=2101; checkStaleness();
assert.equal(stateIdText.textContent,'-'); assert.equal(latestSignalSamples.length,0);
__clock.now+=1;
updateUI({...goodStatus,timestamp_ms:10});
assert.equal(lastDeviceTimestamp,10);
assert.equal(latestSignalSamples.length,0);
""")


if __name__ == '__main__':
    unittest.main()
