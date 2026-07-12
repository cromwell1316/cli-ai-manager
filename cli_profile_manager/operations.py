#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess

from cli_profile_manager.metadata import label_profile, load_metadata
from cli_profile_manager.paths import (
    DISPLAY_SLOT_COUNT,
    TOOLS,
    agy_windows_credential_path,
    credential_path,
    find_windows_user,
    first_free_profile,
    get_display_profiles,
    get_occupied_profiles,
    make_tool_env,
    normalize_credential_path,
    parse_profile,
    profile_home,
    resolve_sync_bases,
)

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_NOT_FOUND = 3
EXIT_NO_TOKEN = 4
EXIT_RUNTIME = 5

RESULT_SUCCESS = "success"
RESULT_CANCELLED = "cancelled"
RESULT_VALIDATION_ERROR = "validation_error"
RESULT_NOT_FOUND = "not_found"
RESULT_NO_TOKEN = "no_token"
RESULT_RUNTIME_FAILURE = "runtime_failure"
core_quota_payload = None
run_persistent_cli_quota_snapshot = None
run_windows_agy_quota_snapshot = None
core_audit = None
core_process_policy = None
core_runtime_service = None
core_sync = None
core_config = None
core_agy_credentials = None
core_claude_credentials = None
core_codex_credentials = None
core_credentials_common = None
core_windows_support = None
core_shutil = None
DEFAULT_AGY_QUOTA_TIMEOUT_SECONDS = 120
DEFAULT_QUOTA_TIMEOUT_SECONDS = 20


def is_native_windows():
    return os.name == "nt"


class OperationResult:
    __slots__ = ("status", "exit_code", "payload", "message", "error_type", "exception")

    def __init__(self, status, exit_code, payload=None, message=None, error_type=None, exception=None):
        self.status = status
        self.exit_code = exit_code
        self.payload = {} if payload is None else payload
        self.message = message
        self.error_type = error_type
        self.exception = exception

    @property
    def ok(self):
        return self.status == RESULT_SUCCESS and self.exit_code == EXIT_OK

    def json_error_payload(self):
        return {
            "ok": False,
            "error": {
                "type": self.error_type or self.status,
                "message": self.message or "",
                "code": self.exit_code,
            },
        }


class FileFact:
    __slots__ = ("path", "exists", "mtime_ns", "size")

    def __init__(self, path, exists, mtime_ns=None, size=None):
        self.path = path
        self.exists = exists
        self.mtime_ns = mtime_ns
        self.size = size


class ProfileFact:
    __slots__ = (
        "tool_key",
        "num",
        "home",
        "home_fact",
        "credential",
        "account",
        "agy_log_dir",
        "windows_credential",
        "agy_cli_token",
    )

    def __init__(
        self,
        tool_key,
        num,
        home,
        home_fact,
        credential,
        account=None,
        agy_log_dir=None,
        windows_credential=None,
        agy_cli_token=None,
    ):
        self.tool_key = tool_key
        self.num = num
        self.home = home
        self.home_fact = home_fact
        self.credential = credential
        self.account = account
        self.agy_log_dir = agy_log_dir
        self.windows_credential = windows_credential
        self.agy_cli_token = agy_cli_token


def success(payload=None, message=None, exit_code=EXIT_OK):
    return OperationResult(RESULT_SUCCESS, exit_code, payload or {}, message)


def validation_error(message, payload=None):
    return OperationResult(RESULT_VALIDATION_ERROR, EXIT_USAGE, payload or {}, str(message), "usage_error")


def not_found(message, payload=None):
    return OperationResult(RESULT_NOT_FOUND, EXIT_NOT_FOUND, payload or {}, str(message), "not_found")


def no_token(message, payload=None):
    return OperationResult(RESULT_NO_TOKEN, EXIT_NO_TOKEN, payload or {}, str(message), "no_token")


def runtime_failure(message, payload=None, exception=None):
    return OperationResult(RESULT_RUNTIME_FAILURE, EXIT_RUNTIME, payload or {}, str(message), "runtime_error", exception)


def cancelled(message, payload=None):
    return OperationResult(RESULT_CANCELLED, EXIT_USAGE, payload or {}, str(message), "confirmation_required")


def _file_fact(path):
    path = str(path)
    try:
        stat = os.stat(path)
    except OSError:
        return FileFact(path, False)
    return FileFact(path, True, stat.st_mtime_ns, stat.st_size)


