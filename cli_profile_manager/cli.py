#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import argparse
import re

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

core_refresh_paths_from_env()
core_refresh_metadata_from_env()

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
SERVICE_ENV_TRUE = ("1", "true", "yes", "on")
SERVICE_MUTATING_COMMANDS = {"audit", "clear", "export", "import", "label", "login", "sync"}
agy_credentials = None
claude_credentials = None
codex_credentials = None
core_quota_payload = None
run_persistent_cli_quota_snapshot = None
core_credentials_common = None
core_sync = None
core_logging = None
core_shutil = None
core_shlex = None
core_subprocess = None
core_runtime_service = None
core_audit = None
core_safety = None

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
ANSI_RE = re.compile(
    r"(?:\x1b\[[0-?]*[ -/]*[@-~]|\x1b\][^\x07]*(?:\x07|\x1b\\)|\x1b[@-_])"
)

def _logging():
    global core_logging
    if core_logging is None:
        import logging
        from pathlib import Path

        log_file = os.path.join(Path(__file__).resolve().parents[1], "ai-man.log")
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        core_logging = logging
    return core_logging

def _shutil():
    global core_shutil
    if core_shutil is None:
        import shutil

        core_shutil = shutil
    return core_shutil

def _shlex():
    global core_shlex
    if core_shlex is None:
        import shlex

        core_shlex = shlex
    return core_shlex

def _subprocess():
    global core_subprocess
    if core_subprocess is None:
        import subprocess

        core_subprocess = subprocess
    return core_subprocess

def _runtime_service():
    global core_runtime_service
    if core_runtime_service is None:
        from cli_profile_manager import runtime_service as module

        core_runtime_service = module
    return core_runtime_service

def _agy_credentials():
    global agy_credentials
    if agy_credentials is None:
        from cli_profile_manager.credentials import agy as module

        agy_credentials = module
    return agy_credentials

def _claude_credentials():
    global claude_credentials
    if claude_credentials is None:
        from cli_profile_manager.credentials import claude as module

        claude_credentials = module
    return claude_credentials

def _codex_credentials():
    global codex_credentials
    if codex_credentials is None:
        from cli_profile_manager.credentials import codex as module

        codex_credentials = module
    return codex_credentials

def _quota_payload_func():
    global core_quota_payload
    if core_quota_payload is None:
        from cli_profile_manager.quota import quota_payload as func

        core_quota_payload = func
    return core_quota_payload

def _persistent_quota_runner():
    global run_persistent_cli_quota_snapshot
    if run_persistent_cli_quota_snapshot is None:
        from cli_profile_manager.quota import run_persistent_cli_quota_snapshot as func

        run_persistent_cli_quota_snapshot = func
    return run_persistent_cli_quota_snapshot

def _credentials_common():
    global core_credentials_common
    if core_credentials_common is None:
        from cli_profile_manager.credentials import common as module

        core_credentials_common = module
    return core_credentials_common

def _sync_module():
    global core_sync
    if core_sync is None:
        from cli_profile_manager import sync as module

        core_sync = module
    return core_sync

def _process_policy():
    from cli_profile_manager import process_policy as module

    return module

def _audit():
    global core_audit
    if core_audit is None:
        from cli_profile_manager import audit as module

        core_audit = module
    return core_audit

def _safety():
    global core_safety
    if core_safety is None:
        from cli_profile_manager import safety as module

        core_safety = module
    return core_safety

def safety_decision(operation, command=None, tool=None, profile=None, target=None, facts=None, yes=False, dry_run=False):
    descriptor = _safety().operation_descriptor(
        operation,
        command=command,
        tool=tool,
        profile=profile,
        target=target,
        facts=facts,
    )
    decision = _safety().evaluate(descriptor, yes=yes, dry_run=dry_run)
    _safety().audit_decision(_audit(), decision)
    return decision

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
    return _credentials_common().ensure_parent(path)

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
    return _credentials_common().write_text_atomic(path, content)

def write_json_atomic(path, data):
    return _credentials_common().write_json_atomic(path, data)

def read_json_object(path, encoding="utf-8"):
    return _credentials_common().read_json_object(path, encoding)

def account_email_from_google_accounts(profile_home):
    return _agy_credentials().account_email_from_profile(profile_home, TOOLS["agy"]["acct_file"])

def decode_windows_agy_credential(win_cred_path):
    return _agy_credentials().decode_windows_credential(win_cred_path)

def read_wsl_agy_oauth(token_path):
    return _agy_credentials().read_wsl_oauth(token_path)

def build_windows_agy_credential(token_data, account=None):
    return _agy_credentials().build_windows_credential(token_data, account)

def import_windows_agy_credential(win_cred_path, profile_num):
    dest_home = profile_home("agy", profile_num)
    dest_file = credential_path("agy", profile_num)
    return _agy_credentials().import_windows_credential(
        win_cred_path,
        dest_home,
        dest_file,
        TOOLS["agy"]["acct_file"],
    )

