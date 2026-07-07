#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import base64
import argparse
import glob
import shlex
import subprocess
import termios
import tty
import shutil
import time
import logging
from pathlib import Path
from datetime import datetime

# Setup logging
log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ai-man.log")
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Base configuration paths
METADATA_DIR = os.path.expanduser(os.environ.get("AI_MAN_METADATA_DIR", "~/.config/cli-profile-manager"))
METADATA_PATH = os.path.join(METADATA_DIR, "profiles_metadata.json")
DISPLAY_SLOT_COUNT = 12
EXIT_OK = 0
EXIT_USAGE = 2
EXIT_NOT_FOUND = 3
EXIT_NO_TOKEN = 4
EXIT_RUNTIME = 5
AGY_WINDOWS_TARGET = "gemini:antigravity"
AGY_WINDOWS_USERNAME = "antigravity"

# Tool configurations
TOOLS = {
    "agy": {
        "name": "Antigravity CLI (agy)",
        "env_var": "HOME",
        "base_dir": os.path.expanduser(os.environ.get("AI_MAN_AGY_HOME", "~/agy-homes")),
        "cmd": "agy",
        "cred_file": os.path.join(".gemini", "oauth_creds.json"),
        "acct_file": os.path.join(".gemini", "google_accounts.json"),
        "import_help": "Import a Windows Credential Manager backup (.json) file"
    },
    "codex": {
        "name": "OpenAI Codex CLI",
        "env_var": "CODEX_HOME",
        "base_dir": os.path.expanduser(os.environ.get("AI_MAN_CODEX_HOME", "~/codex-homes")),
        "cmd": "codex",
        "cred_file": "auth.json",
        "acct_file": None,
        "import_help": "Import a Codex auth.json file"
    },
    "claude": {
        "name": "Anthropic Claude CLI",
        "env_var": "CLAUDE_CONFIG_DIR",
        "base_dir": os.path.expanduser(os.environ.get("AI_MAN_CLAUDE_HOME", "~/claude-homes")),
        "cmd": "claude",
        "cred_file": ".credentials.json",
        "acct_file": None,
        "import_help": "Import a Claude .credentials.json file"
    }
}

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

def clear_screen():
    sys.stdout.write("\033[H\033[J")
    sys.stdout.flush()

def get_key():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == '\x1b':
            ch2 = sys.stdin.read(1)
            if ch2 == '[':
                ch3 = sys.stdin.read(1)
                if ch3 == 'A': return 'up'
                elif ch3 == 'B': return 'down'
                elif ch3 == 'C': return 'right'
                elif ch3 == 'D': return 'left'
            return 'esc'
        elif ch in ('\n', '\r'):
            return 'enter'
        elif ch == '\x03': # Ctrl+C
            return 'ctrl+c'
        else:
            return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def load_metadata():
    if os.path.exists(METADATA_PATH):
        try:
            with open(METADATA_PATH, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_metadata(data):
    os.makedirs(METADATA_DIR, exist_ok=True)
    try:
        with open(METADATA_PATH, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving metadata: {e}")

def get_profiles(tool_key):
    return get_occupied_profiles(tool_key)

def get_occupied_profiles(tool_key):
    base_dir = TOOLS[tool_key]["base_dir"]
    if not os.path.exists(base_dir):
        os.makedirs(base_dir, exist_ok=True)
    
    profiles = set()
    for d in os.listdir(base_dir):
        if d.startswith("p") and d[1:].isdigit():
            profiles.add(int(d[1:]))
        # For Windows agy, the profile might just be a cred-pN.json file
        elif os.name == "nt" and tool_key == "agy" and d.startswith("cred-p") and d.endswith(".json"):
            num_part = d[6:-5]
            if num_part.isdigit():
                profiles.add(int(num_part))

    profiles = list(profiles)
    profiles.sort()
    return profiles

def get_display_profiles(tool_key):
    profiles = set(get_occupied_profiles(tool_key))
    profiles.update(range(1, DISPLAY_SLOT_COUNT + 1))
    result = list(profiles)
    result.sort()
    return result

def first_free_profile(tool_key):
    occupied = set(get_occupied_profiles(tool_key))
    n = 1
    while n in occupied:
        n += 1
    return n

def parse_profile(value):
    raw = str(value).strip().lower()
    if raw.startswith("p"):
        raw = raw[1:]
    if not raw.isdigit():
        raise ValueError(f"invalid profile '{value}': expected pN with a positive integer")
    num = int(raw)
    if num <= 0:
        raise ValueError(f"invalid profile '{value}': profile number must be positive")
    return num

def is_valid_display_profile(tool_key, n):
    return n in get_display_profiles(tool_key)

def ensure_parent(path):
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)

def normalize_credential_path(tool_key, cred_file):
    cred_file = cred_file.strip()
    if (cred_file.startswith('"') and cred_file.endswith('"')) or (cred_file.startswith("'") and cred_file.endswith("'")):
        cred_file = cred_file[1:-1]
    if len(cred_file) >= 3 and cred_file[1:3] == ":\\":
        drive = cred_file[0].lower()
        cred_file = f"/mnt/{drive}/" + cred_file[3:].replace("\\", "/")
    cred_file = os.path.expanduser(cred_file)
    if os.path.isdir(cred_file):
        if tool_key == "codex":
            cred_file = os.path.join(cred_file, "auth.json")
        elif tool_key == "claude":
            cred_file = os.path.join(cred_file, ".credentials.json")
    return cred_file

def profile_home(tool_key, n):
    return os.path.join(TOOLS[tool_key]["base_dir"], f"p{n}")

def credential_path(tool_key, n):
    tool = TOOLS[tool_key]
    return os.path.join(profile_home(tool_key, n), tool["cred_file"])

def agy_windows_credential_path(n, base_dir=None):
    base = base_dir or TOOLS["agy"]["base_dir"]
    return os.path.join(str(base), f"cred-p{n}.json")

def make_tool_env(tool_key, n):
    tool = TOOLS[tool_key]
    home = profile_home(tool_key, n)
    env = os.environ.copy()
    env[tool["env_var"]] = home
    if tool_key == "agy":
        env["HOME"] = home
    return env

def write_text_atomic(path, content):
    ensure_parent(path)
    tmp_path = f"{path}.tmp-{os.getpid()}"
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(content)
    os.replace(tmp_path, path)

def write_json_atomic(path, data):
    ensure_parent(path)
    tmp_path = f"{path}.tmp-{os.getpid()}"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp_path, path)

