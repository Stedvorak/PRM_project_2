# PRM Project 2 - Image Processing

## Mission
Complete the image processing assignment within four hours.
Prioritize correctness, reproducibility, and complete submission.

## Multi-agent coordination
The main agent owns architecture, integration, and final delivery.

Delegate independent work to subagents:
- Data Explorer: inspect images, formats, dimensions, metadata, quality.
- Methods Researcher: identify suitable image processing methods.
- Validation Agent: design tests, metrics, and acceptance criteria.
- Implementation Agent: implement independent components when useful.

Use parallel subagents only for independent tasks.
Prefer read-only exploration before implementation.
Never allow concurrent edits to the same files.
Keep subagent reports concise.

## Technical guidelines
- Use Python unless the assignment requires otherwise.
- Prefer NumPy, OpenCV, SciPy, scikit-image and Matplotlib.
- Use deterministic settings when applicable.
- Preserve original input images.
- Save important intermediate and final images.
- Avoid unnecessary dependencies.
- Do not invent results or metrics.

## Submission
Maintain docs/CHECKLIST.md from the beginning.
Verify all required code, figures, results and reports.
Reserve at least 30 minutes for final verification.
Verify Git push and submission status explicitly.

## Algorithm naming and version control

CRITICAL: Never lose track of the latest algorithm version.

1. Give every evaluated method a unique ID:
   M01, M02, M03, etc.

2. Use descriptive names, e.g.:
   M01_gaussian_baseline
   M02_clahe
   M03_combined_pipeline

3. Keep a method registry in docs/METHODS.md.
   Record:
   - Method ID and version
   - Algorithm description
   - Source file
   - Parameters
   - Evaluation metrics
   - Result files
   - Status: experimental, candidate, selected, rejected

4. Store experiment outputs in separate directories.
   Never overwrite results from a different experiment.

5. Maintain docs/FINAL_METHOD.md containing:
   - Selected method ID and version
   - Exact implementation path
   - Parameters
   - Evaluation results
   - Git commit hash
   - Verified remote branch and commit

6. Do not silently replace the selected algorithm.
   Any replacement requires updated results,
   registry entries and explicit justification.

7. Before every final push:
   - Check git status.
   - Verify the selected implementation is tracked.
   - Run relevant tests.
   - Commit all required deliverables.
   - Push to the intended remote branch.
   - Fetch the remote state.
   - Verify the remote branch points to the
     expected commit.
   - Confirm the final algorithm and report
     belong to that same commit.

8. Never report "pushed successfully" based only
   on a successful local commit.

9. If the remote differs from local HEAD,
   explicitly report the discrepancy.
   Never force-push without user approval.

10. Reserve the final 30 minutes for submission.
    Stop experimenting and prioritize integration,
    verification, documentation and delivery.

