import hashlib
import os
import re
import time

from .executable_lookup import executable_path
from .paths import DISPLAY_SLOT_COUNT, TOOLS, get_display_profiles, get_occupied_profiles, profile_home
from .quota import (
    QuotaProbeError,
    agy_quota_backend_configured,
    persistent_quota_sessions_snapshot,
    quota_command_for,
    resolve_quota_backend,
    tmux_path,
)
from .windows_support import windows_agy_concurrency_policy, windows_agy_recovery_commands


TOKEN_LIKE_RE = re.compile(
    r"(?i)(sk-[a-z0-9_-]+|xox[a-z]-[a-z0-9-]+|gh[pousr]_[a-z0-9_]+|ya29\.[a-z0-9._-]+|refresh_token)"
)
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@([A-Z0-9.-]+\.[A-Z]{2,})\b", re.I)
DIAGNOSTICS_MODES = {"fast", "deep"}


def _invalid_mode(mode):
    return mode not in DIAGNOSTICS_MODES


def stable_hash(value):
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:12]


def redact_account(value, show_accounts=False):
    if value is None or show_accounts:
        return value
    text = str(value)
    if text.startswith("redacted:"):
        return text

    def repl(match):
        return f"redacted:{stable_hash(match.group(0))}@{match.group(1).lower()}"

    return EMAIL_RE.sub(repl, text)


def redact_sensitive(value, show_accounts=False):
    if isinstance(value, dict):
        return {key: redact_sensitive(item, show_accounts) for key, item in value.items()}
    if isinstance(value, list):
        return [redact_sensitive(item, show_accounts) for item in value]
    if not isinstance(value, str):
        return value
    text = TOKEN_LIKE_RE.sub("[redacted-token]", value)
    return redact_account(text, show_accounts)


def relevant_env_snapshot():
    keys = [
        "AI_MAN_AGY_HOME",
        "AI_MAN_CODEX_HOME",
        "AI_MAN_CLAUDE_HOME",
        "AI_MAN_METADATA_DIR",
        "AI_MAN_WSL_HOME",
        "AI_MAN_WINDOWS_HOME",
        "AI_MAN_INTERACTIVE_QUOTA",
        "AI_MAN_INTERACTIVE_QUOTA_TIMEOUT",
        "AI_MAN_INTERACTIVE_AGY_QUOTA_TIMEOUT",
        "AI_MAN_INTERACTIVE_AGY_QUOTA_CONCURRENCY",
        "AI_MAN_QUOTA_STARTUP_SECONDS",
        "AI_MAN_AGY_QUOTA_STARTUP_SECONDS",
        "AI_MAN_QUOTA_POST_COMMAND_SECONDS",
        "AI_MAN_QUOTA_KEY_DELAY_SECONDS",
        "AI_MAN_QUOTA_SESSION_TTL_SECONDS",
        "AI_MAN_QUOTA_SESSION_MAX",
        "AI_MAN_AGY_QUOTA_BACKEND",
        "AI_MAN_AUDIT",
        "AI_MAN_AUDIT_BACKEND",
        "AI_MAN_AUDIT_STRICT",
        "AI_MAN_AUDIT_RETENTION_DAYS",
        "AI_MAN_AUDIT_MAX_BYTES",
        "AI_MAN_AUDIT_SHOW_ACCOUNTS",
        "AI_MAN_AUDIT_SHOW_PATHS",
        "AI_MAN_PROCESS_LIMITS",
        "AI_MAN_PROCESS_MEMORY_MB",
        "AI_MAN_PROCESS_CPU_PERCENT",
        "AI_MAN_PROCESS_MAX_PROCESSES",
        "AI_MAN_PROCESS_NICE",
        "AI_MAN_PROCESS_IONICE_CLASS",
        "AI_MAN_PROCESS_IONICE_LEVEL",
        "AI_MAN_PROCESS_SYSTEMD",
        "AI_MAN_QUOTA_PROCESS_LIMITS",
        "AI_MAN_QUOTA_PROCESS_MEMORY_MB",
        "AI_MAN_QUOTA_PROCESS_CPU_PERCENT",
        "AI_MAN_QUOTA_PROCESS_MAX_PROCESSES",
        "AI_MAN_QUOTA_PROCESS_NICE",
        "AI_MAN_QUOTA_PROCESS_IONICE_CLASS",
        "AI_MAN_QUOTA_PROCESS_IONICE_LEVEL",
    ]
    return {key: os.environ.get(key) for key in keys if key in os.environ}


