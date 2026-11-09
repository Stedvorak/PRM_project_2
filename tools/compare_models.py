"""Real-data grouped candidate comparison; no overlapping-window random split."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix, f1_score
from sklearn.model_selection import LeaveOneGroupOut, StratifiedGroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

try:
    from tools.train_model import (STATES, FEATURE_NAMES, SAMPLE_RATE_HZ, WINDOW_SAMPLES,
                                  cpp_float, export_cpp, git_commit, load_manifest, window_records)
except ModuleNotFoundError:  # Direct `python tools/compare_models.py ...`.
    from train_model import (STATES, FEATURE_NAMES, SAMPLE_RATE_HZ, WINDOW_SAMPLES,
                             cpp_float, export_cpp, git_commit, load_manifest, window_records)


CANDIDATES = {
    "M01": {"name": "decision_tree_depth5", "kind": "tree", "max_depth": 5,
            "min_samples_leaf": 2, "class_weight": "balanced", "random_state": 42},
    "M02": {"name": "decision_tree_depth3", "kind": "tree", "max_depth": 3,
            "min_samples_leaf": 2, "class_weight": "balanced", "random_state": 42},
    "M03": {"name": "random_forest_8_depth4", "kind": "forest", "n_estimators": 8,
            "max_depth": 4, "min_samples_leaf": 2, "class_weight": "balanced", "random_state": 42},
    "M04": {"name": "standardized_logistic_regression", "kind": "logistic", "C": 1.0,
            "max_iter": 2000, "class_weight": "balanced", "random_state": 42},
}


def estimator_for(method_id: str):
    params = dict(CANDIDATES[method_id])
    params.pop("name")
    kind = params.pop("kind")
    if kind == "tree":
        return DecisionTreeClassifier(**params)
    if kind == "forest":
        return RandomForestClassifier(**params, n_jobs=1)
    return make_pipeline(StandardScaler(), LogisticRegression(**params))


def grouped_dataset(manifest_path: Path, stride: int = 25):
    """Validate source declarations and bind each complete recording to one group."""
    raw = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    records = load_manifest(manifest_path)
    by_id = {entry["recording_id"]: entry for entry in raw["recordings"]}
    groups_by_record = {}
    for record in records:
        group = by_id[record["recording_id"]].get("group_id")
        if not isinstance(group, str) or not group.strip():
            raise ValueError("Every recording requires an explicit nonempty group_id")
        groups_by_record[record["recording_id"]] = group
        record["group_id"] = group
    x, y, recording_ids = window_records(records, stride)
    groups = np.asarray([groups_by_record[r] for r in recording_ids])
    return records, x, y, np.asarray(recording_ids), groups


def group_folds(y: np.ndarray, groups: np.ndarray):
    """Create all-class folds while never separating windows of one group."""
    all_classes = set(range(4))
    unique_groups = sorted(set(groups.tolist()))
    if set(y.tolist()) != all_classes or len(unique_groups) < 2:
        raise ValueError("Need all four classes and at least two independent groups")
    group_classes = {group: set(y[groups == group].tolist()) for group in unique_groups}
    if all(classes == all_classes for classes in group_classes.values()):
        splits = LeaveOneGroupOut().split(np.zeros(len(y)), y, groups)
        strategy = "leave_one_whole_collection_group_out"
    else:
        count = min(len(set(groups[y == c].tolist())) for c in range(4))
        if count < 2:
            raise ValueError("Each class needs at least two groups for honest grouped validation")
        # Class-specific bouts can be assigned deterministically to equal-class folds.
        if all(len(classes) == 1 for classes in group_classes.values()):
            assignments = {}
            for c in range(4):
                for i, group in enumerate(sorted(set(groups[y == c].tolist()))):
                    assignments[group] = i % count
            splits = []
            for fold in range(count):
                test = np.asarray([assignments[g] == fold for g in groups])
                splits.append((np.flatnonzero(~test), np.flatnonzero(test)))
            strategy = "deterministic_stratified_whole_bout_groups"
        else:
            splits = StratifiedGroupKFold(n_splits=count, shuffle=False).split(
                np.zeros(len(y)), y, groups)
            strategy = "stratified_group_kfold"
    result = []
    tested = np.zeros(len(y), dtype=int)
    for index, (train, test) in enumerate(splits):
        train_groups, test_groups = set(groups[train]), set(groups[test])
        if train_groups & test_groups:
            raise ValueError("Group leakage detected")
        if set(y[train]) != all_classes or set(y[test]) != all_classes:
            raise ValueError("Every fold must retain all four classes in train and test")
        tested[test] += 1
        result.append({"fold": index, "train": train, "test": test,
                       "train_groups": sorted(train_groups), "test_groups": sorted(test_groups)})
    if not np.all(tested == 1):
        raise ValueError("Grouped validation must hold out each window exactly once")
    return strategy, result


def score(y, predicted):
    matrix = confusion_matrix(y, predicted, labels=range(4))
    return {"accuracy": float(accuracy_score(y, predicted)),
            "balanced_accuracy": float(balanced_accuracy_score(y, predicted)),
            "macro_f1": float(f1_score(y, predicted, labels=range(4), average="macro", zero_division=0)),
            "confusion_matrix": matrix.tolist(),
            "recall_by_class": {name: float(matrix[c,c] / matrix[c].sum())
                                for c, name in enumerate(STATES)}}


def _tree_lines(tree, indent="  ", weight=1.0, additive=False):
    lines = []
    def emit(node, pad):
        left, right = tree.children_left[node], tree.children_right[node]
        if left == right:
            p = tree.value[node][0].astype(float)
            p = p / p.sum() * weight
            for c, value in enumerate(p):
                op = "+=" if additive else "="
                lines.append(f"{pad}probabilities[{c}] {op} static_cast<float>({cpp_float(value)});")
            return
        lines.append(f"{pad}if (features[{int(tree.feature[node])}] <= {cpp_float(tree.threshold[node])}) {{")
        emit(int(left), pad + "  ")
        lines.append(f"{pad}}} else {{")
        emit(int(right), pad + "  ")
        lines.append(f"{pad}}}")
    emit(0, indent)
    return lines


def export_model(estimator, method_id: str, version: str) -> str:
    if list(estimator.classes_) != list(range(4)):
        raise ValueError("Model must have all four classes in protocol order")
    if isinstance(estimator, DecisionTreeClassifier):
        return export_cpp(estimator, method_id, version)
    lines = ["#pragma once", '#include "prm_features.h"', "namespace prm {",
             f"// {method_id} v{version}: grouped evaluation in sibling metrics.json.",
             "inline bool modelAvailable() { return true; }",
             "inline bool predictProbabilities(const float* features, float* probabilities) {",
             "  if (!features || !probabilities) return false;",
             "  for (size_t i=0; i<kFeatureCount; ++i) if (!std::isfinite(features[i])) return false;"]
    if isinstance(estimator, RandomForestClassifier):
        lines.append("  for (size_t i=0; i<kClassCount; ++i) probabilities[i]=0.0f;")
        for model in estimator.estimators_:
            lines.extend(_tree_lines(model.tree_, weight=1 / len(estimator.estimators_), additive=True))
    else:
        scaler = estimator.named_steps["standardscaler"]
        model = estimator.named_steps["logisticregression"]
        # Fold scaling into weights: w*(x-mean)/scale+b == (w/scale)*x + corrected_b.
        weights = model.coef_ / scaler.scale_[None, :]
        intercept = model.intercept_ - weights @ scaler.mean_
        lines.append("  double logits[4] = {};")
        for c in range(4):
            expression = cpp_float(intercept[c]) + "".join(
                f" + ({cpp_float(weights[c,j])}) * static_cast<double>(features[{j}])"
                for j in range(12))
            lines.append(f"  logits[{c}] = {expression};")
        lines.extend(["  double largest=logits[0];",
                      "  for (size_t i=1; i<4; ++i) if(logits[i]>largest) largest=logits[i];",
                      "  double total=0.0;",
                      "  for (size_t i=0; i<4; ++i) { logits[i]=std::exp(logits[i]-largest); total+=logits[i]; }",
                      "  if (!std::isfinite(total) || total<=0.0) return false;",
                      "  for (size_t i=0; i<4; ++i) probabilities[i]=static_cast<float>(logits[i]/total);"])
    lines.extend(["  return true;", "}", "}  // namespace prm", ""])
    return "\n".join(lines)


def model_description(estimator):
    if isinstance(estimator, DecisionTreeClassifier):
        return {"nodes": int(estimator.tree_.node_count), "depth": int(estimator.get_depth())}
    if isinstance(estimator, RandomForestClassifier):
        return {"trees": len(estimator.estimators_),
                "nodes": sum(int(t.tree_.node_count) for t in estimator.estimators_),
                "depth": max(int(t.get_depth()) for t in estimator.estimators_)}
    model = estimator.named_steps["logisticregression"]
    return {"coefficients": int(model.coef_.size), "intercepts": int(model.intercept_.size),
            "iterations": model.n_iter_.tolist()}


def compare(manifest_path: Path, output_root: Path = Path("outputs/results"), version: str = "1",
            summary_root: Path = Path("outputs/comparison/C01_v1"), stride: int = 25):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", version) or ".." in version:
        raise ValueError("Unsafe version path")
    destinations = {method: output_root / f"{method}_v{version}" for method in CANDIDATES}
    if summary_root.exists() or any(path.exists() for path in destinations.values()):
        raise FileExistsError("Refusing to overwrite an evaluated method or comparison directory")
    records, x, y, recording_ids, groups = grouped_dataset(manifest_path, stride)
    strategy, folds = group_folds(y, groups)
    results = []
    for method, params in CANDIDATES.items():
        probabilities = np.full((len(y), 4), np.nan)
        fold_ids = np.full(len(y), -1, dtype=int)
        fold_metrics = []
        for fold in folds:
            train, test = fold["train"], fold["test"]
            estimator = estimator_for(method)
            estimator.fit(x[train], y[train])
            p = estimator.predict_proba(x[test])
            probabilities[test] = p
            fold_ids[test] = fold["fold"]
            fold_metrics.append({"fold": fold["fold"], "train_groups": fold["train_groups"],
                                 "test_groups": fold["test_groups"], "train_windows": len(train),
                                 "test_windows": len(test), **score(y[test], np.argmax(p, axis=1))})
        if not np.isfinite(probabilities).all() or np.any(fold_ids < 0):
            raise ValueError("Incomplete held-out predictions")
        predicted = np.argmax(probabilities, axis=1)
        final = estimator_for(method)
        final.fit(x, y)  # Deployment candidate only; never used for held-out metrics.
        header = export_model(final, method, version)
        metrics = {"method_id": method, "version": version, "name": params["name"],
                   "source": "real_sensor", "evaluated_at_utc": datetime.now(timezone.utc).isoformat(),
                   "code_commit": git_commit(), "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
                   "parameters": params, "sample_rate_hz": SAMPLE_RATE_HZ,
                   "window_samples": WINDOW_SAMPLES, "stride_samples": stride,
                   "feature_names": list(FEATURE_NAMES), "states": list(STATES),
                   "validation_strategy": strategy, "folds": fold_metrics,
                   "pooled_grouped_heldout": score(y, predicted),
                   "mean_fold_balanced_accuracy": float(np.mean([f["balanced_accuracy"] for f in fold_metrics])),
                   "fold_balanced_accuracy_std": float(np.std([f["balanced_accuracy"] for f in fold_metrics])),
                   "windows": len(y), "recordings": len(records), "groups": len(set(groups)),
                   "recording_groups": [{"recording_id": r["recording_id"], "group_id": r["group_id"],
                                         "state": r["state"], "sha256": r["sha256"]} for r in records],
                   "export_header_bytes": len(header.encode("utf-8")), "final_model": model_description(final),
                   "hardware_verified": False, "deployment_training": "all approved recordings after grouped evaluation",
                   "limitations": ["Few collection groups; overlapping held-out windows are correlated.",
                       "Candidate selection uses these CV results; they are not an untouched final test of the selected model.",
                       "Recording/collection groups do not establish independent persons or cross-person generalization.",
                       "Header size and model node count are software measurements, not runtime memory or latency.",
                       "No on-board accuracy or real-time performance is implied by offline evaluation."]}
        directory = destinations[method]
        directory.mkdir(parents=True, exist_ok=False)
        (directory / "metrics.json").write_text(json.dumps(metrics, indent=2, allow_nan=False)+"\n", encoding="utf-8")
        (directory / "prm_model.h").write_text(header, encoding="utf-8")
        shutil.copyfile(manifest_path, directory / "manifest.json")
        with (directory / "heldout_predictions.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(["recording_id", "group_id", "fold", "true_state_id", "predicted_state_id", *STATES])
            writer.writerows((r,g,int(f),int(t),int(p),*map(float,probs))
                for r,g,f,t,p,probs in zip(recording_ids,groups,fold_ids,y,predicted,probabilities))
        np.savez_compressed(directory / "feature_windows.npz", features=x, targets=y,
                            recording_ids=recording_ids, group_ids=groups, folds=fold_ids,
                            heldout_probabilities=probabilities,
                            deployment_probabilities=final.predict_proba(x))
        results.append({"method_id": method, "version": version, "name": params["name"],
                        "mean_fold_balanced_accuracy": metrics["mean_fold_balanced_accuracy"],
                        "fold_balanced_accuracy_std": metrics["fold_balanced_accuracy_std"],
                        **metrics["pooled_grouped_heldout"], "header_bytes": metrics["export_header_bytes"],
                        "result_directory": directory.as_posix()})
    summary_root.mkdir(parents=True, exist_ok=False)
    ranked = sorted(results, key=lambda r: (-r["mean_fold_balanced_accuracy"], -r["macro_f1"], r["header_bytes"]))
    summary = {"comparison_id": "C01", "version": version, "validation_strategy": strategy,
               "results": results, "ranking": [r["method_id"] for r in ranked],
               "recommended_candidate": ranked[0]["method_id"],
               "selection_status": "recommendation only; parent must inspect class recalls, feasibility and install explicitly",
               "hardware_verified": False}
    (summary_root / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output-root", type=Path, default=Path("outputs/results"))
    parser.add_argument("--version", default="1")
    parser.add_argument("--summary-root", type=Path, default=Path("outputs/comparison/C01_v1"))
    parser.add_argument("--stride", type=int, default=25)
    args = parser.parse_args()
    try:
        summary = compare(args.manifest,args.output_root,args.version,args.summary_root,args.stride)
    except (ValueError,OSError,json.JSONDecodeError) as exc:
        parser.exit(2,f"Comparison failed: {exc}\n")
    for result in summary["results"]:
        print(f"{result['method_id']}: grouped balanced accuracy={result['mean_fold_balanced_accuracy']:.6f}; "
              f"macroF1={result['macro_f1']:.6f}; export bytes={result['header_bytes']}")
    print("Recommended candidate:",summary["recommended_candidate"],"(not automatically installed)")


if __name__ == "__main__":
    main()
