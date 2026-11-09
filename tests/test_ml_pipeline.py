"""Synthetic software fixtures only: these are NOT classifier/hardware evaluation."""
import json
from pathlib import Path

import numpy as np
import pytest
from sklearn.tree import DecisionTreeClassifier

from tools.collect_serial import parse_sample
from tools.train_model import (
    COLUMNS, FEATURE_NAMES, STATES, extract_features, export_cpp, load_manifest,
    read_recording, split_recordings, train, window_records,
)


def synthetic_window():
    """Known numeric fixture, never placed in data/ or claimed as real measurements."""
    result = np.zeros((100, 7), dtype=float)
    result[:, 0] = np.arange(100) * 40
    result[:, 3] = 1  # +1 g z; all remaining components zero.
    return result


def write_fixture(path, state_index=0, take=0):
    samples = synthetic_window()
    samples[:, 1] = state_index + take * 0.01
    np.savetxt(path, samples, delimiter=",", header=",".join(COLUMNS), comments="")


def synthetic_manifest(tmp_path):
    recordings = []
    for state_index, state in enumerate(STATES):
        for take in range(3):
            path = tmp_path / f"{state}_{take}.csv"
            write_fixture(path, state_index, take)
            recordings.append({"recording_id": f"{state}_{take}",
                               "state": state, "path": path.name})
    manifest = tmp_path / "synthetic_test_fixture.json"
    # Test-only marker permits exercising the real-only validation path.
    # This manifest exists solely under pytest's temporary directory.
    manifest.write_text(json.dumps({"source": "real_sensor", "sample_rate_hz": 25,
                                    "recordings": recordings}), encoding="utf-8")
    return manifest


def test_constant_features_have_exact_values():
    expected = [0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0]
    features = extract_features(synthetic_window())
    np.testing.assert_array_equal(features, expected)
    assert len(FEATURE_NAMES) == 12
    assert features.dtype == np.float32


def test_dynamic_features_match_independent_formula():
    samples = synthetic_window()
    samples[:, 1] = np.linspace(-0.5, 0.5, 100).astype(np.float32)
    samples[:, 4] = 3
    samples[:, 5] = 4
    actual = extract_features(samples)
    accel = samples[:, 1:4]
    magnitude = np.linalg.norm(accel, axis=1)
    expected = [*accel.mean(axis=0), *accel.std(axis=0), magnitude.mean(),
                magnitude.std(), 5, 0,
                np.sqrt(np.mean(np.sum(np.diff(accel, axis=0) ** 2, axis=1))),
                np.ptp(magnitude)]
    np.testing.assert_allclose(actual, expected, atol=1e-6, rtol=1e-6)


@pytest.mark.parametrize("kind", ["nan", "duplicate", "reverse", "gap", "short", "negative"])
def test_invalid_window_rejected(kind):
    sample = synthetic_window()
    if kind == "nan":
        sample[20, 1] = np.nan
    elif kind == "duplicate":
        sample[20, 0] = sample[19, 0]
    elif kind == "reverse":
        sample[20, 0] = sample[19, 0] - 1
    elif kind == "gap":
        sample[20:, 0] += 100
    elif kind == "short":
        sample = sample[:-1]
    elif kind == "negative":
        sample[:, 0] -= 1
    with pytest.raises(ValueError):
        extract_features(sample)


def test_recording_split_preserves_all_classes_and_ids(tmp_path):
    records = load_manifest(synthetic_manifest(tmp_path))
    training, testing = split_recordings(records)
    assert {r["state"] for r in training} == set(STATES)
    assert {r["state"] for r in testing} == set(STATES)
    assert not ({r["recording_id"] for r in training} &
                {r["recording_id"] for r in testing})
    assert split_recordings(records) == (training, testing)


def test_too_few_recordings_rejected():
    with pytest.raises(ValueError, match="two independent"):
        split_recordings([{"state": state, "recording_id": state} for state in STATES])


def test_manifest_rejects_unspecified_source_and_duplicate_files(tmp_path):
    manifest = synthetic_manifest(tmp_path)
    raw = json.loads(manifest.read_text())
    raw["source"] = "synthetic"
    manifest.write_text(json.dumps(raw))
    with pytest.raises(ValueError, match="real_sensor"):
        load_manifest(manifest)
    raw["source"] = "real_sensor"
    raw["recordings"][1]["path"] = raw["recordings"][0]["path"]
    manifest.write_text(json.dumps(raw))
    with pytest.raises(ValueError, match="same recording"):
        load_manifest(manifest)


def test_manifest_rejects_copied_content_holdout(tmp_path):
    manifest = synthetic_manifest(tmp_path)
    raw = json.loads(manifest.read_text())
    first, second = [tmp_path / r["path"] for r in raw["recordings"][:2]]
    second.write_bytes(first.read_bytes())
    with pytest.raises(ValueError, match="Duplicate recording contents"):
        load_manifest(manifest)


def test_export_keeps_four_class_order_and_rejects_missing_class():
    x = np.zeros((8, 12), dtype=np.float32)
    x[:, 0] = np.repeat(np.arange(4), 2)
    y = np.repeat(np.arange(4), 2)
    classifier = DecisionTreeClassifier(random_state=42).fit(x, y)
    header = export_cpp(classifier, "M01", "1")
    assert "modelAvailable() { return true; }" in header
    assert all(f"probabilities[{i}]" in header for i in range(4))
    with pytest.raises(ValueError, match="all four"):
        export_cpp(DecisionTreeClassifier().fit(x[:4], y[:4]), "M01", "1")


def test_full_pipeline_writes_only_isolated_candidate(tmp_path):
    manifest = synthetic_manifest(tmp_path)
    output = train(manifest, tmp_path / "test_only_outputs", "M01", "test")
    metrics = json.loads((output / "metrics.json").read_text())
    assert metrics["hardware_verified"] is False
    assert metrics["train_windows"] == 8
    assert metrics["test_windows"] == 4
    assert not set(metrics["train_recordings"]) & set(metrics["test_recordings"])
    assert np.asarray(metrics["confusion_matrix"]).shape == (4, 4)
    assert (output / "prm_model.h").exists()
    with pytest.raises(FileExistsError):
        train(manifest, tmp_path / "test_only_outputs", "M01", "test")


@pytest.mark.parametrize("line", ["", "boot: info", "t_ms,ax_g,ay_g,az_g,gx_dps,gy_dps,gz_dps",
                                  "0,nan,0,0,0,0,0", "-1,0,0,0,0,0,0"])
def test_capture_ignores_nonmeasurements(line):
    assert parse_sample(line) is None


def test_capture_parses_only_real_wire_values():
    assert parse_sample("40,0.1,-0.2,1.0,0,2,3\n") == [40, 0.1, -0.2, 1, 0, 2, 3]