def read_json_object(path, encoding="utf-8"):
    with open(path, "r", encoding=encoding) as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data

def account_email_from_google_accounts(profile_home):
    ga_path = os.path.join(profile_home, TOOLS["agy"]["acct_file"])
    if not os.path.exists(ga_path):
        return None
    try:
        data = read_json_object(ga_path)
    except Exception:
        return None
    email = data.get("active")
    if isinstance(email, str) and email.strip():
        return email.strip().rstrip(",")
    return None

def decode_windows_agy_credential(win_cred_path):
    data = read_json_object(win_cred_path, encoding="utf-8-sig")
    target = data.get("Target")
    if target and target != AGY_WINDOWS_TARGET:
        raise ValueError(f"unexpected Windows credential target: {target}")
    blob_b64 = data.get("BlobBase64")
    if not isinstance(blob_b64, str) or not blob_b64:
        raise ValueError("Windows credential is missing BlobBase64")
    try:
        token_text = base64.b64decode(blob_b64).decode("utf-8")
        token_data = json.loads(token_text)
    except Exception as e:
        raise ValueError(f"Windows credential BlobBase64 is not valid OAuth JSON: {e}") from e
    if not isinstance(token_data, dict):
        raise ValueError("Windows credential token payload must be a JSON object")
    account = data.get("Account")
    if isinstance(account, str):
        account = account.strip().rstrip(",") or None
    else:
        account = None
    return token_data, account

def read_wsl_agy_oauth(token_path):
    return read_json_object(token_path)

def build_windows_agy_credential(token_data, account=None):
    token_text = json.dumps(token_data, indent=2)
    token_bytes = token_text.encode("utf-8")
    return {
        "Target": AGY_WINDOWS_TARGET,
        "Type": 1,
        "Persist": 2,
        "Flags": 0,
        "UserName": AGY_WINDOWS_USERNAME,
        "Account": account,
        "BlobBase64": base64.b64encode(token_bytes).decode("utf-8"),
        "BlobSize": len(token_bytes),
        "SavedAt": datetime.now().isoformat()
    }

def import_windows_agy_credential(win_cred_path, profile_num):
    token_data, account = decode_windows_agy_credential(win_cred_path)
    dest_home = profile_home("agy", profile_num)
    dest_file = credential_path("agy", profile_num)
    write_json_atomic(dest_file, token_data)
    if account:
        write_json_atomic(os.path.join(dest_home, TOOLS["agy"]["acct_file"]), {"active": account})
    return dest_file

def export_wsl_agy_credential(profile_num, win_cred_path):
    home = profile_home("agy", profile_num)
    token_data = read_wsl_agy_oauth(credential_path("agy", profile_num))
    account = account_email_from_google_accounts(home)
    write_json_atomic(win_cred_path, build_windows_agy_credential(token_data, account))
    return win_cred_path

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
    elif os.path.exists(cred_path):
        has_token = True
        token_state = "present"
        credential_source = "codex-auth" if tool_key == "codex" else "claude-credentials"

    if tool_key == "codex":
        if has_token:
            try:
                with open(cred_path, "r") as f:
                    data = json.load(f)
                idt = data.get("tokens", {}).get("id_token")
                if idt:
                    payload_b64 = idt.split(".")[1]
                    payload_b64 += "=" * (4 - len(payload_b64) % 4)
                    payload = json.loads(base64.urlsafe_b64decode(payload_b64).decode("utf-8"))
                    email = payload.get("email") or payload.get("https://api.openai.com/profile", {}).get("email") or "logged in"
                elif data.get("OPENAI_API_KEY"):
                    email = "API Key"
                token_state = "valid"
                account = email
            except Exception as e:
                token_state = "invalid"
                warnings.append(str(e))
                email = "logged in"
                
    elif tool_key == "claude":
        if has_token:
            try:
                with open(cred_path, "r") as f:
                    data = json.load(f)
                oauth = data.get("claudeAiOauth", {})
                sub = oauth.get("subscriptionType")
                tier = oauth.get("rateLimitTier")
                if sub and tier:
                    email = f"Logged in ({sub}/{tier})"
                elif sub:
                    email = f"Logged in ({sub})"
                else:
                    email = "Logged in"
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

