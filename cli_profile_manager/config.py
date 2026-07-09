import os
import re
from pathlib import Path

from .metadata import METADATA_DIR
from .paths import TOOLS, resolve_sync_bases
from .process_policy import process_policy


TOKEN_LIKE_RE = re.compile(
    r"(?i)(sk-[a-z0-9_-]+|xox[a-z]-[a-z0-9-]+|gh[pousr]_[a-z0-9_]+|ya29\.[a-z0-9._-]+|refresh_token)"
)


def redact_sensitive(value):
    if not isinstance(value, str):
        return value
    return TOKEN_LIKE_RE.sub("[redacted-token]", value)


CONFIG_ENV_VARS = [
    {
        "name": "AI_MAN_AGY_HOME",
        "description": "Antigravity profile root",
        "default": "~/agy-homes",
        "type": "path",
    },
    {
        "name": "AI_MAN_CODEX_HOME",
        "description": "Codex profile root",
        "default": "~/codex-homes",
        "type": "path",
    },
    {
        "name": "AI_MAN_CLAUDE_HOME",
        "description": "Claude profile root",
        "default": "~/claude-homes",
        "type": "path",
    },
    {
        "name": "AI_MAN_METADATA_DIR",
        "description": "metadata and labels directory",
        "default": "~/.config/cli-profile-manager",
        "type": "path",
    },
    {
        "name": "AI_MAN_WSL_HOME",
        "description": "WSL sync root override",
        "default": "~",
        "type": "path",
    },
    {
        "name": "AI_MAN_WINDOWS_HOME",
        "description": "Windows sync root override",
        "default": "detected Windows user home",
        "type": "path",
    },
    {
        "name": "AI_MAN_INTERACTIVE_QUOTA",
        "description": "enable automatic interactive quota loading",
        "default": "1",
        "type": "bool",
    },
    {
        "name": "AI_MAN_SERVICE",
        "description": "enable optional local runtime service client for eligible read-only commands",
        "default": "0",
        "type": "bool",
    },
    {
        "name": "AI_MAN_INTERACTIVE_QUOTA_TIMEOUT",
        "description": "generic interactive quota timeout in seconds",
        "default": "12",
        "type": "float",
        "minimum": 1.0,
    },
    {
        "name": "AI_MAN_INTERACTIVE_AGY_QUOTA_TIMEOUT",
        "description": "AGY interactive quota timeout in seconds",
        "default": "40",
        "type": "float",
        "minimum": 1.0,
    },
    {
        "name": "AI_MAN_INTERACTIVE_AGY_QUOTA_CONCURRENCY",
        "description": "AGY interactive quota worker count",
        "default": "2",
        "type": "int",
        "minimum": 1,
    },
    {
        "name": "AI_MAN_INTERACTIVE_QUOTA_FRESH_SECONDS",
        "description": "quota color freshness threshold in seconds",
        "default": "600",
        "type": "float",
        "minimum": 1.0,
    },
    {
        "name": "AI_MAN_QUOTA_STARTUP_SECONDS",
        "description": "native CLI startup wait before slash command probing",
        "default": "3 or 8 for AGY",
        "type": "float",
        "minimum": 0.0,
    },
    {
        "name": "AI_MAN_QUOTA_POST_COMMAND_SECONDS",
        "description": "post-command wait after quota slash command",
        "default": "4 or 8 for AGY",
        "type": "float",
        "minimum": 0.0,
    },
    {
        "name": "AI_MAN_QUOTA_KEY_DELAY_SECONDS",
        "description": "per-key delay when typing slash commands into the PTY",
        "default": "0.04",
        "type": "float",
        "minimum": 0.0,
    },
    {
        "name": "AI_MAN_QUOTA_SESSION_TTL_SECONDS",
        "description": "persistent quota session idle TTL in seconds",
        "default": "1800",
        "type": "float",
        "minimum": 1.0,
    },
    {
        "name": "AI_MAN_QUOTA_SESSION_MAX",
        "description": "maximum persistent quota sessions",
        "default": "24",
        "type": "int",
        "minimum": 1,
    },
    {
        "name": "AI_MAN_AGY_QUOTA_COMMAND",
        "description": "AGY quota slash command override",
        "default": "/usage",
        "type": "string",
    },
    {
        "name": "AI_MAN_CODEX_QUOTA_COMMAND",
        "description": "Codex quota slash command override",
        "default": "/status",
        "type": "string",
    },
    {
        "name": "AI_MAN_CLAUDE_QUOTA_COMMAND",
        "description": "Claude quota slash command override",
        "default": "/usage",
        "type": "string",
    },
    {
        "name": "AI_MAN_PROCESS_LIMITS",
        "description": "enable process resource limits",
        "default": "1",
        "type": "bool",
    },
    {
        "name": "AI_MAN_PROCESS_MEMORY_MB",
        "description": "foreground launch memory cap in MB",
        "default": "4096",
        "type": "int",
    },
    {
        "name": "AI_MAN_PROCESS_CPU_PERCENT",
        "description": "foreground launch CPU quota percent",
        "default": "300",
        "type": "int",
    },
    {
        "name": "AI_MAN_PROCESS_MAX_PROCESSES",
        "description": "foreground launch process count cap",
        "default": "256",
        "type": "int",
    },
    {
        "name": "AI_MAN_PROCESS_NICE",
        "description": "foreground launch nice adjustment",
        "default": "5",
        "type": "int",
    },
    {
        "name": "AI_MAN_PROCESS_IONICE_CLASS",
        "description": "foreground launch ionice class",
        "default": "2",
        "type": "int",
    },
    {
        "name": "AI_MAN_PROCESS_IONICE_LEVEL",
        "description": "foreground launch ionice level",
        "default": "6",
        "type": "int",
    },
    {
        "name": "AI_MAN_PROCESS_SYSTEMD",
        "description": "prefer systemd user scopes when available",
        "default": "1",
        "type": "bool",
    },
    {
        "name": "AI_MAN_QUOTA_PROCESS_LIMITS",
        "description": "enable quota probe process limits",
        "default": "1",
        "type": "bool",
    },
    {
        "name": "AI_MAN_QUOTA_PROCESS_MEMORY_MB",
        "description": "quota probe memory cap in MB",
        "default": "2048",
        "type": "int",
    },
    {
        "name": "AI_MAN_QUOTA_PROCESS_CPU_PERCENT",
        "description": "quota probe CPU quota percent",
        "default": "150",
        "type": "int",
    },
    {
        "name": "AI_MAN_QUOTA_PROCESS_MAX_PROCESSES",
        "description": "quota probe process count cap",
        "default": "512",
        "type": "int",
    },
    {
        "name": "AI_MAN_QUOTA_PROCESS_NICE",
        "description": "quota probe nice adjustment",
        "default": "10",
        "type": "int",
    },
    {
        "name": "AI_MAN_QUOTA_PROCESS_IONICE_CLASS",
        "description": "quota probe ionice class",
        "default": "2",
        "type": "int",
    },
    {
        "name": "AI_MAN_QUOTA_PROCESS_IONICE_LEVEL",
        "description": "quota probe ionice level",
        "default": "7",
        "type": "int",
    },
]