def export_wsl_agy_credential(profile_num, win_cred_path):
    home = profile_home("agy", profile_num)
    return _agy_credentials().export_wsl_credential(
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

        email = account_email_from_google_accounts(profile_home) or "logged in"

        write_json_atomic(win_cred_path, build_windows_agy_credential(token_data, email))

        _logging().info(f"Generated Windows credential {win_cred_path} for account {email}")
        return True
    except Exception as e:
        _logging().error(f"Failed to generate Windows cred from Linux token: {e}")
        return False


class CommandSnapshot:
    def __init__(self, metadata=None):
        self.metadata = load_metadata() if metadata is None else metadata
        self.occupied_by_tool = {}
        self.display_by_tool = {}
        self.status_by_profile = {}
        self.account_by_profile = {}

    def occupied_profiles(self, tool_key):
        if tool_key not in self.occupied_by_tool:
            self.occupied_by_tool[tool_key] = core_get_occupied_profiles(tool_key)
        return self.occupied_by_tool[tool_key]

    def display_profiles(self, tool_key):
        if tool_key not in self.display_by_tool:
            profiles = set(self.occupied_profiles(tool_key))
            profiles.update(range(1, DISPLAY_SLOT_COUNT + 1))
            self.display_by_tool[tool_key] = sorted(profiles)
        return self.display_by_tool[tool_key]

    def first_free_profile(self, tool_key):
        occupied = set(self.occupied_profiles(tool_key))
        n = 1
        while n in occupied:
            n += 1
        return n

    def account_email(self, tool_key, n, home):
        key = (tool_key, n)
        if key not in self.account_by_profile:
            self.account_by_profile[key] = (
                account_email_from_google_accounts(home) if tool_key == "agy" else None
            )
        return self.account_by_profile[key]

    def status(self, tool_key, n):
        key = (tool_key, n)
        if key not in self.status_by_profile:
            self.status_by_profile[key] = _status_payload(
                tool_key,
                n,
                self.metadata,
                occupied_profiles=self.occupied_profiles(tool_key),
                account_email_provider=lambda home, _tool=tool_key, _n=n: self.account_email(_tool, _n, home),
            )
        return self.status_by_profile[key]

    def status_with_quota(self, tool_key, n, timeout_seconds=None):
        status = dict(self.status(tool_key, n))
        if status["has_token"]:
            status["quota"] = quota_payload(tool_key, n, timeout_seconds)["quota"]
        else:
            status["quota"] = {
                "state": "no_token",
                "limits": {},
                "warnings": ["profile has no token"],
            }
        return status


def command_snapshot():
    return CommandSnapshot()


def get_profile_status(tool_key, n, metadata, account_email_provider=None):
    tool = TOOLS[tool_key]
    profile_home = os.path.join(tool["base_dir"], f"p{n}")
    cred_path = os.path.join(profile_home, tool["cred_file"])
    account_lookup = account_email_provider or account_email_from_google_accounts

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
                    email = account or account_lookup(profile_home) or "logged in"
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
                account = account_lookup(profile_home)
                email = account or "logged in"
            except Exception as e:
                token_state = "invalid"
                credential_source = "wsl-oauth"
                warnings.append(str(e))
                email = f"invalid token: {e}"
        else:
            read_agy_cli_token = getattr(_agy_credentials(), "read_agy_cli_token", None)
            if read_agy_cli_token is not None:
                try:
                    read_agy_cli_token(profile_home)
                    has_token = True
                    token_state = "valid"
                    credential_source = "agy-cli-token"
                    account = account_lookup(profile_home)
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
                email = _codex_credentials().account_from_auth(cred_path)
                token_state = "valid"
                account = email
            except Exception as e:
                token_state = "invalid"
                warnings.append(str(e))
                email = "logged in"

    elif tool_key == "claude":
        if has_token:
            try:
                email = _claude_credentials().account_summary(cred_path)
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

def _status_payload(tool_key, n, metadata, occupied_profiles=None, account_email_provider=None):
    occupied_profiles = get_occupied_profiles(tool_key) if occupied_profiles is None else occupied_profiles
    status = get_profile_status(tool_key, n, metadata, account_email_provider=account_email_provider)
    status["exists"] = n in occupied_profiles
    return status


def status_payload(tool_key, n, metadata=None, snapshot=None):
    if snapshot is not None:
        return snapshot.status(tool_key, n)
    metadata = metadata if metadata is not None else load_metadata()
    return _status_payload(tool_key, n, metadata)

def quota_payload(tool_key, n, timeout_seconds=None, runner=None):
    tool = TOOLS[tool_key]
    home = profile_home(tool_key, n)
    command = [tool["cmd"]]
    timeout = timeout_seconds if timeout_seconds is not None else 20
    kwargs = {"timeout_seconds": timeout}
    if runner is None:
        runner = _persistent_quota_runner()
    if runner is not None:
        kwargs["runner"] = runner
    try:
        return _quota_payload_func()(
            tool_key,
            f"p{n}",
            command,
            make_tool_env(tool_key, n),
            home,
            **kwargs,
        )
    except TypeError as e:
        if "unexpected keyword argument 'runner'" not in str(e):
            raise
        kwargs.pop("runner", None)
        return _quota_payload_func()(
            tool_key,
            f"p{n}",
            command,
            make_tool_env(tool_key, n),
            home,
            **kwargs,
        )

def status_payload_with_quota(tool_key, n, metadata=None, timeout_seconds=None, snapshot=None):
    if snapshot is not None:
        return snapshot.status_with_quota(tool_key, n, timeout_seconds)
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

def audit_context_from_argv(argv):
    command = argv[0] if argv else None
    tool = None
    profile = None
    if command in ("list", "status", "quota", "launch", "login", "import", "export", "label", "clear"):
        if len(argv) > 1:
            tool = argv[1]
        if command in ("status", "quota", "launch", "export", "label", "clear") and len(argv) > 2:
            profile = argv[2]
        elif command == "login" and len(argv) > 2:
            profile = argv[2]
        elif command == "import" and len(argv) > 3:
            profile = argv[3]
    return {"command": command, "tool": tool, "profile": profile}

def diagnostics_payload(*args, **kwargs):
    from cli_profile_manager.diagnostics import diagnostics_payload as func

    return func(*args, **kwargs)

def visible_len(text):
    return len(ANSI_RE.sub("", str(text)))

def plain_fit(text, width):
    text = str(text)
    if width <= 0:
        return ""
    length = visible_len(text)
    if length <= width:
        return text + (" " * (width - length))
    plain = ANSI_RE.sub("", text)
    if width <= 3:
        return plain[:width]
    return plain[:width - 3] + "..."

def quota_summary(status):
    quota = status.get("quota")
    if not quota:
        return ""
    state = quota.get("state", "unknown")
    if state != "available":
        return state
    if quota.get("source_command") == "/usage":
        agy = agy_quota_summary(quota)
        if agy:
            return agy
    labels = {
        "five_hour": "5h",
        "weekly": "week",
        "daily": "day",
        "local_messages": "local",
        "cloud_tasks": "cloud",
        "requests": "req",
        "messages": "msg",
        "tasks": "tasks",
        "tokens": "tokens",
        "context": "ctx",
        "usage": "usage",
    }
    current_limit = quota.get("current_limit")
    if current_limit:
        data = quota.get("limits", {}).get(current_limit, {})
        value = data.get("percent_left", data.get("percent"))
        if value is not None:
            model = labels.get(current_limit, data.get("model", current_limit))
            return f"{model}:{value:g}%"
    parts = []
    for name, data in quota.get("limits", {}).items():
        value = data.get("percent_left", data.get("percent"))
        if value is not None:
            label = labels.get(name, data.get("model", name))
            parts.append(f"{label}:{value:g}%")
    return ", ".join(parts) or state


def agy_quota_label(model):
    model_l = model.lower()
    if "gemini" in model_l and "flash" in model_l:
        label = "F"
    elif "gemini" in model_l and "pro" in model_l:
        label = "P"
    elif "claude" in model_l:
        label = "C"
    elif "gpt" in model_l:
        label = "G"
    else:
        return model[:8]

    if "medium" in model_l:
        tier = "M"
    elif "high" in model_l:
        tier = "H"
    elif "low" in model_l:
        tier = "L"
    elif "sonnet" in model_l:
        tier = "S"
    elif "opus" in model_l:
        tier = "O"
    else:
        tier = ""
    return f"{label}{tier}"


def agy_quota_entries(quota):
    limits = quota.get("limits", {})
    order = {"F": 0, "P": 1, "C": 2, "G": 3}
    label_order = {
        "FM": 0,
        "FH": 1,
        "FL": 2,
        "P": 3,
        "PL": 4,
        "PH": 5,
        "CS": 6,
        "CO": 7,
    }
    entries = []
    for idx, (name, data) in enumerate(limits.items()):
        value = data.get("percent_left", data.get("percent"))
        if value is None:
            continue
        model = data.get("model", name)
        label = agy_quota_label(model)
        entries.append((label, f"{value:g}%", order.get(label[:1], 99), label_order.get(label, 99), idx, name))
    entries.sort(key=lambda item: (item[2], item[3], item[4], item[5]))
    return [(label, value) for label, value, _, _, _, _ in entries]


def agy_quota_summary(quota):
    return " ".join(f"{label}:{value}" for label, value in agy_quota_entries(quota))

def status_table_lines(tool_key, statuses, terminal_width=None):
    terminal_width = terminal_width or _shutil().get_terminal_size((120, 24)).columns
    terminal_width = max(72, terminal_width)
    has_quota = any("quota" in status for status in statuses)
    fixed = 8 + 1 + 8 + 1 + 1
    quota_width = 24 if has_quota else 0
    if has_quota:
        fixed += quota_width + 1
    home_width = 24 if terminal_width >= 112 else 0
    if home_width:
        fixed += home_width + 1
    label_width = 16 if terminal_width >= 96 else 10
    fixed += label_width + 1
    account_width = max(18, terminal_width - fixed)
    if terminal_width < 90 and has_quota:
        quota_width = 18
        fixed = 8 + 1 + 8 + 1 + quota_width + 1 + label_width + 1
        account_width = max(16, terminal_width - fixed)

    headers = [
        ("Profile", 8),
        ("Account", account_width),
        ("Token", 8),
    ]
    if has_quota:
        headers.append(("Quota", quota_width))
    headers.append(("Label", label_width))
    if home_width:
        headers.append(("Home", home_width))
    lines = [" ".join(plain_fit(name, width) for name, width in headers)]
    lines.append("-" * min(terminal_width, len(lines[0])))
    for status in statuses:
        token = status.get("token_state") or ("yes" if status["has_token"] else "no")
        label = status["label"] or ""
        row = [
            plain_fit(status["profile"], 8),
            plain_fit(status["email"], account_width),
            plain_fit(token, 8),
        ]
        if has_quota:
            row.append(plain_fit(quota_summary(status), quota_width))
        row.append(plain_fit(label, label_width))
        if home_width:
            row.append(plain_fit(status["home"], home_width))
        lines.append(" ".join(row).rstrip())
    return lines

def print_status_table(tool_key, statuses):
    for line in status_table_lines(tool_key, statuses):
        print(line)

def cmd_config_show(args):
    from cli_profile_manager.config import effective_config_payload

    payload = effective_config_payload(
        include_sources=getattr(args, "sources", False) or getattr(args, "json", False),
        filter_text=getattr(args, "filter", None),
    )
    if args.json:
        print_json_payload(payload)
        return EXIT_OK
    print("Configuration")
    print("Profile roots:")
    for tool_key, root in payload["profile_roots"].items():
        print(f"  {tool_key}: {root}")
    print(f"Metadata: {payload['metadata_dir']}")
    print(f"Sync roots: wsl={payload['sync_roots']['wsl']} windows={payload['sync_roots']['windows']}")
    quota = payload["quota"]
    print(
        "Quota: "
        f"enabled={quota['interactive_enabled']} "
        f"timeout={quota['interactive_timeout']} "
        f"agy_timeout={quota['interactive_agy_timeout']} "
        f"agy_workers={quota['interactive_agy_concurrency']} "
        f"fresh_seconds={quota['interactive_fresh_seconds']} "
        f"session_ttl_seconds={quota['session_ttl_seconds']} "
        f"session_max={quota['session_max']}"
    )
    if payload["warnings"]:
        print("Warnings:")
        for warning in payload["warnings"]:
            print(f"  {warning}")
    if getattr(args, "sources", False):
        print("Settings:")
        for setting in payload["settings"]:
            print(
                f"  {setting['key']}: {setting['value']} "
                f"({setting['source']}:{setting['source_name']})"
            )
    return EXIT_OK

def cmd_list(args):
    snapshot = command_snapshot()
    profiles = snapshot.display_profiles(args.tool)
    if args.quota:
        statuses = [snapshot.status_with_quota(args.tool, n, args.timeout) for n in profiles]
    else:
        statuses = [snapshot.status(args.tool, n) for n in profiles]
    payload = {
        "tool": args.tool,
        "next_profile": f"p{snapshot.first_free_profile(args.tool)}",
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
    snapshot = command_snapshot()
    if args.quota:
        status = snapshot.status_with_quota(args.tool, n, args.timeout)
    else:
        status = snapshot.status(args.tool, n)
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
    snapshot = command_snapshot()
    status = snapshot.status(args.tool, n)
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
    _audit().record(
        "subprocess",
        "attempted",
        command="launch",
        tool=tool_key,
        profile=f"p{n}",
        details={"argv": [tool["cmd"]] + list(extra_args), "platform": os.name},
    )
    if os.name == "nt" and tool_key == "agy":
        switcher = os.path.join(tool["base_dir"], "agy-multiaccount.ps1")
        if not os.path.exists(switcher):
            print_error(f"Windows agy launch requires Credential Manager switcher: {switcher}")
            return EXIT_NOT_FOUND
        powershell = _shutil().which("powershell.exe") or _shutil().which("powershell")
        if powershell is None:
            print_error("PowerShell is required for Windows agy Credential Manager switching")
            return EXIT_NOT_FOUND
        os.makedirs(profile_home(tool_key, n), exist_ok=True)
        quoted_args = " ".join(_shlex().quote(arg) for arg in extra_args)
        command = (
            f"& {_shlex().quote(switcher)} Set-AgyCred {n}; "
            f"$env:USERPROFILE={_shlex().quote(profile_home(tool_key, n))}; "
            f"$env:HOME=$env:USERPROFILE; "
            f"& {_shlex().quote(tool['cmd'])}"
        )
        if quoted_args:
            command = f"{command} {quoted_args}"
        completed = _subprocess().run([powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command])
        _audit().record(
            "subprocess",
            "completed",
            command="launch",
            tool=tool_key,
            profile=f"p{n}",
            backend="powershell",
            result="succeeded" if completed.returncode == 0 else "failed",
            exit_code=completed.returncode,
        )
        return completed.returncode

    if _shutil().which(tool["cmd"]) is None:
        _audit().record(
            "subprocess",
            "failed",
            command="launch",
            tool=tool_key,
            profile=f"p{n}",
            result="failed",
            error_class="missing_cli",
            details={"cli": tool["cmd"]},
        )
        print_error(f"{tool['cmd']} CLI is not installed or not in PATH; install it or adjust PATH")
        return EXIT_NOT_FOUND
    os.makedirs(profile_home(tool_key, n), exist_ok=True)
    cmd = [tool["cmd"]] + extra_args
    cmd, preexec_fn, policy = _process_policy().prepare_popen(
        cmd,
        tier="launch",
        needs_pty=False,
        unit_name=f"ai-man-{tool_key}-p{n}",
    )
    _audit().record(
        "subprocess",
        "decision",
        command="launch",
        tool=tool_key,
        profile=f"p{n}",
        backend=policy.get("backend"),
        details={"process_policy": {key: policy.get(key) for key in ("enabled", "backend", "tier", "memory_mb", "cpu_percent", "max_processes")}},
    )
    _logging().info(
        "Launching %s profile p%s backend=%s policy_enabled=%s: %s",
        tool_key,
        n,
        policy.get("backend"),
        policy.get("enabled"),
        " ".join(cmd),
    )
    try:
        completed = _subprocess().run(cmd, env=make_tool_env(tool_key, n), preexec_fn=preexec_fn)
        _audit().record(
            "subprocess",
            "completed",
            command="launch",
            tool=tool_key,
            profile=f"p{n}",
            backend=policy.get("backend"),
            result="succeeded" if completed.returncode == 0 else "failed",
            exit_code=completed.returncode,
        )
        return completed.returncode
    except KeyboardInterrupt:
        _audit().record("subprocess", "failed", command="launch", tool=tool_key, profile=f"p{n}", result="failed", error_class="KeyboardInterrupt")
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
    decision = safety_decision(
        "launch",
        command="launch",
        tool=args.tool,
        profile=f"p{n}",
        target=profile_home(args.tool, n),
        facts={"command": dry_payload["command"], "platform": args.platform},
        dry_run=args.dry_run,
    )
    snapshot = command_snapshot()
    if n not in snapshot.display_profiles(args.tool):
        message = f"profile p{n} does not exist and is outside visible slots"
        if args.json:
            print_json_error(message, EXIT_USAGE, "usage_error")
        else:
            print_error(message)
        return EXIT_USAGE
    status = snapshot.status(args.tool, n)
    dry_payload["status"] = status
    dry_payload["would_launch"] = status["has_token"]
    dry_payload["safety"] = _safety().payload(decision)
    if args.dry_run:
        print_json_payload(dry_payload) if args.json else print(" ".join(_shlex().quote(part) for part in dry_payload["command"]))
        return EXIT_OK
    if not status["has_token"]:
        message = f"profile p{n} has no token; run ai-man login {args.tool} p{n} or import credentials first"
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
    safety_decision(
        "login",
        command="login",
        tool=args.tool,
        profile=f"p{n}",
        target=profile_home(args.tool, n),
        facts={"external_command": TOOLS[args.tool]["cmd"]},
    )
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
        _shutil().copy2(source, tmp_path)
        os.replace(tmp_path, dest_file)
    return n, dest_file

def cmd_import(args):
    _audit().record("credential", "attempted", command="import", tool=args.tool, details={"dry_run": args.dry_run, "path": args.path})
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
        decision = safety_decision(
            "import",
            command="import",
            tool=args.tool,
            profile=f"p{import_num}",
            target=dest_file,
            facts={"source": source, "destination": dest_file},
            dry_run=True,
        )
        payload["safety"] = _safety().payload(decision)
        if args.json:
            print_json_payload(payload)
        else:
            print(f"Would import {args.tool} credential into p{import_num}: {dest_file}")
        return EXIT_OK
    source = normalize_credential_path(args.tool, args.path)
    import_num = n if n is not None else first_free_profile(args.tool)
    decision = safety_decision(
        "import",
        command="import",
        tool=args.tool,
        profile=f"p{import_num}",
        target=credential_path(args.tool, import_num),
        facts={"source": source, "destination": credential_path(args.tool, import_num)},
    )
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
            "safety": _safety().payload(decision),
        })
    else:
        print(f"Imported {args.tool} credential into p{imported_num}: {dest_file}")
    _audit().record("credential", "completed", command="import", tool=args.tool, profile=f"p{imported_num}", result="succeeded", details={"destination": dest_file})
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
        _shutil().copy2(src_file, tmp_path)
        os.replace(tmp_path, dest_file)
    return dest_file

