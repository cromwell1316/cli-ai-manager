#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import base64
import argparse
import shlex
import subprocess
import shutil
import logging
from pathlib import Path
from datetime import datetime

from cli_profile_manager.credentials import agy as agy_credentials
from cli_profile_manager.credentials import claude as claude_credentials
from cli_profile_manager.credentials import codex as codex_credentials
from cli_profile_manager.credentials.common import (
    ensure_parent as core_ensure_parent,
    read_json_object as core_read_json_object,
    write_json_atomic as core_write_json_atomic,
    write_text_atomic as core_write_text_atomic,
)
from cli_profile_manager.metadata import (
    METADATA_DIR as CORE_METADATA_DIR,
    METADATA_PATH as CORE_METADATA_PATH,
    label_profile as core_label_profile,
    load_metadata as core_load_metadata,
    refresh_from_env as core_refresh_metadata_from_env,
    save_metadata as core_save_metadata,
)
from cli_profile_manager.paths import (
    DISPLAY_SLOT_COUNT as CORE_DISPLAY_SLOT_COUNT,
    TOOLS as CORE_TOOLS,
    agy_windows_credential_path as core_agy_windows_credential_path,
    credential_path as core_credential_path,
    find_windows_user as core_find_windows_user,
    first_free_profile as core_first_free_profile,
    get_display_profiles as core_get_display_profiles,
    get_occupied_profiles as core_get_occupied_profiles,
    is_valid_display_profile as core_is_valid_display_profile,
    make_tool_env as core_make_tool_env,
    normalize_credential_path as core_normalize_credential_path,
    parse_profile as core_parse_profile,
    profile_home as core_profile_home,
    refresh_from_env as core_refresh_paths_from_env,
    resolve_sync_bases as core_resolve_sync_bases,
)
from cli_profile_manager.quota import quota_payload as core_quota_payload
from cli_profile_manager.sync import (
    deletion_preflight_paths as core_deletion_preflight_paths,
    is_windows_agy_backup_name as core_is_windows_agy_backup_name,
    path_is_within as core_path_is_within,
    profile_number_from_dir_name as core_profile_number_from_dir_name,
    sync_agy_credentials_between_bases as core_sync_agy_credentials_between_bases,
    sync_profiles_between_bases,
)

core_refresh_paths_from_env()
core_refresh_metadata_from_env()

# Setup logging
log_file = os.path.join(Path(__file__).resolve().parents[1], "ai-man.log")
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Base configuration paths
METADATA_DIR = CORE_METADATA_DIR
METADATA_PATH = CORE_METADATA_PATH
DISPLAY_SLOT_COUNT = CORE_DISPLAY_SLOT_COUNT
EXIT_OK = 0
EXIT_USAGE = 2
EXIT_NOT_FOUND = 3
EXIT_NO_TOKEN = 4
EXIT_RUNTIME = 5
AGY_WINDOWS_TARGET = "gemini:antigravity"
AGY_WINDOWS_USERNAME = "antigravity"

# Tool configurations
TOOLS = CORE_TOOLS

# ANSI Colors
CLR_RESET = "\033[0m"
CLR_BOLD = "\033[1m"
CLR_RED = "\033[31m"
CLR_GREEN = "\033[32m"
CLR_YELLOW = "\033[33m"
CLR_BLUE = "\033[34m"
CLR_MAGENTA = "\033[35m"
CLR_CYAN = "\033[36m"
CLR_WHITE = "\033[37m"
CLR_BG_CYAN = "\033[46m"
CLR_BLACK_TEXT = "\033[30m"

def load_metadata():
    return core_load_metadata()

def save_metadata(data):
    try:
        core_save_metadata(data)
    except Exception as e:
        print(f"Error saving metadata: {e}")

def get_profiles(tool_key):
    return get_occupied_profiles(tool_key)

def get_occupied_profiles(tool_key):
    return core_get_occupied_profiles(tool_key)

def get_display_profiles(tool_key):
    return core_get_display_profiles(tool_key)

def first_free_profile(tool_key):
    return core_first_free_profile(tool_key)

def parse_profile(value):
    return core_parse_profile(value)

def is_valid_display_profile(tool_key, n):
    return core_is_valid_display_profile(tool_key, n)

def ensure_parent(path):
    return core_ensure_parent(path)

def normalize_credential_path(tool_key, cred_file):
    return core_normalize_credential_path(tool_key, cred_file)