def _profile_num_from_name(name):
    if name.startswith("p") and name[1:].isdigit():
        return int(name[1:])
    return None


def _audit():
    global core_audit
    if core_audit is None:
        from cli_profile_manager import audit as module

        core_audit = module
    return core_audit


def _process_policy():
    global core_process_policy
    if core_process_policy is None:
        from cli_profile_manager import process_policy as module

        core_process_policy = module
    return core_process_policy


def _runtime_service():
    global core_runtime_service
    if core_runtime_service is None:
        from cli_profile_manager import runtime_service as module

        core_runtime_service = module
    return core_runtime_service


def _sync():
    global core_sync
    if core_sync is None:
        from cli_profile_manager import sync as module

        core_sync = module
    return core_sync


def _config():
    global core_config
    if core_config is None:
        from cli_profile_manager import config as module

        core_config = module
    return core_config


def _agy_credentials():
    global core_agy_credentials
    if core_agy_credentials is None:
        from cli_profile_manager.credentials import agy as module

        core_agy_credentials = module
    return core_agy_credentials


def _claude_credentials():
    global core_claude_credentials
    if core_claude_credentials is None:
        from cli_profile_manager.credentials import claude as module

        core_claude_credentials = module
    return core_claude_credentials


def _codex_credentials():
    global core_codex_credentials
    if core_codex_credentials is None:
        from cli_profile_manager.credentials import codex as module

        core_codex_credentials = module
    return core_codex_credentials


def _credentials_common():
    global core_credentials_common
    if core_credentials_common is None:
        from cli_profile_manager.credentials import common as module

        core_credentials_common = module
    return core_credentials_common


def _windows_support():
    global core_windows_support
    if core_windows_support is None:
        from cli_profile_manager import windows_support as module

        core_windows_support = module
    return core_windows_support


def _shutil():
    global core_shutil
    if core_shutil is None:
        import shutil as module

        core_shutil = module
    return core_shutil


def _redacted_windows_backup_summary(path, profile=None):
    path = os.path.abspath(str(path))
    payload = {
        "profile": f"p{profile}" if profile else None,
        "path": path,
        "exists": os.path.exists(path),
        "valid": False,
        "account": None,
        "saved_at": None,
        "blob_size": None,
        "size": None,
        "error": None,
    }
    if not payload["exists"]:
        payload["error"] = "missing"
        return payload
    try:
        stat = os.stat(path)
        payload["size"] = stat.st_size
        data = _credentials_common().read_json_object(path, encoding="utf-8-sig")
        _token_data, account = decode_windows_agy_credential(path)
        payload.update({
            "valid": True,
            "account": account,
            "saved_at": data.get("SavedAt"),
            "blob_size": data.get("BlobSize"),
        })
    except Exception as exc:
        payload["error"] = str(exc).replace("BlobBase64", "credential blob")
    return payload


def agy_windows_backups_payload(base_dir=None):
    base = os.path.abspath(str(base_dir or TOOLS["agy"]["base_dir"]))
    backups = []
    if os.path.isdir(base):
        for name in sorted(os.listdir(base)):
            num = _windows_agy_credential_num(name)
            if num is None:
                continue
            backups.append(_redacted_windows_backup_summary(os.path.join(base, name), num))
    return {
        "ok": True,
        "tool": "agy",
        "base_dir": base,
        "backups": backups,
    }


def _run_windows_agy_helper_action(action, profile_num, base_dir):
    powershell = _windows_support().powershell_executable(_shutil())
    if powershell is None:
        raise FileNotFoundError("PowerShell is required for Windows agy Credential Manager recovery")
    helper = _windows_support().ensure_windows_agy_helper(base_dir)
    argv = _windows_support().windows_agy_launch_argv(
        powershell,
        helper,
        action,
        profile_num,
        base_dir,
        TOOLS["agy"]["cmd"],
        [],
    )
    completed = subprocess.run(argv, text=True, capture_output=True, check=False)
    output = "\n".join(part for part in (completed.stdout, completed.stderr) if part)
    if completed.returncode != 0:
        raise RuntimeError(output.strip() or f"Windows AGY helper action {action} failed with exit code {completed.returncode}")
    return {"returncode": completed.returncode, "helper": helper, "output": output.strip()}