def cmd_export(args):
    _audit().record("credential", "attempted", command="export", tool=args.tool, profile=args.profile, details={"dry_run": args.dry_run, "to": args.to})
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
            decision = safety_decision(
                "export",
                command="export",
                tool=args.tool,
                profile=f"p{n}",
                target=dest_file,
                facts={"source": credential_path(args.tool, n), "destination": dest_file},
                dry_run=True,
            )
            payload["safety"] = _safety().payload(decision)
            if args.json:
                print_json_payload(payload)
            else:
                print(f"Would export {args.tool} p{n}: {dest_file}")
            return EXIT_OK
        _, planned_dest = resolve_export_destination(args.tool, n, args.to)
        decision = safety_decision(
            "export",
            command="export",
            tool=args.tool,
            profile=f"p{n}",
            target=planned_dest,
            facts={"source": credential_path(args.tool, n), "destination": planned_dest},
        )
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
            "safety": _safety().payload(decision),
        })
    else:
        print(f"Exported {args.tool} p{n}: {dest_file}")
    _audit().record("credential", "completed", command="export", tool=args.tool, profile=f"p{n}", result="succeeded", details={"destination": dest_file})
    return EXIT_OK

def label_profile(tool_key, profile_num, label):
    core_label_profile(tool_key, profile_num, label)