def profile_home(tool_key, n):
    return core_profile_home(tool_key, n)

def credential_path(tool_key, n):
    return core_credential_path(tool_key, n)

def agy_windows_credential_path(n, base_dir=None):
    return core_agy_windows_credential_path(n, base_dir)

def make_tool_env(tool_key, n):
    return core_make_tool_env(tool_key, n)

def write_text_atomic(path, content):
    return core_write_text_atomic(path, content)

def write_json_atomic(path, data):
    return core_write_json_atomic(path, data)

def read_json_object(path, encoding="utf-8"):
    return core_read_json_object(path, encoding)

def account_email_from_google_accounts(profile_home):
    return agy_credentials.account_email_from_google_accounts(profile_home, TOOLS["agy"]["acct_file"])

def decode_windows_agy_credential(win_cred_path):
    return agy_credentials.decode_windows_credential(win_cred_path)

def read_wsl_agy_oauth(token_path):
    return agy_credentials.read_wsl_oauth(token_path)

def build_windows_agy_credential(token_data, account=None):
    return agy_credentials.build_windows_credential(token_data, account)

def import_windows_agy_credential(win_cred_path, profile_num):
    dest_home = profile_home("agy", profile_num)
    dest_file = credential_path("agy", profile_num)
    return agy_credentials.import_windows_credential(
        win_cred_path,
        dest_home,
        dest_file,
        TOOLS["agy"]["acct_file"],
    )

def export_wsl_agy_credential(profile_num, win_cred_path):
    home = profile_home("agy", profile_num)
    return agy_credentials.export_wsl_credential(
        credential_path("agy", profile_num),
        home,
        win_cred_path,
        TOOLS["agy"]["acct_file"],
    )

def generate_win_cred_from_linux_token(token_path, win_cred_path, profile_home, tool):
    try:
        token_data = read_wsl_agy_oauth(token_path)
        if not token_data:
            return False

        # Try to find email
        email = account_email_from_google_accounts(profile_home) or "logged in"

        if email in ("(no login)", "logged in"):
            log_dir = os.path.join(profile_home, ".gemini", "antigravity-cli", "log")
            if os.path.exists(log_dir):
                try:
                    for log_file in sorted(os.listdir(log_dir), reverse=True):
                        if log_file.startswith("cli-") and log_file.endswith(".log"):
                            log_path = os.path.join(log_dir, log_file)
                            with open(log_path, "r", errors="ignore") as lf:
                                for line in lf:
                                    if "email=" in line:
                                        parts = line.split("email=")
                                        if len(parts) > 1:
                                            email = parts[1].split()[0].strip().rstrip(",")
                                            break
                        if email not in ("(no login)", "logged in"):
                            break
                except Exception:
                    pass

        write_json_atomic(win_cred_path, build_windows_agy_credential(token_data, email))

        logging.info(f"Generated Windows credential {win_cred_path} for account {email}")
        return True
    except Exception as e:
        logging.error(f"Failed to generate Windows cred from Linux token: {e}")
        return False