def tool_diagnostics(
    tool_key,
    status_provider=None,
    show_accounts=False,
    occupied_profiles=None,
    display_profiles=None,
):
    tool = TOOLS[tool_key]
    occupied = get_occupied_profiles(tool_key) if occupied_profiles is None else occupied_profiles
    display = get_display_profiles(tool_key) if display_profiles is None else display_profiles
    profiles = []
    status_provider = status_provider or (lambda _tool, _num: None)
    for num in display:
        status = status_provider(tool_key, num)
        profile = {
            "profile": f"p{num}",
            "home": profile_home(tool_key, num),
            "occupied": num in occupied,
        }
        if status:
            profile.update({
                "has_token": status.get("has_token"),
                "token_state": status.get("token_state"),
                "credential_source": status.get("credential_source"),
                "account": redact_account(status.get("account") or status.get("email"), show_accounts),
                "warnings": redact_sensitive(status.get("warnings", []), show_accounts),
            })
        profiles.append(profile)
    cli_path = executable_path(tool["cmd"])
    return {
        "name": tool["name"],
        "command": tool["cmd"],
        "quota_command": quota_command_for(tool_key),
        "base_dir": tool["base_dir"],
        "credential_file": tool["cred_file"],
        "cli_available": cli_path is not None,
        "cli_path": cli_path,
        "display_slot_count": DISPLAY_SLOT_COUNT,
        "occupied_profiles": [f"p{num}" for num in occupied],
        "visible_profiles": [f"p{num}" for num in display],
        "profiles": profiles,
    }


def fast_process_policy_diagnostics():
    from . import process_policy

    def int_env(name, default, warnings):
        raw = os.environ.get(name)
        if raw is None:
            return default
        try:
            return int(raw)
        except ValueError:
            warnings.append(f"{name}={raw!r} is invalid; using {default}")
            return default

    enabled = os.environ.get("AI_MAN_PROCESS_LIMITS", "1").lower() not in ("0", "false", "no", "off", "disabled")
    quota_enabled = os.environ.get("AI_MAN_QUOTA_PROCESS_LIMITS")
    validation_enabled = os.environ.get("AI_MAN_VALIDATION_PROCESS_LIMITS")

    def tier_enabled(tier):
        if tier == "quota" and quota_enabled is not None:
            return quota_enabled.lower() not in ("0", "false", "no", "off", "disabled")
        if tier == "validation" and validation_enabled is not None:
            return validation_enabled.lower() not in ("0", "false", "no", "off", "disabled")
        return enabled

    policies = {}
    for tier, defaults in process_policy.DEFAULTS.items():
        tier_is_enabled = tier_enabled(tier)
        backend = "disabled"
        if tier_is_enabled:
            backend = "systemd-run-check-skipped" if defaults.get("prefer_systemd") and tier == "launch" else "setrlimit"
        prefix = "AI_MAN_QUOTA_" if tier == "quota" else "AI_MAN_VALIDATION_" if tier == "validation" else "AI_MAN_"
        warnings = []
        policies[tier] = {
            "tier": tier,
            "enabled": tier_is_enabled,
            "backend": backend,
            "memory_mb": int_env(f"{prefix}PROCESS_MEMORY_MB", defaults["memory_mb"], warnings),
            "cpu_percent": int_env(f"{prefix}PROCESS_CPU_PERCENT", defaults["cpu_percent"], warnings),
            "max_processes": int_env(f"{prefix}PROCESS_MAX_PROCESSES", defaults["max_processes"], warnings),
            "warnings": warnings,
        }
    return {
        "supported": os.name != "nt",
        "systemd_user_scope_available": None,
        "systemd_user_scope_check": "skipped_fast_diagnostics",
        "policies": policies,
    }


def fast_audit_diagnostics():
    from . import audit

    selected_path = audit.sqlite_path() if audit.backend_name() == "sqlite" else audit.jsonl_path()
    return {
        "ok": True,
        "enabled": audit.audit_enabled(),
        "strict": audit.strict_mode(),
        "backend": audit.backend_name(),
        "path": str(selected_path),
        "audit_dir": str(audit.audit_dir()),
        "audit_dir_mode": audit.user_only_mode(audit.audit_dir()),
        "path_mode": audit.user_only_mode(selected_path),
        "record_count": None,
        "record_count_check": "skipped_fast_diagnostics",
        "retention_days": audit.retention_days(),
        "max_bytes": audit.max_bytes(),
    }