def cmd_label(args):
    try:
        n = parse_profile(args.profile)
    except ValueError as e:
        print_error(str(e))
        return EXIT_USAGE
    safety_decision(
        "label",
        command="label",
        tool=args.tool,
        profile=f"p{n}",
        target=profile_home(args.tool, n),
        facts={"label": args.label},
    )
    label_profile(args.tool, n, args.label)
    _audit().record("profile", "completed", command="label", tool=args.tool, profile=f"p{n}", result="succeeded", details={"label": args.label})
    print(f"Label set for {args.tool} p{n}: {args.label}")
    return EXIT_OK

def cmd_clear(args):
    try:
        n = parse_profile(args.profile)
    except ValueError as e:
        if getattr(args, "json", False):
            print_json_error(str(e), EXIT_USAGE, "usage_error")
        else:
            print_error(str(e))
        return EXIT_USAGE
    home = profile_home(args.tool, n)
    decision = safety_decision(
        "clear",
        command="clear",
        tool=args.tool,
        profile=f"p{n}",
        target=home,
        facts={"exists": os.path.exists(home), "delete_paths": [home] if os.path.exists(home) else []},
        yes=args.yes,
    )
    if not decision["ok"]:
        if getattr(args, "json", False):
            print_json_payload({
                "ok": False,
                "error": {
                    "type": "confirmation_required",
                    "message": decision["message"],
                    "code": EXIT_USAGE,
                },
                "safety": _safety().payload(decision),
            })
        else:
            print_error(decision["message"])
        return EXIT_USAGE
    try:
        cleared_home = clear_profile_data(args.tool, n)
    except ValueError as e:
        if getattr(args, "json", False):
            print_json_error(str(e), EXIT_USAGE, "usage_error")
        else:
            print_error(str(e))
        return EXIT_USAGE
    _audit().record("profile", "completed", command="clear", tool=args.tool, profile=f"p{n}", result="succeeded", details={"home": cleared_home})
    if getattr(args, "json", False):
        print_json_payload({
            "ok": True,
            "tool": args.tool,
            "profile": f"p{n}",
            "cleared": cleared_home,
            "safety": _safety().payload(decision),
        })
    else:
        print(f"Cleared {args.tool} p{n}: {cleared_home}")
    return EXIT_OK