def _bool_value(raw, default=True):
    if raw is None:
        return default
    return str(raw).lower() not in ("0", "false", "no", "off")


def _numeric_value(name, raw, fallback, value_type, minimum, warnings):
    if raw is None:
        return fallback
    try:
        value = int(raw) if value_type == "int" else float(raw)
    except ValueError:
        warnings.append(f"{name}={raw!r} is invalid; using {fallback}")
        return fallback
    if value < minimum:
        warnings.append(f"{name}={raw!r} is below {minimum:g}; using {fallback}")
        return fallback
    return value


def _env_item(definition):
    return {
        "name": definition["name"],
        "description": definition["description"],
        "default": definition["default"],
        "type": definition["type"],
        "value": redact_sensitive(os.environ.get(definition["name"])),
    }


def effective_config_payload():
    warnings = []
    wsl_base, windows_base = resolve_sync_bases("wsl")
    quota = {
        "interactive_enabled": _bool_value(os.environ.get("AI_MAN_INTERACTIVE_QUOTA"), True),
        "interactive_timeout": _numeric_value(
            "AI_MAN_INTERACTIVE_QUOTA_TIMEOUT",
            os.environ.get("AI_MAN_INTERACTIVE_QUOTA_TIMEOUT"),
            12.0,
            "float",
            1.0,
            warnings,
        ),
        "interactive_agy_timeout": _numeric_value(
            "AI_MAN_INTERACTIVE_AGY_QUOTA_TIMEOUT",
            os.environ.get("AI_MAN_INTERACTIVE_AGY_QUOTA_TIMEOUT"),
            40.0,
            "float",
            1.0,
            warnings,
        ),
        "interactive_agy_concurrency": _numeric_value(
            "AI_MAN_INTERACTIVE_AGY_QUOTA_CONCURRENCY",
            os.environ.get("AI_MAN_INTERACTIVE_AGY_QUOTA_CONCURRENCY"),
            2,
            "int",
            1,
            warnings,
        ),
        "interactive_fresh_seconds": _numeric_value(
            "AI_MAN_INTERACTIVE_QUOTA_FRESH_SECONDS",
            os.environ.get("AI_MAN_INTERACTIVE_QUOTA_FRESH_SECONDS"),
            600.0,
            "float",
            1.0,
            warnings,
        ),
        "startup_seconds": _numeric_value(
            "AI_MAN_QUOTA_STARTUP_SECONDS",
            os.environ.get("AI_MAN_QUOTA_STARTUP_SECONDS"),
            3.0,
            "float",
            0.0,
            warnings,
        ),
        "post_command_seconds": _numeric_value(
            "AI_MAN_QUOTA_POST_COMMAND_SECONDS",
            os.environ.get("AI_MAN_QUOTA_POST_COMMAND_SECONDS"),
            4.0,
            "float",
            0.0,
            warnings,
        ),
        "key_delay_seconds": _numeric_value(
            "AI_MAN_QUOTA_KEY_DELAY_SECONDS",
            os.environ.get("AI_MAN_QUOTA_KEY_DELAY_SECONDS"),
            0.04,
            "float",
            0.0,
            warnings,
        ),
        "session_ttl_seconds": _numeric_value(
            "AI_MAN_QUOTA_SESSION_TTL_SECONDS",
            os.environ.get("AI_MAN_QUOTA_SESSION_TTL_SECONDS"),
            1800.0,
            "float",
            1.0,
            warnings,
        ),
        "session_max": _numeric_value(
            "AI_MAN_QUOTA_SESSION_MAX",
            os.environ.get("AI_MAN_QUOTA_SESSION_MAX"),
            24,
            "int",
            1,
            warnings,
        ),
        "commands": {
            "agy": redact_sensitive(os.environ.get("AI_MAN_AGY_QUOTA_COMMAND", "/usage")),
            "codex": redact_sensitive(os.environ.get("AI_MAN_CODEX_QUOTA_COMMAND", "/status")),
            "claude": redact_sensitive(os.environ.get("AI_MAN_CLAUDE_QUOTA_COMMAND", "/usage")),
        },
    }
    process_limits = {
        "launch": process_policy("launch"),
        "quota": process_policy("quota"),
        "validation": process_policy("validation"),
    }
    for policy in process_limits.values():
        warnings.extend(policy.get("warnings", []))
    return {
        "ok": True,
        "profile_roots": {tool: config["base_dir"] for tool, config in TOOLS.items()},
        "metadata_dir": METADATA_DIR,
        "sync_roots": {
            "wsl": str(Path(wsl_base)),
            "windows": str(Path(windows_base)),
        },
        "quota": quota,
        "process_limits": process_limits,
        "environment": [_env_item(definition) for definition in CONFIG_ENV_VARS],
        "warnings": warnings,
    }