def get_profile_status(tool_key, n, metadata):
    tool = TOOLS[tool_key]
    profile_home = os.path.join(tool["base_dir"], f"p{n}")
    cred_path = os.path.join(profile_home, tool["cred_file"])

    email = "(no login)"
    has_token = False
    token_state = "missing"
    credential_source = None
    account = None
    warnings = []

    if tool_key == "agy":
        if os.name == "nt":
            win_cred_path = agy_windows_credential_path(n, tool["base_dir"])
            if os.path.exists(win_cred_path):
                try:
                    _, account = decode_windows_agy_credential(win_cred_path)
                    has_token = True
                    token_state = "valid"
                    credential_source = "windows-backup"
                    email = account or account_email_from_google_accounts(profile_home) or "logged in"
                except Exception as e:
                    token_state = "invalid"
                    credential_source = "windows-backup"
                    warnings.append(str(e))
                    email = f"invalid token: {e}"
        elif os.path.exists(cred_path):
            try:
                read_wsl_agy_oauth(cred_path)
                has_token = True
                token_state = "valid"
                credential_source = "wsl-oauth"
                account = account_email_from_google_accounts(profile_home)
                email = account_email_from_google_accounts(profile_home) or "logged in"
            except Exception as e:
                token_state = "invalid"
                credential_source = "wsl-oauth"
                warnings.append(str(e))
                email = f"invalid token: {e}"
        else:
            read_agy_cli_token = getattr(agy_credentials, "read_agy_cli_token", None)
            if read_agy_cli_token is not None:
                try:
                    read_agy_cli_token(profile_home)
                    has_token = True
                    token_state = "valid"
                    credential_source = "agy-cli-token"
                    account = account_email_from_google_accounts(profile_home)
                    email = account or "logged in"
                except FileNotFoundError:
                    pass
                except Exception as e:
                    token_state = "invalid"
                    credential_source = "agy-cli-token"
                    warnings.append(str(e))
                    email = f"invalid token: {e}"
    elif os.path.exists(cred_path):
        has_token = True
        token_state = "present"
        credential_source = "codex-auth" if tool_key == "codex" else "claude-credentials"

    if tool_key == "codex":
        if has_token:
            try:
                email = codex_credentials.account_from_auth(cred_path)
                token_state = "valid"
                account = email
            except Exception as e:
                token_state = "invalid"
                warnings.append(str(e))
                email = "logged in"

    elif tool_key == "claude":
        if has_token:
            try:
                email = claude_credentials.account_summary(cred_path)
                token_state = "valid"
                account = email
            except Exception as e:
                token_state = "invalid"
                warnings.append(str(e))
                email = "Logged in"

    label = metadata.get(tool_key, {}).get(f"p{n}", {}).get("label", "")
    return {
        "num": n,
        "profile": f"p{n}",
        "email": email,
        "has_token": has_token,
        "token_state": token_state,
        "credential_source": credential_source,
        "account": account or (email if has_token and not email.startswith("invalid token:") else None),
        "warnings": warnings,
        "label": label,
        "home": profile_home
    }

def status_payload(tool_key, n, metadata=None):
    metadata = metadata if metadata is not None else load_metadata()
    status = get_profile_status(tool_key, n, metadata)
    status["exists"] = n in get_occupied_profiles(tool_key)
    return status

def quota_payload(tool_key, n, timeout_seconds=None):
    tool = TOOLS[tool_key]
    home = profile_home(tool_key, n)
    command = [tool["cmd"]]
    timeout = timeout_seconds if timeout_seconds is not None else 20
    return core_quota_payload(
        tool_key,
        f"p{n}",
        command,
        make_tool_env(tool_key, n),
        home,
        timeout_seconds=timeout,
    )

def status_payload_with_quota(tool_key, n, metadata=None, timeout_seconds=None):
    status = status_payload(tool_key, n, metadata)
    if status["has_token"]:
        status["quota"] = quota_payload(tool_key, n, timeout_seconds)["quota"]
    else:
        status["quota"] = {
            "state": "no_token",
            "limits": {},
            "warnings": ["profile has no token"],
        }
    return status

def print_error(message):
    print(f"Error: {message}", file=sys.stderr)

def print_json_payload(payload):
    print(json.dumps(payload, indent=2))

def print_json_error(message, code, error_type="runtime_error"):
    print_json_payload({
        "ok": False,
        "error": {
            "type": error_type,
            "message": str(message),
            "code": code,
        },
    })

def quota_summary(status):
    quota = status.get("quota")
    if not quota:
        return ""
    state = quota.get("state", "unknown")
    if state != "available":
        return state
    current_limit = quota.get("current_limit")
    if current_limit:
        data = quota.get("limits", {}).get(current_limit, {})
        value = data.get("percent_left", data.get("percent"))
        if value is not None:
            model = data.get("model", current_limit)
            return f"{model}:{value:g}%"
    parts = []
    for name, data in quota.get("limits", {}).items():
        value = data.get("percent_left", data.get("percent"))
        if value is not None:
            label = data.get("model", name)
            parts.append(f"{label}:{value:g}%")
    return ", ".join(parts) or state

def print_status_table(tool_key, statuses):
    has_quota = any("quota" in status for status in statuses)
    quota_header = f" {'Quota':<24}" if has_quota else ""
    print(f"{'Profile':<8} {'Account':<32} {'Token':<8} {'Label':<16}{quota_header} Home")
    print("-" * (121 if has_quota else 96))
    for status in statuses:
        token = status.get("token_state") or ("yes" if status["has_token"] else "no")
        label = status["label"] or ""
        quota = f" {quota_summary(status):<24}" if has_quota else ""
        print(f"{status['profile']:<8} {status['email']:<32} {token:<8} {label:<16}{quota} {status['home']}")