def print_status_table(tool_key, statuses):
    print(f"{'Profile':<8} {'Account':<32} {'Token':<8} {'Label':<16} Home")
    print("-" * 96)
    for status in statuses:
        token = status.get("token_state") or ("yes" if status["has_token"] else "no")
        label = status["label"] or ""
        print(f"{status['profile']:<8} {status['email']:<32} {token:<8} {label:<16} {status['home']}")

def cmd_list(args):
    metadata = load_metadata()
    profiles = get_display_profiles(args.tool)
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
    status = status_payload(args.tool, n)
    if args.json:
        print_json_payload(status)
    else:
        print_status_table(args.tool, [status])
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

def export_credential_file(tool_key, profile_num, to_path=None):
    status = status_payload(tool_key, profile_num)
    if not status["has_token"]:
        raise PermissionError(f"profile p{profile_num} has no token to export")
    src_file = credential_path(tool_key, profile_num)
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
    os.makedirs(export_dir, exist_ok=True)
    if tool_key == "agy":
        if dest_file is None:
            dest_file = os.path.join(export_dir, f"cred-p{profile_num}-exported.json")
        export_wsl_agy_credential(profile_num, dest_file)
    else:
        if dest_file is None:
            dest_file = os.path.join(export_dir, f"{tool_key}-p{profile_num}-exported.json")
        ensure_parent(dest_file)
        tmp_path = f"{dest_file}.tmp-{os.getpid()}"
        shutil.copy2(src_file, tmp_path)
        os.replace(tmp_path, dest_file)
    return dest_file

def cmd_export(args):
    try:
        n = parse_profile(args.profile)
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
    metadata = load_metadata()
    metadata.setdefault(tool_key, {}).setdefault(f"p{profile_num}", {})["label"] = label
    save_metadata(metadata)

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
    override_wsl = os.environ.get("AI_MAN_WSL_HOME")
    override_win = os.environ.get("AI_MAN_WINDOWS_HOME")
    if os.name == "nt":
        win_home = Path(override_win or os.environ.get("USERPROFILE", r"C:\Users\Oliver"))
        if override_wsl:
            wsl_home = Path(override_wsl)
        else:
            wsl_home = Path(r"\\wsl.localhost\Ubuntu\home\olivercromwell")
        if not override_wsl and not wsl_home.exists():
            wsl_home = Path(r"\\wsl$\Ubuntu\home\olivercromwell")
    else:
        wsl_home = Path(override_wsl or os.path.expanduser("~"))
        win_home = Path(override_win or f"/mnt/c/Users/{find_windows_user()}")
    src_base = wsl_home if direction == "wsl" else win_home
    dst_base = win_home if direction == "wsl" else wsl_home
    return src_base, dst_base

def count_files_under(path):
    total = 0
    if not path.exists():
        return total
    for _, _, files in os.walk(path):
        total += len(files)
    return total

def profile_number_from_dir_name(name):
    if name.startswith("p") and name[1:].isdigit():
        return int(name[1:])
    return None

def is_windows_agy_backup_name(name):
    return name.startswith("cred-p") and name.endswith(".json") and name[6:-5].isdigit()

def path_is_within(child, parent):
    child = Path(child).resolve()
    parent = Path(parent).resolve()
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False

def deletion_preflight_paths(path):
    if not path.exists():
        return []
    paths = []
    for root, dirs, files in os.walk(path):
        for file_name in files:
            paths.append(str(Path(root) / file_name))
        for dir_name in dirs:
            dir_path = Path(root) / dir_name
            if not any(dir_path.iterdir()):
                paths.append(str(dir_path))
    if not paths:
        paths.append(str(path))
    return sorted(paths)

