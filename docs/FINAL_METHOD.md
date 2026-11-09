# Final Selected Method

Selected method: NONE — genuine recordings and evaluation are not available.

Experimental candidate: M01 v1 (not evaluated, not selected).
Default implementation: firmware/include/prm_model.h (unavailable-model guard).
Feature implementation: firmware/include/prm_features.h.
Training implementation and parameters: docs/ML.md; docs/METHODS.md.
Evaluation results: unavailable; no genuine accuracy, breathing rate, inference
latency, acquisition rate or on-board memory measurements have been recorded.
Result files: none from real data. Software tests use temporary synthetic fixtures.
Implementation Git commit: pending integration commit; do not infer from this template.
Verified remote firmware commit: pending integration verification.
Shared protocol v0.2 commit: 91667e00e0bfef30a313fe35c800e566fdda7835 (verified on main and codex/firmware at protocol publication).
Verification status: NOT VERIFIED ON HARDWARE; NO FINAL ALGORITHM SELECTED.

Before delivery: select exactly one genuinely evaluated candidate, install its
exact generated header explicitly, run firmware/contract/hardware checks, record
metrics and report paths, verify implementation/report belong to the delivered
commit, push/fetch and compare the remote hash. Do not silently replace a model.
