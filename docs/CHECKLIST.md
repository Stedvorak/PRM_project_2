# Assignment checklist — real-time AI

- [x] Read the complete real-time AI assignment
- [x] Identify deliverables: own labeled data, trained on-board classifier, four LED states, BLE GitHub Pages monitor/timeline/alarms, AP-hosted signal/probabilities, own extension, rebuild documentation
- [x] Approve interface v0.2 and verify shared main/firmware remote commit 91667e00e0bfef30a313fe35c800e566fdda7835
- [ ] Confirm actual lab start/end time and reserve final 30 minutes
- [x] Confirm ESP32-S3 rev0.2 on COM3, 16MB quad flash, user-verified8MB PSRAM; configure N16R8 target
- [x] Configure sensor3.3V, SDA8/SCL9, preferred0x68 with verified0x69 fallback
- [ ] Physically verify MPU-6050 connection and detection, LED GPIO/type and power-only demo mode
- [ ] Collect and inspect real labeled sensor recordings (four classes, multiple independent recordings)
- [ ] Evaluate registered methods with recording-group held-out data
- [ ] Select exactly one genuinely evaluated final method
- [x] Build demo firmware for explicit N16R8 and pass50 software tests (including14 actual client-JS runtime tests)
- [ ] Flash and verify sensor acquisition, failure handling and LED on physical board
- [ ] Verify BLE read/notify, 1 Hz heartbeat, reconnect and Wi-Fi coexistence on hardware
- [x] Integrate Antigravity embedded PROGMEM page and BLE monitor source from verified2064cf8; adapt to v0.2
- [ ] Verify GitHub Pages deployment and actual browser pairing
- [ ] Demonstrate live signal, probabilities, timeline, both duration alarms and lost connection
- [ ] Implement and demonstrate one agreed own extension
- [ ] Save real evaluation results and required figures
- [ ] Complete wiring photo, group members, monitoring link, build/train instructions and AI-tool disclosure
- [ ] Verify at least three intermediate lab commits pushed as work proceeds
- [x] Verify teacher tomasvicar access (GitHub API returned write permission; recheck at delivery)
- [ ] Final tests, tracked model/report/results, PR integration and remote commit comparison
- [ ] Demonstrate every completed part to teacher before lab ends
- [ ] Verify final submission

Software tests using synthetic fixtures must never be reported as real sensor or model evaluation.
No input data or trained model currently exists. Default firmware must report unavailable predictions.