def agy_credential_recovery_operation(action, profile=None, source=None, set_live=False, dry_run=False):
    try:
        action = action.replace("_", "-")
        if action == "whoami":
            return success(agy_windows_backups_payload())

        n = parse_profile(profile) if profile else 0
        base_dir = TOOLS["agy"]["base_dir"]
        backup_path = agy_windows_credential_path(n, base_dir) if n > 0 else None
        live_action = action in {"set", "save", "clear"}
        restore_action = action == "restore"
        if not (live_action or restore_action):
            raise ValueError(f"unknown AGY credential recovery action: {action}")

        if live_action and not is_native_windows() and not dry_run:
            raise RuntimeError("live Windows AGY Credential Manager recovery requires native Windows")

        if action in {"set", "save", "restore"} and n <= 0:
            raise ValueError("profile is required and must be a positive pN number")

        if action == "set":
            summary = _redacted_windows_backup_summary(backup_path, n)
            if not summary["valid"]:
                raise FileNotFoundError(f"valid Windows AGY backup not found for p{n}: {summary['error']}")
            payload = {
                "ok": True,
                "tool": "agy",
                "action": "set",
                "profile": f"p{n}",
                "backup": summary,
                "live_slot": "gemini:antigravity",
                "would_set_live": bool(dry_run),
            }
            if dry_run:
                payload["dry_run"] = True
                return success(payload)
            payload["helper"] = _run_windows_agy_helper_action("Set", n, base_dir)
            payload["set_live"] = True
            return success(payload)

        if action == "save":
            payload = {
                "ok": True,
                "tool": "agy",
                "action": "save",
                "profile": f"p{n}",
                "destination": os.path.abspath(backup_path),
                "live_slot": "gemini:antigravity",
                "would_save_live": bool(dry_run),
            }
            if dry_run:
                payload["dry_run"] = True
                return success(payload)
            payload["helper"] = _run_windows_agy_helper_action("Save", n, base_dir)
            payload["saved"] = _redacted_windows_backup_summary(backup_path, n)
            return success(payload)

        if action == "clear":
            payload = {
                "ok": True,
                "tool": "agy",
                "action": "clear",
                "live_slot": "gemini:antigravity",
                "would_clear_live": bool(dry_run),
            }
            if dry_run:
                payload["dry_run"] = True
                return success(payload)
            payload["helper"] = _run_windows_agy_helper_action("Clear", 0, base_dir)
            payload["cleared_live"] = True
            return success(payload)

        source_path = normalize_credential_path("agy", source or "")
        if not source_path:
            raise ValueError("restore source path is required")
        source_summary = _redacted_windows_backup_summary(source_path)
        if not source_summary["valid"]:
            raise FileNotFoundError(f"valid Windows AGY backup not found: {source_summary['error']}")
        if set_live and not is_native_windows() and not dry_run:
            raise RuntimeError("setting the live Windows AGY Credential Manager slot requires native Windows")
        destination = os.path.abspath(backup_path)
        payload = {
            "ok": True,
            "tool": "agy",
            "action": "restore",
            "profile": f"p{n}",
            "source": source_summary,
            "destination": destination,
            "set_live": bool(set_live),
            "would_restore": bool(dry_run),
            "would_set_live": bool(dry_run and set_live),
        }
        if dry_run:
            payload["dry_run"] = True
            return success(payload)
        _credentials_common().ensure_parent(destination)
        tmp_path = f"{destination}.tmp-{os.getpid()}"
        _shutil().copy2(source_path, tmp_path)
        os.replace(tmp_path, destination)
        if source_summary.get("account"):
            _credentials_common().write_json_atomic(
                os.path.join(profile_home("agy", n), TOOLS["agy"]["acct_file"]),
                {"active": source_summary["account"]},
            )
        payload["restored"] = _redacted_windows_backup_summary(destination, n)
        if set_live:
            payload["helper"] = _run_windows_agy_helper_action("Set", n, base_dir)
        return success(payload)
    except ValueError as e:
        return validation_error(str(e))
    except FileNotFoundError as e:
        return not_found(str(e))
    except Exception as e:
        return runtime_failure(f"AGY credential recovery failed: {e}", exception=e)


def _windows_agy_credential_num(name):
    if name.startswith("cred-p") and name.endswith(".json"):
        raw = name[6:-5]
        if raw.isdigit():
            return int(raw)
    return None


