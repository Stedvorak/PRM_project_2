"""Plot saved genuine measurements and grouped-CV results; never train a model."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

STATES = ("calm", "fast", "unattached", "shaking")
COLORS = ("#247ba0", "#f29e38", "#7a5195")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save(fig, output: Path, stem: str):
    for suffix in ("png", "svg"):
        target = output / f"{stem}.{suffix}"
        if target.exists():
            raise FileExistsError(f"Refusing to overwrite figure {target}")
        fig.savefig(target, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def confusion(root: Path, output: Path):
    metrics = read_json(root / "outputs/results/M01_v1/metrics.json")
    with (root / "outputs/results/M01_v1/heldout_predictions.csv").open(newline="") as stream:
        predictions = list(csv.DictReader(stream))
    matrix = np.zeros((4, 4), dtype=int)
    for row in predictions:
        matrix[int(row["true_state_id"]), int(row["predicted_state_id"])] += 1
    assert matrix.tolist() == metrics["pooled_grouped_heldout"]["confusion_matrix"]
    assert int(matrix.sum()) == metrics["windows"]
    proportions = matrix / matrix.sum(axis=1, keepdims=True)
    fig, ax = plt.subplots(figsize=(6.8, 5.5))
    image = ax.imshow(proportions, vmin=0, vmax=1, cmap="Blues")
    for i in range(4):
        for j in range(4):
            ax.text(j, i, f"{matrix[i,j]}\n{100*proportions[i,j]:.1f}%", ha="center", va="center",
                    color="white" if proportions[i, j] > .55 else "#152b3a", fontsize=11)
    ax.set(xticks=range(4), yticks=range(4), xticklabels=STATES, yticklabels=STATES,
           xlabel="Predicted state", ylabel="True state",
           title=f"M01 v1: pooled grouped-CV confusion matrix\n{matrix.sum()} out-of-group windows; counts and row percentages")
    fig.colorbar(image, ax=ax, label="Fraction of each true class")
    fig.text(.5, -.015, "Two collection rounds; overlapping windows stay within their recording group.\nNot an untouched final test or a hardware accuracy measurement.",
             ha="center", fontsize=9)
    fig.tight_layout()
    save(fig, output, "M01_v1_grouped_confusion")


def comparison(root: Path, output: Path):
    candidates = [read_json(root / f"outputs/results/M{i:02d}_v1/metrics.json") for i in range(1, 7)]
    labels = ["M01\nTree\n(depth limit 5)", "M02\nTree\n(depth limit 3)",
              "M03\nForest\n(8 trees, depth 4)", "M04\nStandardized\nlogistic regression",
              "M05\nInvariant tree\n(depth limit 5)", "M06\nInvariant forest\n(8 trees, depth 4)"]
    mean = np.array([m["mean_fold_balanced_accuracy"] for m in candidates]) * 100
    pooled = np.array([m["pooled_grouped_heldout"]["balanced_accuracy"] for m in candidates]) * 100
    x = np.arange(len(candidates))
    fig, ax = plt.subplots(figsize=(12, 5.6))
    a = ax.bar(x - .19, mean, .36, label="Mean fold balanced accuracy (equal fold weights)", color="#247ba0")
    b = ax.bar(x + .19, pooled, .36, label="Pooled held-out balanced accuracy", color="#e6a23c")
    ax.bar_label(a, fmt="%.2f%%", fontsize=8, padding=3)
    ax.bar_label(b, fmt="%.2f%%", fontsize=8, padding=3)
    ax.set(xticks=x, xticklabels=labels, ylim=(0, 105), ylabel="Balanced accuracy (%)",
           title="Six candidates on the same two whole-collection-group folds")
    ax.tick_params(axis="x", labelsize=8)
    ax.legend(loc="upper right", fontsize=9)
    ax.grid(axis="y", alpha=.2)
    ax.set_axisbelow(True)
    fig.text(.5, -.035, "Fold test sizes differ (108 versus 216 windows), so mean-fold and pooled scores differ.\nCandidate selection uses these folds; no independent final-test claim is made.",
             ha="center", fontsize=9)
    fig.tight_layout()
    save(fig, output, "candidate_grouped_balanced_accuracy")


def signals(root: Path, output: Path):
    manifest = read_json(root / "outputs/results/M01_v1/manifest.json")
    fig, axes = plt.subplots(4, 2, figsize=(12, 9), sharex="col")
    for row, state in enumerate(STATES):
        record = next(r for r in manifest["recordings"] if r["state"] == state)
        source = root / record["raw_path"]
        with source.open(newline="", encoding="utf-8-sig") as stream:
            values = list(csv.DictReader(stream))
        timestamps = np.array([int(r["t_ms"]) for r in values], dtype=np.int64)
        elapsed = (timestamps - timestamps[0]) / 1000.0
        selected = elapsed <= 5
        for col, keys, unit in ((0, ("ax_g", "ay_g", "az_g"), "Acceleration (g)"),
                                (1, ("gx_dps", "gy_dps", "gz_dps"), "Angular velocity (deg/s)")):
            ax = axes[row, col]
            for key, color in zip(keys, COLORS):
                measured = np.array([float(r[key]) for r in values])
                ax.plot(elapsed[selected], measured[selected], color=color, linewidth=.8, label=key)
            ax.set_ylabel(f"{state}\n{unit}")
            ax.grid(alpha=.2)
            if row == 0:
                ax.legend(loc="upper right", ncol=3, fontsize=8)
            ax.set_xlim(0, 5)
        axes[row, 0].set_title(record["recording_id"], fontsize=8, loc="left")
        axes[row, 1].set_title(f"First sample at {int(timestamps[0])} ms since boot", fontsize=8, loc="left")
    for ax in axes[-1]:
        ax.set_xlabel("Elapsed time from first actual sample (s)")
    fig.suptitle("Representative real six-axis recordings: first 5 seconds of first take per class", fontsize=12)
    fig.text(.5, .005, "Original 50 Hz serial measurements; actual timestamps; sensor DLPF 10 Hz. No synthetic signal, calibration or interpolation.\nRepresentative excerpts illustrate measurements, not independent classifier evaluation; shaking includes physical sensor clipping.",
             ha="center", fontsize=9)
    fig.tight_layout(rect=(0, .055, 1, .96))
    save(fig, output, "real_six_axis_recordings")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    output = args.output or args.root / "outputs/figures/delivery_v2"
    output.mkdir(parents=True, exist_ok=True)
    expected = [output / f"{stem}.{suffix}" for stem in
                ("M01_v1_grouped_confusion", "candidate_grouped_balanced_accuracy", "real_six_axis_recordings")
                for suffix in ("png", "svg")]
    if any(p.exists() for p in expected):
        raise FileExistsError("Use a new output directory to preserve existing figures")
    confusion(args.root, output)
    comparison(args.root, output)
    signals(args.root, output)
    print(f"Saved six genuine-result figure artifacts to {output}")


if __name__ == "__main__":
    main()
