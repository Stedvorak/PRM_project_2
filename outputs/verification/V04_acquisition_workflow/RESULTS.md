# Acquisition readiness and real hardware test

- Separate N16R8 acquisition firmware build: PASS.
- Main N16R8 demo and25Hz capture builds: PASS (V03 logs).
- Integrated software tests:68 passed; synthetic fixtures only, not real model evaluation.
- Checked image: ESP32-S3,16MB flash,80MHz, DIO image header. The pinned
  PlatformIO builder intentionally maps QIO/QOUT image headers to DIO; runtime
  SDK configuration remains qio_opi for quad flash/octal PSRAM.
- Physical50Hz acquisition upload to COM3: PASS, all written region hashes verified.
- Actual identity probe: FAILED; repeated address ACK=false at both0x68 and0x69
  on configured SDA8/SCL9. No WHO_AM_I PASS or configuration PASS was observed.
- Numeric sensor measurements/labeled recordings created: none.
- Board is currently running acquisition-only firmware, not the AP/BLE demo.

Evidence: upload-authorized.txt, sensor-detection.txt, build.txt,
bootloader-image-info.txt, pytest.txt. The initial upload.txt records a
network-restricted package-install attempt; upload-authorized.txt is the
subsequent successful authorized upload. Probe failure is a real test result,
not proof of which physical wiring/power condition caused it.

Connect VCC3.3V/GND/SDA8/SCL9 and rerun:

```powershell
.\.venv\Scripts\python.exe tools/record_session.py --port COM3 --detect-only --reset
.\.venv\Scripts\python.exe tools/record_session.py --port COM3 --label calm --duration 30
```

Only run the labeled command once the operator has established that physical
state. Never treat a missing sensor as a valid four-class prediction. Raw50Hz
recordings remain separate from M01's25Hz inputs and require explicit conversion.
