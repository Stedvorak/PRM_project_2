"""Selected real-data tree export checks; compiled/runtime evidence stays separate."""
from pathlib import Path
import subprocess

import numpy as np
import pytest

from tools.verify_model_export import parse_tree_header, tree_probabilities, verify


ROOT = Path(__file__).resolve().parents[1]


def test_installed_candidate_matches_saved_real_reference_vectors():
    result = verify(ROOT / "firmware/include/prm_model.h",
                    ROOT / "outputs/results/M01_v1/prm_model.h",
                    ROOT / "outputs/results/M01_v1/feature_windows.npz")
    assert result["installed_matches_candidate_bytes"] is True
    assert result["real_feature_vectors_checked"] == 324
    assert result["maximum_absolute_probability_error"] <= 1e-7
    assert result["state_id_agreement"] is True
    assert result["hardware_runtime_verified"] is False


def test_float32_inputs_use_exported_double_threshold_boundaries():
    # Synthetic software fixture: threshold is strictly between adjacent float32
    # values, so converting the threshold to float32 would change a decision.
    header = """
if (features[0] <= 1.00000006) {
  probabilities[0] = static_cast<float>(1.0);
  probabilities[1] = static_cast<float>(0.0);
  probabilities[2] = static_cast<float>(0.0);
  probabilities[3] = static_cast<float>(0.0);
} else {
  probabilities[0] = static_cast<float>(0.0);
  probabilities[1] = static_cast<float>(1.0);
  probabilities[2] = static_cast<float>(0.0);
  probabilities[3] = static_cast<float>(0.0);
}
return true;
"""
    tree = parse_tree_header(header)
    x = np.zeros((2, 12), dtype=np.float32)
    x[:, 0] = [np.float32(1), np.nextafter(np.float32(1), np.float32(2))]
    np.testing.assert_array_equal(np.argmax(tree_probabilities(tree, x), axis=1), [0, 1])
    x[0, 0] = np.nan
    with pytest.raises(ValueError, match="finite"):
        tree_probabilities(tree, x)


def test_modified_installation_is_rejected(tmp_path):
    candidate = ROOT / "outputs/results/M01_v1/prm_model.h"
    altered = tmp_path / "changed.h"
    altered.write_bytes(candidate.read_bytes() + b"\n// changed\n")
    with pytest.raises(ValueError, match="differs"):
        verify(altered, candidate, ROOT / "outputs/results/M01_v1/feature_windows.npz")


def test_actual_selected_header_compiles_for_esp32(tmp_path):
    compiler = ROOT / ".pio-core/packages/toolchain-xtensa-esp32s3/bin/xtensa-esp32s3-elf-g++.exe"
    if not compiler.exists():
        pytest.skip("ESP32 target compiler unavailable")
    source = tmp_path / "selected_probe.cpp"
    source.write_text('#include "prm_model.h"\nint main(){float x[12]={};float p[4];return prm::predictProbabilities(x,p)?0:1;}\n', encoding="utf-8")
    result = subprocess.run([str(compiler), "-std=gnu++11", "-Wall", "-Werror", "-fsyntax-only",
                             "-I", str(ROOT / "firmware/include"), str(source)],
                            capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
