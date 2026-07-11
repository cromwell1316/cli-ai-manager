#!/usr/bin/env python3
import argparse
import contextlib
import io
import json
import os
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
DEFAULT_RELATIVE_TOLERANCE = 0.35
DEFAULT_ABSOLUTE_TOLERANCE_MS = 5.0


def percentile(values, pct):
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((pct / 100) * (len(ordered) - 1))))
    return ordered[index]


def summarize(name, values):
    return {
        "name": name,
        "runs": len(values),
        "min_ms": round(min(values), 3) if values else None,
        "median_ms": round(statistics.median(values), 3) if values else None,
        "p95_ms": round(percentile(values, 95), 3) if values else None,
        "max_ms": round(max(values), 3) if values else None,
    }


def result_map(payload_or_results):
    results = payload_or_results.get("results", payload_or_results) if isinstance(payload_or_results, dict) else payload_or_results
    return {result["name"]: result for result in results}


def compare_results(current_payload, baseline_payload, relative_tolerance=DEFAULT_RELATIVE_TOLERANCE, absolute_tolerance_ms=DEFAULT_ABSOLUTE_TOLERANCE_MS):
    current = result_map(current_payload)
    baseline = result_map(baseline_payload)
    comparisons = []
    regressions = []
    missing_current = sorted(set(baseline) - set(current))
    missing_baseline = sorted(set(current) - set(baseline))
    for name in sorted(set(current) & set(baseline)):
        current_result = current[name]
        baseline_result = baseline[name]
        current_ms = current_result.get("median_ms")
        baseline_ms = baseline_result.get("median_ms")
        if current_ms is None or baseline_ms is None:
            status = "skipped"
            delta_ms = None
            ratio = None
            threshold_ms = None
        else:
            threshold_ms = round(max(float(absolute_tolerance_ms), float(baseline_ms) * float(relative_tolerance)), 3)
            delta_ms = round(float(current_ms) - float(baseline_ms), 3)
            ratio = round(float(current_ms) / float(baseline_ms), 4) if float(baseline_ms) > 0 else None
            status = "regression" if delta_ms > threshold_ms else "ok"
        comparison = {
            "name": name,
            "status": status,
            "current_median_ms": current_ms,
            "baseline_median_ms": baseline_ms,
            "delta_ms": delta_ms,
            "ratio": ratio,
            "threshold_ms": threshold_ms,
            "relative_tolerance": relative_tolerance,
            "absolute_tolerance_ms": absolute_tolerance_ms,
        }
        comparisons.append(comparison)
        if status == "regression":
            regressions.append(comparison)
    return {
        "ok": not regressions,
        "regressions": regressions,
        "missing_current": missing_current,
        "missing_baseline": missing_baseline,
        "comparisons": comparisons,
    }


def time_call(fn, iterations):
    values = []
    for _ in range(iterations):
        started = time.perf_counter()
        fn()
        values.append((time.perf_counter() - started) * 1000)
    return values


def run_command(args):
    completed = subprocess.run(
        [sys.executable, str(ROOT / "profile_manager.py")] + args,
        cwd=str(ROOT),
        env=os.environ.copy(),
        text=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"command failed: {' '.join(args)} -> {completed.returncode}")


def run_python(args):
    completed = subprocess.run(
        [sys.executable] + args,
        cwd=str(ROOT),
        env=os.environ.copy(),
        text=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"python failed: {' '.join(args)} -> {completed.returncode}")