def clear_profile_data(tool_key, n):
    home = profile_home(tool_key, n)
    base = os.path.abspath(TOOLS[tool_key]["base_dir"])
    target = os.path.abspath(home)
    if not target.startswith(base + os.sep):
        raise ValueError(f"refusing to clear unsafe path: {target}")
    if os.path.exists(home):
        _shutil().rmtree(home)
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
    return _sync_module().profile_number_from_dir_name(name)

def is_windows_agy_backup_name(name):
    return _sync_module().is_windows_agy_backup_name(name)

def path_is_within(child, parent):
    return _sync_module().path_is_within(child, parent)

def deletion_preflight_paths(path):
    return _sync_module().deletion_preflight_paths(path)

def sync_agy_credentials_between_bases(src_base, dst_base, direction, dry_run=False):
    return _sync_module().sync_agy_credentials_between_bases(src_base, dst_base, direction, dry_run)

def sync_profiles_noninteractive(direction, mode, dry_run=False, yes=False):
    src_base, dst_base = resolve_sync_bases(direction)
    return _sync_module().sync_profiles_between_bases(src_base, dst_base, direction, mode, dry_run, yes)

def cmd_sync(args):
    operation = "sync-hard" if args.mode == "hard" else "sync-soft"
    try:
        src_base, dst_base = resolve_sync_bases(args.source)
    except Exception:
        src_base, dst_base = None, None
    decision = safety_decision(
        operation,
        command="sync",
        target=str(dst_base) if dst_base is not None else None,
        facts={
            "source": args.source,
            "mode": args.mode,
            "source_base": str(src_base) if src_base is not None else None,
            "destination_base": str(dst_base) if dst_base is not None else None,
        },
        yes=args.yes,
        dry_run=args.dry_run,
    )
    _audit().record("sync", "decision", command="sync", details={"source": args.source, "mode": args.mode, "dry_run": args.dry_run, "safety": _safety().payload(decision)})
    if not decision["ok"]:
        if args.json:
            print_json_payload({
                "ok": False,
                "error": {
                    "type": "confirmation_required",
                    "message": decision["message"],
                    "code": EXIT_USAGE,
                },
                "safety": _safety().payload(decision),
            })
        else:
            print_error(decision["message"])
        return EXIT_USAGE
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
        result["safety"] = _safety().payload(decision)
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

