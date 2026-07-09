#!/usr/bin/env python3
import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HORIZONS_DIR = ROOT / "management" / "horizons"
VALID_STATUSES = {
    "planned",
    "active",
    "implemented",
    "completed",
    "verified",
    "blocked",
    "deferred",
}
COMPLETE_STATUSES = {"implemented", "completed", "verified"}
TOKEN_RE = re.compile(
    r"(?i)(sk-[a-z0-9_-]+|xox[a-z]-[a-z0-9-]+|gh[pousr]_[a-z0-9_]+|ya29\.[a-z0-9._-]+|refresh_token)"
)
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
HOME_RE = re.compile(re.escape(str(Path.home())))


def rel(path):
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def redact(text):
    text = TOKEN_RE.sub("[redacted-token]", text)
    text = EMAIL_RE.sub("[redacted-email]", text)
    return HOME_RE.sub("~", text)


def read_text(path):
    return path.read_text(encoding="utf-8")


def status_from_text(text):
    match = re.search(r"^Status:\s*([A-Za-z_-]+)\.?\s*$", text, re.M)
    return match.group(1).lower() if match else None


def source_of_truths(text):
    return re.findall(r"^Source of Truth:\s*(.+?)\s*$", text, re.M)


def files_listed_in_readme(text):
    files = []
    in_files = False
    for line in text.splitlines():
        if line.strip() == "## Files":
            in_files = True
            continue
        if in_files and line.startswith("## "):
            break
        if in_files:
            match = re.match(r"- `([^`]+)`", line.strip())
            if match:
                files.append(match.group(1))
    return files


def bash_commands(text):
    commands = []
    in_bash = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            if in_bash:
                in_bash = False
            elif stripped in ("```bash", "```sh", "```shell"):
                in_bash = True
            continue
        if not in_bash or not stripped or stripped.startswith("#"):
            continue
        commands.append(stripped)
    return commands


def acceptance_matrix_ok(path):
    text = read_text(path)
    lines = [line.strip() for line in text.splitlines() if line.strip().startswith("|")]
    if len(lines) < 3:
        return False
    return any("---" in line for line in lines) and any("---" not in line for line in lines[2:])


def check_horizon(path):
    issues = []
    warnings = []
    readme = path / "README.md"
    if not readme.exists():
        return {
            "horizon": rel(path),
            "status": None,
            "issues": [f"{rel(path)}: missing README.md"],
            "warnings": warnings,
        }
    readme_text = read_text(readme)
    status = status_from_text(readme_text)
    if status not in VALID_STATUSES:
        issues.append(f"{rel(readme)}: unrecognized or missing status {status!r}")
    listed_files = files_listed_in_readme(readme_text)
    if not listed_files:
        issues.append(f"{rel(readme)}: missing ## Files list")
    for filename in listed_files:
        if not (path / filename).exists():
            issues.append(f"{rel(readme)}: listed file does not exist: {filename}")
    md_files = sorted(path.glob("*.md"))
    for md_file in md_files:
        text = read_text(md_file)
        md_status = status_from_text(text)
        if md_status not in VALID_STATUSES:
            issues.append(f"{rel(md_file)}: unrecognized or missing status {md_status!r}")
        for source in source_of_truths(text):
            source_path = ROOT / source
            if not source_path.exists():
                issues.append(f"{rel(md_file)}: Source of Truth does not exist: {source}")
            elif source_path != readme:
                warnings.append(f"{rel(md_file)}: Source of Truth is not local README: {source}")
    matrices = sorted(path.glob("V_*Acceptance_Matrix.md"))
    if not matrices:
        issues.append(f"{rel(path)}: missing V_*Acceptance_Matrix.md")
    elif not any(acceptance_matrix_ok(matrix) for matrix in matrices):
        issues.append(f"{rel(path)}: acceptance matrix has no table rows")
    validation = path / "V_00_Validation_Plan.md"
    if not validation.exists():
        issues.append(f"{rel(path)}: missing V_00_Validation_Plan.md")
    else:
        commands = bash_commands(read_text(validation))
        if status in COMPLETE_STATUSES and not commands:
            issues.append(f"{rel(validation)}: completed horizon has no executable validation commands")
        elif not commands:
            warnings.append(f"{rel(validation)}: no executable validation commands")
    return {
        "horizon": rel(path),
        "status": status,
        "issues": issues,
        "warnings": warnings,
    }


