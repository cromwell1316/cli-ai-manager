import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import benchmark_runtime


def test_benchmark_compare_names_regressed_section():
    current = {
        "results": [
            {"name": "fast-section", "median_ms": 10.0},
            {"name": "slow-section", "median_ms": 30.0},
        ]
    }
    baseline = {
        "results": [
            {"name": "fast-section", "median_ms": 9.0},
            {"name": "slow-section", "median_ms": 10.0},
        ]
    }

    report = benchmark_runtime.compare_results(
        current,
        baseline,
        relative_tolerance=0.25,
        absolute_tolerance_ms=2.0,
    )

    assert report["ok"] is False
    assert [item["name"] for item in report["regressions"]] == ["slow-section"]
    assert report["regressions"][0]["delta_ms"] == 20.0


def test_benchmark_compare_tolerates_host_noise():
    current = {"results": [{"name": "python-startup", "median_ms": 51.0}]}
    baseline = {"results": [{"name": "python-startup", "median_ms": 50.0}]}

    report = benchmark_runtime.compare_results(
        current,
        baseline,
        relative_tolerance=0.05,
        absolute_tolerance_ms=5.0,
    )

    assert report["ok"] is True
    assert report["comparisons"][0]["status"] == "ok"


def test_benchmark_cli_compare_and_write_baseline(tmp_path):
    baseline = {
        "ok": True,
        "schema_version": 2,
        "scenario": "quota-parser",
        "iterations": 1,
        "profiles": 12,
        "results": [{"name": "quota-parser", "runs": 1, "median_ms": 50.0}],
    }
    baseline_path = tmp_path / "baseline.json"
    output_path = tmp_path / "current.json"
    baseline_path.write_text(json.dumps(baseline), encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "benchmark_runtime.py"),
            "--scenario",
            "quota-parser",
            "--iterations",
            "1",
            "--json",
            "--compare",
            str(baseline_path),
            "--write-baseline",
            str(output_path),
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    written = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["comparison"]["ok"] is True
    assert payload["schema_version"] == 2
    assert written["results"][0]["name"] == "quota-parser"


def test_benchmark_surfaces_include_profile_index_and_quota_mock():
    class Args:
        scenario = "all"
        iterations = 1
        profiles = 3

    names = {result["name"] for result in benchmark_runtime.run_benchmark(Args)}

    assert "profile-index" in names
    assert "quota-cold-mock" in names
    assert "quota-warm-mock" in names
