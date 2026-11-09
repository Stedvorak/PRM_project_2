# Method Registry

| ID | Version | Method | Source | Parameters | Metrics | Result files | Status |
|---|---|---|---|---|---|---|---|
| M01 | 1 | recording-group-held-out decision tree on 12 inertial features | tools/train_model.py; firmware/include/prm_features.h; generated candidate prm_model.h | 25 Hz; 100 samples/window; stride25; depth5; minimum leaf2; balanced weights; seed42; per-class whole-recording holdout25%; DLPF5/10Hz | NOT EVALUATED: no genuine recordings available | Planned outputs/results/M01_v1/metrics.json, heldout_predictions.csv, feature_windows.npz, manifest.json, prm_model.h; none exist yet | experimental |

Only one method may be selected. No final method is selected yet.
The deployed firmware/include/prm_model.h deliberately reports model unavailable;
this is not a classifier and must never produce invented four-class probabilities.

The method description, parameters and class order are documented in ML.md.
Register each newly evaluated method/version separately. Never overwrite another
experiment directory. Test fixtures establish software behavior only; they are
not real model evaluation. Before selection record real metrics, files, exact
implementation and verified remote commit in FINAL_METHOD.md.