def iter_horizons(selected=None):
    if selected:
        path = Path(selected)
        if not path.is_absolute():
            path = ROOT / path
        return [path]
    return sorted(path for path in HORIZONS_DIR.iterdir() if path.is_dir())


def validate_horizons(selected=None):
    results = [check_horizon(path) for path in iter_horizons(selected)]
    issues = [issue for result in results for issue in result["issues"]]
    warnings = [warning for result in results for warning in result["warnings"]]
    return {
        "ok": not issues,
        "checked": len(results),
        "issues": issues,
        "warnings": warnings,
        "horizons": results,
    }


def run_evidence_command(command, timeout_seconds):
    if "horizon_governance.py" in command and "--evidence" in command:
        return {
            "command": redact(command),
            "returncode": 0,
            "elapsed_ms": 0.0,
            "stdout": "skipped self-referential evidence collection command",
            "stderr": "",
        }
    started = time.time()
    completed = subprocess.run(
        command,
        cwd=str(ROOT),
        shell=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout_seconds,
        check=False,
    )
    elapsed_ms = round((time.time() - started) * 1000, 3)
    return {
        "command": redact(command),
        "returncode": completed.returncode,
        "elapsed_ms": elapsed_ms,
        "stdout": redact(completed.stdout)[-4000:],
        "stderr": redact(completed.stderr)[-4000:],
    }


def collect_evidence(horizon, timeout_seconds=120.0, write=False):
    path = Path(horizon)
    if not path.is_absolute():
        path = ROOT / path
    validation = path / "V_00_Validation_Plan.md"
    if not validation.exists():
        raise SystemExit(f"missing validation plan: {rel(validation)}")
    commands = bash_commands(read_text(validation))
    results = [run_evidence_command(command, timeout_seconds) for command in commands]
    payload = {
        "ok": all(result["returncode"] == 0 for result in results),
        "horizon": rel(path),
        "generated_at": int(time.time()),
        "commands": results,
    }
    if write:
        write_evidence(path, payload)
    return payload


def write_evidence(path, payload):
    evidence_path = path / "V_99_Automated_Evidence.md"
    source = rel(path / "README.md")
    lines = [
        "# V_99 Automated Evidence",
        "",
        "Owner: cli-profile-manager",
        f"Source of Truth: {source}",
        "Lifecycle: generated",
        "Document Class: validation evidence",
        "",
        "Status: completed.",
        "",
        f"Generated At: {payload['generated_at']}",
        "",
        "| Command | Return Code | Elapsed ms |",
        "| --- | ---: | ---: |",
    ]
    for result in payload["commands"]:
        command = result["command"].replace("|", "\\|")
        lines.append(f"| `{command}` | {result['returncode']} | {result['elapsed_ms']} |")
    lines.extend(["", "## Sanitized Output", ""])
    for result in payload["commands"]:
        lines.append(f"### `{result['command']}`")
        if result["stdout"]:
            lines.extend(["", "stdout:", "", "```text", result["stdout"].rstrip(), "```", ""])
        if result["stderr"]:
            lines.extend(["", "stderr:", "", "```text", result["stderr"].rstrip(), "```", ""])
    evidence_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return evidence_path


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate horizon docs and collect sanitized evidence")
    parser.add_argument("--horizon", help="single horizon directory to validate or collect evidence for")
    parser.add_argument("--json", action="store_true", help="print JSON output")
    parser.add_argument("--evidence", action="store_true", help="run validation commands from V_00")
    parser.add_argument("--write", action="store_true", help="write V_99_Automated_Evidence.md with sanitized output")
    parser.add_argument("--timeout", type=float, default=120.0, help="per-command evidence timeout in seconds")
    args = parser.parse_args(argv)

    if args.evidence:
        if not args.horizon:
            parser.error("--evidence requires --horizon")
        payload = collect_evidence(args.horizon, args.timeout, args.write)
    else:
        payload = validate_horizons(args.horizon)

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"ok={payload['ok']}")
        if "checked" in payload:
            print(f"checked={payload['checked']}")
            for issue in payload["issues"]:
                print(f"ERROR: {issue}")
            for warning in payload["warnings"]:
                print(f"WARN: {warning}")
        else:
            for result in payload["commands"]:
                print(f"{result['returncode']} {result['elapsed_ms']}ms {result['command']}")
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