def cmd_list(args):
    metadata = load_metadata()
    profiles = get_display_profiles(args.tool)
    if args.quota:
        statuses = [status_payload_with_quota(args.tool, n, metadata, args.timeout) for n in profiles]
    else:
        statuses = [status_payload(args.tool, n, metadata) for n in profiles]
    payload = {
        "tool": args.tool,
        "next_profile": f"p{first_free_profile(args.tool)}",
        "profiles": statuses,
    }
    if args.json:
        print_json_payload(payload)
    else:
        print(f"{TOOLS[args.tool]['name']}")
        print(f"Next profile: {payload['next_profile']}")
        print_status_table(args.tool, statuses)
    return EXIT_OK

def cmd_status(args):
    try:
        n = parse_profile(args.profile)
    except ValueError as e:
        if args.json:
            print_json_error(str(e), EXIT_USAGE, "usage_error")
        else:
            print_error(str(e))
        return EXIT_USAGE
    if args.quota:
        status = status_payload_with_quota(args.tool, n, timeout_seconds=args.timeout)
    else:
        status = status_payload(args.tool, n)
    if args.json:
        print_json_payload(status)
    else:
        print_status_table(args.tool, [status])
    return EXIT_OK

def cmd_quota(args):
    try:
        n = parse_profile(args.profile)
    except ValueError as e:
        if args.json:
            print_json_error(str(e), EXIT_USAGE, "usage_error")
        else:
            print_error(str(e))
        return EXIT_USAGE
    status = status_payload(args.tool, n)
    if not status["has_token"]:
        message = f"profile p{n} has no token; use login or import first"
        if args.json:
            print_json_error(message, EXIT_NO_TOKEN, "no_token")
        else:
            print_error(message)
        return EXIT_NO_TOKEN
    payload = quota_payload(args.tool, n, args.timeout)
    if args.json:
        print_json_payload(payload)
    else:
        state = payload["quota"].get("state", "unknown")
        print(f"{args.tool} p{n} quota: {quota_summary({'quota': payload['quota']}) or state}")
        for warning in payload["quota"].get("warnings", []):
            print(f"warning: {warning}")
    return EXIT_OK

def run_cli_tool(tool_key, n, extra_args=None):
    tool = TOOLS[tool_key]
    extra_args = extra_args or []
    if os.name == "nt" and tool_key == "agy":
        switcher = os.path.join(tool["base_dir"], "agy-multiaccount.ps1")
        if not os.path.exists(switcher):
            print_error(f"Windows agy launch requires Credential Manager switcher: {switcher}")
            return EXIT_NOT_FOUND
        powershell = shutil.which("powershell.exe") or shutil.which("powershell")
        if powershell is None:
            print_error("PowerShell is required for Windows agy Credential Manager switching")
            return EXIT_NOT_FOUND
        os.makedirs(profile_home(tool_key, n), exist_ok=True)
        quoted_args = " ".join(shlex.quote(arg) for arg in extra_args)
        command = (
            f"& {shlex.quote(switcher)} Set-AgyCred {n}; "
            f"$env:USERPROFILE={shlex.quote(profile_home(tool_key, n))}; "
            f"$env:HOME=$env:USERPROFILE; "
            f"& {shlex.quote(tool['cmd'])}"
        )
        if quoted_args:
            command = f"{command} {quoted_args}"
        completed = subprocess.run([powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command])
        return completed.returncode

    if shutil.which(tool["cmd"]) is None:
        print_error(f"{tool['cmd']} CLI is not installed or not in PATH")
        return EXIT_NOT_FOUND
    os.makedirs(profile_home(tool_key, n), exist_ok=True)
    cmd = [tool["cmd"]] + extra_args
    logging.info(f"Launching {tool_key} profile p{n}: {' '.join(cmd)}")
    try:
        completed = subprocess.run(cmd, env=make_tool_env(tool_key, n))
        return completed.returncode
    except KeyboardInterrupt:
        return 130

