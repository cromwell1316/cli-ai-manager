#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from dataclasses import dataclass, field
import os
import shutil
from typing import Any

from cli_profile_manager import audit, process_policy, runtime_service, sync
from cli_profile_manager.config import effective_config_payload
from cli_profile_manager.credentials import agy as agy_credentials
from cli_profile_manager.credentials import claude as claude_credentials
from cli_profile_manager.credentials import codex as codex_credentials
from cli_profile_manager.credentials import common as credentials_common
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
run_direct_cli_prompt_snapshot = None
AGY_PROFILE_PROMPT = "review this code in one sentence"


@dataclass
class OperationResult:
    status: str
    exit_code: int
    payload: dict[str, Any] = field(default_factory=dict)
    message: str | None = None
    error_type: str | None = None
    exception: Exception | None = None

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


class CommandSnapshot:
    def __init__(self, metadata=None):
        self.metadata = load_metadata() if metadata is None else metadata
        self.occupied_by_tool = {}
        self.display_by_tool = {}
        self.status_by_profile = {}
        self.account_by_profile = {}

    def occupied_profiles(self, tool_key):
        if tool_key not in self.occupied_by_tool:
            self.occupied_by_tool[tool_key] = get_occupied_profiles(tool_key)
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


def _direct_prompt_runner():
    global run_direct_cli_prompt_snapshot
    if run_direct_cli_prompt_snapshot is None:
        from cli_profile_manager.quota import run_direct_cli_prompt_snapshot as func

        run_direct_cli_prompt_snapshot = func
    return run_direct_cli_prompt_snapshot


def quota_probe_command(tool_key, n):
    if tool_key == "agy":
        return [f"agy{n}", "-p", AGY_PROFILE_PROMPT]
    return [TOOLS[tool_key]["cmd"]]


def quota_probe_env(tool_key, n):
    if tool_key == "agy":
        return os.environ.copy()
    return make_tool_env(tool_key, n)


def quota_probe_cwd(tool_key, n):
    if tool_key == "agy":
        return os.getcwd()
    return profile_home(tool_key, n)


def quota_probe_runner(tool_key, runner=None):
    if runner is not None:
        return runner
    if tool_key == "agy":
        return _direct_prompt_runner()
    return _persistent_quota_runner()


def account_email_from_google_accounts(home):
    return agy_credentials.account_email_from_profile(home, TOOLS["agy"]["acct_file"])


def decode_windows_agy_credential(win_cred_path):
    return agy_credentials.decode_windows_credential(win_cred_path)


def read_wsl_agy_oauth(token_path):
    return agy_credentials.read_wsl_oauth(token_path)


def build_windows_agy_credential(token_data, account=None):
    return agy_credentials.build_windows_credential(token_data, account)


def import_windows_agy_credential(win_cred_path, profile_num):
    return agy_credentials.import_windows_credential(
        win_cred_path,
        profile_home("agy", profile_num),
        credential_path("agy", profile_num),
        TOOLS["agy"]["acct_file"],
    )


def export_wsl_agy_credential(profile_num, win_cred_path):
    return agy_credentials.export_wsl_credential(
        credential_path("agy", profile_num),
        profile_home("agy", profile_num),
        win_cred_path,
        TOOLS["agy"]["acct_file"],
    )


def get_profile_status(tool_key, n, metadata, account_email_provider=None):
    tool = TOOLS[tool_key]
    home = os.path.join(tool["base_dir"], f"p{n}")
    cred_path = os.path.join(home, tool["cred_file"])
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
                    email = account or account_lookup(home) or "logged in"
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
                account = account_lookup(home)
                email = account or "logged in"
            except Exception as e:
                token_state = "invalid"
                credential_source = "wsl-oauth"
                warnings.append(str(e))
                email = f"invalid token: {e}"
        else:
            read_agy_cli_token = getattr(agy_credentials, "read_agy_cli_token", None)
            if read_agy_cli_token is not None:
                try:
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
    elif os.path.exists(cred_path):
        has_token = True
        token_state = "present"
        credential_source = "codex-auth" if tool_key == "codex" else "claude-credentials"

    if tool_key == "codex" and has_token:
        try:
            email = codex_credentials.account_from_auth(cred_path)
            token_state = "valid"
            account = email
        except Exception as e:
            token_state = "invalid"
            warnings.append(str(e))
            email = "logged in"
    elif tool_key == "claude" and has_token:
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
        "home": home,
    }


def _status_payload(tool_key, n, metadata, occupied_profiles=None, account_email_provider=None):
    occupied_profiles = get_occupied_profiles(tool_key) if occupied_profiles is None else occupied_profiles
    status = get_profile_status(tool_key, n, metadata, account_email_provider=account_email_provider)
    status["exists"] = n in occupied_profiles
    return status


def status_payload(tool_key, n, metadata=None, snapshot=None):
    if snapshot is not None:
        return snapshot.status(tool_key, n)
    return _status_payload(tool_key, n, load_metadata() if metadata is None else metadata)


def quota_payload(tool_key, n, timeout_seconds=None, runner=None):
    timeout = timeout_seconds if timeout_seconds is not None else 20
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
        dest_file = import_windows_agy_credential(source, n)
    else:
        credentials_common.ensure_parent(dest_file)
        tmp_path = f"{dest_file}.tmp-{os.getpid()}"
        shutil.copy2(source, tmp_path)
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
        dest_file = credential_path(tool_key, import_num)
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
        export_wsl_agy_credential(profile_num, dest_file)
    else:
        credentials_common.ensure_parent(dest_file)
        tmp_path = f"{dest_file}.tmp-{os.getpid()}"
        shutil.copy2(src_file, tmp_path)
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
                "source": credential_path(tool_key, n),
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
        shutil.rmtree(home)
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
    return sync.sync_profiles_between_bases(src_base, dst_base, direction, mode, dry_run, yes)


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
    return success(effective_config_payload(include_sources=include_sources, filter_text=filter_text))


def audit_operation(action, **kwargs):
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
    return process_policy.prepare_popen(
        cmd,
        tier="launch",
        needs_pty=False,
        unit_name=f"ai-man-{tool_key}-p{n}",
    )
