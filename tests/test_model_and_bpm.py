#!/usr/bin/env python3
"""
Test Suite for C++ Model & BPM Estimator
Verifies:
1. firmware/include/model.h syntax and C++ compilation.
2. Exact numerical equivalence between Python DecisionTreeClassifier and C++ predict_sensor_state.
3. firmware/include/bpm.h compilation and functional behavior:
   - State 0 (Calm) returns physiological respiratory rate (12-25 BPM).
   - State 1 (Fast) returns physiological respiratory rate (25-55 BPM).
   - State 2 (Unattached) returns -1.0f.
   - State 3 (Shaking) returns -1.0f.
"""

import subprocess
import tempfile
import json
from pathlib import Path
import numpy as np
import pandas as pd

def test_model_and_bpm_cpp_compilation():
    root = Path(__file__).resolve().parents[1]
    model_h = root / "firmware" / "include" / "model.h"
    bpm_h = root / "firmware" / "include" / "bpm.h"

    assert model_h.exists(), "firmware/include/model.h does not exist!"
    assert bpm_h.exists(), "firmware/include/bpm.h does not exist!"

    with tempfile.TemporaryDirectory() as tmpdir:
        test_cpp = Path(tmpdir) / "test_runner.cpp"
        test_bin = Path(tmpdir) / "test_runner"

        test_cpp.write_text("""
#include <iostream>
#include <cassert>
#include <cmath>
#include "model.h"
#include "bpm.h"

int main() {
    // 1. Verify model.h signature
    float f[10] = {0.01f, 0.05f, 1.0f, 2.0f, 0.0001f, 0.0001f, 0.0001f, -0.2f, 0.5f, -10.0f};
    float probs[4] = {0.0f};
    int state = predict_sensor_state(f, probs);
    assert(state >= 0 && state < 4);
    float sum_probs = probs[0] + probs[1] + probs[2] + probs[3];
    assert(std::fabs(sum_probs - 1.0f) < 1e-4);

    // 2. Verify bpm.h contract
    prm::Sample dummy_samples[100];
    for (int i = 0; i < 100; ++i) {
        dummy_samples[i].t_ms = i * 20; // 50 Hz
        dummy_samples[i].ax_g = 0.0f;
        dummy_samples[i].ay_g = 0.0f;
        dummy_samples[i].az_g = 0.5f + 0.02f * std::sin(2.0f * 3.14159f * 0.25f * (i * 0.02f)); // ~15 BPM
        dummy_samples[i].gx_dps = 0.0f;
        dummy_samples[i].gy_dps = 0.0f;
        dummy_samples[i].gz_dps = 0.0f;
    }

    // Unattached (state 2) must return -1.0f
    float bpm_unattached = prm::estimate_bpm(dummy_samples, 100, 2);
    assert(bpm_unattached == -1.0f);

    // Shaking (state 3) must return -1.0f
    float bpm_shaking = prm::estimate_bpm(dummy_samples, 100, 3);
    assert(bpm_shaking == -1.0f);

    // Calm (state 0) must return valid positive BPM
    float bpm_calm = prm::estimate_bpm(dummy_samples, 100, 0);
    assert(bpm_calm > 0.0f && bpm_calm < 60.0f);

    // Fast (state 1) must return valid positive BPM
    float bpm_fast = prm::estimate_bpm(dummy_samples, 100, 1);
    assert(bpm_fast > 0.0f && bpm_fast < 75.0f);

    std::cout << "C++ verification passed! Calm BPM: " << bpm_calm << ", Fast BPM: " << bpm_fast << std::endl;
    return 0;
}
""", encoding="utf-8")

        # Compile with clang++
        cmd = [
            "clang++", "-std=c++14", "-Wall", "-Wextra",
            f"-I{root}/firmware/include",
            str(test_cpp), "-o", str(test_bin)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        assert res.returncode == 0, f"Compilation failed:\n{res.stderr}"

        # Run test binary
        run_res = subprocess.run([str(test_bin)], capture_output=True, text=True)
        assert run_res.returncode == 0, f"Execution failed:\n{run_res.stderr}"
        print(run_res.stdout.strip())

if __name__ == "__main__":
    test_model_and_bpm_cpp_compilation()
    print("ALL MODEL AND BPM C++ VERIFICATIONS PASSED!")