def cmd_launch(args):
    try:
        n = parse_profile(args.profile)
    except ValueError as e:
        if args.json:
            print_json_error(str(e), EXIT_USAGE, "usage_error")
        else:
            print_error(str(e))
        return EXIT_USAGE
    dry_payload = {
        "ok": True,
        "tool": args.tool,
        "profile": f"p{n}",
        "platform": args.platform,
        "home": profile_home(args.tool, n),
        "command": [TOOLS[args.tool]["cmd"]] + (args.args or []),
        "environment": {TOOLS[args.tool]["env_var"]: profile_home(args.tool, n)},
    }
    if args.tool == "agy":
        dry_payload["environment"]["HOME"] = profile_home(args.tool, n)
    if not is_valid_display_profile(args.tool, n):
        message = f"profile p{n} does not exist and is outside visible slots"
        if args.json:
            print_json_error(message, EXIT_USAGE, "usage_error")
        else:
            print_error(message)
        return EXIT_USAGE
    status = status_payload(args.tool, n)
    dry_payload["status"] = status
    dry_payload["would_launch"] = status["has_token"]
    if args.dry_run:
        print_json_payload(dry_payload) if args.json else print(" ".join(shlex.quote(part) for part in dry_payload["command"]))
        return EXIT_OK
    if not status["has_token"]:
        message = f"profile p{n} has no token; use login or import first"
        if args.json:
            print_json_error(message, EXIT_NO_TOKEN, "no_token")
        else:
            print_error(message)
        return EXIT_NO_TOKEN
    return run_cli_tool(args.tool, n, args.args)

def cmd_login(args):
    try:
        n = parse_profile(args.profile) if args.profile else first_free_profile(args.tool)
    except ValueError as e:
        print_error(str(e))
        return EXIT_USAGE
    return run_cli_tool(args.tool, n, [])

def import_credential_file(tool_key, cred_file, profile_num=None):
    tool = TOOLS[tool_key]
    source = normalize_credential_path(tool_key, cred_file)
    if not os.path.exists(source):
        raise FileNotFoundError(f"file '{source}' not found")
    n = profile_num if profile_num is not None else first_free_profile(tool_key)
    if n <= 0:
        raise ValueError("profile number must be positive")
    dest_dir = profile_home(tool_key, n)
    dest_file = credential_path(tool_key, n)
    if tool_key == "agy":
        dest_file = import_windows_agy_credential(source, n)
    else:
        ensure_parent(dest_file)
        tmp_path = f"{dest_file}.tmp-{os.getpid()}"
        shutil.copy2(source, tmp_path)
        os.replace(tmp_path, dest_file)
    return n, dest_file

def cmd_import(args):
    try:
        n = parse_profile(args.profile) if args.profile else None
    except ValueError as e:
        if args.json:
            print_json_error(str(e), EXIT_USAGE, "usage_error")
        else:
            print_error(str(e))
        return EXIT_USAGE
    if args.dry_run:
        try:
            source = normalize_credential_path(args.tool, args.path)
            if not os.path.exists(source):
                raise FileNotFoundError(f"file '{source}' not found")
            import_num = n if n is not None else first_free_profile(args.tool)
            if import_num <= 0:
                raise ValueError("profile number must be positive")
            if args.tool == "agy":
                decode_windows_agy_credential(source)
            dest_file = credential_path(args.tool, import_num)
        except FileNotFoundError as e:
            if args.json:
                print_json_error(str(e), EXIT_NOT_FOUND, "not_found")
            else:
                print_error(str(e))
            return EXIT_NOT_FOUND
        except ValueError as e:
            if args.json:
                print_json_error(str(e), EXIT_USAGE, "usage_error")
            else:
                print_error(str(e))
            return EXIT_USAGE
        except Exception as e:
            if args.json:
                print_json_error(f"import dry-run failed: {e}", EXIT_RUNTIME, "runtime_error")
            else:
                print_error(f"import dry-run failed: {e}")
            return EXIT_RUNTIME
        payload = {
            "ok": True,
            "dry_run": True,
            "tool": args.tool,
            "profile": f"p{import_num}",
            "source": source,
            "destination": dest_file,
            "would_import": True,
        }
        if args.json:
            print_json_payload(payload)
        else:
            print(f"Would import {args.tool} credential into p{import_num}: {dest_file}")
        return EXIT_OK
    try:
        imported_num, dest_file = import_credential_file(args.tool, args.path, n)
    except FileNotFoundError as e:
        if args.json:
            print_json_error(str(e), EXIT_NOT_FOUND, "not_found")
        else:
            print_error(str(e))
        return EXIT_NOT_FOUND
    except Exception as e:
        if args.json:
            print_json_error(f"import failed: {e}", EXIT_RUNTIME, "runtime_error")
        else:
            print_error(f"import failed: {e}")
        return EXIT_RUNTIME
    if args.json:
        print_json_payload({
            "ok": True,
            "tool": args.tool,
            "profile": f"p{imported_num}",
        "destination": dest_file,
    })
    else:
        print(f"Imported {args.tool} credential into p{imported_num}: {dest_file}")
    return EXIT_OK