def sync_agy_credentials_between_bases(src_base, dst_base, direction, dry_run=False):
    result = {"converted": 0, "invalid": 0, "items": []}
    src_agy = Path(src_base) / "agy-homes"
    dst_agy = Path(dst_base) / "agy-homes"
    if not src_agy.exists():
        return result

    if direction == "wsl":
        for profile_dir in src_agy.iterdir():
            if not profile_dir.is_dir():
                continue
            n = profile_number_from_dir_name(profile_dir.name)
            if n is None:
                continue
            token_path = profile_dir / ".gemini" / "oauth_creds.json"
            if not token_path.exists():
                continue
            dest = dst_agy / f"cred-p{n}.json"
            try:
                token_data = read_wsl_agy_oauth(str(token_path))
                account = account_email_from_google_accounts(str(profile_dir))
            except Exception as e:
                result["invalid"] += 1
                result["items"].append({"source": str(token_path), "destination": str(dest), "status": "invalid", "error": str(e)})
                continue
            result["converted"] += 1
            result["items"].append({"source": str(token_path), "destination": str(dest), "status": "converted"})
            if not dry_run:
                write_json_atomic(str(dest), build_windows_agy_credential(token_data, account))
    else:
        for cred_path in src_agy.glob("cred-p*.json"):
            stem = cred_path.stem
            num_text = stem[6:]
            if not num_text.isdigit():
                continue
            n = int(num_text)
            dest_profile = dst_agy / f"p{n}"
            dest = dest_profile / ".gemini" / "oauth_creds.json"
            try:
                token_data, account = decode_windows_agy_credential(str(cred_path))
            except Exception as e:
                result["invalid"] += 1
                result["items"].append({"source": str(cred_path), "destination": str(dest), "status": "invalid", "error": str(e)})
                continue
            result["converted"] += 1
            result["items"].append({"source": str(cred_path), "destination": str(dest), "status": "converted"})
            if not dry_run:
                write_json_atomic(str(dest), token_data)
                if account:
                    write_json_atomic(str(dest_profile / ".gemini" / "google_accounts.json"), {"active": account})
    return result

def sync_profiles_noninteractive(direction, mode, dry_run=False, yes=False):
    dirs_to_sync = ["agy-homes", "codex-homes", "claude-homes", ".config/cli-profile-manager"]
    hard_mode = mode == "hard"
    if hard_mode and not yes and not dry_run:
        raise PermissionError("hard sync requires --yes")
    src_base, dst_base = resolve_sync_bases(direction)
    if not src_base.exists():
        raise FileNotFoundError(f"source path not found: {src_base}")
    if not dst_base.exists():
        raise FileNotFoundError(f"destination path not found: {dst_base}")
    copied = 0
    skipped = 0
    delete_paths = []
    copied_items = []
    skipped_items = []
    for name in dirs_to_sync:
        src = src_base / name
        dst = dst_base / name
        if not src.exists():
            continue
        if not path_is_within(dst, dst_base):
            raise PermissionError(f"refusing to sync unsafe destination path: {dst}")
        if hard_mode and dst.exists():
            delete_paths.extend(deletion_preflight_paths(dst))
        if hard_mode and dst.exists() and not dry_run:
            shutil.rmtree(dst)
        if not dry_run:
            dst.mkdir(parents=True, exist_ok=True)
        for root, dirs, files in os.walk(src):
            dirs[:] = [d for d in dirs if d not in ("cache", "log", ".tempmediaStorage", ".venv", "node_modules")]
            rel_root = Path(root).relative_to(src)
            if not dry_run:
                (dst / rel_root).mkdir(parents=True, exist_ok=True)
            for file_name in files:
                if direction == "windows" and name == "agy-homes" and is_windows_agy_backup_name(file_name):
                    skipped += 1
                    continue
                src_file = Path(root) / file_name
                if src_file.is_symlink():
                    skipped += 1
                    skipped_items.append({"source": str(src_file), "reason": "symlink"})
                    continue
                dst_file = dst / rel_root / file_name
                if hard_mode or not dst_file.exists() or src_file.stat().st_mtime > dst_file.stat().st_mtime:
                    copied += 1
                    copied_items.append({"source": str(src_file), "destination": str(dst_file)})
                    if not dry_run:
                        dst_file.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src_file, dst_file)
                else:
                    skipped += 1
                    skipped_items.append({"source": str(src_file), "destination": str(dst_file), "reason": "up-to-date"})
    conversion = sync_agy_credentials_between_bases(src_base, dst_base, direction, dry_run)
    return {
        "ok": True,
        "direction": direction,
        "mode": mode,
        "dry_run": dry_run,
        "source_base": str(src_base),
        "destination_base": str(dst_base),
        "files": copied,
        "copied": copied,
        "skipped": skipped,
        "converted": conversion["converted"],
        "invalid": conversion["invalid"],
        "would_delete": len(delete_paths),
        "delete_paths": delete_paths,
        "copied_items": copied_items,
        "skipped_items": skipped_items,
        "conversion_items": conversion["items"],
    }

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

