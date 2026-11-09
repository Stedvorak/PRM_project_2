# Final delivery guide

Group: David B?rtek and ?t?p?n Dvo??k.
Repository: https://github.com/Stedvorak/PRM_project_2/tree/main
BLE monitor: https://stedvorak.github.io/PRM_project_2/web-station/

## Board demonstration

The ESP32-S3 COM3 now runs the trained silent monitoring firmware, not acquisition
firmware. Selected classifier is M01v1, a seven-node/depth2 decision tree.
Sensor SDA8/SCL9,3.3V, address0x68; verified WS2812/NeoPixel RGB onGPIO48.
Runtime colors: calm green, fast red, unattached blue, shaking magenta.
Diagnostic cycling and application USB inference/capture streams are disabled.

Join Wi-Fi PRM-Project-2, password prm-lab-2026, then open
http://192.168.4.1/ . The page is David's embedded INDEX_HTML from web_page.h,
served directly from PROGMEM with no filesystem upload required. A real Edge
browser loaded it over the ESP32 AP, rendered real classification/four
probabilities/100real X/Y/Z samples and received continued live API responses.
See outputs/verification/H09_browser_board/report.json and live-page.png.
Breaths/minute is correctly unavailable, not estimated from a class label.

## Verified source and results

Integrated code commit:4ac1448007295eea1f42d1a000e763e219b7024e.
Selected model introduction:619e0c6b3005f175d9e11638cd51de7ba227dc9c.
Selected model SHA256:abe113bc81318bea4ee2d595bb72880d89c53ddba053a46d189cb0a61bcb7a27.
Later final documentation commits preserve the same firmware/model and are
identified by the final GitHub main SHA in the delivery response.

All12real recordings/24CSV+metadata files are on remote main and byte-verified.
There are17993samples, three files/two separated acquisition bouts per class.
Evaluation holds out two complete collection rounds, not random overlapping
windows. M01 pooled accuracy83.64%, mean-fold balanced86.11%, macroF1 0.8351.
Unattached held-out recall53.09% and placement dependence are real limitations.
Live unattached22/22 matched; live calm15/30 was unstable and remains in evidence.
The user reports teacher acceptance of sections1/2; no other grading is assumed.
All115post-merge software tests passed. Actual on-board inference ran at2Hz,
with feature+prediction below2.5ms. Scientific figures and six-method results
are under outputs/figures/delivery_v2 and outputs/results.

## Rebuild without retraining

From the repository root, with Python3.11:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
.\.venv\Scripts\python.exe -m platformio run -e esp32-s3 -j 4
.\.venv\Scripts\python.exe -m platformio run -e esp32-s3 -t upload --upload-port COM3
```

The selected model is already in firmware/include/prm_model.h. Do not run
collection firmware during the final monitoring demonstration. Original
recordings are preserved. MODEL_COMPARISON.md documents an optional isolated
reproduction command; it is not needed for submission and never auto-installs.

## Outstanding requirements

- Real BLE connection, notifications, timeline, duration alarms and lost-link
  alarm still require a compatible operator device. This PC's RealtekBluetooth4.2
  adapter reports not ready; do not present software mocks as hardware success.
- Add an actual wiring photograph: docs/wiring.jpg does not currently exist.
- Coordinate David's prepared sections4/5 demonstration without rewriting them.
- Obtain final teacher/submission acknowledgement. Only sections1/2 acceptance
  has been explicitly reported.

Teacher tomasvicar has verified write access. More than3intermediate pushes
were performed and verified during the lab (ledger in SUBMISSION.md). Both
branch histories were merged through reviewed PR1; no force push or reset used.
AI assistance: OpenAI Codex/native subagents for firmware, ML, tests/integration;
Antigravity/Gemini for David's web interfaces. Members must explain the code.

Final documentation is maintained in an isolated worktree. David's active
checkout, selected model and device firmware are not changed by documentation.

Physical webpage/gravity-display troubleshooting evidence is in PHYSICAL_WEB_CHECK.md; no firmware/model changes were made for that investigation.