def cmd_audit(args):
    audit = _audit()
    action = args.audit_action
    if action == "status":
        payload = audit.status_payload()
        if args.json:
            print_json_payload(payload)
        else:
            print(f"Audit: {'enabled' if payload['enabled'] else 'disabled'} backend={payload['backend']} records={payload['record_count']}")
            print(f"Path: {payload['path']}")
        return EXIT_OK
    if action == "list":
        events = audit.query_events(
            limit=args.limit,
            category=args.category,
            command=args.command_name,
            tool=args.tool,
            profile=args.profile,
            result=args.result,
            correlation_id=args.correlation_id,
            since=args.since,
            until=args.until,
        )
        if args.json:
            print_json_payload({"ok": True, "events": events})
        else:
            for event in events:
                print(f"{event['timestamp']} {event['category']}.{event['action']} {event.get('command') or '-'} {event.get('result') or '-'} {event['event_id']}")
        return EXIT_OK
    if action == "show":
        events = audit.show_events(args.identifier)
        if args.json:
            print_json_payload({"ok": True, "events": events})
        else:
            for event in events:
                print(json.dumps(event, indent=2))
        return EXIT_OK if events else EXIT_NOT_FOUND
    if action == "export":
        events = audit.query_events(limit=None)
        if args.format == "json":
            print_json_payload({"ok": True, "events": events})
        else:
            for event in reversed(events):
                print(json.dumps(event, sort_keys=True))
        return EXIT_OK
    if action == "purge":
        decision = safety_decision(
            "audit-purge",
            command="audit",
            target=str(audit.audit_dir()),
            facts={"backend": audit.backend_name()},
            yes=args.yes,
        )
        if not decision["ok"]:
            if args.json:
                print_json_payload({
                    "ok": False,
                    "error": {
                        "type": "confirmation_required",
                        "message": decision["message"],
                        "code": EXIT_USAGE,
                    },
                    "safety": _safety().payload(decision),
                })
            else:
                print_error(decision["message"])
            return EXIT_USAGE
        removed = audit.purge_all()
        payload = {"ok": True, "removed": removed, "safety": _safety().payload(decision)}
        print_json_payload(payload) if args.json else print(f"Purged {removed} audit events")
        return EXIT_OK
    if action == "compact":
        decision = safety_decision(
            "audit-compact",
            command="audit",
            target=str(audit.audit_dir()),
            facts={"days": args.days, "max_bytes": args.max_bytes, "backend": audit.backend_name()},
        )
        result = audit.compact_retention(args.days, args.max_bytes)
        payload = {"ok": True, **result, "safety": _safety().payload(decision)}
        print_json_payload(payload) if args.json else print(f"Removed {result['removed']} audit events; kept {result['kept']}")
        return EXIT_OK
    print_error(f"unknown audit action: {action}")
    return EXIT_USAGE