def run_python_stdout(args):
    completed = subprocess.run(
        [sys.executable] + args,
        cwd=str(ROOT),
        env=os.environ.copy(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"python failed: {' '.join(args)} -> {completed.returncode}: {completed.stderr}")
    return completed.stdout


def scenario_commands(iterations):
    scenarios = {
        "help": ["--help"],
        "list-agy-json": ["list", "agy", "--json"],
        "diagnostics-agy-json": ["diagnostics", "agy", "--json"],
        "config-json": ["config", "show", "--json"],
    }
    return [summarize(name, time_call(lambda args=args: run_command(args), iterations)) for name, args in scenarios.items()]


def scenario_python_startup(iterations):
    return [summarize("python-startup", time_call(lambda: run_python(["-c", "pass"]), iterations))]


def scenario_import_profile_manager(iterations):
    result = summarize(
        "import-profile-manager",
        time_call(lambda: run_python(["-c", "import profile_manager"]), iterations),
    )
    module_count = run_python_stdout(["-c", "import sys, profile_manager; print(len(sys.modules))"]).strip()
    try:
        result["module_count"] = int(module_count)
    except ValueError:
        result["module_count"] = None
    result["section"] = "import"
    return [result]


@contextlib.contextmanager
def fake_runtime():
    old_env = os.environ.copy()
    with tempfile.TemporaryDirectory(prefix="ai-man-bench-") as tmp:
        tmp_path = Path(tmp)
        os.environ.update(
            {
                "AI_MAN_AGY_HOME": str(tmp_path / "agy-homes"),
                "AI_MAN_CODEX_HOME": str(tmp_path / "codex-homes"),
                "AI_MAN_CLAUDE_HOME": str(tmp_path / "claude-homes"),
                "AI_MAN_METADATA_DIR": str(tmp_path / "metadata"),
                "AI_MAN_WSL_HOME": str(tmp_path / "wsl"),
                "AI_MAN_WINDOWS_HOME": str(tmp_path / "windows"),
            }
        )
        agy_home = tmp_path / "agy-homes" / "p1" / ".gemini"
        agy_home.mkdir(parents=True)
        (agy_home / "oauth_creds.json").write_text(json.dumps({"refresh_token": "synthetic"}), encoding="utf-8")
        (agy_home / "google_accounts.json").write_text(json.dumps({"active": "bench@example.com"}), encoding="utf-8")
        (tmp_path / "metadata").mkdir(parents=True)
        (tmp_path / "metadata" / "profiles_metadata.json").write_text(
            json.dumps({"agy": {"p1": {"label": "bench"}}}),
            encoding="utf-8",
        )
        try:
            from cli_profile_manager import metadata, paths

            paths.refresh_from_env()
            metadata.refresh_from_env()
            yield tmp_path
        finally:
            os.environ.clear()
            os.environ.update(old_env)
            from cli_profile_manager import metadata, paths

            paths.refresh_from_env()
            metadata.refresh_from_env()


def scenario_parse_args(iterations):
    from cli_profile_manager import cli

    samples = (
        ["--help"],
        ["config", "show", "--json"],
        ["list", "agy", "--json"],
        ["status", "agy", "p1", "--json"],
        ["diagnostics", "agy", "--json"],
    )

    def parse_all():
        parser = cli.build_parser()
        for argv in samples:
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                try:
                    parser.parse_args(argv)
                except SystemExit as exc:
                    if exc.code != 0:
                        raise

    return [summarize("parse-args", time_call(parse_all, iterations))]


def scenario_command_execute(iterations):
    from cli_profile_manager import cli

    commands = {
        "command-config-json": ["config", "show", "--json"],
        "command-list-agy-json": ["list", "agy", "--json"],
        "command-status-agy-json": ["status", "agy", "p1", "--json"],
        "command-diagnostics-agy-json": ["diagnostics", "agy", "--json"],
    }

    def run_in_process(argv):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            rc = cli.run_cli(argv)
        if rc != 0:
            raise RuntimeError(f"in-process command failed: {' '.join(argv)} -> {rc}")

    with fake_runtime():
        return [
            summarize(name, time_call(lambda argv=argv: run_in_process(argv), iterations))
            for name, argv in commands.items()
        ]


def scenario_profile_index(iterations, profiles):
    from cli_profile_manager import operations

    def build_index():
        snapshot = operations.command_snapshot()
        display = snapshot.display_profiles("agy")
        for num in display[:profiles]:
            snapshot.status("agy", num)

    with fake_runtime() as tmp_path:
        for num in range(2, profiles + 1):
            home = tmp_path / "agy-homes" / f"p{num}" / ".gemini"
            home.mkdir(parents=True)
            (home / "oauth_creds.json").write_text(json.dumps({"refresh_token": f"synthetic-{num}"}), encoding="utf-8")
        return [summarize("profile-index", time_call(build_index, iterations))]


def fake_status(num):
    return {
        "num": num,
        "profile": f"p{num}",
        "email": f"user{num:02d}@example.com",
        "has_token": True,
        "token_state": "valid",
        "credential_source": "benchmark",
        "account": f"user{num:02d}@example.com",
        "warnings": [],
        "label": "benchmark" if num == 1 else "",
        "home": f"/tmp/agy-homes/p{num}",
        "quota": {
            "state": "available",
            "source_command": "/usage",
            "fetched_at": time.time(),
            "limits": {
                "gemini_3_5_flash_medium": {"model": "Gemini 3.5 Flash (Medium)", "percent": num % 101},
                "gemini_3_1_pro_low": {"model": "Gemini 3.1 Pro (Low)", "percent": (num * 7) % 101},
                "claude_sonnet_4_6_thinking": {"model": "Claude Sonnet 4.6 (Thinking)", "percent": 100},
            },
        },
    }


def scenario_status_redraw(iterations, profiles):
    from cli_profile_manager import interactive

    base_statuses = [fake_status(num) for num in range(1, profiles + 1)]
    original_clear = interactive.clear_screen
    original_header = interactive.print_header
    original_enabled = interactive.interactive_quota_enabled
    try:
        interactive.clear_screen = lambda: None
        interactive.print_header = lambda title="": None
        interactive.interactive_quota_enabled = lambda: False

        def render():
            with contextlib.redirect_stdout(io.StringIO()):
                interactive.render_status_screen("agy", base_statuses=base_statuses)

        return [summarize("status-redraw", time_call(render, iterations))]
    finally:
        interactive.clear_screen = original_clear
        interactive.print_header = original_header
        interactive.interactive_quota_enabled = original_enabled


AGY_SAMPLE = """
Account: benchmark@example.com
ALL MODELS
Gemini 3.5 Flash (Medium)
[████░░░░░░] 41.00%
Refreshes in 10h
Gemini 3.1 Pro (Low)
[██████░░░░] 66.00%
66% remaining · Refreshes in 4h
Claude Sonnet 4.6 (Thinking)
[██████████] 100.00%
Quota available
"""


def scenario_quota_parser(iterations):
    from cli_profile_manager.quota import parse_quota

    return [summarize("quota-parser", time_call(lambda: parse_quota("agy", AGY_SAMPLE), iterations))]


def scenario_quota_warm_mock(iterations):
    from cli_profile_manager.quota import parse_quota, quota_snapshot_ready

    cold_sample = "Antigravity CLI 1.1.1\n>\n? for shortcuts\n" + AGY_SAMPLE

    def cold_probe():
        quota_snapshot_ready("agy", "Antigravity CLI 1.1.1\n>\n")
        parse_quota("agy", cold_sample)

    def warm_probe():
        parse_quota("agy", AGY_SAMPLE)

    return [
        summarize("quota-cold-mock", time_call(cold_probe, iterations)),
        summarize("quota-warm-mock", time_call(warm_probe, iterations)),
    ]


def run_benchmark(args):
    if args.scenario == "commands":
        return scenario_commands(args.iterations)
    if args.scenario == "python-startup":
        return scenario_python_startup(args.iterations)
    if args.scenario == "import-profile-manager":
        return scenario_import_profile_manager(args.iterations)
    if args.scenario == "parse-args":
        return scenario_parse_args(args.iterations)
    if args.scenario == "command-execute":
        return scenario_command_execute(args.iterations)
    if args.scenario == "status-redraw":
        return scenario_status_redraw(args.iterations, args.profiles)
    if args.scenario == "quota-parser":
        return scenario_quota_parser(args.iterations)
    if args.scenario == "profile-index":
        return scenario_profile_index(args.iterations, args.profiles)
    if args.scenario == "quota-warm-mock":
        return scenario_quota_warm_mock(args.iterations)
    results = []
    results.extend(scenario_python_startup(max(1, min(args.iterations, 5))))
    results.extend(scenario_import_profile_manager(max(1, min(args.iterations, 5))))
    results.extend(scenario_parse_args(args.iterations))
    results.extend(scenario_command_execute(args.iterations))
    results.extend(scenario_profile_index(args.iterations, args.profiles))
    results.extend(scenario_commands(max(1, min(args.iterations, 5))))
    results.extend(scenario_status_redraw(args.iterations, args.profiles))
    results.extend(scenario_quota_parser(args.iterations))
    results.extend(scenario_quota_warm_mock(args.iterations))
    return results


def benchmark_payload(args, results):
    return {
        "ok": True,
        "schema_version": 2,
        "scenario": args.scenario,
        "iterations": args.iterations,
        "profiles": args.profiles,
        "python": {
            "version": sys.version.split()[0],
            "executable": sys.executable,
        },
        "results": results,
    }


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Local runtime benchmarks for cli-profile-manager.")
    parser.add_argument(
        "--scenario",
        choices=[
            "all",
            "commands",
            "python-startup",
            "import-profile-manager",
            "parse-args",
            "command-execute",
            "profile-index",
            "status-redraw",
            "quota-parser",
            "quota-warm-mock",
        ],
        default="all",
    )
    parser.add_argument("--iterations", type=int, default=20)
    parser.add_argument("--profiles", type=int, default=12)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--compare", help="compare current benchmark output to a baseline JSON file")
    parser.add_argument("--write-baseline", help="write current benchmark output to a JSON baseline file")
    parser.add_argument("--relative-tolerance", type=float, default=DEFAULT_RELATIVE_TOLERANCE)
    parser.add_argument("--absolute-tolerance-ms", type=float, default=DEFAULT_ABSOLUTE_TOLERANCE_MS)
    args = parser.parse_args(argv)

    results = run_benchmark(args)
    payload = benchmark_payload(args, results)
    if args.write_baseline:
        write_json(args.write_baseline, payload)
    comparison = None
    if args.compare:
        comparison = compare_results(
            payload,
            load_json(args.compare),
            relative_tolerance=args.relative_tolerance,
            absolute_tolerance_ms=args.absolute_tolerance_ms,
        )
        payload["comparison"] = comparison
        payload["ok"] = bool(comparison["ok"])
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        for result in results:
            print(
                f"{result['name']:<22} runs={result['runs']:<4} "
                f"median={result['median_ms']:>8.3f}ms p95={result['p95_ms']:>8.3f}ms max={result['max_ms']:>8.3f}ms"
            )
        if comparison:
            if comparison["regressions"]:
                print("Regressions:")
                for item in comparison["regressions"]:
                    print(
                        f"  {item['name']}: current={item['current_median_ms']:.3f}ms "
                        f"baseline={item['baseline_median_ms']:.3f}ms delta={item['delta_ms']:.3f}ms "
                        f"threshold={item['threshold_ms']:.3f}ms"
                    )
            if comparison["missing_current"]:
                print("Missing current results: " + ", ".join(comparison["missing_current"]))
            if comparison["missing_baseline"]:
                print("New results without baseline: " + ", ".join(comparison["missing_baseline"]))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