def find_windows_user():
    return core_find_windows_user()


def default_export_dir():
    win_user = find_windows_user()
    for candidate in (
        f"/mnt/c/Users/{win_user}/Downloads",
        f"/mnt/c/Users/{win_user}/Desktop",
        "/mnt/c",
    ):
        if os.path.exists(candidate):
            return candidate
    return os.getcwd()

def resolve_export_destination(tool_key, profile_num, to_path=None):
    if to_path:
        to_path = os.path.expanduser(to_path)
        if os.path.isdir(to_path):
            export_dir = to_path
            dest_file = None
        else:
            export_dir = os.path.dirname(to_path) or "."
            dest_file = to_path
    else:
        export_dir = default_export_dir()
        dest_file = None
    if dest_file is None:
        if tool_key == "agy":
            dest_file = os.path.join(export_dir, f"cred-p{profile_num}-exported.json")
        else:
            dest_file = os.path.join(export_dir, f"{tool_key}-p{profile_num}-exported.json")
    return export_dir, dest_file

def export_credential_file(tool_key, profile_num, to_path=None):
    status = status_payload(tool_key, profile_num)
    if not status["has_token"]:
        raise PermissionError(f"profile p{profile_num} has no token to export")
    src_file = credential_path(tool_key, profile_num)
    export_dir, dest_file = resolve_export_destination(tool_key, profile_num, to_path)
    os.makedirs(export_dir, exist_ok=True)
    if tool_key == "agy":
        export_wsl_agy_credential(profile_num, dest_file)
    else:
        ensure_parent(dest_file)
        tmp_path = f"{dest_file}.tmp-{os.getpid()}"
        shutil.copy2(src_file, tmp_path)
        os.replace(tmp_path, dest_file)
    return dest_file

def cmd_export(args):
    try:
        n = parse_profile(args.profile)
        if args.dry_run:
            status = status_payload(args.tool, n)
            if not status["has_token"]:
                raise PermissionError(f"profile p{n} has no token to export")
            _, dest_file = resolve_export_destination(args.tool, n, args.to)
            payload = {
                "ok": True,
                "dry_run": True,
                "tool": args.tool,
                "profile": f"p{n}",
                "source": credential_path(args.tool, n),
                "destination": dest_file,
                "would_export": True,
            }
            if args.json:
                print_json_payload(payload)
            else:
                print(f"Would export {args.tool} p{n}: {dest_file}")
            return EXIT_OK
        dest_file = export_credential_file(args.tool, n, args.to)
    except ValueError as e:
        if args.json:
            print_json_error(str(e), EXIT_USAGE, "usage_error")
        else:
            print_error(str(e))
        return EXIT_USAGE
    except PermissionError as e:
        if args.json:
            print_json_error(str(e), EXIT_NO_TOKEN, "no_token")
        else:
            print_error(str(e))
        return EXIT_NO_TOKEN
    except Exception as e:
        if args.json:
            print_json_error(f"export failed: {e}", EXIT_RUNTIME, "runtime_error")
        else:
            print_error(f"export failed: {e}")
        return EXIT_RUNTIME
    if args.json:
        print_json_payload({
            "ok": True,
            "tool": args.tool,
            "profile": f"p{n}",
            "destination": dest_file,
        })
    else:
        print(f"Exported {args.tool} p{n}: {dest_file}")
    return EXIT_OK

def label_profile(tool_key, profile_num, label):
    core_label_profile(tool_key, profile_num, label)

def cmd_label(args):
    try:
        n = parse_profile(args.profile)
    except ValueError as e:
        print_error(str(e))
        return EXIT_USAGE
    label_profile(args.tool, n, args.label)
    print(f"Label set for {args.tool} p{n}: {args.label}")
    return EXIT_OK