def cmd_service(args):
    runtime = _runtime_service()
    action = args.service_action
    if action == "run":
        _audit().record("runtime_service", "started", command="service", details={"action": "run"})
        try:
            runtime.serve_forever()
            _audit().record("runtime_service", "completed", command="service", result="succeeded", details={"action": "run"})
            return EXIT_OK
        except Exception as e:
            _audit().record("runtime_service", "failed", command="service", result="failed", error_class=type(e).__name__, details={"message": str(e)})
            print_error(f"service failed: {e}")
            return EXIT_RUNTIME
    if action == "status":
        payload = {"ok": True, "service": runtime.service_status()}
        try:
            health = runtime.service_health() if payload["service"]["running"] else None
        except Exception:
            health = None
        if health:
            payload["service"]["health"] = health
        if args.json:
            print_json_payload(payload)
        else:
            state = "running" if payload["service"]["running"] else "stopped"
            if payload["service"]["stale"]:
                state = "stale"
            print(f"Service: {state}")
            print(f"Socket: {payload['service']['socket_path']}")
            print(f"PID: {payload['service']['pid'] or '-'}")
        return EXIT_OK
    if action == "start":
        decision = safety_decision(
            "service-start",
            command="service",
            target=str(runtime.socket_path()),
            facts={"action": "start", "status": runtime.service_status()},
        )
        payload = runtime.start_service(os.path.join(os.path.dirname(os.path.dirname(__file__)), "profile_manager.py"))
        _audit().record("runtime_service", "completed", command="service", result="succeeded" if payload.get("ok") else "failed", details={"action": "start", "running": payload.get("running")})
        if args.json:
            print_json_payload({"ok": bool(payload.get("ok")), "service": payload, "safety": _safety().payload(decision)})
        else:
            print("Service running" if payload.get("ok") else f"Service failed: {payload.get('error', 'unknown error')}")
        return EXIT_OK if payload.get("ok") else EXIT_RUNTIME
    if action == "stop":
        decision = safety_decision(
            "service-stop",
            command="service",
            target=str(runtime.socket_path()),
            facts={"action": "stop", "status": runtime.service_status()},
        )
        payload = runtime.stop_service()
        _audit().record("runtime_service", "completed", command="service", result="succeeded", details={"action": "stop", "stopped": payload.get("stopped")})
        if args.json:
            print_json_payload({"ok": True, "service": payload, "safety": _safety().payload(decision)})
        else:
            print("Service stopped" if payload.get("stopped") else "Service was not running")
        return EXIT_OK
    if action == "restart":
        decision = safety_decision(
            "service-restart",
            command="service",
            target=str(runtime.socket_path()),
            facts={"action": "restart", "status": runtime.service_status()},
        )
        runtime.stop_service()
        payload = runtime.start_service(os.path.join(os.path.dirname(os.path.dirname(__file__)), "profile_manager.py"))
        _audit().record("runtime_service", "completed", command="service", result="succeeded" if payload.get("ok") else "failed", details={"action": "restart", "running": payload.get("running")})
        if args.json:
            print_json_payload({"ok": bool(payload.get("ok")), "service": payload, "safety": _safety().payload(decision)})
        else:
            print("Service restarted" if payload.get("ok") else f"Service failed: {payload.get('error', 'unknown error')}")
        return EXIT_OK if payload.get("ok") else EXIT_RUNTIME
    print_error(f"unknown service action: {action}")
    return EXIT_USAGE

def diagnostics_status_provider(tool_key, n):
    try:
        return status_payload(tool_key, n)
    except Exception as e:
        return {
            "has_token": False,
            "token_state": "diagnostic_error",
            "credential_source": None,
            "account": None,
            "email": None,
            "warnings": [str(e)],
        }

def cmd_diagnostics(args):
    snapshot = command_snapshot()

    def snapshot_status_provider(tool_key, n):
        try:
            return snapshot.status(tool_key, n)
        except Exception as e:
            return {
                "has_token": False,
                "token_state": "diagnostic_error",
                "credential_source": None,
                "account": None,
                "email": None,
                "warnings": [str(e)],
            }

    def snapshot_profile_index(tool_key):
        return {
            "occupied_profiles": snapshot.occupied_profiles(tool_key),
            "display_profiles": snapshot.display_profiles(tool_key),
        }

    payload = diagnostics_payload(
        args.tool,
        status_provider=snapshot_status_provider,
        show_accounts=args.show_accounts,
        profile_index_provider=snapshot_profile_index,
    )
    if args.json:
        print_json_payload(payload)
        return EXIT_OK
    print("Diagnostics")
    print(f"Generated: {payload['generated_at']}")
    for tool_key, data in payload["tools"].items():
        available = "yes" if data["cli_available"] else "no"
        print(f"{tool_key}: cli={available} path={data['cli_path'] or '-'} profiles={len(data['visible_profiles'])}")
    runtime = payload["quota_runtime"]
    scheduler = runtime.get("scheduler") or {}
    print(f"quota: enabled={runtime['enabled']} active={runtime['active_jobs']} cache={len(runtime['cache'])}")
    if scheduler:
        print(f"scheduler: workers={scheduler['worker_count']} queue={scheduler['queue_size']} closed={scheduler['closed']}")
    sessions = payload["persistent_sessions"]
    print(f"persistent sessions: {sessions['count']}")
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
    clear_p.add_argument("--json", action="store_true")
    clear_p.set_defaults(func=cmd_clear)

    sync_p = sub.add_parser("sync", help="sync profile directories between WSL and Windows")
    sync_p.add_argument("--from", dest="source", choices=("wsl", "windows"), default="wsl")
    sync_p.add_argument("--mode", choices=("soft", "hard"), default="soft")
    sync_p.add_argument("--dry-run", action="store_true")
    sync_p.add_argument("--yes", action="store_true", help="confirm hard sync")
    sync_p.add_argument("--json", action="store_true")
    sync_p.set_defaults(func=cmd_sync)

    diagnostics_p = sub.add_parser(
        "diagnostics",
        aliases=["doctor"],
        help="show safe runtime diagnostics",
    )
    diagnostics_p.add_argument("tool", choices=TOOLS.keys(), nargs="?")
    diagnostics_p.add_argument("--json", action="store_true")
    diagnostics_p.add_argument("--show-accounts", action="store_true", help="include full account identifiers")
    diagnostics_p.set_defaults(func=cmd_diagnostics)

    config_p = sub.add_parser("config", help="inspect effective runtime configuration")
    config_p.set_defaults(func=cmd_config_show, json=False)
    config_sub = config_p.add_subparsers(dest="config_command")
    config_show_p = config_sub.add_parser("show", help="show effective paths, quota settings, and env overrides")
    config_show_p.add_argument("--json", action="store_true")
    config_show_p.add_argument("--sources", action="store_true", help="include setting source information in text output")
    config_show_p.add_argument("--filter", help="show settings matching a key, environment name, category, or description")
    config_show_p.set_defaults(func=cmd_config_show)

    audit_p = sub.add_parser("audit", help="inspect and manage local audit events")
    audit_p.set_defaults(func=cmd_audit, audit_action="status", json=False)
    audit_sub = audit_p.add_subparsers(dest="audit_action")
    audit_status_p = audit_sub.add_parser("status")
    audit_status_p.add_argument("--json", action="store_true")
    audit_status_p.set_defaults(func=cmd_audit)
    audit_list_p = audit_sub.add_parser("list")
    audit_list_p.add_argument("--json", action="store_true")
    audit_list_p.add_argument("--limit", type=int, default=50)
    audit_list_p.add_argument("--category")
    audit_list_p.add_argument("--command", dest="command_name")
    audit_list_p.add_argument("--tool")
    audit_list_p.add_argument("--profile")
    audit_list_p.add_argument("--result")
    audit_list_p.add_argument("--correlation-id")
    audit_list_p.add_argument("--since", help="inclusive ISO-8601 lower timestamp bound")
    audit_list_p.add_argument("--until", help="inclusive ISO-8601 upper timestamp bound")
    audit_list_p.set_defaults(func=cmd_audit)
    audit_show_p = audit_sub.add_parser("show")
    audit_show_p.add_argument("identifier")
    audit_show_p.add_argument("--json", action="store_true")
    audit_show_p.set_defaults(func=cmd_audit)
    audit_export_p = audit_sub.add_parser("export")
    audit_export_p.add_argument("--format", choices=("jsonl", "json"), default="jsonl")
    audit_export_p.set_defaults(func=cmd_audit)
    audit_purge_p = audit_sub.add_parser("purge")
    audit_purge_p.add_argument("--yes", action="store_true")
    audit_purge_p.add_argument("--json", action="store_true")
    audit_purge_p.set_defaults(func=cmd_audit)
    audit_compact_p = audit_sub.add_parser("compact")
    audit_compact_p.add_argument("--days", type=int)
    audit_compact_p.add_argument("--max-bytes", type=int)
    audit_compact_p.add_argument("--json", action="store_true")
    audit_compact_p.set_defaults(func=cmd_audit)

    service_p = sub.add_parser("service", help="manage optional long-lived local runtime")
    service_p.set_defaults(func=cmd_service, service_action="status", json=False)
    service_sub = service_p.add_subparsers(dest="service_action")
    for action in ("start", "stop", "restart", "status"):
        action_p = service_sub.add_parser(action)
        action_p.add_argument("--json", action="store_true")
        action_p.set_defaults(func=cmd_service)
    run_p = service_sub.add_parser("run", help=argparse.SUPPRESS)
    run_p.set_defaults(func=cmd_service, json=False)

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
    if should_use_service(argv):
        result = try_run_service_command(argv)
        if result is not None:
            return result
    audit_started = None
    audit_parent_token = None
    audit_corr_token = None
    audit_context = audit_context_from_argv(argv)
    if audit_context["command"]:
        audit_started = _audit().make_event("command", "started", **audit_context, details={"argv": argv})
        _audit().write_event(audit_started)
        audit_corr_token = _audit().CURRENT_CORRELATION_ID.set(audit_started["correlation_id"])
        audit_parent_token = _audit().CURRENT_PARENT_ID.set(audit_started["event_id"])
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        return None
    if getattr(args, "args", None) and args.args[:1] == ["--"]:
        args.args = args.args[1:]
    try:
        result = args.func(args)
    except SystemExit as e:
        if audit_started:
            _audit().complete_span(audit_started, result="failed", exit_code=e.code, error_class="SystemExit")
        raise
    except Exception as e:
        if audit_started:
            _audit().complete_span(audit_started, result="failed", exit_code=EXIT_RUNTIME, error_class=type(e).__name__, details={"message": str(e)})
        raise
    finally:
        if audit_started:
            _audit().CURRENT_PARENT_ID.reset(audit_parent_token)
            _audit().CURRENT_CORRELATION_ID.reset(audit_corr_token)
    if audit_started:
        _audit().complete_span(audit_started, result="succeeded" if result == EXIT_OK else "failed", exit_code=result)
    notify_service_after_command(argv, result)
    return result

