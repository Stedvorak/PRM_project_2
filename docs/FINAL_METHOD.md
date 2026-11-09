# Final Selected Method

Selected method: M01 v1, decision tree on12 inertial window features.
Exact deployed implementation: firmware/include/prm_model.h.
Candidate artifact: outputs/results/M01_v1/prm_model.h.
Selected header SHA-256: abe113bc81318bea4ee2d595bb72880d89c53ddba053a46d189cb0a61bcb7a27.
Feature implementation: firmware/include/prm_features.h.
Training/evaluation source: tools/compare_models.py.
Dataset: data/validated/manifest.json; all12 approved recordings,17993 raw samples.
Parameters:25Hz;100-sample window;stride25;depth limit5;minimum leaf2;
balanced class weights;random_state42. Final fitted tree:7nodes,depth2.
Validation: two whole collection rounds held out in opposite directions;
324 windows. Mean-fold balanced accuracy86.1111%; pooled accuracy/balanced
accuracy83.64198%; macro F1 0.8351369. Pooled unattached recall53.0864%.
Candidate selection used these CV folds; not an untouched final test.

Result files: outputs/results/M01_v1/metrics.json, heldout_predictions.csv,
feature_windows.npz and prm_model.h; outputs/comparison/C01_v1/summary.json;
outputs/comparison/C02_invariant_v1/summary.json; outputs/figures/delivery_v2/.
Export verification:324 actual feature vectors match final training predictions
with zero probability error; target C++ compilation passes. This is software
parity evidence, not a hardware accuracy test.

Selected model integration commit:619e0c6b3005f175d9e11638cd51de7ba227dc9c,
verified on origin/codex/firmware. Later RGB/documentation/integration commits
preserve the exact selected header SHA-256 above.
Verified integrated main code commit:4ac1448007295eea1f42d1a000e763e219b7024e.
Both development histories, final silent firmware, model, data, results and report
are present there. D01_main_delivery/files-and-model.json verifies remote files.
The Pages build at that code commit is verified in pages-code-deployment.json.
Subsequent delivery changes are documentation/evidence only; firmware and model
are unchanged, including the board image recorded in final-demo-integrity.json.
Verified raw dataset remote commit: fa89ca242ae11dccdc65ededd9f67d704043e643
on origin/codex/firmware (all24 originals/metadata tracked).
Hardware verification: trained monitoring inference-check image uploaded toCOM3,
written flash hashes verified. H01_onboard_inference contains22 genuine events
at2Hz; total feature+prediction2.377–2.458ms, model prediction9–10us, no deadline
violations. Sensor0x68 boot detection passed. Physical state was not labeled;
these results verify real-time execution, not live class correctness.
PC BLE tests H02/H03 failed with Windows adapter-not-ready error.
H05_http_ap passed over actual Wi-Fi AP: ready=True,100real samples andHTTP200
embedded page. GPIO48 RGB colors were explicitly visually confirmed by user
(H04 operator-confirmation); state colors are enabled, test cycling disabled.
H06 operator-confirmed unattached:22/22matching events; H07 calm:15/30matching,
an unstable result retained transparently. Both met real-time timing checks.
User reports teacher acceptance of sections1 and2; this does not change recorded
offline or live metrics. USB telemetry is testing-only. Final silent esp32-s3
image was built/flashed with verified hashes and GPIO48 state output. Its page
was rendered in actual Edge with four probabilities and real X/Y/Z data;
H09_browser_board records10status/9signal HTTP200responses, no JSexceptions
and the screenshot. Final upload/merge hashes recorded at delivery.

Limitations: same-device/operator data, only two inferred rounds, correlated
windows, placement dependence and weak unseen unattached orientations. Do not
silently replace this selected model; record a new ID/version/results and rationale.

Breathing-rate extension M07 v1 is separate from this selected classifier. Its implementation and evidence boundaries are documented in RESPIRATION.md. The M01 header hash, classifier parameters and measured validation results are unchanged. No classifier retraining was performed.