def fast_quota_runtime_snapshot(tool_key=None):
    return {
        "enabled": os.environ.get("AI_MAN_INTERACTIVE_QUOTA", "1").lower() not in ("0", "false", "no", "off"),
        "active_jobs": 0,
        "cache": [],
        "scheduler": None,
        "states": [
            "empty",
            "queued",
            "running",
            "available",
            "stale_refreshing",
            "retry_wait",
            "failed",
            "auth_required",
            "disabled",
        ],
        "failure_states": [
            "timeout",
            "parser_miss",
            "missing_cli",
            "process_exit",
            "auth_required",
            "empty_output",
            "pty_failure",
            "exception",
            "resource_limited",
            "tty_unavailable",
            "account_ineligible",
            "resource_exhausted",
            "unsupported",
            "unknown",
        ],
        "legal_transitions": {
            "queued": ["running", "available", "retry_wait", "failed", "auth_required", "disabled"],
            "running": ["available", "retry_wait", "failed", "auth_required", "disabled"],
        },
        "mode": "fast",
        "tool": tool_key,
    }


def diagnostics_payload(
    tool_key=None,
    status_provider=None,
    show_accounts=False,
    profile_index_provider=None,
    mode="deep",
):
    from .runtime_service import service_status
    from .safety import command_inventory

    if _invalid_mode(mode):
        raise ValueError(f"unknown diagnostics mode: {mode}")

    selected_tools = [tool_key] if tool_key else list(TOOLS)
    if mode == "deep":
        from .config import config_health_payload
        from .audit import diagnostics_payload as audit_diagnostics
        from .interactive import quota_runtime_snapshot
        from .process_policy import diagnostics_payload as process_policy_diagnostics

        config_health = config_health_payload()
        audit_payload = audit_diagnostics()
        process_limits = process_policy_diagnostics()
        quota_runtime = quota_runtime_snapshot(tool_key)
    else:
        from .config import effective_config_payload

        config_payload = effective_config_payload(include_sources=True, include_internal=True, include_health=False)
        config_health = {
            "health": config_payload["config_health"],
            "settings": config_payload["settings_by_key"],
        }
        audit_payload = fast_audit_diagnostics()
        process_limits = fast_process_policy_diagnostics()
        quota_runtime = fast_quota_runtime_snapshot(tool_key)
    agy_backend = {
        "configured": agy_quota_backend_configured(),
        "resolved": None,
        "tmux_path": tmux_path(),
    }
    try:
        agy_backend["resolved"] = resolve_quota_backend("agy")
    except QuotaProbeError as e:
        agy_backend["resolved"] = e.state
        agy_backend["warning"] = str(e)
    native_windows = os.name == "nt"
    agy_concurrency = windows_agy_concurrency_policy(native_windows=native_windows)
    agy_concurrency["recovery_commands"] = windows_agy_recovery_commands("pN")
    agy_concurrency["live_slot_inspection"] = {
        "available": native_windows,
        "method": "managed PowerShell helper and Credential Manager APIs" if native_windows else "native Windows only",
        "token_safe": True,
        "target": agy_concurrency["target"],
    }
    payload = {
        "ok": True,
        "mode": mode,
        "generated_at": int(time.time()),
        "tools": {
            key: tool_diagnostics(
                key,
                status_provider=status_provider,
                show_accounts=show_accounts,
                **(profile_index_provider(key) if profile_index_provider else {}),
            )
            for key in selected_tools
        },
        "environment": relevant_env_snapshot(),
        "audit": audit_payload,
        "process_limits": process_limits,
        "safety_policy": {
            "commands": command_inventory(),
        },
        "config_health": config_health["health"],
        "effective_config": config_health["settings"],
        "service_runtime": service_status(),
        "quota_runtime": quota_runtime,
        "persistent_sessions": persistent_quota_sessions_snapshot(tool_key),
        "agy_quota_backend": agy_backend,
        "agy_windows_concurrency": agy_concurrency,
    }
    return redact_sensitive(payload, show_accounts)