class ProfileIndex:
    def __init__(self, tool_key):
        self.tool_key = tool_key
        self.tool = TOOLS[tool_key]
        self.base_dir = self.tool["base_dir"]
        self.base_fact = _file_fact(self.base_dir)
        self._occupied_profiles = None
        self._display_profiles = None
        self._facts = {}
        self._scan_base()

    def _scan_base(self):
        if not self.base_fact.exists:
            os.makedirs(self.base_dir, exist_ok=True)
            self.base_fact = _file_fact(self.base_dir)

        profiles = set()
        try:
            with os.scandir(self.base_dir) as entries:
                for entry in entries:
                    num = _profile_num_from_name(entry.name)
                    if num is not None:
                        profiles.add(num)
                        continue
                    if is_native_windows() and self.tool_key == "agy":
                        num = _windows_agy_credential_num(entry.name)
                        if num is not None:
                            profiles.add(num)
        except OSError:
            profiles = set()
        self._occupied_profiles = sorted(profiles)

    def occupied_profiles(self):
        return self._occupied_profiles

    def display_profiles(self):
        if self._display_profiles is None:
            profiles = set(self._occupied_profiles)
            profiles.update(range(1, DISPLAY_SLOT_COUNT + 1))
            self._display_profiles = sorted(profiles)
        return self._display_profiles

    def fact(self, n):
        if n not in self._facts:
            home = profile_home(self.tool_key, n)
            cred = credential_path(self.tool_key, n)
            account_file = self.tool.get("acct_file")
            account = _file_fact(os.path.join(home, account_file)) if account_file else None
            self._facts[n] = ProfileFact(
                tool_key=self.tool_key,
                num=n,
                home=home,
                home_fact=_file_fact(home),
                credential=_file_fact(cred),
                account=account,
                agy_log_dir=_file_fact(os.path.join(home, ".gemini", "antigravity-cli", "log")) if self.tool_key == "agy" else None,
                windows_credential=_file_fact(agy_windows_credential_path(n, self.base_dir)) if self.tool_key == "agy" else None,
                agy_cli_token=_file_fact(os.path.join(home, _agy_credentials().AGY_CLI_TOKEN_FILE)) if self.tool_key == "agy" else None,
            )
        return self._facts[n]

    def fingerprint(self):
        facts = [self.base_fact]
        for num in sorted(self._facts):
            fact = self._facts[num]
            facts.extend(
                item
                for item in (
                    fact.home_fact,
                    fact.credential,
                    fact.account,
                    fact.agy_log_dir,
                    fact.windows_credential,
                    fact.agy_cli_token,
                )
                if item is not None
            )
        return tuple((fact.path, fact.exists, fact.mtime_ns, fact.size) for fact in facts)

    def is_stale(self):
        current = ProfileIndex(self.tool_key)
        for num in self._facts:
            current.fact(num)
        return current.fingerprint() != self.fingerprint()


class CommandSnapshot:
    def __init__(self, metadata=None):
        self.metadata = load_metadata() if metadata is None else metadata
        self.index_by_tool = {}
        self.occupied_by_tool = {}
        self.display_by_tool = {}
        self.status_by_profile = {}
        self.account_by_profile = {}

    def profile_index(self, tool_key):
        if tool_key not in self.index_by_tool:
            self.index_by_tool[tool_key] = ProfileIndex(tool_key)
        return self.index_by_tool[tool_key]

    def occupied_profiles(self, tool_key):
        if tool_key not in self.occupied_by_tool:
            self.occupied_by_tool[tool_key] = self.profile_index(tool_key).occupied_profiles()
        return self.occupied_by_tool[tool_key]

    def display_profiles(self, tool_key):
        if tool_key not in self.display_by_tool:
            self.display_by_tool[tool_key] = self.profile_index(tool_key).display_profiles()
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
                account_email_from_google_accounts(home)
                if tool_key == "agy"
                else None
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
                profile_fact=self.profile_index(tool_key).fact(n),
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

    def is_stale(self):
        return any(index.is_stale() for index in self.index_by_tool.values())


def command_snapshot(metadata=None):
    return CommandSnapshot(metadata)


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


def _windows_agy_quota_runner():
    global run_windows_agy_quota_snapshot
    if run_windows_agy_quota_snapshot is None:
        from cli_profile_manager.quota import run_windows_agy_quota_snapshot as func

        run_windows_agy_quota_snapshot = func
    return run_windows_agy_quota_snapshot


