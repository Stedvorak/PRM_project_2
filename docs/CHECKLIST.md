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
- [x] Build separate50Hz acquisition firmware and pass68 integrated software tests (18 client-JS,14 recorder)
- [x] Flash checked acquisition image to COM3 and verify written flash hashes
- [x] Run actual sensor detection test: FAILED, no ACK at0x68/0x69 on GPIO8/9; no measurements fabricated
- [x] Repeat physical detection successfully: address0x68, WHO_AM_I0x68,50Hz on SDA8/SCL9 (V05 log)
- [x] Record and independently validate first real unattached/table30-second session:1499 valid samples,49.943Hz,20-21ms intervals; one malformed line rejected, no missing CSV fields or timestamp-gap loss
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
One real unattached recording exists; the other classes and multiple independent
recordings are still needed. No trained model exists. Demo firmware must report
unavailable predictions until genuine model training/evaluation is complete.