def print_header(title=""):
    width = 62
    border = "═" * (width - 2)
    print(f"{CLR_BOLD}{CLR_CYAN}╔{border}╗{CLR_RESET}")
    if title:
        padding = (width - 2 - len(title)) // 2
        pad_str = " " * padding
        extra = " " if (width - 2 - len(title)) % 2 != 0 else ""
        print(f"{CLR_BOLD}{CLR_CYAN}║{CLR_RESET}{pad_str}{CLR_BOLD}{CLR_WHITE}{title}{CLR_RESET}{pad_str}{extra}{CLR_BOLD}{CLR_CYAN}║{CLR_RESET}")
    print(f"{CLR_BOLD}{CLR_CYAN}╚{border}╝{CLR_RESET}")

def run_menu(options, title="", shortcuts=None):
    shortcuts = shortcuts or {}
    selected_idx = 0
    while True:
        clear_screen()
        print_header(title)
        print()
        
        for idx, option in enumerate(options):
            if idx == selected_idx:
                print(f"  {CLR_BOLD}{CLR_CYAN}--> \033[40m\033[1;37m{option}{CLR_RESET}")
            else:
                print(f"      \033[90m{option}{CLR_RESET}")
        print()
        print(f"{CLR_WHITE}Use {CLR_BOLD}↑/↓{CLR_RESET}{CLR_WHITE}, digits/shortcuts, {CLR_BOLD}Enter{CLR_RESET}{CLR_WHITE} to confirm, {CLR_BOLD}Esc/q{CLR_RESET}{CLR_WHITE} to go back.{CLR_RESET}")
        
        key = get_key()
        if key == 'up':
            selected_idx = (selected_idx - 1) % len(options)
        elif key == 'down':
            selected_idx = (selected_idx + 1) % len(options)
        elif key == 'enter':
            return selected_idx
        elif key.isdigit() and key != "0":
            idx = int(key) - 1
            if 0 <= idx < len(options):
                return idx
        elif key in shortcuts:
            return shortcuts[key]
        elif key in ('esc', 'q'):
            return -1
        elif key == 'ctrl+c':
            sys.exit(0)

def view_status(tool_key):
    clear_screen()
    tool_name = TOOLS[tool_key]["name"]
    print_header(f"STATUS: {tool_name.upper()}")
    print()
    
    metadata = load_metadata()
    profiles = get_display_profiles(tool_key)
    
    print(f"{CLR_BOLD}{CLR_WHITE}{'Profile':<9} {'Active Account / Tier':<30} {'Status':<12} {'Label':<12}{CLR_RESET}")
    print("-" * 64)
    
    for n in profiles:
        status = get_profile_status(tool_key, n, metadata)
        stat_str = f"{CLR_GREEN}Active{CLR_RESET}" if status["has_token"] else f"{CLR_RED}No Token{CLR_RESET}"
        lbl_str = f"({status['label']})" if status["label"] else ""
        email_color = CLR_CYAN if status["has_token"] else CLR_RESET
        print(f"p{status['num']:<7} {email_color}{status['email']:<30}{CLR_RESET} {stat_str:<12} {CLR_YELLOW}{lbl_str:<12}{CLR_RESET}")
        
    print()
    input("Press Enter to return...")

def launch_account(tool_key):
    tool = TOOLS[tool_key]
    metadata = load_metadata()
    while True:
        profiles = get_display_profiles(tool_key)
        options = []
        for n in profiles:
            status = get_profile_status(tool_key, n, metadata)
            lbl = f" ({status['label']})" if status['label'] else ""
            tok = f"{CLR_GREEN}[Active]{CLR_RESET}" if status['has_token'] else f"{CLR_RED}[No Token]{CLR_RESET}"
            options.append(f"p{status['num']:<3} | {status['email']:<28} {tok}{CLR_YELLOW}{lbl}{CLR_RESET}")
            
        sel = run_menu(options, f"LAUNCH {tool['name'].upper()}")
        if sel == -1:
            break
            
        profile_num = profiles[sel]
        status = status_payload(tool_key, profile_num, metadata)
        if not status["has_token"]:
            clear_screen()
            print_header(f"LAUNCH p{profile_num} ({tool['cmd']})")
            print(f"\n{CLR_RED}Profile p{profile_num} has no token. Use login or import first.{CLR_RESET}")
            input("\nPress Enter to continue...")
            continue
        
        clear_screen()
        print_header(f"LAUNCHING p{profile_num} ({tool['cmd']})")
        print(f"\nConfig directory: {profile_home(tool_key, profile_num)}\n")
        print(f"{CLR_YELLOW}Running CLI... Exit the tool normally to return here.{CLR_RESET}\n")
        code = run_cli_tool(tool_key, profile_num)
        if code != EXIT_OK:
            print(f"{CLR_RED}Command exited with code {code}.{CLR_RESET}")
            input("\nPress Enter to continue...")
        
        # Refresh metadata
        metadata = load_metadata()