def cmd_clear(args):
    try:
        n = parse_profile(args.profile)
    except ValueError as e:
        print_error(str(e))
        return EXIT_USAGE
    home = profile_home(args.tool, n)
    if not args.yes:
        print_error(f"refusing to clear {home} without --yes")
        return EXIT_USAGE
    try:
        cleared_home = clear_profile_data(args.tool, n)
    except ValueError as e:
        print_error(str(e))
        return EXIT_USAGE
    print(f"Cleared {args.tool} p{n}: {cleared_home}")
    return EXIT_OK

def clear_profile_data(tool_key, n):
    home = profile_home(tool_key, n)
    base = os.path.abspath(TOOLS[tool_key]["base_dir"])
    target = os.path.abspath(home)
    if not target.startswith(base + os.sep):
        raise ValueError(f"refusing to clear unsafe path: {target}")
    if os.path.exists(home):
        shutil.rmtree(home)
    return home

def resolve_sync_bases(direction):
    return core_resolve_sync_bases(direction)

def count_files_under(path):
    total = 0
    if not path.exists():
        return total
    for _, _, files in os.walk(path):
        total += len(files)
    return total

def profile_number_from_dir_name(name):
    return core_profile_number_from_dir_name(name)

def is_windows_agy_backup_name(name):
    return core_is_windows_agy_backup_name(name)

def path_is_within(child, parent):
    return core_path_is_within(child, parent)

def deletion_preflight_paths(path):
    return core_deletion_preflight_paths(path)

def sync_agy_credentials_between_bases(src_base, dst_base, direction, dry_run=False):
    return core_sync_agy_credentials_between_bases(src_base, dst_base, direction, dry_run)

def sync_profiles_noninteractive(direction, mode, dry_run=False, yes=False):
    src_base, dst_base = resolve_sync_bases(direction)
    return sync_profiles_between_bases(src_base, dst_base, direction, mode, dry_run, yes)

def cmd_sync(args):
    try:
        result = sync_profiles_noninteractive(args.source, args.mode, args.dry_run, args.yes)
    except PermissionError as e:
        if args.json:
            print_json_error(str(e), EXIT_USAGE, "usage_error")
        else:
            print_error(str(e))
        return EXIT_USAGE
    except FileNotFoundError as e:
        if args.json:
            print_json_error(str(e), EXIT_NOT_FOUND, "not_found")
        else:
            print_error(str(e))
        return EXIT_NOT_FOUND
    except Exception as e:
        if args.json:
            print_json_error(f"sync failed: {e}", EXIT_RUNTIME, "runtime_error")
        else:
            print_error(f"sync failed: {e}")
        return EXIT_RUNTIME
    if args.json:
        print_json_payload(result)
        return EXIT_OK
    action = "Would update" if args.dry_run else "Updated"
    print(
        f"{action} {result['copied']} files, skipped {result['skipped']}, "
        f"converted {result['converted']} agy credentials, invalid {result['invalid']} "
        f"({args.source} -> {'windows' if args.source == 'wsl' else 'wsl'}, {args.mode}); "
        f"hard-delete preflight: {result['would_delete']} paths"
    )
    if result["delete_paths"]:
        print("Would delete:")
        for path in result["delete_paths"]:
            print(f"  {path}")
    return EXIT_OK