def should_use_service(argv):
    if os.environ.get("AI_MAN_SERVICE_CLIENT_ACTIVE") == "1":
        return False
    if str(os.environ.get("AI_MAN_SERVICE", "")).lower() not in SERVICE_ENV_TRUE:
        return False
    runtime = _runtime_service()
    return runtime.eligible_argv(argv)

def try_run_service_command(argv):
    runtime = _runtime_service()
    old_active = os.environ.get("AI_MAN_SERVICE_CLIENT_ACTIVE")
    os.environ["AI_MAN_SERVICE_CLIENT_ACTIVE"] = "1"
    try:
        try:
            response = runtime.run_via_service(argv)
        except Exception:
            _audit().record("runtime_service", "skipped", command=argv[0] if argv else None, result="fallback", error_class="ServiceError")
            return None
    finally:
        if old_active is None:
            os.environ.pop("AI_MAN_SERVICE_CLIENT_ACTIVE", None)
        else:
            os.environ["AI_MAN_SERVICE_CLIENT_ACTIVE"] = old_active
    if not response.get("ok"):
        _audit().record("runtime_service", "failed", command=argv[0] if argv else None, result="fallback", details=response.get("error"))
        return None
    _audit().record("runtime_service", "succeeded", command=argv[0] if argv else None, result="succeeded", details={"returncode": response.get("returncode")})
    stdout = response.get("stdout") or ""
    stderr = response.get("stderr") or ""
    if stdout:
        print(stdout, end="")
    if stderr:
        print(stderr, end="", file=sys.stderr)
    return int(response.get("returncode", EXIT_RUNTIME))

def notify_service_after_command(argv, result):
    if result != EXIT_OK:
        return
    if not argv or argv[0] not in SERVICE_MUTATING_COMMANDS:
        return
    runtime = _runtime_service()
    if hasattr(runtime, "mutation_invalidation"):
        invalidation = runtime.mutation_invalidation(argv)
    elif runtime.mutates_runtime_state(argv):
        invalidation = {"reason": argv[0], "domains": [], "command": argv[0]}
    else:
        invalidation = None
    if invalidation is None:
        return
    if hasattr(runtime, "invalidate_service_for"):
        runtime.invalidate_service_for(**invalidation)
    else:
        runtime.invalidate_service()

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
