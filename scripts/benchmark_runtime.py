#!/usr/bin/env python3
import argparse
import contextlib
import io
import json
import os
import statistics
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


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


def scenario_commands(iterations):
    scenarios = {
        "help": ["--help"],
        "list-agy-json": ["list", "agy", "--json"],
        "diagnostics-agy-json": ["diagnostics", "agy", "--json"],
        "config-json": ["config", "show", "--json"],
    }
    return [summarize(name, time_call(lambda args=args: run_command(args), iterations)) for name, args in scenarios.items()]


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


def run_benchmark(args):
    if args.scenario == "commands":
        return scenario_commands(args.iterations)
    if args.scenario == "status-redraw":
        return scenario_status_redraw(args.iterations, args.profiles)
    if args.scenario == "quota-parser":
        return scenario_quota_parser(args.iterations)
    results = []
    results.extend(scenario_commands(max(1, min(args.iterations, 5))))
    results.extend(scenario_status_redraw(args.iterations, args.profiles))
    results.extend(scenario_quota_parser(args.iterations))
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(description="Local runtime benchmarks for cli-profile-manager.")
    parser.add_argument("--scenario", choices=["all", "commands", "status-redraw", "quota-parser"], default="all")
    parser.add_argument("--iterations", type=int, default=20)
    parser.add_argument("--profiles", type=int, default=12)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    results = run_benchmark(args)
    payload = {
        "ok": True,
        "scenario": args.scenario,
        "iterations": args.iterations,
        "profiles": args.profiles,
        "results": results,
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        for result in results:
            print(
                f"{result['name']:<22} runs={result['runs']:<4} "
                f"median={result['median_ms']:>8.3f}ms p95={result['p95_ms']:>8.3f}ms max={result['max_ms']:>8.3f}ms"
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
