# Real data and classifier results

M01 v1 is the selected feasible firmware candidate: a small decision tree using
the twelve deployed inertial features. This report summarizes saved genuine
recordings and session-grouped offline evaluation; hardware timing and live
demonstration evidence must be recorded separately.

## Data and grouping

The twelve approved raw recordings contain 17,993 real six-axis samples: three
CSV files per class (calm 4,498; fast 4,498; unattached 4,497; shaking 4,500 samples).
Observed rates are 49.941657–49.943360Hz, timestamp intervals 20–21ms. There are no
nonfinite/missing CSV values, timestamp overlaps, duplicate file hashes or
estimated missing samples within recordings. Four malformed incoming serial
lines were rejected rather than converted into measurements.

The later two files of each class have only 240–300ms between them and are kept
together. They are not counted as independent experimental sessions. Two
inferred collection rounds form the validation groups: R1_initial contains the
first take of every class; R2_followup contains all later takes. All data appears
to share a board boot and operator; independent people or experimental sessions
are not established.

Original 50 Hz files remain unchanged. Sensor DLPF5 provides 10 Hz bandwidth; the
saved preprocessing retains every second real sample, with original timestamps
and values, to supply the deployed 25 Hz feature extraction. Windows have 100
samples (about 4 s) and stride 25 (about 1 s). Whole groups are split before windowing.
No overlapping windows or adjacent recording takes cross training/test groups.

## Candidate comparison

All six candidates use the same two leave-one-whole-collection-group-out folds:
train R2/test R1 (108 test windows), and train R1/test R2 (216 test windows). Scores
below are loaded from each method's actual metrics.json; they are not training
scores or synthetic-fixture results.

| ID | Candidate | Mean fold balanced accuracy | Pooled held-out balanced accuracy | Pooled macro F1 | Export header bytes |
|---|---|---:|---:|---:|---:|
| M01 v1 | Decision tree, depth limit 5 |86.11%|83.64%|83.51%|1,416|
| M02 v1 | Decision tree, depth limit 3 |86.11%|83.64%|83.51%|1,416|
| M03 v1 | Random forest, 8 trees, depth 4 |74.31%|74.07%|74.51%|11,450|
| M04 v1 | Standardized logistic regression |75.00%|75.00%|74.29%|3,764|
| M05 v1 | Orientation-invariant feature tree |60.88%|64.51%|65.39%|3,288|
| M06 v1 | Orientation-invariant feature forest |71.53%|73.46%|74.58%|18,046|

Mean-fold scores give both folds equal weight. Pooled scores combine their
held-out predictions and therefore weight the larger test fold more. These are
different summaries;86.11% must not be reported as pooled accuracy. Pooled
accuracy and balanced accuracy both equal 83.64% here because the pooled classes
have equal support (81 windows each).

M01 and M02 tie and export the same final model size: 7 nodes, achieved depth 2.
M01 is retained as the selected method without inventing a performance
advantage over M02. Larger candidates did not improve these grouped scores.
Header size/node count are software properties, not measured ESP32 runtime
memory or inference latency. The deployment model is trained on all approved
recordings only after grouped evaluation.

## Selected M01 v1 held-out results

Pooled confusion matrix; rows are true states, columns are predictions:

| True / predicted | calm | fast | unattached | shaking |
|---|---:|---:|---:|---:|
| calm |73|7|1|0|
| fast |0|81|0|0|
| unattached |3|35|43|0|
| shaking |0|7|0|74|

Class recall is calm 90.12%, fast 100.00%, unattached 53.09%, shaking 91.36%.
The major failure is unattached classified as fast (35 windows). Fold balanced
accuracies are 93.52% and78.70%; unattached recall in the train R1/test R2 direction
falls to 29.63%. This suggests collection/placement dependence (not an isolated causal test) and limits the
strength of any live performance claim. Mean acceleration features retain board
orientation information; consistent placement matters, and the limited dataset
does not establish robustness to arbitrary remounting.

Shaking includes genuine sensor saturation: near-rail acceleration occurs in
191, 1 and 9 rows of its three recordings (absolute value at least 1.999 g).
Gyroscope values can reach 250.1374 deg/s from signed16-bit raw / 131 scaling;
these are real clipped readings rather than malformed values. Originals are
preserved; saturation limits information in vigorous movement.

## Figures and reproduction

- [M01 grouped confusion matrix](../outputs/figures/delivery_v2/M01_v1_grouped_confusion.png)
- [Six-candidate balanced accuracy comparison](../outputs/figures/delivery_v2/candidate_grouped_balanced_accuracy.png)
- [Representative real six-axis signals](../outputs/figures/delivery_v2/real_six_axis_recordings.png)

Matching SVG files support export. The confusion plot is reconstructed from
actual heldout_predictions.csv and checked against metrics.json. Signal plots
use actual raw timestamps and all six recorded axes, with no generated traces.

```powershell
python -B tools/plot_results.py
```

This requires NumPy and Matplotlib; figures were generated using the existing
global Python NumPy 1.26.4 and Matplotlib 3.9.3. Existing figure directories are never
overwritten; use `--output outputs/figures/delivery_v3` for a later regeneration.

Sources: outputs/results/M01_v1 through M06_v1/metrics.json; their held-out
predictions and manifests; original data/raw CSV/metadata pairs. Exact method
identity, implementation and commit verification belong in METHODS.md and
FINAL_METHOD.md.

## Practical limits

There are only two inferred collection groups, with correlated overlapping
windows. Candidate selection uses these same results, so they are not an
untouched final test of the selected method. Person, placement and collection
conditions are insufficiently varied for a generalization claim. Offline
evaluation does not verify LED GPIO, on-board accuracy, inference timing,
BLE/Wi-Fi coexistence, browser pairing, alarm demonstrations or teacher delivery.
No such hardware result is inferred from a successful compile or these figures.
