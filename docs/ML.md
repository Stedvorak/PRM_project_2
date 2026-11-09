# M01: real-recording decision-tree pipeline

Status: implementation ready for data collection; no genuine recordings, trained
model, classifier accuracy or hardware measurements have been produced yet.
`firmware/include/prm_model.h` intentionally returns unavailable until a model is
explicitly trained, reviewed and installed. A live signal can exist before a
prediction is available; do not invent probabilities.

## Acquisition

Build the firmware's explicit data-collection environment and connect the actual
MPU-6050. The collector expects serial at 115200 baud, lines with seven values:
`t_ms,ax_g,ay_g,az_g,gx_dps,gy_dps,gz_dps`. Acceleration is in g and gyro in degrees
per second. This is a training-only USB path, not the BLE/HTTP contract. Restore
the demo build afterward: during the demonstration USB is power only and the
chip performs sensing, feature extraction and inference independently.

Install acquisition dependency if needed: `python -m pip install pyserial==3.5`.
Example for an actual user-selected COM port, with no fabricated input:

```powershell
python -B tools/collect_serial.py --port COM5 --state calm --recording-id calm_session1_take1 --seconds 30 --output data/calm_session1_take1.csv
```

Capture at least two independent recordings for each of `calm`, `fast`,
`unattached`, `shaking`; several sessions per class are preferable. Do not split
one continuous take into separate files and claim independent sessions. Include
held-in-hand movement and lying still in unattached. Record different realistic
breathing rates and keep labels constant within each recording. The collector
preserves only received numeric samples, reports measured acquisition rate and
rejects timestamp resets. It does not interpolate gaps. Inspect partial recordings
after errors before use. The label is an observation supplied by the operator;
software cannot prove that a manifest declaration is truthful.

## Manifest

Create a JSON manifest relative to its own directory (example structure only;
the referenced real files must exist). Every recording has one unique ID and
one class. The example is intentionally not enough data to train:

```json
{
  "source": "real_sensor",
  "sample_rate_hz": 25,
  "recordings": [
    {"recording_id": "calm_session1_take1", "state": "calm", "path": "calm_session1_take1.csv"}
  ]
}
```

The CSV header must be exactly
`t_ms,ax_g,ay_g,az_g,gx_dps,gy_dps,gz_dps`. Preserve original files. `data/` is
ignored by Git; explicitly arrange dataset delivery/access according to the
assignment and never claim a clone reproduces training without the recordings.

## Features, split and evaluation

Sampling target: 25 Hz. Window: 100 consecutive samples (approximately 4 seconds).
Window stride: 25 samples (approximately 1 second). Windows crossing gaps above
80 ms are excluded, not repaired. Firmware rejects such windows too.

`prm_features.h` and `train_model.py` use the same float32 sensor representation,
double accumulation, population standard deviation and twelve feature positions:

1. Mean ax, ay, az in g (three features).
2. Population standard deviation of ax, ay, az in g (three features).
3. Mean and population standard deviation of acceleration magnitude in g.
4. Mean and population standard deviation of gyro magnitude in degrees/second.
5. Root mean square Euclidean difference between consecutive acceleration vectors
   in g (not a rate-normalized derivative).
6. Acceleration magnitude range in g.

Entire recording IDs are stratified per class before windowing; fixed seed 42,
holdout fraction 0.25 within each class, minimum two recordings per class.
Duplicate IDs, file paths and identical CSV content are rejected. The decision
tree uses depth 5, minimum leaf 2 and balanced class weights. Metrics are accuracy,
balanced accuracy and a 4-by-4 confusion matrix in state-ID order. Each prediction
and input recording SHA-256 is saved. Overlapping held-out windows remain
correlated; this holdout does not establish generalization across persons unless
independent people/sessions were actually recorded. Tree leaf probabilities are
not calibrated clinical confidence. This is an educational prototype.

## Train, register and install explicitly

```powershell
python -B tools/train_model.py data/manifest.json --method-id M01 --version 1
```

Outputs go to `outputs/results/M01_v1/`: `metrics.json`,
`heldout_predictions.csv`, `feature_windows.npz`, `manifest.json`, and
`prm_model.h`. Existing experiment directories are never overwritten. Use a new
method ID/version for a newly evaluated algorithm/configuration. Do not report
software-test fixtures as measurements or real training results.

Before selecting a model, register its exact algorithm parameters, evaluation,
source and result files in `docs/METHODS.md`; mark candidates honestly. Exactly
one final selected method is recorded in `docs/FINAL_METHOD.md`, with implementation
and verified Git commit. Then explicitly copy the reviewed candidate header:

```powershell
Copy-Item -LiteralPath outputs/results/M01_v1/prm_model.h -Destination firmware/include/prm_model.h
```

Rebuild and test on the real board. The generated header uses only standard C++
math and feature definitions; class order remains calm, fast, unattached, shaking.
Breathing rate is not estimated by M01 and must remain null. No automatic model
selection or silent replacement is performed by training. Record on-board tests
separately; offline metrics do not establish BLE stability, LED correctness,
sampling cadence, inference time, memory use or live classification performance.

## Software verification

`python -B -m pytest -p no:cacheprovider tests/test_ml_pipeline.py` exercises
feature math, grouped splitting, source checks, malformed recording rejection,
four-class export and refusal to overwrite results. All inputs are explicitly
synthetic test fixtures under pytest temporary directories. Passing these tests
is software correctness evidence only, not model or hardware evaluation.
