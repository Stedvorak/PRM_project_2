"""Algebraically verify the installed tree export against saved real feature vectors.

This parses the restricted generated C++ tree grammar; it does not execute
compiled C++ or measure hardware runtime. Hardware verification is separate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

import numpy as np


NUMBER = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
BRANCH = re.compile(r"if \(features\[(\d+)\] <= (" + NUMBER + r")\) \{")
LEAF = re.compile(r"probabilities\[(\d+)\] = static_cast<float>\((" + NUMBER + r")\);")


def parse_tree_header(header: str):
    lines = [line.strip() for line in header.splitlines() if line.strip()]
    start = next((i for i, line in enumerate(lines) if BRANCH.fullmatch(line) or LEAF.fullmatch(line)), None)
    if start is None:
        raise ValueError("No supported generated tree found")

    def parse(index):
        branch = BRANCH.fullmatch(lines[index])
        if branch:
            feature, threshold = int(branch[1]), float(branch[2])
            if not 0 <= feature < 12 or not np.isfinite(threshold):
                raise ValueError("Invalid feature/threshold")
            left, index = parse(index + 1)
            if lines[index] != "} else {":
                raise ValueError("Missing generated else branch")
            right, index = parse(index + 1)
            if lines[index] != "}":
                raise ValueError("Missing generated closing brace")
            return ("branch", feature, threshold, left, right), index + 1
        values = []
        for expected in range(4):
            match = LEAF.fullmatch(lines[index])
            if not match or int(match[1]) != expected:
                raise ValueError("Generated leaf must assign four ordered probabilities")
            value = np.float32(float(match[2]))
            if not np.isfinite(value) or not 0 <= value <= 1:
                raise ValueError("Invalid generated probability")
            values.append(value)
            index += 1
        if abs(float(np.sum(values, dtype=np.float64)) - 1) > 0.001:
            raise ValueError("Generated probabilities do not sum to one")
        return ("leaf", np.asarray(values, dtype=np.float32)), index

    try:
        tree, end = parse(start)
        if lines[end] != "return true;":
            raise ValueError("Unexpected statements after generated tree")
    except IndexError as exc:
        raise ValueError("Truncated generated tree") from exc
    return tree


def tree_probabilities(tree, features):
    values = np.asarray(features, dtype=np.float32)
    if values.ndim != 2 or values.shape[1] != 12 or not np.isfinite(values).all():
        raise ValueError("Expected finite float32 feature vectors with12 columns")
    result = np.empty((len(values), 4), dtype=np.float32)
    for index, row in enumerate(values):
        node = tree
        while node[0] == "branch":
            # C++ float input is promoted to double for the exported exact
            # double threshold; mirror that conversion explicitly.
            node = node[3] if float(row[node[1]]) <= node[2] else node[4]
        result[index] = node[1]
    return result


def verify(header_path: Path, candidate_path: Path, vectors_path: Path):
    installed = header_path.read_bytes()
    candidate = candidate_path.read_bytes()
    if installed != candidate:
        raise ValueError("Installed model differs from selected evaluated candidate")
    tree = parse_tree_header(installed.decode("utf-8-sig"))
    with np.load(vectors_path, allow_pickle=False) as data:
        features = data["features"]
        expected = data["deployment_probabilities"]
    actual = tree_probabilities(tree, features)
    if expected.shape != actual.shape or not np.isfinite(expected).all():
        raise ValueError("Saved reference probabilities are invalid")
    error = float(np.max(np.abs(actual.astype(np.float64) - expected)))
    if error > 1e-7 or not np.array_equal(np.argmax(actual, axis=1), np.argmax(expected, axis=1)):
        raise ValueError(f"Export/reference disagreement: maximum probability error {error}")
    return {
        "kind": "software algebraic traversal of generated C++ tree; not compiled execution",
        "installed_matches_candidate_bytes": True,
        "installed_model_sha256": hashlib.sha256(installed).hexdigest(),
        "reference_vectors_sha256": hashlib.sha256(vectors_path.read_bytes()).hexdigest(),
        "real_feature_vectors_checked": len(features),
        "features_per_vector": int(features.shape[1]),
        "maximum_absolute_probability_error": error,
        "state_id_agreement": True,
        "predicted_state_counts": {str(c): int(np.sum(np.argmax(actual, axis=1) == c)) for c in range(4)},
        "hardware_runtime_verified": False,
        "note": "References are final all-data model outputs for parity, not held-out accuracy metrics.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--header", type=Path, default=Path("firmware/include/prm_model.h"))
    parser.add_argument("--candidate", type=Path, default=Path("outputs/results/M01_v1/prm_model.h"))
    parser.add_argument("--vectors", type=Path, default=Path("outputs/results/M01_v1/feature_windows.npz"))
    args = parser.parse_args()
    try:
        result = verify(args.header, args.candidate, args.vectors)
    except (OSError, ValueError) as exc:
        parser.exit(2, f"Model verification failed: {exc}\n")
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