def quota_probe_command(tool_key, n):
    if tool_key == "agy" and is_native_windows():
        from cli_profile_manager.quota import WINDOWS_AGY_QUOTA_PROMPT

        return [TOOLS[tool_key]["cmd"], "-p", WINDOWS_AGY_QUOTA_PROMPT]
    return [TOOLS[tool_key]["cmd"]]


def quota_probe_env(tool_key, n):
    return make_tool_env(tool_key, n)


def quota_probe_cwd(tool_key, n):
    return profile_home(tool_key, n)


def quota_probe_runner(tool_key, runner=None):
    if runner is not None:
        return runner
    if tool_key == "agy" and is_native_windows():
        return _windows_agy_quota_runner()
    return _persistent_quota_runner()


def account_email_from_google_accounts(home):
    return _agy_credentials().account_email_from_profile(home, TOOLS["agy"]["acct_file"])


def decode_windows_agy_credential(win_cred_path):
    return _agy_credentials().decode_windows_credential(win_cred_path)


def read_wsl_agy_oauth(token_path):
    return _agy_credentials().read_wsl_oauth(token_path)


def build_windows_agy_credential(token_data, account=None):
    return _agy_credentials().build_windows_credential(token_data, account)


def import_windows_agy_credential(win_cred_path, profile_num):
    return _agy_credentials().import_windows_credential(
        win_cred_path,
        profile_home("agy", profile_num),
        credential_path("agy", profile_num),
        TOOLS["agy"]["acct_file"],
    )


def export_wsl_agy_credential(profile_num, win_cred_path):
    return _agy_credentials().export_wsl_credential(
        credential_path("agy", profile_num),
        profile_home("agy", profile_num),
        win_cred_path,
        TOOLS["agy"]["acct_file"],
    )


def get_profile_status(tool_key, n, metadata, account_email_provider=None, profile_fact=None):
    tool = TOOLS[tool_key]
    home = profile_fact.home if profile_fact is not None else os.path.join(tool["base_dir"], f"p{n}")
    cred_path = profile_fact.credential.path if profile_fact is not None else os.path.join(home, tool["cred_file"])
    cred_exists = profile_fact.credential.exists if profile_fact is not None else os.path.exists(cred_path)
    account_lookup = account_email_provider or account_email_from_google_accounts

    email = "(no login)"
    has_token = False
    token_state = "missing"
    credential_source = None
    account = None
    warnings = []

    if tool_key == "agy":
        if is_native_windows():
            win_cred_path = (
                profile_fact.windows_credential.path
                if profile_fact is not None and profile_fact.windows_credential is not None
                else agy_windows_credential_path(n, tool["base_dir"])
            )
            win_cred_exists = (
                profile_fact.windows_credential.exists
                if profile_fact is not None and profile_fact.windows_credential is not None
                else os.path.exists(win_cred_path)
            )
            if win_cred_exists:
                try:
                    _, account = decode_windows_agy_credential(win_cred_path)
                    has_token = True
                    token_state = "valid"
                    credential_source = "windows-backup"
                    email = account or account_lookup(home) or "logged in"
                except Exception as e:
                    token_state = "invalid"
                    credential_source = "windows-backup"
                    warnings.append(str(e))
                    email = f"invalid token: {e}"
        elif cred_exists:
            try:
                read_wsl_agy_oauth(cred_path)
                has_token = True
                token_state = "valid"
                credential_source = "wsl-oauth"
                account = account_lookup(home)
                email = account or "logged in"
            except Exception as e:
                token_state = "invalid"
                credential_source = "wsl-oauth"
                warnings.append(str(e))
                email = f"invalid token: {e}"
        else:
            read_agy_cli_token = getattr(_agy_credentials(), "read_agy_cli_token", None)
            if read_agy_cli_token is not None:
                agy_cli_token_exists = (
                    profile_fact.agy_cli_token.exists
                    if profile_fact is not None and profile_fact.agy_cli_token is not None
                    else None
                )
                try:
                    if agy_cli_token_exists is False:
                        raise FileNotFoundError(profile_fact.agy_cli_token.path)
                    read_agy_cli_token(home)
                    has_token = True
                    token_state = "valid"
                    credential_source = "agy-cli-token"
                    account = account_lookup(home)
                    email = account or "logged in"
                except FileNotFoundError:
                    pass
                except Exception as e:
                    token_state = "invalid"
                    credential_source = "agy-cli-token"
                    warnings.append(str(e))
                    email = f"invalid token: {e}"
    elif cred_exists:
        has_token = True
        token_state = "present"
        credential_source = "codex-auth" if tool_key == "codex" else "claude-credentials"

    if tool_key == "codex" and has_token:
        try:
            email = _codex_credentials().account_from_auth(cred_path)
            token_state = "valid"
            account = email
        except Exception as e:
            token_state = "invalid"
            warnings.append(str(e))
            email = "logged in"
    elif tool_key == "claude" and has_token:
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
        "home": home,
    }


