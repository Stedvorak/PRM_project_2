"""Execute actual estimator C++ using an explicitly configured host compiler."""
import os
from pathlib import Path
import subprocess

import pytest


def test_respiration_cpp(tmp_path):
    compiler = os.environ.get("PRM_HOST_CXX")
    if not compiler:
        pytest.skip("Set PRM_HOST_CXX to a host C++ compiler (or zig.exe)")
    root = Path(__file__).resolve().parents[1]
    output = tmp_path / "respiration_test.exe"
    command = [compiler]
    if Path(compiler).stem == "zig":
        command.append("c++")
    subprocess.run(command + ["-std=c++11", "-O2", "-Wall", "-Werror",
        "-I" + str(root / "firmware/include"),
        str(root / "tests/cpp/respiration_test.cpp"), "-o", str(output)],
        check=True, timeout=180)
    result = subprocess.run([str(output)], check=True, capture_output=True,
                            text=True, timeout=10)
    assert '"synthetic_cpp_cases_passed":20' in result.stdout
