import os
from pathlib import Path

from .diagnostics import redact_sensitive
from .metadata import METADATA_DIR
from .paths import TOOLS, resolve_sync_bases


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
        "commands": {
            "agy": redact_sensitive(os.environ.get("AI_MAN_AGY_QUOTA_COMMAND", "/usage")),
            "codex": redact_sensitive(os.environ.get("AI_MAN_CODEX_QUOTA_COMMAND", "/status")),
            "claude": redact_sensitive(os.environ.get("AI_MAN_CLAUDE_QUOTA_COMMAND", "/usage")),
        },
    }
    return {
        "ok": True,
        "profile_roots": {tool: config["base_dir"] for tool, config in TOOLS.items()},
        "metadata_dir": METADATA_DIR,
        "sync_roots": {
            "wsl": str(Path(wsl_base)),
            "windows": str(Path(windows_base)),
        },
        "quota": quota,
        "environment": [_env_item(definition) for definition in CONFIG_ENV_VARS],
        "warnings": warnings,
    }