def _status_payload(tool_key, n, metadata, occupied_profiles=None, account_email_provider=None, profile_fact=None):
    occupied_profiles = get_occupied_profiles(tool_key) if occupied_profiles is None else occupied_profiles
    status = get_profile_status(
        tool_key,
        n,
        metadata,
        account_email_provider=account_email_provider,
        profile_fact=profile_fact,
    )
    status["exists"] = n in occupied_profiles
    return status


def status_payload(tool_key, n, metadata=None, snapshot=None):
    if snapshot is not None:
        return snapshot.status(tool_key, n)
    return _status_payload(tool_key, n, load_metadata() if metadata is None else metadata)


def quota_payload(tool_key, n, timeout_seconds=None, runner=None):
    default_timeout = DEFAULT_AGY_QUOTA_TIMEOUT_SECONDS if tool_key == "agy" else DEFAULT_QUOTA_TIMEOUT_SECONDS
    timeout = timeout_seconds if timeout_seconds is not None else default_timeout
    kwargs = {"timeout_seconds": timeout}
    runner = quota_probe_runner(tool_key, runner)
    if runner is not None:
        kwargs["runner"] = runner
    try:
        return _quota_payload_func()(
            tool_key,
            f"p{n}",
            quota_probe_command(tool_key, n),
            quota_probe_env(tool_key, n),
            quota_probe_cwd(tool_key, n),
            **kwargs,
        )
    except TypeError as e:
        if "unexpected keyword argument 'runner'" not in str(e):
            raise
        kwargs.pop("runner", None)
        return _quota_payload_func()(
            tool_key,
            f"p{n}",
            quota_probe_command(tool_key, n),
            quota_probe_env(tool_key, n),
            quota_probe_cwd(tool_key, n),
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


def list_profiles_operation(tool_key, include_quota=False, timeout_seconds=20, snapshot=None):
    snapshot = snapshot or command_snapshot()
    profiles = snapshot.display_profiles(tool_key)
    statuses = (
        [snapshot.status_with_quota(tool_key, n, timeout_seconds) for n in profiles]
        if include_quota
        else [snapshot.status(tool_key, n) for n in profiles]
    )
    return success({
        "tool": tool_key,
        "next_profile": f"p{snapshot.first_free_profile(tool_key)}",
        "profiles": statuses,
    })


def profile_status_operation(tool_key, profile, include_quota=False, timeout_seconds=20, snapshot=None):
    try:
        n = parse_profile(profile)
    except ValueError as e:
        return validation_error(str(e))
    snapshot = snapshot or command_snapshot()
    payload = snapshot.status_with_quota(tool_key, n, timeout_seconds) if include_quota else snapshot.status(tool_key, n)
    return success(payload)


def profile_quota_operation(tool_key, profile, timeout_seconds=20, snapshot=None):
    try:
        n = parse_profile(profile)
    except ValueError as e:
        return validation_error(str(e))
    snapshot = snapshot or command_snapshot()
    status = snapshot.status(tool_key, n)
    if not status["has_token"]:
        return no_token(f"profile p{n} has no token; use login or import first")
    return success(quota_payload(tool_key, n, timeout_seconds))


def import_credential_file(tool_key, cred_file, profile_num=None):
    source = normalize_credential_path(tool_key, cred_file)
    if not os.path.exists(source):
        raise FileNotFoundError(f"file '{source}' not found")
    n = profile_num if profile_num is not None else first_free_profile(tool_key)
    if n <= 0:
        raise ValueError("profile number must be positive")
    dest_file = credential_path(tool_key, n)
    if tool_key == "agy":
        if is_native_windows():
            _, account = decode_windows_agy_credential(source)
            os.makedirs(profile_home("agy", n), exist_ok=True)
            dest_file = agy_windows_credential_path(n)
            _credentials_common().ensure_parent(dest_file)
            tmp_path = f"{dest_file}.tmp-{os.getpid()}"
            _shutil().copy2(source, tmp_path)
            os.replace(tmp_path, dest_file)
            if account:
                _credentials_common().write_json_atomic(
                    os.path.join(profile_home("agy", n), TOOLS["agy"]["acct_file"]),
                    {"active": account},
                )
        else:
            dest_file = import_windows_agy_credential(source, n)
    else:
        _credentials_common().ensure_parent(dest_file)
        tmp_path = f"{dest_file}.tmp-{os.getpid()}"
        _shutil().copy2(source, tmp_path)
        os.replace(tmp_path, dest_file)
    return n, dest_file


def import_credential_operation(tool_key, cred_file, profile=None, dry_run=False):
    try:
        n = parse_profile(profile) if profile else None
        source = normalize_credential_path(tool_key, cred_file)
        if not os.path.exists(source):
            raise FileNotFoundError(f"file '{source}' not found")
        import_num = n if n is not None else first_free_profile(tool_key)
        if import_num <= 0:
            raise ValueError("profile number must be positive")
        if tool_key == "agy":
            decode_windows_agy_credential(source)
        dest_file = (
            agy_windows_credential_path(import_num)
            if tool_key == "agy" and is_native_windows()
            else credential_path(tool_key, import_num)
        )
        if dry_run:
            return success({
                "ok": True,
                "dry_run": True,
                "tool": tool_key,
                "profile": f"p{import_num}",
                "source": source,
                "destination": dest_file,
                "would_import": True,
            })
        imported_num, dest_file = import_credential_file(tool_key, cred_file, n)
        return success({
            "ok": True,
            "tool": tool_key,
            "profile": f"p{imported_num}",
            "destination": dest_file,
        })
    except ValueError as e:
        return validation_error(str(e))
    except FileNotFoundError as e:
        return not_found(str(e))
    except Exception as e:
        return runtime_failure(f"import failed: {e}", exception=e)


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
        if is_native_windows():
            src_file = agy_windows_credential_path(profile_num)
            decode_windows_agy_credential(src_file)
            _credentials_common().ensure_parent(dest_file)
            tmp_path = f"{dest_file}.tmp-{os.getpid()}"
            _shutil().copy2(src_file, tmp_path)
            os.replace(tmp_path, dest_file)
        else:
            export_wsl_agy_credential(profile_num, dest_file)
    else:
        _credentials_common().ensure_parent(dest_file)
        tmp_path = f"{dest_file}.tmp-{os.getpid()}"
        _shutil().copy2(src_file, tmp_path)
        os.replace(tmp_path, dest_file)
    return dest_file


def export_credential_operation(tool_key, profile, to_path=None, dry_run=False):
    try:
        n = parse_profile(profile)
        if dry_run:
            status = status_payload(tool_key, n)
            if not status["has_token"]:
                raise PermissionError(f"profile p{n} has no token to export")
            _, dest_file = resolve_export_destination(tool_key, n, to_path)
            return success({
                "ok": True,
                "dry_run": True,
                "tool": tool_key,
                "profile": f"p{n}",
                "source": agy_windows_credential_path(n) if tool_key == "agy" and is_native_windows() else credential_path(tool_key, n),
                "destination": dest_file,
                "would_export": True,
            })
        dest_file = export_credential_file(tool_key, n, to_path)
        return success({"ok": True, "tool": tool_key, "profile": f"p{n}", "destination": dest_file})
    except ValueError as e:
        return validation_error(str(e))
    except PermissionError as e:
        return no_token(str(e))
    except Exception as e:
        return runtime_failure(f"export failed: {e}", exception=e)


def label_profile_operation(tool_key, profile, label):
    try:
        n = parse_profile(profile)
        label_profile(tool_key, n, label)
        return success({"ok": True, "tool": tool_key, "profile": f"p{n}", "label": label})
    except ValueError as e:
        return validation_error(str(e))
    except Exception as e:
        return runtime_failure(f"label failed: {e}", exception=e)


def clear_profile_data(tool_key, n):
    home = profile_home(tool_key, n)
    base = os.path.abspath(TOOLS[tool_key]["base_dir"])
    target = os.path.abspath(home)
    if not target.startswith(base + os.sep):
        raise ValueError(f"refusing to clear unsafe path: {target}")
    if os.path.exists(home):
        _shutil().rmtree(home)
    if tool_key == "agy":
        win_cred = os.path.abspath(agy_windows_credential_path(n, base))
        if not win_cred.startswith(base + os.sep):
            raise ValueError(f"refusing to clear unsafe path: {win_cred}")
        if os.path.exists(win_cred):
            os.remove(win_cred)
    return home


def clear_profile_operation(tool_key, profile):
    try:
        n = parse_profile(profile)
        cleared_home = clear_profile_data(tool_key, n)
        return success({"ok": True, "tool": tool_key, "profile": f"p{n}", "cleared": cleared_home})
    except ValueError as e:
        return validation_error(str(e))
    except Exception as e:
        return runtime_failure(f"clear failed: {e}", exception=e)


def sync_profiles_noninteractive(direction, mode, dry_run=False, yes=False):
    src_base, dst_base = resolve_sync_bases(direction)
    return _sync().sync_profiles_between_bases(src_base, dst_base, direction, mode, dry_run, yes)


def sync_profiles_operation(direction, mode, dry_run=False, yes=False):
    try:
        return success(sync_profiles_noninteractive(direction, mode, dry_run, yes))
    except PermissionError as e:
        return validation_error(str(e))
    except FileNotFoundError as e:
        return not_found(str(e))
    except Exception as e:
        return runtime_failure(f"sync failed: {e}", exception=e)


def config_show_operation(include_sources=False, filter_text=None):
    return success(_config().effective_config_payload(include_sources=include_sources, filter_text=filter_text))


def config_health_operation():
    payload = _config().config_health_payload()
    return success({"ok": True, **payload})


def audit_operation(action, **kwargs):
    audit = _audit()
    if action == "status":
        return success(audit.status_payload())
    if action == "list":
        return success({
            "ok": True,
            "events": audit.query_events(
                limit=kwargs.get("limit"),
                category=kwargs.get("category"),
                command=kwargs.get("command"),
                tool=kwargs.get("tool"),
                profile=kwargs.get("profile"),
                result=kwargs.get("result"),
                correlation_id=kwargs.get("correlation_id"),
                since=kwargs.get("since"),
                until=kwargs.get("until"),
            ),
        })
    if action == "show":
        events = audit.show_events(kwargs.get("identifier"))
        return success({"ok": True, "events": events}) if events else not_found("audit event not found", {"ok": True, "events": events})
    if action == "export":
        return success({"ok": True, "events": audit.query_events(limit=None)})
    if action == "purge":
        return success({"ok": True, "removed": audit.purge_all()})
    if action == "compact":
        return success({"ok": True, **audit.compact_retention(kwargs.get("days"), kwargs.get("max_bytes"))})
    return validation_error(f"unknown audit action: {action}")


def runtime_service_operation(action, profile_manager_path=None):
    runtime_service = _runtime_service()
    if action == "status":
        payload = {"ok": True, "service": runtime_service.service_status()}
        try:
            health = runtime_service.service_health() if payload["service"]["running"] else None
        except Exception:
            health = None
        if health:
            payload["service"]["health"] = health
        return success(payload)
    if action == "start":
        payload = runtime_service.start_service(profile_manager_path)
        return success({"ok": bool(payload.get("ok")), "service": payload}) if payload.get("ok") else runtime_failure(payload.get("error", "unknown error"), {"ok": False, "service": payload})
    if action == "stop":
        return success({"ok": True, "service": runtime_service.stop_service()})
    if action == "restart":
        runtime_service.stop_service()
        payload = runtime_service.start_service(profile_manager_path)
        return success({"ok": bool(payload.get("ok")), "service": payload}) if payload.get("ok") else runtime_failure(payload.get("error", "unknown error"), {"ok": False, "service": payload})
    return validation_error(f"unknown service action: {action}")


def prepare_launch_command(tool_key, n, extra_args=None):
    tool = TOOLS[tool_key]
    cmd = [tool["cmd"]] + list(extra_args or [])
    return _process_policy().prepare_popen(
        cmd,
        tier="launch",
        needs_pty=False,
        unit_name=f"ai-man-{tool_key}-p{n}",
    )
