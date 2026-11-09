# Final Selected Method

Selected method: NONE — four-class recordings and classifier evaluation remain incomplete.

Experimental candidate: M01 v1 (not evaluated, not selected).
Default implementation: firmware/include/prm_model.h (unavailable-model guard).
Feature implementation: firmware/include/prm_features.h.
Training implementation and parameters: docs/ML.md; docs/METHODS.md.
Classifier evaluation results: unavailable; no genuine accuracy, breathing rate,
inference latency or runtime on-board memory measurements have been recorded.
Real acquisition evidence: first unattached/table session,1499 valid samples at
49.94332199773288Hz; data/raw/20261109T135811_347025Z_unattached_07ff5cfb.csv
and matching.json. Validation: outputs/verification/V06_unattached_session/validation.json.
This is sensor acquisition evidence, not classifier evaluation or model selection.
Software tests use temporary synthetic fixtures.
Firmware/feature integration commit: cf6004e4513bf6466b194e81a4dc2a78dca6c19e.
Verified remote firmware commit at integration checkpoint:
cf6004e4513bf6466b194e81a4dc2a78dca6c19e (origin/codex/firmware, fetched and compared).
This identifies the unavailable-model implementation, not a selected classifier.
Later acquisition/monitor/documentation commits do not replace its model header.
Shared protocol v0.2 commit: 91667e00e0bfef30a313fe35c800e566fdda7835 (verified on main and codex/firmware at protocol publication).
Verification status: NOT VERIFIED ON HARDWARE; NO FINAL ALGORITHM SELECTED.

Before delivery: select exactly one genuinely evaluated candidate, install its
exact generated header explicitly, run firmware/contract/hardware checks, record
metrics and report paths, verify implementation/report belong to the delivered
commit, push/fetch and compare the remote hash. Do not silently replace a model.
