#!/usr/bin/env python3
import argparse
import concurrent.futures
import json
import os
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE_MANAGER = ROOT / "profile_manager.py"


def run_json(args, timeout=None):
    completed = subprocess.run(
        [sys.executable, str(PROFILE_MANAGER)] + args + ["--json"],
        cwd=str(ROOT),
        env=os.environ.copy(),
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        payload = {
            "ok": False,
            "error": {
                "type": "invalid_json",
                "message": completed.stderr.strip() or completed.stdout[:200],
                "code": completed.returncode,
            },
        }
    return completed.returncode, payload


def profile_numbers(raw):
    values = []
    for item in raw.split(","):
        item = item.strip().lower()
        if not item:
            continue
        if item.startswith("p"):
            item = item[1:]
        values.append(int(item))
    return values


def quota_summary(quota):
    limits = quota.get("limits") or {}
    parts = []
    for name, data in limits.items():
        value = data.get("percent_left", data.get("percent"))
        if value is None:
            continue
        label = data.get("model", name)
        parts.append(f"{label}:{value:g}%")
    return " ".join(parts[:8])


def dry_run(profiles):
    _, payload = run_json(["diagnostics", "agy"])
    tool = payload.get("tools", {}).get("agy", {})
    known = {profile["profile"]: profile for profile in tool.get("profiles", [])}
    rows = []
    for num in profiles:
        profile = known.get(f"p{num}", {})
        rows.append({
            "profile": f"p{num}",
            "occupied": profile.get("occupied", False),
            "has_token": profile.get("has_token", False),
            "token_state": profile.get("token_state"),
            "credential_source": profile.get("credential_source"),
        })
    return rows


def probe_profile(num, timeout):
    started = time.monotonic()
    code, payload = run_json(["quota", "agy", f"p{num}", "--timeout", str(timeout)], timeout=timeout + 15)
    elapsed = round(time.monotonic() - started, 3)
    if code != 0:
        error = payload.get("error", {})
        return {
            "profile": f"p{num}",
            "ok": False,
            "elapsed_seconds": elapsed,
            "state": error.get("type", "error"),
            "warning": error.get("message", f"exit code {code}"),
            "summary": "",
        }
    quota = payload.get("quota", {})
    warnings = quota.get("warnings") or []
    return {
        "profile": f"p{num}",
        "ok": quota.get("state") == "available",
        "elapsed_seconds": elapsed,
        "state": quota.get("state", "unknown"),
        "warning": warnings[0] if warnings else "",
        "summary": quota_summary(quota),
    }


def live_run(profiles, concurrency, timeout):
    rows = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, concurrency)) as executor:
        futures = {executor.submit(probe_profile, num, timeout): num for num in profiles}
        for future in concurrent.futures.as_completed(futures):
            rows.append(future.result())
    return sorted(rows, key=lambda row: int(row["profile"][1:]))


def print_rows(rows):
    print(f"{'Profile':<8} {'OK':<5} {'State':<16} {'Elapsed':<8} Summary / Warning")
    print("-" * 96)
    for row in rows:
        ok = row.get("ok")
        ok_text = "-" if ok is None else ("yes" if ok else "no")
        detail = row.get("summary") or row.get("warning") or ""
        print(f"{row['profile']:<8} {ok_text:<5} {str(row.get('state', '')):<16} {str(row.get('elapsed_seconds', '-')):<8} {detail}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Live AGY quota validation without storing secrets.")
    parser.add_argument("--profiles", default="1,2,3,4,5,6,7,8,9,10,11,12")
    parser.add_argument("--concurrency", type=int, default=int(os.environ.get("AI_MAN_INTERACTIVE_AGY_QUOTA_CONCURRENCY", "2")))
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--dry-run", action="store_true", help="inspect profiles without launching agy")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    profiles = profile_numbers(args.profiles)
    rows = dry_run(profiles) if args.dry_run else live_run(profiles, args.concurrency, args.timeout)
    payload = {
        "ok": all(row.get("ok", True) for row in rows),
        "dry_run": args.dry_run,
        "concurrency": args.concurrency,
        "timeout": args.timeout,
        "profiles": rows,
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print_rows(rows)
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
