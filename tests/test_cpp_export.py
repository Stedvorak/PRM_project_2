"""Compile a synthetic export for the actual ESP32 target; no hardware metrics."""
from pathlib import Path
import shutil
import subprocess

import numpy as np
import pytest
from sklearn.tree import DecisionTreeClassifier

from tools.train_model import export_cpp


def test_generated_model_and_runtime_compile_for_esp32(tmp_path):
    root = Path(__file__).resolve().parents[1]
    compiler_dir = root / ".pio-core/packages/toolchain-xtensa-esp32s3/bin"
    compiler = compiler_dir / "xtensa-esp32s3-elf-g++.exe"
    if not compiler.exists():
        found = shutil.which("xtensa-esp32s3-elf-g++")
        if not found:
            pytest.skip("Build the ESP32 firmware first to install its target compiler")
        compiler = Path(found)
    # Synthetic fixtures test export compilation, never classifier performance.
    features = np.zeros((16, 12), dtype=np.float32)
    features[:, 0] = np.repeat(np.arange(4), 4)
    labels = np.repeat(np.arange(4), 4)
    tree = DecisionTreeClassifier(max_depth=3, random_state=42).fit(features, labels)
    (tmp_path / "candidate.h").write_text(export_cpp(tree, "M01", "test"), encoding="utf-8")
    source = tmp_path / "compile_probe.cpp"
    source.write_text(
        '#include "candidate.h"\n#include "prm_runtime.h"\n'
        'int main() { prm::SampleRing ring; float f[prm::kFeatureCount] = {}; '
        'float p[prm::kClassCount] = {}; uint8_t state; float confidence; '
        'return prm::predictProbabilities(f,p) && '
        'prm::validateProbabilities(p,state,confidence) ? 0 : 1; }\n',
        encoding="utf-8",
    )
    result = subprocess.run(
        [str(compiler), "-std=gnu++11", "-Wall", "-Werror", "-fsyntax-only",
         "-I", str(root / "firmware/include"), str(source)],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