def add_account(tool_key):
    tool = TOOLS[tool_key]
    clear_screen()
    print_header(f"ADD NEW PROFILE ({tool['cmd']})")
    print()
    
    next_p = first_free_profile(tool_key)
    
    p_num_input = input(f"Enter profile number [Default: {next_p}]: ").strip()
    if p_num_input:
        try:
            next_p = parse_profile(p_num_input)
        except ValueError:
            print(f"{CLR_RED}Invalid profile number!{CLR_RESET}")
            input("\nPress Enter to return...")
            return
            
    os.makedirs(profile_home(tool_key, next_p), exist_ok=True)
    
    clear_screen()
    print_header(f"SETUP p{next_p} ({tool['cmd']})")
    print(f"\nConfig directory: {profile_home(tool_key, next_p)}\n")
    print("Launching CLI to sign in.")
    print("Complete the browser authentication flow. Once logged in, exit the tool.\n")
    input("Press Enter to start authentication...")
    
    logging.info(f"Adding new profile p{next_p} for {tool_key}")
    code = run_cli_tool(tool_key, next_p)
    if code == EXIT_OK:
        logging.info(f"Successfully configured new profile p{next_p} for {tool_key}")
    else:
        print(f"{CLR_RED}Command exited with code {code}.{CLR_RESET}")
        
    print(f"\n{CLR_GREEN}Setup finished for p{next_p}!{CLR_RESET}")
    input("Press Enter to return...")

def set_label(tool_key):
    tool = TOOLS[tool_key]
    metadata = load_metadata()
    while True:
        profiles = get_display_profiles(tool_key)
        options = []
        for n in profiles:
            status = get_profile_status(tool_key, n, metadata)
            lbl = f" ({status['label']})" if status['label'] else " (no label)"
            options.append(f"p{status['num']:<3} | {status['email']:<28} {CLR_YELLOW}{lbl}{CLR_RESET}")
            
        sel = run_menu(options, f"LABEL {tool['name'].upper()}")
        if sel == -1:
            break
            
        profile_num = profiles[sel]
        clear_screen()
        print_header(f"LABEL p{profile_num} ({tool['cmd']})")
        print()
        
        current_lbl = metadata.get(tool_key, {}).get(f"p{profile_num}", {}).get("label", "")
        print(f"Current label: {CLR_YELLOW}{current_lbl or '(none)'}{CLR_RESET}\n")
        new_lbl = input("Enter new label (or empty to clear): ").strip()
        
        label_profile(tool_key, profile_num, new_lbl)
        metadata = load_metadata()
        
        print(f"\n{CLR_GREEN}Label updated successfully!{CLR_RESET}")
        input("Press Enter to return...")

def find_windows_user():
    try:
        users = os.listdir("/mnt/c/Users")
        for u in users:
            if u not in ["Public", "Default", "Default User", "All Users", "desktop.ini"]:
                return u
    except Exception:
        pass
    return "Oliver"

def magic_import(tool_key):
    tool = TOOLS[tool_key]
    clear_screen()
    print_header(f"MAGIC IMPORT: {tool['name'].upper()}")
    print()
    
    win_user = find_windows_user()
    print(f"Scanning Windows drives for user: {win_user}...\n")
    
    found_files = []
    if tool_key == "agy":
        pattern = f"/mnt/c/Users/{win_user}/agy-homes/cred-*.json"
        found_files.extend(glob.glob(pattern))
    elif tool_key == "codex":
        pattern = f"/mnt/c/Users/{win_user}/codex-homes/p*/auth.json"
        found_files.extend(glob.glob(pattern))
    elif tool_key == "claude":
        pattern = f"/mnt/c/Users/{win_user}/claude-homes/p*/.credentials.json"
        found_files.extend(glob.glob(pattern))
        
    if not found_files:
        print(f"{CLR_YELLOW}No Windows credentials found automatically.{CLR_RESET}")
        input("\nPress Enter to return...")
        return
        
    options = []
    for f in found_files:
        options.append(f)
        
    sel = run_menu(options, "SELECT FILE TO IMPORT")
    if sel == -1:
        return
        
    cred_file = found_files[sel]
    
    next_p = first_free_profile(tool_key)
    
    p_num_input = input(f"\nSelected: {cred_file}\nEnter target profile number [Default: {next_p}]: ").strip()
    if p_num_input:
        try:
            next_p = parse_profile(p_num_input)
        except ValueError:
            print(f"\n{CLR_RED}Invalid profile number!{CLR_RESET}")
            input("\nPress Enter to return...")
            return
            
    print(f"\nImporting into profile p{next_p}...")
    
    try:
        _, dest_file = import_credential_file(tool_key, cred_file, next_p)
        print(f"\n{CLR_GREEN}Successfully imported credential to {dest_file}!{CLR_RESET}")
    except Exception as e:
        print(f"\n{CLR_RED}Import error: {e}{CLR_RESET}")
        
    input("\nPress Enter to return...")