def build_parser():
    parser = argparse.ArgumentParser(
        prog="ai-man",
        description="Keyboard-first profile manager for agy, codex, and claude.",
    )
    sub = parser.add_subparsers(dest="command")

    list_p = sub.add_parser("list", help="list profiles for a tool")
    list_p.add_argument("tool", choices=TOOLS.keys())
    list_p.add_argument("--json", action="store_true")
    list_p.add_argument("--quota", action="store_true", help="probe each profile CLI through a PTY and include quota")
    list_p.add_argument("--timeout", type=float, default=20, help="quota probe timeout per profile in seconds")
    list_p.set_defaults(func=cmd_list)

    status_p = sub.add_parser("status", help="show one profile status")
    status_p.add_argument("tool", choices=TOOLS.keys())
    status_p.add_argument("profile")
    status_p.add_argument("--json", action="store_true")
    status_p.add_argument("--quota", action="store_true", help="probe the profile CLI through a PTY and include quota")
    status_p.add_argument("--timeout", type=float, default=20, help="quota probe timeout in seconds")
    status_p.set_defaults(func=cmd_status)

    quota_p = sub.add_parser("quota", help="probe one profile quota through its native CLI")
    quota_p.add_argument("tool", choices=TOOLS.keys())
    quota_p.add_argument("profile")
    quota_p.add_argument("--json", action="store_true")
    quota_p.add_argument("--timeout", type=float, default=20, help="quota probe timeout in seconds")
    quota_p.set_defaults(func=cmd_quota)

    launch_p = sub.add_parser("launch", help="launch a CLI under an existing profile")
    launch_p.add_argument("tool", choices=TOOLS.keys())
    launch_p.add_argument("profile")
    launch_p.add_argument("args", nargs=argparse.REMAINDER, help="arguments passed after -- to the target CLI")
    launch_p.add_argument("--dry-run", action="store_true", help="show launch plan without running the tool")
    launch_p.add_argument("--json", action="store_true")
    launch_p.add_argument("--platform", choices=("auto", "wsl", "windows"), default="auto")
    launch_p.set_defaults(func=cmd_launch)

    login_p = sub.add_parser("login", aliases=["add"], help="run native CLI login flow")
    login_p.add_argument("tool", choices=TOOLS.keys())
    login_p.add_argument("profile", nargs="?")
    login_p.set_defaults(func=cmd_login)

    import_p = sub.add_parser("import", help="import a credential file")
    import_p.add_argument("tool", choices=TOOLS.keys())
    import_p.add_argument("path")
    import_p.add_argument("profile", nargs="?")
    import_p.add_argument("--dry-run", action="store_true")
    import_p.add_argument("--json", action="store_true")
    import_p.set_defaults(func=cmd_import)

    export_p = sub.add_parser("export", help="export a profile credential")
    export_p.add_argument("tool", choices=TOOLS.keys())
    export_p.add_argument("profile")
    export_p.add_argument("--to")
    export_p.add_argument("--dry-run", action="store_true")
    export_p.add_argument("--json", action="store_true")
    export_p.set_defaults(func=cmd_export)

    label_p = sub.add_parser("label", help="set or clear a profile label")
    label_p.add_argument("tool", choices=TOOLS.keys())
    label_p.add_argument("profile")
    label_p.add_argument("label")
    label_p.set_defaults(func=cmd_label)

    clear_p = sub.add_parser("clear", help="delete a profile directory")
    clear_p.add_argument("tool", choices=TOOLS.keys())
    clear_p.add_argument("profile")
    clear_p.add_argument("--yes", action="store_true", help="confirm profile deletion")
    clear_p.set_defaults(func=cmd_clear)

    sync_p = sub.add_parser("sync", help="sync profile directories between WSL and Windows")
    sync_p.add_argument("--from", dest="source", choices=("wsl", "windows"), default="wsl")
    sync_p.add_argument("--mode", choices=("soft", "hard"), default="soft")
    sync_p.add_argument("--dry-run", action="store_true")
    sync_p.add_argument("--yes", action="store_true", help="confirm hard sync")
    sync_p.add_argument("--json", action="store_true")
    sync_p.set_defaults(func=cmd_sync)

    return parser

def normalize_launch_argv(argv):
    if not argv or argv[0] != "launch" or "--" in argv[:1]:
        return argv
    if len(argv) < 4:
        return argv
    try:
        passthrough_index = argv.index("--")
    except ValueError:
        passthrough_index = len(argv)

    head = argv[1:passthrough_index]
    tail = argv[passthrough_index:]
    if len(head) < 2:
        return argv

    tool = head[0]
    profile = head[1]
    rest = head[2:]
    launch_flags = []
    passthrough_before_separator = []
    idx = 0
    while idx < len(rest):
        item = rest[idx]
        if item in ("--dry-run", "--json"):
            launch_flags.append(item)
            idx += 1
        elif item == "--platform" and idx + 1 < len(rest):
            launch_flags.extend([item, rest[idx + 1]])
            idx += 2
        else:
            passthrough_before_separator.extend(rest[idx:])
            break
    if passthrough_before_separator and not tail:
        tail = ["--"] + passthrough_before_separator

    return ["launch"] + launch_flags + [tool, profile] + tail

def run_cli(argv):
    argv = normalize_launch_argv(argv)
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        return None
    if getattr(args, "args", None) and args.args[:1] == ["--"]:
        args.args = args.args[1:]
    return args.func(args)

def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    result = run_cli(argv)
    if result is not None:
        return result

    from cli_profile_manager.interactive import run_interactive_main

    return run_interactive_main()

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        from cli_profile_manager.interactive import clear_screen

        clear_screen()
        sys.exit(0)
