# Submission status — evidence, not assumptions

- [x] Sections1 and2 accepted by teacher, reported explicitly by user.
- [x] M01 v1 selected, header SHA256 abe113bc81318bea4ee2d595bb72880d89c53ddba053a46d189cb0a61bcb7a27.
- [x] All12 real recordings and metadata pushed; raw dataset commit fa89ca242ae11dccdc65ededd9f67d704043e643.
- [x] Grouped evaluation and all6 candidates/results/figures pushed; model commit619e0c6b3005f175d9e11638cd51de7ba227dc9c.
- [x] Trained monitoring firmware uploaded, hash verified; real onboard inference and sensor detection confirmed.
- [x] GPIO48 RGB red/green/blue/magenta visually confirmed by user; runtime mapping enabled.
- [x] Real ESP32 AP association and both HTTP APIs verified; embedded webpage HTTP200.
- [x] Final silent monitoring image flashed onCOM3 with verified hashes; USB inference diagnostics disabled.
- [x] Actual Edge browser rendered board page, four probabilities and live real X/Y/Z plot;10status/9signal HTTP200responses, no JSexceptions; evidenceH09_browser_board/live-page.png and report.json.
- [x] Public HTTPS monitor exists at https://stedvorak.github.io/PRM_project_2/web-station/ .
- [ ] Physical BLE connect/notifications/timeline/alarms: PC adapter currently not ready; operator device check pending.
- [x] David prepared sections4 and5; preserve his implementation (user report; teacher demonstration remains coordinated with David).
- [x] Actual wiring photograph: operator-supplied Image.jfif preserved byte-for-byte as docs/wiring.jpg and displayed in README; wiring pin table and build instructions are available.
- [x] Reviewed integration via PR1; verified integrated code commit4ac1448007295eea1f42d1a000e763e219b7024e contains both histories, all24 raw files, results, website and exact selected model.
- [x] Pages built integrated main at4ac1448007295eea1f42d1a000e763e219b7024e; actual HTTPS monitor matches remote source after newline normalization (D01_main_delivery/pages-code-deployment.json).
- [x] Teacher tomasvicar access: GitHub API returned write permission at delivery recheck.
- [x] At least3 intermediate commits were pushed as work proceeded, each push/fetch verified in this session:91667e0(14:07),7c0fa51(14:16),cf6004e(14:43),d212b83(14:52),1b3fe4a(15:01),fa89ca2(15:20),619e0c6(15:34),2026-11-09Europe/Prague.
- [ ] Final teacher demonstration/submission acknowledgement. Do not claim accepted sections beyond user-confirmed1/2.

Group: David Bártek, Štěpán Dvořák. Frontend tools: Antigravity/Gemini; firmware/ML/integration: OpenAI Codex and native subagents. All members must explain the code.

Important limitations: same operator/device and two inferred acquisition rounds;
M01 placement dependence; pooled unattached recall53.09%; live calm check15/30.
Figures are genuine grouped-CV/data plots, not a physical wiring photograph.

M07 v1 respiration extension: monitoring build passed (206.10 s), upload to COM3 passed (41.624 s), written image hash verified and board reset. M01 header unchanged. Physical numeric BPM/accuracy awaits operator verification on another device; this PC stays on eduroam. Expanded validation was stopped by user request. See RESPIRATION.md and outputs/verification/M07_respiration/deployment.json.
