# Session-grouped model comparison

`tools/compare_models.py` consumes a validated25Hz real-sensor manifest. Original
50Hz files must be preserved; conversion and session/bout assignments are explicit
preparation steps performed before this tool. Every recording has one group_id.
All overlapping windows from a recording/group stay on the same side of a fold.

When complete collection rounds each contain all four classes, validation leaves
one whole round out. Class-specific bouts are assigned deterministically to
stratified whole-bout folds. Mixed groups use StratifiedGroupKFold. Every fold
must include all four classes in train and test, and every window is held out
exactly once. Inadequate groups cause an error, never a random window split.
Adjacent takes from one acquisition bout should share a group. Group IDs do not
establish independent people or cross-person generalization.

All candidates use existing12 features,100 samples/window,25-sample stride:

| ID | Version | Algorithm | Main parameters |
|---|---|---|---|
| M01 |1| Decision tree | depth5, leaf2, balanced, seed42 |
| M02 |1| Decision tree | depth3, leaf2, balanced, seed42 |
| M03 |1| Random forest |8 trees, depth4, leaf2, balanced, seed42 |
| M04 |1| Standardized logistic regression | C1, max_iter2000, balanced, seed42 |

Scaling for logistic regression is fitted separately inside each training fold.
Metrics use held-out predictions only: accuracy, balanced accuracy, macroF1,
confusion matrix and per-class recall, both per fold and pooled. Mean-fold
balanced accuracy ranks candidates, then pooled macroF1 and exported header
size. Inspect fold variance and class recalls before choosing; a simpler model
may be preferable within a small score difference. Selection on these same
folds means the result is not an untouched final test of the chosen model.

After validation each candidate is fitted on all approved recordings for export.
Its generated header is a candidate, never installed automatically. Decision
tree/forest exports use unrolled exact thresholds and four leaf probabilities;
logistic export folds StandardScaler into double coefficients and uses stable
softmax. State order remains calm, fast, unattached, shaking. M01 remains the
original registered algorithm; this tool does not change its feature definition.

```powershell
.\.venv\Scripts\python.exe tools/compare_models.py data/validated/manifest.json --version 1
```

Each `outputs/results/Mxx_v1/` is immutable and includes metrics.json,
heldout_predictions.csv, feature_windows.npz, manifest.json and prm_model.h.
The NPZ also has deployment_probabilities from the final all-data model, useful
for checking actual exported inference parity; those are not held-out metrics.
`outputs/comparison/C01_v1/summary.json` records the ranking/recommendation.
Existing directories are refused. Register actual results in METHODS.md and
explicitly select/install only one model, with measured on-board verification.
Header bytes/nodes are software size indicators, never runtime memory/latency.

Tests use temporary synthetic fixtures only. No real candidate evaluation is
performed by unit tests and no hardware result is inferred from compilation.

## Actual recorded-data comparison C01 v1

Evaluation consumed12 approved recordings and324 derived25Hz windows. Grouping
is deliberately conservative: R1_initial contains the first take of each class;
R2_followup contains the later adjacent takes. Both complete rounds contain all
four classes. Each direction holds out a complete round before windowing/model
fit. These are two temporal collection rounds from the same device/person, not
proof of independent physical sessions or cross-person generalization.

| Method | Mean fold balanced accuracy | Pooled held-out accuracy | Pooled macroF1 | Export bytes |
|---|---:|---:|---:|---:|
| M01 v1 |86.1111%|83.6420%|0.835137|1416|
| M02 v1 |86.1111%|83.6420%|0.835137|1416|
| M03 v1 |74.3056%|74.0741%|0.745110|11450|
| M04 v1 |75.0000%|75.0000%|0.742857|3764|

M01 is the recommendation, pending root selection/hardware verification. M02's
shallower limit produces the same7-node, depth2 final tree and identical
validation predictions, so it offers no measured benefit. M01's fold balanced
accuracies are93.5185% and78.7037%, showing collection-round variation. Pooled
recalls in protocol order are90.1235%,100%,53.0864%,91.3580%. In particular,
unattached recall is only29.6296% when R1 trains and R2 tests; this weakness must
not be hidden by the aggregate score. Calibration/placement variation and the
small two-round sample limit claims. Breathing-rate estimation is not implemented.

Actual artifacts are outputs/results/M01_v1 through M04_v1 and
outputs/comparison/C01_v1/summary.json. Metrics, inputs' hashes, group membership,
all held-out predictions and final all-data export references are saved. These
offline results do not establish on-board latency, live accuracy or hardware
demonstration success; those require separate genuine measurements.

## Actual orientation-invariant comparison C02 v1

The poor round-transfer performance of unattached motivated an explicit second
comparison, not a replacement of M01. `tools/compare_invariant.py` masks
axis-specific means/std columns0..5 during training, leaving acceleration
magnitude mean/std, gyro magnitude mean/std, Euclidean acceleration-difference
RMS and acceleration-magnitude range (columns6..11). The12-feature deployment
ABI is unchanged. No final tree uses columns0..5, and predictions on original
versus masked feature vectors are checked for exact equality.

| Method | Algorithm | Mean fold balanced accuracy | Pooled accuracy | MacroF1 | Header bytes |
|---|---|---:|---:|---:|---:|
| M05 v1 | masked-feature tree depth5/leaf2 |60.8796%|64.5062%|0.653884|3288|
| M06 v1 | masked-feature forest8/depth4/leaf2 |71.5278%|73.4568%|0.745810|18046|

Both use balanced classes, seed42, identical324 windows, and the exact same two
whole-round LOGO folds as C01. Both perform worse than M01/M02 on the declared
ranking metric, so M01 remains the recommendation subject to root selection and
hardware verification. The invariant experiments do not remove the original
generalization limitation or prove a trustworthy breathing detector.

Artifacts are in outputs/results/M05_v1 and M06_v1, with comparison summary in
outputs/comparison/C02_invariant_v1. Both generated exports passed the installed
ESP32 C++ compiler's syntax check; export_compile.json records this software-only
result. These adaptive comparisons reuse the small existing CV dataset and are
not an untouched final validation test.
