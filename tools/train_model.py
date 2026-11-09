"""M01: grouped-recording decision tree, measured evaluation and C++ export.

Training accepts only explicit manifests of real labeled recordings. Synthetic
fixtures in software tests are never genuine classification evaluation results.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
from typing import Any

import numpy as np
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier


STATES = ("calm", "fast", "unattached", "shaking")
COLUMNS = ("t_ms", "ax_g", "ay_g", "az_g", "gx_dps", "gy_dps", "gz_dps")
WINDOW_SAMPLES = 100
SAMPLE_RATE_HZ = 25
FEATURE_NAMES = (
    "mean_ax_g", "mean_ay_g", "mean_az_g", "std_ax_g", "std_ay_g", "std_az_g",
    "mean_accel_magnitude_g", "std_accel_magnitude_g", "mean_gyro_magnitude_dps",
    "std_gyro_magnitude_dps", "accel_difference_rms_g", "accel_magnitude_range_g",
)


def extract_features(samples: np.ndarray) -> np.ndarray:
    """Convert exactly 100 timestamped six-axis samples to 12 float32 features."""
    values = np.asarray(samples, dtype=np.float64)
    if values.shape != (WINDOW_SAMPLES, len(COLUMNS)):
        raise ValueError("Feature extraction requires exactly 100 seven-column samples")
    if not np.isfinite(values).all():
        raise ValueError("Samples contain nonfinite values")
    times = values[:, 0]
    gaps = np.diff(times)
    if (times < 0).any() or (times != np.floor(times)).any():
        raise ValueError("Timestamps must be nonnegative integer milliseconds")
    if (gaps <= 0).any() or (gaps > 80).any():
        raise ValueError("Sample timestamps must increase with no gap above 80 ms")
    # Firmware samples are float32, accumulated in double. Cast before computing
    # so quantization is identical to the deployment representation.
    axes = values[:, 1:].astype(np.float32).astype(np.float64)
    acceleration = axes[:, :3]
    acc_mag = np.sqrt(np.sum(acceleration * acceleration, axis=1))
    gyro_mag = np.sqrt(np.sum(axes[:, 3:] * axes[:, 3:], axis=1))
    combined = np.column_stack((acceleration, acc_mag, gyro_mag))
    means = np.mean(combined, axis=0)
    variances = np.maximum(np.mean(combined * combined, axis=0) - means * means, 0)
    deviations = np.sqrt(variances)
    differences = np.diff(acceleration, axis=0)
    diff_rms = np.sqrt(np.mean(np.sum(differences * differences, axis=1)))
    features = np.concatenate((means[:3], deviations[:3],
        [means[3], deviations[3], means[4], deviations[4], diff_rms, np.ptp(acc_mag)]))
    result = features.astype(np.float32)
    if not np.isfinite(result).all():
        raise ValueError("Feature overflow")
    return result


def read_recording(path: Path) -> np.ndarray:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != list(COLUMNS):
            raise ValueError(f"{path}: expected header {','.join(COLUMNS)}")
        rows: list[list[float]] = []
        for row in reader:
            try:
                rows.append([float(row[name]) for name in COLUMNS])
            except (TypeError, ValueError, KeyError) as exc:
                raise ValueError(f"{path}: malformed recording row") from exc
    data = np.asarray(rows, dtype=np.float64)
    if data.ndim != 2 or data.shape[1] != len(COLUMNS) or len(data) < WINDOW_SAMPLES:
        raise ValueError(f"{path}: recording must contain at least 100 samples")
    if not np.isfinite(data).all():
        raise ValueError(f"{path}: recording contains nonfinite values")
    times = data[:, 0]
    if (times < 0).any() or (times != np.floor(times)).any() or (np.diff(times) <= 0).any():
        raise ValueError(f"{path}: timestamps must be increasing integer milliseconds")
    return data


def load_manifest(path: Path) -> list[dict[str, Any]]:
    """Manifest paths are relative to the manifest directory, grouped before windows."""
    manifest = json.loads(path.read_text(encoding="utf-8-sig"))
    if manifest.get("source") != "real_sensor":
        raise ValueError('Manifest must explicitly declare "source": "real_sensor"')
    if manifest.get("sample_rate_hz") != SAMPLE_RATE_HZ:
        raise ValueError("Manifest sample_rate_hz must be 25")
    entries = manifest.get("recordings")
    if not isinstance(entries, list) or not entries:
        raise ValueError("Manifest must contain recordings")
    seen_paths: set[Path] = set()
    seen_ids: set[str] = set()
    seen_hashes: set[str] = set()
    records = []
    for entry in entries:
        if not isinstance(entry, dict) or entry.get("state") not in STATES:
            raise ValueError("Each recording needs one of the four state labels")
        recording_id = entry.get("recording_id")
        if not isinstance(recording_id, str) or not recording_id.strip() or recording_id in seen_ids:
            raise ValueError("Each recording requires a unique nonempty recording_id")
        if not isinstance(entry.get("path"), str):
            raise ValueError("Each recording requires a CSV path")
        recording_path = (path.parent / entry["path"]).resolve()
        if recording_path in seen_paths:
            raise ValueError("The same recording file cannot be included twice")
        checksum = hashlib.sha256(recording_path.read_bytes()).hexdigest()
        if checksum in seen_hashes:
            raise ValueError("Duplicate recording contents: copied files cannot form a holdout")
        seen_paths.add(recording_path)
        seen_ids.add(recording_id)
        seen_hashes.add(checksum)
        records.append({"recording_id": recording_id, "path": recording_path,
            "state": entry["state"], "sha256": checksum})
    return records


def split_recordings(records: list[dict[str, Any]], seed: int = 42,
                     test_fraction: float = 0.25) -> tuple[list[dict], list[dict]]:
    """Stratify whole recording IDs so overlapping windows never cross the split."""
    if not 0 < test_fraction < 1:
        raise ValueError("test_fraction must be between zero and one")
    training, testing = [], []
    for state in STATES:
        group = sorted((record for record in records if record["state"] == state),
                       key=lambda record: record["recording_id"])
        if len(group) < 2:
            raise ValueError(f"Need at least two independent recordings for {state}")
        state_train, state_test = train_test_split(group, test_size=test_fraction,
                                                 random_state=seed, shuffle=True)
        training.extend(state_train)
        testing.extend(state_test)
    return training, testing


def window_records(records: list[dict[str, Any]], stride: int = 25
                  ) -> tuple[np.ndarray, np.ndarray, list[str]]:
    if stride < 1:
        raise ValueError("Stride must be positive")
    features, targets, recording_ids = [], [], []
    for record in records:
        data = read_recording(record["path"])
        record_count = 0
        for start in range(0, len(data) - WINDOW_SAMPLES + 1, stride):
            window = data[start:start + WINDOW_SAMPLES]
            # Gap-containing windows are excluded, never reconstructed.
            if (np.diff(window[:, 0]) > 80).any():
                continue
            features.append(extract_features(window))
            targets.append(STATES.index(record["state"]))
            recording_ids.append(record["recording_id"])
            record_count += 1
        if not record_count:
            raise ValueError(f"{record['path']}: no complete contiguous valid window")
    return np.asarray(features, dtype=np.float32), np.asarray(targets), recording_ids


def cpp_float(value: float) -> str:
    text = format(float(value), ".17g")
    return text if "." in text or "e" in text.lower() else text + ".0"


def export_cpp(classifier: DecisionTreeClassifier, method_id: str, version: str) -> str:
    if list(classifier.classes_) != list(range(4)):
        raise ValueError("Export requires all four classes in state-ID order")
    tree = classifier.tree_
    lines = ["#pragma once", '#include "prm_features.h"', "", "namespace prm {",
             f"// {method_id} v{version}: trained from real_sensor manifest; see metrics.json.",
             "inline bool modelAvailable() { return true; }",
             "inline bool predictProbabilities(const float* features, float* probabilities) {",
             "  if (!features || !probabilities) return false;",
             "  for (size_t i = 0; i < kFeatureCount; ++i)",
             "    if (!std::isfinite(features[i])) return false;"]

    def emit(node: int, indent: str) -> None:
        left, right = tree.children_left[node], tree.children_right[node]
        if left == right:
            weights = np.asarray(tree.value[node][0], dtype=float)
            probabilities = weights / weights.sum()
            for i, value in enumerate(probabilities):
                # Store as float at final assignment; use exact decision threshold as
                # double to match sklearn's float32 input / double threshold comparison.
                lines.append(f"{indent}probabilities[{i}] = static_cast<float>({cpp_float(value)});")
            return
        feature = int(tree.feature[node])
        lines.append(f"{indent}if (features[{feature}] <= {cpp_float(tree.threshold[node])}) {{")
        emit(int(left), indent + "  ")
        lines.append(f"{indent}}} else {{")
        emit(int(right), indent + "  ")
        lines.append(f"{indent}}}")

    emit(0, "  ")
    lines.extend(["  return true;", "}", "", "}  // namespace prm", ""])
    return "\n".join(lines)


def git_commit() -> str | None:
    result = subprocess.run(["git", "-c", "safe.directory=" + Path.cwd().as_posix(),
                             "rev-parse", "HEAD"], capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None


def train(manifest_path: Path, output_root: Path, method_id: str, version: str,
          *, seed: int = 42, test_fraction: float = 0.25, max_depth: int = 5,
          min_samples_leaf: int = 2, stride: int = 25) -> Path:
    if not re.fullmatch(r"M\d{2,}", method_id):
        raise ValueError("Method ID must be M01, M02, ...")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", version) or ".." in version:
        raise ValueError("Version must be a safe nonempty path component")
    if max_depth < 1 or min_samples_leaf < 1:
        raise ValueError("Tree parameters must be positive")
    output = output_root / f"{method_id}_v{version}"
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite experiment {output}")
    records = load_manifest(manifest_path)
    training, testing = split_recordings(records, seed, test_fraction)
    x_train, y_train, train_groups = window_records(training, stride)
    x_test, y_test, test_groups = window_records(testing, stride)
    classifier = DecisionTreeClassifier(max_depth=max_depth, min_samples_leaf=min_samples_leaf,
                                       class_weight="balanced", random_state=seed)
    classifier.fit(x_train, y_train)
    probabilities = classifier.predict_proba(x_test)
    predicted = np.argmax(probabilities, axis=1)
    metrics = {"method_id": method_id, "version": version,
        "source": "real_sensor", "evaluated_at_utc": datetime.now(timezone.utc).isoformat(),
        "code_commit": git_commit(), "states": list(STATES),
        "feature_names": list(FEATURE_NAMES), "sample_rate_hz": SAMPLE_RATE_HZ,
        "window_samples": WINDOW_SAMPLES, "stride_samples": stride,
        "parameters": {"seed": seed, "test_fraction": test_fraction,
            "max_depth": max_depth, "min_samples_leaf": min_samples_leaf,
            "class_weight": "balanced"},
        "train_recordings": [r["recording_id"] for r in training],
        "test_recordings": [r["recording_id"] for r in testing],
        "recordings": [{"recording_id": r["recording_id"], "path": str(r["path"]),
                        "state": r["state"], "sha256": r["sha256"]} for r in records],
        "train_windows": len(y_train), "test_windows": len(y_test),
        "accuracy": float(accuracy_score(y_test, predicted)),
        "balanced_accuracy": float(balanced_accuracy_score(y_test, predicted)),
        "confusion_matrix": confusion_matrix(y_test, predicted, labels=range(4)).tolist(),
        "hardware_verified": False,
        "limitations": ["Held-out windows within each recording are correlated; not independent trials.",
            "Same-person/same-session recordings do not establish cross-person generalization.",
            "Probabilities are tree leaf frequencies, not calibrated clinical confidence.",
            "No on-board accuracy, timing or memory claim is made by this offline evaluation."]}
    # Reserve a unique directory only after validation/training, never overwrite.
    output.mkdir(parents=True, exist_ok=False)
    (output / "metrics.json").write_text(json.dumps(metrics, indent=2, allow_nan=False) + "\n",
                                        encoding="utf-8")
    (output / "prm_model.h").write_text(export_cpp(classifier, method_id, version), encoding="utf-8")
    shutil.copyfile(manifest_path, output / "manifest.json")
    with (output / "heldout_predictions.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["recording_id", "true_state_id", "predicted_state_id", *STATES])
        writer.writerows((group, int(target), int(pred), *map(float, probs))
            for group, target, pred, probs in zip(test_groups, y_test, predicted, probabilities))
    np.savez_compressed(output / "feature_windows.npz", x_train=x_train, y_train=y_train,
                        x_test=x_test, y_test=y_test, train_groups=np.asarray(train_groups),
                        test_groups=np.asarray(test_groups))
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--method-id", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--output-root", type=Path, default=Path("outputs/results"))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--test-fraction", type=float, default=0.25)
    parser.add_argument("--max-depth", type=int, default=5)
    parser.add_argument("--min-samples-leaf", type=int, default=2)
    parser.add_argument("--stride", type=int, default=25)
    args = parser.parse_args()
    try:
        result = train(args.manifest, args.output_root, args.method_id, args.version,
            seed=args.seed, test_fraction=args.test_fraction, max_depth=args.max_depth,
            min_samples_leaf=args.min_samples_leaf, stride=args.stride)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        parser.exit(2, f"Training failed: {exc}\n")
    print(f"Saved genuine offline evaluation and model candidate to {result}")
    print("Review metrics, register method in docs/METHODS.md, then explicitly select/install.")
    print("No firmware model was replaced automatically.")


if __name__ == "__main__":
    main()