def export_credential(tool_key):
    tool = TOOLS[tool_key]
    metadata = load_metadata()
    while True:
        profiles = get_profiles(tool_key)
        options = []
        valid_profiles = []
        for n in profiles:
            status = get_profile_status(tool_key, n, metadata)
            if status['has_token']:
                lbl = f" ({status['label']})" if status['label'] else ""
                options.append(f"p{status['num']:<3} | {status['email']:<28} {CLR_GREEN}[Active]{CLR_RESET}{CLR_YELLOW}{lbl}{CLR_RESET}")
                valid_profiles.append(n)
                
        if not valid_profiles:
            clear_screen()
            print_header(f"EXPORT {tool['name'].upper()}")
            print(f"\n{CLR_YELLOW}No active profiles to export.{CLR_RESET}")
            input("\nPress Enter to return...")
            break
            
        sel = run_menu(options, f"EXPORT {tool['name'].upper()}")
        if sel == -1:
            break
            
        profile_num = valid_profiles[sel]
        try:
            dest_file = export_credential_file(tool_key, profile_num)
            print(f"\n{CLR_GREEN}Successfully exported to Windows: {dest_file}{CLR_RESET}")
        except Exception as e:
            print(f"\n{CLR_RED}Export error: {e}{CLR_RESET}")
                
        input("\nPress Enter to return...")

def clear_profile(tool_key):
    tool = TOOLS[tool_key]
    metadata = load_metadata()
    while True:
        profiles = get_display_profiles(tool_key)
        options = []
        for n in profiles:
            status = get_profile_status(tool_key, n, metadata)
            lbl = f" ({status['label']})" if status['label'] else ""
            tok = f"{CLR_GREEN}[Active]{CLR_RESET}" if status['has_token'] else f"{CLR_RED}[No Token]{CLR_RESET}"
            options.append(f"p{status['num']:<3} | {status['email']:<28} {tok}{CLR_YELLOW}{lbl}{CLR_RESET}")
            
        sel = run_menu(options, f"CLEAR PROFILE: {tool['name'].upper()}")
        if sel == -1:
            break
            
        profile_num = profiles[sel]
        home = profile_home(tool_key, profile_num)
        
        clear_screen()
        print_header(f"CLEAR p{profile_num}")
        print(f"\n{CLR_RED}WARNING: This will completely delete the profile folder and log you out!{CLR_RESET}")
        print(f"Path: {home}")
        confirm = input("\nType 'yes' to confirm deletion: ").strip().lower()
        if confirm == 'yes':
            logging.info(f"Clearing profile p{profile_num} for {tool_key} at {home}")
            try:
                clear_profile_data(tool_key, profile_num)
                print(f"\n{CLR_GREEN}Profile p{profile_num} has been cleared.{CLR_RESET}")
                logging.info(f"Successfully cleared profile p{profile_num}")
            except Exception as e:
                logging.error(f"Error clearing profile p{profile_num}: {e}")
                print(f"\n{CLR_RED}Error clearing profile: {e}{CLR_RESET}")
        else:
            print("\nOperation cancelled.")
            
        input("\nPress Enter to return...")

def import_credential(tool_key):
    tool = TOOLS[tool_key]
    clear_screen()
    print_header(f"IMPORT CREDENTIAL: {tool['name'].upper()}")
    print()
    
    print(f"{CLR_WHITE}{tool['import_help']}{CLR_RESET}\n")
    
    cred_file = input("Enter path to file to import: ").strip()
    
    cred_file = normalize_credential_path(tool_key, cred_file)
    
    if not os.path.exists(cred_file):
        print(f"\n{CLR_RED}Error: File '{cred_file}' not found.{CLR_RESET}")
        input("\nPress Enter to return...")
        return
        
    next_p = first_free_profile(tool_key)
    
    p_num_input = input(f"Enter target profile number [Default: {next_p}]: ").strip()
    if p_num_input:
        try:
            next_p = parse_profile(p_num_input)
        except ValueError:
            print(f"\n{CLR_RED}Invalid profile number!{CLR_RESET}")
            input("\nPress Enter to return...")
            return
            
    print(f"\nImporting into profile p{next_p}...")
    
    try:
        _, dest_file = import_credential_file(tool_key, cred_file, next_p)
        print(f"\n{CLR_GREEN}Successfully imported credential to {dest_file}!{CLR_RESET}")
            
    except Exception as e:
        print(f"\n{CLR_RED}Import error: {e}{CLR_RESET}")
        
    input("\nPress Enter to return...")

def run_tool_manager(tool_key):
    tool = TOOLS[tool_key]
    menu_options = [
        "[>] Launch Account",
        "[+] Add New Profile (OAuth)",
        "[*] Magic Import from Windows",
        "[<] Import Windows Credential (Manual)",
        "[^] Export Credential to Windows",
        "[-] Clear / Logout Profile",
        "[#] Set Profile Label",
        "[i] Detailed Account Status",
        "[x] Back to main menu"
    ]
    
    while True:
        shortcuts = {
            ">": 0,
            "+": 1,
            "a": 1,
            "*": 2,
            "i": 3,
            "<": 3,
            "e": 4,
            "^": 4,
            "c": 5,
            "-": 5,
            "l": 6,
            "#": 6,
            "s": 7,
        }
        sel = run_menu(menu_options, tool["name"].upper(), shortcuts)
        if sel == 0:
            launch_account(tool_key)
        elif sel == 1:
            add_account(tool_key)
        elif sel == 2:
            magic_import(tool_key)
        elif sel == 3:
            import_credential(tool_key)
        elif sel == 4:
            export_credential(tool_key)
        elif sel == 5:
            clear_profile(tool_key)
        elif sel == 6:
            set_label(tool_key)
        elif sel == 7:
            view_status(tool_key)
        elif sel in (8, -1):
            break

