# Method Registry

| ID | Version | Method | Source | Parameters | Metrics | Result files | Status |
|---|---|---|---|---|---|---|---|
| M01 | 1.0 | DecisionTree (12 features) | tools/train_model.py | depth=3, win=100, step=25 | accuracy=91.6% | firmware/include/prm_model.h | rejected |
| M02 | 1.0 | Shallow DecisionTree + BPM | scripts/train.py | max_depth=4, min_samples_leaf=3, win=100 (2.0s), step=25 (0.5s), 10 features | train_acc=99.8%, test_acc=100.0% | firmware/include/model.h, firmware/include/bpm.h, outputs/evaluation.json | selected |

Statuses: experimental, candidate, selected, rejected.

Only one method may be selected.
Every evaluated method must have reproducible parameters
and identifiable result files.