def sync_profiles():
    clear_screen()
    print_header("SYNC PROFILES (WSL <-> WINDOWS)")
    print()

    options = [
        "1. [SOFT] WSL -> Windows (Update newer files only)",
        "2. [SOFT] Windows -> WSL (Update newer files only)",
        "3. [HARD] WSL -> Windows (Exact mirror, delete extra files)",
        "4. [HARD] Windows -> WSL (Exact mirror, delete extra files)",
        "5. Cancel"
    ]
    
    sel = run_menu(options, "SYNC DIRECTION & MODE")
    if sel in (4, -1):
        return
        
    is_hard = sel in (2, 3)
    is_wsl_to_win = sel in (0, 2)
    direction = "wsl" if is_wsl_to_win else "windows"
    mode = "hard" if is_hard else "soft"
    src_base, dst_base = resolve_sync_bases(direction)
    
    clear_screen()
    print_header("SYNCHRONIZING...")
    print()

    print(f"Mode:  {'HARD (Mirror)' if is_hard else 'SOFT (Incremental)'}")
    print(f"Source: {src_base}")
    print(f"Dest:   {dst_base}\n")

    if is_hard:
        try:
            preflight = sync_profiles_noninteractive(direction, mode, dry_run=True, yes=True)
            print(f"Hard-delete preflight: {preflight['would_delete']} destination paths would be removed.")
            for path in preflight["delete_paths"]:
                print(f"  {path}")
        except Exception as e:
            print(f"{CLR_RED}Preflight failed: {e}{CLR_RESET}")
            input("\nPress Enter to return...")
            return
        print(f"{CLR_RED}WARNING: Hard sync will DELETE extra files in Dest that are not in Source.{CLR_RESET}")
        confirm = input("Type 'yes' to proceed: ").strip().lower()
        if confirm != 'yes':
            print("Operation cancelled.")
            input("\nPress Enter to return...")
            return

    try:
        result = sync_profiles_noninteractive(direction, mode, dry_run=False, yes=True)
    except Exception as e:
        logging.error(f"Sync failed: {e}")
        print(f"{CLR_RED}Sync failed: {e}{CLR_RESET}")
        input("\nPress Enter to return...")
        return

    logging.info(f"Sync completed successfully: {result}")
    print(
        f"{CLR_GREEN}Updated {result['copied']} files, skipped {result['skipped']}, "
        f"converted {result['converted']} agy credentials, invalid {result['invalid']}.{CLR_RESET}"
    )
    print(f"\n{CLR_CYAN}Sync Complete!{CLR_RESET}")
    input("\nPress Enter to return...")

def build_parser():
    parser = argparse.ArgumentParser(
        prog="ai-man",
        description="Keyboard-first profile manager for agy, codex, and claude.",
    )
    sub = parser.add_subparsers(dest="command")

    list_p = sub.add_parser("list", help="list profiles for a tool")
    list_p.add_argument("tool", choices=TOOLS.keys())
    list_p.add_argument("--json", action="store_true")
    list_p.set_defaults(func=cmd_list)

    status_p = sub.add_parser("status", help="show one profile status")
    status_p.add_argument("tool", choices=TOOLS.keys())
    status_p.add_argument("profile")
    status_p.add_argument("--json", action="store_true")
    status_p.set_defaults(func=cmd_status)

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
    import_p.add_argument("--json", action="store_true")
    import_p.set_defaults(func=cmd_import)

    export_p = sub.add_parser("export", help="export a profile credential")
    export_p.add_argument("tool", choices=TOOLS.keys())
    export_p.add_argument("profile")
    export_p.add_argument("--to")
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

    while True:
        options = [
            "[1] Antigravity CLI (agy)",
            "[2] OpenAI Codex CLI",
            "[3] Anthropic Claude CLI",
            "[4] Sync Profiles (WSL <-> Windows)",
            "[x] Exit"
        ]
        sel = run_menu(options, "UNIFIED PROFILE MANAGER")
        if sel == 0:
            run_tool_manager("agy")
        elif sel == 1:
            run_tool_manager("codex")
        elif sel == 2:
            run_tool_manager("claude")
        elif sel == 3:
            sync_profiles()
        elif sel in (4, -1):
            clear_screen()
            print("Exiting Profile Manager. Goodbye!")
            break
    return EXIT_OK

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        clear_screen()
        sys.exit(0)
