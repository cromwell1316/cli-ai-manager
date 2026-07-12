import os
import re

from . import metadata, paths


TOKEN_LIKE_RE = re.compile(
    r"(?i)(sk-[a-z0-9_-]+|xox[a-z]-[a-z0-9-]+|gh[pousr]_[a-z0-9_]+|ya29\.[a-z0-9._-]+|refresh_token)"
)
BOOL_FALSE = {"0", "false", "no", "off", "disabled"}
BOOL_TRUE = {"1", "true", "yes", "on", "enabled"}
PROCESS_POLICY_DEFAULTS = {
    "launch": {
        "enabled": True,
        "memory_mb": 4096,
        "cpu_percent": 300,
        "max_processes": None,
        "nice": 5,
        "ionice_class": 2,
        "ionice_level": 6,
        "prefer_systemd": True,
    },
    "quota": {
        "enabled": True,
        "memory_mb": 6144,
        "cpu_percent": 150,
        "max_processes": 4096,
        "nice": 10,
        "ionice_class": 2,
        "ionice_level": 7,
        "prefer_systemd": False,
    },
    "validation": {
        "enabled": True,
        "memory_mb": 2048,
        "cpu_percent": 200,
        "max_processes": 128,
        "nice": 10,
        "ionice_class": 2,
        "ionice_level": 7,
        "prefer_systemd": False,
    },
}
PROCESS_POLICY_FIELD_KEYS = {
    "memory_mb": "MEMORY_MB",
    "cpu_percent": "CPU_PERCENT",
    "max_processes": "MAX_PROCESSES",
    "nice": "NICE",
    "ionice_class": "IONICE_CLASS",
    "ionice_level": "IONICE_LEVEL",
}
PROCESS_POLICY_SETTING_KEYS = {
    "launch": {
        "memory_mb": "process.memory_mb",
        "cpu_percent": "process.cpu_percent",
        "max_processes": "process.max_processes",
        "nice": "process.nice",
        "ionice_class": "process.ionice_class",
        "ionice_level": "process.ionice_level",
    },
    "quota": {
        "memory_mb": "quota_process.memory_mb",
        "cpu_percent": "quota_process.cpu_percent",
        "max_processes": "quota_process.max_processes",
        "nice": "quota_process.nice",
        "ionice_class": "quota_process.ionice_class",
        "ionice_level": "quota_process.ionice_level",
    },
    "validation": {
        "memory_mb": "validation_process.memory_mb",
        "cpu_percent": "validation_process.cpu_percent",
        "max_processes": "validation_process.max_processes",
        "nice": "validation_process.nice",
        "ionice_class": "validation_process.ionice_class",
        "ionice_level": "validation_process.ionice_level",
    },
}


def redact_sensitive(value):
    if not isinstance(value, str):
        return value
    return TOKEN_LIKE_RE.sub("[redacted-token]", value)


class SettingDefinition:
    __slots__ = (
        "key",
        "env",
        "description",
        "default",
        "value_type",
        "category",
        "minimum",
        "maximum",
        "redact",
        "internal",
        "deprecated_aliases",
    )

    def __init__(
        self,
        key,
        env,
        description,
        default,
        value_type="string",
        category="general",
        minimum=None,
        maximum=None,
        redact=False,
        internal=False,
        deprecated_aliases=(),
    ):
        self.key = key
        self.env = env
        self.description = description
        self.default = default
        self.value_type = value_type
        self.category = category
        self.minimum = minimum
        self.maximum = maximum
        self.redact = redact
        self.internal = internal
        self.deprecated_aliases = deprecated_aliases

    @property
    def name(self):
        return self.env[0] if self.env else self.key


CONFIG_REGISTRY = (
    SettingDefinition("paths.agy_home", ("AI_MAN_AGY_HOME",), "Antigravity profile root", "~/agy-homes", "path", "paths"),
    SettingDefinition("paths.codex_home", ("AI_MAN_CODEX_HOME",), "Codex profile root", "~/codex-homes", "path", "paths"),
    SettingDefinition("paths.claude_home", ("AI_MAN_CLAUDE_HOME",), "Claude profile root", "~/claude-homes", "path", "paths"),
    SettingDefinition("paths.metadata_dir", ("AI_MAN_METADATA_DIR",), "metadata and labels directory", "~/.config/cli-profile-manager", "path", "paths"),
    SettingDefinition("sync.wsl_home", ("AI_MAN_WSL_HOME",), "WSL sync root override", "~", "path", "sync"),
    SettingDefinition("sync.windows_home", ("AI_MAN_WINDOWS_HOME",), "Windows sync root override", None, "path", "sync"),
    SettingDefinition("sync.userprofile", ("USERPROFILE",), "Windows user profile fallback", r"C:\Users\Oliver", "path", "sync"),
    SettingDefinition("interactive.quota_enabled", ("AI_MAN_INTERACTIVE_QUOTA",), "enable automatic interactive quota loading", True, "bool", "interactive"),
    SettingDefinition("interactive.quota_timeout", ("AI_MAN_INTERACTIVE_QUOTA_TIMEOUT",), "generic interactive quota timeout in seconds", 12.0, "float", "interactive", minimum=1.0),
    SettingDefinition("interactive.agy_quota_timeout", ("AI_MAN_INTERACTIVE_AGY_QUOTA_TIMEOUT",), "AGY interactive quota timeout in seconds", 120.0, "float", "interactive", minimum=1.0),
    SettingDefinition("interactive.agy_quota_concurrency", ("AI_MAN_INTERACTIVE_AGY_QUOTA_CONCURRENCY",), "AGY interactive quota worker count", 2, "int", "interactive", minimum=1),
    SettingDefinition("interactive.quota_fresh_seconds", ("AI_MAN_INTERACTIVE_QUOTA_FRESH_SECONDS",), "quota color freshness threshold in seconds", 600.0, "float", "interactive", minimum=1.0),
    SettingDefinition("service.enabled", ("AI_MAN_SERVICE",), "enable optional local runtime service client for eligible read-only commands", False, "bool", "service"),
    SettingDefinition("service.client_active", ("AI_MAN_SERVICE_CLIENT_ACTIVE",), "internal guard for service client recursion", False, "bool", "service", internal=True),
    SettingDefinition("audit.enabled", ("AI_MAN_AUDIT",), "enable local best-effort audit logging", True, "bool", "audit"),
    SettingDefinition("audit.backend", ("AI_MAN_AUDIT_BACKEND",), "audit storage backend", "jsonl", "enum", "audit"),
    SettingDefinition("audit.strict", ("AI_MAN_AUDIT_STRICT",), "fail commands when audit writes fail", False, "bool", "audit"),
    SettingDefinition("audit.retention_days", ("AI_MAN_AUDIT_RETENTION_DAYS",), "audit retention age in days", 90, "int", "audit", minimum=1),
    SettingDefinition("audit.max_bytes", ("AI_MAN_AUDIT_MAX_BYTES",), "audit retention maximum storage bytes", 10 * 1024 * 1024, "int", "audit", minimum=4096),
    SettingDefinition("audit.show_accounts", ("AI_MAN_AUDIT_SHOW_ACCOUNTS",), "include account identifiers in audit output", False, "bool", "audit"),
    SettingDefinition("audit.show_paths", ("AI_MAN_AUDIT_SHOW_PATHS",), "include filesystem paths in audit output", False, "bool", "audit"),
    SettingDefinition("quota.startup_seconds", ("AI_MAN_QUOTA_STARTUP_SECONDS",), "native CLI startup wait before slash command probing", 3.0, "float", "quota", minimum=0.0),
    SettingDefinition("quota.agy_startup_seconds", ("AI_MAN_AGY_QUOTA_STARTUP_SECONDS",), "AGY CLI startup wait before slash command probing", 30.0, "float", "quota", minimum=0.0),
    SettingDefinition("quota.post_command_seconds", ("AI_MAN_QUOTA_POST_COMMAND_SECONDS",), "post-command wait after quota slash command", 4.0, "float", "quota", minimum=0.0),
    SettingDefinition("quota.key_delay_seconds", ("AI_MAN_QUOTA_KEY_DELAY_SECONDS",), "per-key delay when typing slash commands into the PTY", 0.04, "float", "quota", minimum=0.0),
    SettingDefinition("quota.session_ttl_seconds", ("AI_MAN_QUOTA_SESSION_TTL_SECONDS",), "persistent quota session idle TTL in seconds", 1800.0, "float", "quota", minimum=1.0),
    SettingDefinition("quota.session_max", ("AI_MAN_QUOTA_SESSION_MAX",), "maximum persistent quota sessions", 24, "int", "quota", minimum=1),
    SettingDefinition("quota.agy_backend", ("AI_MAN_AGY_QUOTA_BACKEND",), "AGY quota backend selection: auto, tmux, or pty", "auto", "enum", "quota"),
    SettingDefinition("quota.agy_command", ("AI_MAN_AGY_QUOTA_COMMAND",), "AGY quota slash command override", "/usage", "string", "quota", redact=True),
    SettingDefinition("quota.codex_command", ("AI_MAN_CODEX_QUOTA_COMMAND",), "Codex quota slash command override", "/status", "string", "quota", redact=True),
    SettingDefinition("quota.claude_command", ("AI_MAN_CLAUDE_QUOTA_COMMAND",), "Claude quota slash command override", "/usage", "string", "quota", redact=True),
    SettingDefinition("process.enabled", ("AI_MAN_PROCESS_LIMITS",), "enable foreground process resource limits", True, "bool", "process"),
    SettingDefinition("process.memory_mb", ("AI_MAN_PROCESS_MEMORY_MB",), "foreground launch memory cap in MB", 4096, "int", "process", minimum=128, maximum=262144),
    SettingDefinition("process.cpu_percent", ("AI_MAN_PROCESS_CPU_PERCENT",), "foreground launch CPU quota percent", 300, "int", "process", minimum=10, maximum=10000),
    SettingDefinition("process.max_processes", ("AI_MAN_PROCESS_MAX_PROCESSES",), "optional foreground launch process/thread cap", None, "int", "process", minimum=1, maximum=100000),
    SettingDefinition("process.nice", ("AI_MAN_PROCESS_NICE",), "foreground launch nice adjustment", 5, "int", "process", minimum=-20, maximum=19),
    SettingDefinition("process.ionice_class", ("AI_MAN_PROCESS_IONICE_CLASS",), "foreground launch ionice class", 2, "int", "process", minimum=0, maximum=3),
    SettingDefinition("process.ionice_level", ("AI_MAN_PROCESS_IONICE_LEVEL",), "foreground launch ionice level", 6, "int", "process", minimum=0, maximum=7),
    SettingDefinition("process.prefer_systemd", ("AI_MAN_PROCESS_SYSTEMD",), "prefer systemd user scopes when available", True, "bool", "process"),
    SettingDefinition("quota_process.enabled", ("AI_MAN_QUOTA_PROCESS_LIMITS",), "enable quota probe process limits", True, "bool", "process"),
    SettingDefinition("quota_process.memory_mb", ("AI_MAN_QUOTA_PROCESS_MEMORY_MB",), "quota probe memory cap in MB", 6144, "int", "process", minimum=128, maximum=262144),
    SettingDefinition("quota_process.cpu_percent", ("AI_MAN_QUOTA_PROCESS_CPU_PERCENT",), "quota probe CPU quota percent", 150, "int", "process", minimum=10, maximum=10000),
    SettingDefinition("quota_process.max_processes", ("AI_MAN_QUOTA_PROCESS_MAX_PROCESSES",), "quota probe process count cap", 4096, "int", "process", minimum=1, maximum=100000),
    SettingDefinition("quota_process.nice", ("AI_MAN_QUOTA_PROCESS_NICE",), "quota probe nice adjustment", 10, "int", "process", minimum=-20, maximum=19),
    SettingDefinition("quota_process.ionice_class", ("AI_MAN_QUOTA_PROCESS_IONICE_CLASS",), "quota probe ionice class", 2, "int", "process", minimum=0, maximum=3),
    SettingDefinition("quota_process.ionice_level", ("AI_MAN_QUOTA_PROCESS_IONICE_LEVEL",), "quota probe ionice level", 7, "int", "process", minimum=0, maximum=7),
    SettingDefinition("validation_process.enabled", ("AI_MAN_VALIDATION_PROCESS_LIMITS",), "enable validation command process limits", True, "bool", "process"),
    SettingDefinition("validation_process.memory_mb", ("AI_MAN_VALIDATION_PROCESS_MEMORY_MB",), "validation command memory cap in MB", 2048, "int", "process", minimum=128, maximum=262144),
    SettingDefinition("validation_process.cpu_percent", ("AI_MAN_VALIDATION_PROCESS_CPU_PERCENT",), "validation command CPU quota percent", 200, "int", "process", minimum=10, maximum=10000),
    SettingDefinition("validation_process.max_processes", ("AI_MAN_VALIDATION_PROCESS_MAX_PROCESSES",), "validation command process count cap", 128, "int", "process", minimum=1, maximum=100000),
    SettingDefinition("validation_process.nice", ("AI_MAN_VALIDATION_PROCESS_NICE",), "validation command nice adjustment", 10, "int", "process", minimum=-20, maximum=19),
    SettingDefinition("validation_process.ionice_class", ("AI_MAN_VALIDATION_PROCESS_IONICE_CLASS",), "validation command ionice class", 2, "int", "process", minimum=0, maximum=3),
    SettingDefinition("validation_process.ionice_level", ("AI_MAN_VALIDATION_PROCESS_IONICE_LEVEL",), "validation command ionice level", 7, "int", "process", minimum=0, maximum=7),
)


CONFIG_ENV_VARS = [
    {
        "name": definition.name,
        "description": definition.description,
        "default": definition.default,
        "type": definition.value_type,
    }
    for definition in CONFIG_REGISTRY
    if definition.env and not definition.internal
]


def registry():
    return list(CONFIG_REGISTRY)


_DEFINITION_BY_KEY = {definition.key: definition for definition in CONFIG_REGISTRY}


def _definition_by_key():
    return _DEFINITION_BY_KEY


def _parse_bool(raw, default, name, warnings):
    value = str(raw).strip().lower()
    if value in BOOL_TRUE:
        return True
    if value in BOOL_FALSE:
        return False
    warnings.append(f"{name}={raw!r} is invalid; using {default}")
    return default


def _parse_number(raw, default, value_type, minimum, maximum, name, warnings):
    try:
        value = int(raw) if value_type == "int" else float(raw)
    except (TypeError, ValueError):
        warnings.append(f"{name}={raw!r} is invalid; using {default}")
        return default
    if minimum is not None and value < minimum:
        warnings.append(f"{name}={raw!r} is below {minimum:g}; using {default}")
        return default
    if maximum is not None and value > maximum:
        warnings.append(f"{name}={raw!r} is above {maximum:g}; using {default}")
        return default
    return value


def _parse_value(definition, raw, warnings, source_name):
    default = definition.default
    if definition.value_type == "bool":
        return _parse_bool(raw, default, source_name, warnings)
    if definition.value_type in ("int", "float"):
        if raw is None and default is None:
            return None
        return _parse_number(raw, default, definition.value_type, definition.minimum, definition.maximum, source_name, warnings)
    if definition.value_type == "path":
        if raw is None:
            return None
        return os.path.expanduser(str(raw))
    if definition.value_type == "enum":
        value = str(raw).strip().lower()
        if definition.key == "audit.backend" and value not in ("jsonl", "sqlite"):
            warnings.append(f"{source_name}={raw!r} is invalid; using {default}")
            return default
        if definition.key == "quota.agy_backend" and value not in ("auto", "tmux", "pty"):
            warnings.append(f"{source_name}={raw!r} is invalid; using {default}")
            return default
        return value
    return str(raw) if raw is not None else None


def resolve_setting(definition, environ=None):
    environ = os.environ if environ is None else environ
    warnings = []
    source = "default"
    source_name = "default"
    raw = definition.default
    for env_name in definition.env:
        if env_name in environ:
            source = "environment"
            source_name = env_name
            raw = environ.get(env_name)
            break
    value = _parse_value(definition, raw, warnings, source_name)
    display_value = "[redacted]" if definition.redact and source == "environment" else value
    display_value = redact_sensitive(display_value)
    return {
        "key": definition.key,
        "name": definition.name,
        "category": definition.category,
        "description": definition.description,
        "type": definition.value_type,
        "default": redact_sensitive(definition.default),
        "value": display_value,
        "raw_value": redact_sensitive(raw) if source == "environment" else None,
        "source": source,
        "source_name": source_name,
        "aliases": list(definition.env),
        "deprecated_aliases": list(definition.deprecated_aliases),
        "redacted": bool(definition.redact and source == "environment"),
        "internal": definition.internal,
        "warnings": warnings,
    }


def effective_settings(environ=None, include_internal=False):
    settings = [resolve_setting(definition, environ=environ) for definition in CONFIG_REGISTRY]
    if not include_internal:
        settings = [setting for setting in settings if not setting["internal"]]
    return settings


def setting_value(key, environ=None):
    definition = _definition_by_key()[key]
    return resolve_setting(definition, environ=environ)["value"]


def _settings_by_key(settings):
    return {setting["key"]: setting for setting in settings}


def _env_item(setting):
    return {
        "name": setting["name"],
        "description": setting["description"],
        "default": setting["default"],
        "type": setting["type"],
        "value": setting["raw_value"],
        "source": setting["source"],
        "source_name": setting["source_name"],
        "warnings": setting["warnings"],
    }


def _warnings(settings):
    warnings = []
    for setting in settings:
        warnings.extend(setting.get("warnings", []))
    return warnings


def _config_health(settings, warnings):
    invalid_settings = sorted({warning.split("=", 1)[0] for warning in warnings if "=" in warning})
    return {
        "ok": not warnings,
        "registered_settings": len(settings),
        "environment_overrides": sum(1 for setting in settings if setting["source"] == "environment"),
        "invalid_settings": invalid_settings,
        "warnings": warnings,
    }


def _filtered_settings(settings, filter_text=None):
    if not filter_text:
        return list(settings)
    needle = str(filter_text).lower()
    return [
        setting for setting in settings
        if needle in setting["key"].lower()
        or needle in setting["name"].lower()
        or needle in setting["category"].lower()
        or needle in setting["description"].lower()
    ]


def _process_setting_value(setting_key, default, source_name, environ, warnings):
    definition = _definition_by_key()[setting_key]
    raw = environ.get(source_name)
    if definition.value_type == "bool":
        return _parse_bool(raw, default, source_name, warnings)
    return _parse_number(raw, default, definition.value_type, definition.minimum, definition.maximum, source_name, warnings)


def _process_policy_fast(tier, environ=None):
    environ = os.environ if environ is None else environ
    defaults = PROCESS_POLICY_DEFAULTS[tier]
    warnings = []
    enabled = defaults["enabled"]
    if "AI_MAN_PROCESS_LIMITS" in environ:
        enabled = _process_setting_value("process.enabled", enabled, "AI_MAN_PROCESS_LIMITS", environ, warnings)
    if tier == "quota" and "AI_MAN_QUOTA_PROCESS_LIMITS" in environ:
        enabled = _process_setting_value("quota_process.enabled", enabled, "AI_MAN_QUOTA_PROCESS_LIMITS", environ, warnings)
    elif tier == "validation" and "AI_MAN_VALIDATION_PROCESS_LIMITS" in environ:
        enabled = _process_setting_value("validation_process.enabled", enabled, "AI_MAN_VALIDATION_PROCESS_LIMITS", environ, warnings)

    policy = {
        "tier": tier,
        "enabled": enabled,
    }
    for field, suffix in PROCESS_POLICY_FIELD_KEYS.items():
        setting_key = PROCESS_POLICY_SETTING_KEYS[tier][field]
        primary = f"AI_MAN_PROCESS_{suffix}" if tier == "launch" else f"AI_MAN_{tier.upper()}_PROCESS_{suffix}"
        generic = f"AI_MAN_PROCESS_{suffix}"
        if primary in environ:
            value = _process_setting_value(setting_key, defaults[field], primary, environ, warnings)
        elif tier != "launch" and generic in environ:
            value = _process_setting_value(f"process.{field}", defaults[field], generic, environ, warnings)
        else:
            value = defaults[field]
        policy[field] = value
    if "AI_MAN_PROCESS_SYSTEMD" in environ:
        prefer_systemd = _process_setting_value("process.prefer_systemd", defaults["prefer_systemd"], "AI_MAN_PROCESS_SYSTEMD", environ, warnings)
    else:
        prefer_systemd = defaults["prefer_systemd"]
    policy["prefer_systemd"] = prefer_systemd
    policy["warnings"] = warnings
    policy["backend"] = "deferred"
    return policy


def _pure_process_limits(resolve_backend=False):
    if not resolve_backend:
        return {
            "launch": _process_policy_fast("launch"),
            "quota": _process_policy_fast("quota"),
            "validation": _process_policy_fast("validation"),
        }
    from .process_policy import process_policy

    return {
        "launch": process_policy("launch", resolve_backend=resolve_backend),
        "quota": process_policy("quota", resolve_backend=resolve_backend),
        "validation": process_policy("validation", resolve_backend=resolve_backend),
    }


def _pure_sync_roots(by_key):
    wsl_home = by_key["sync.wsl_home"]["value"]
    windows_home = by_key["sync.windows_home"]["value"]
    if windows_home is None:
        windows_home = by_key["sync.userprofile"]["value"] if os.name == "nt" else "/mnt/c/Users/Oliver"
    return {
        "wsl": str(wsl_home),
        "windows": str(windows_home),
    }


def effective_config_payload(include_sources=True, include_internal=False, filter_text=None, include_health=False):
    paths.refresh_from_env()
    metadata.refresh_from_env()

    all_settings = []
    public_settings = []
    by_key = {}
    warnings = []
    for definition in CONFIG_REGISTRY:
        setting = resolve_setting(definition)
        all_settings.append(setting)
        by_key[setting["key"]] = setting
        warnings.extend(setting.get("warnings", []))
        if not setting["internal"]:
            public_settings.append(setting)

    base_settings = all_settings if include_internal else public_settings
    settings = _filtered_settings(base_settings, filter_text) if filter_text else base_settings
    visible_by_key = _settings_by_key(settings)

    quota = {
        "interactive_enabled": by_key["interactive.quota_enabled"]["value"],
        "interactive_timeout": by_key["interactive.quota_timeout"]["value"],
        "interactive_agy_timeout": by_key["interactive.agy_quota_timeout"]["value"],
        "interactive_agy_concurrency": by_key["interactive.agy_quota_concurrency"]["value"],
        "interactive_fresh_seconds": by_key["interactive.quota_fresh_seconds"]["value"],
        "startup_seconds": by_key["quota.startup_seconds"]["value"],
        "agy_startup_seconds": by_key["quota.agy_startup_seconds"]["value"],
        "post_command_seconds": by_key["quota.post_command_seconds"]["value"],
        "key_delay_seconds": by_key["quota.key_delay_seconds"]["value"],
        "session_ttl_seconds": by_key["quota.session_ttl_seconds"]["value"],
        "session_max": by_key["quota.session_max"]["value"],
        "commands": {
            "agy": redact_sensitive(os.environ.get("AI_MAN_AGY_QUOTA_COMMAND", "/usage")),
            "codex": redact_sensitive(os.environ.get("AI_MAN_CODEX_QUOTA_COMMAND", "/status")),
            "claude": redact_sensitive(os.environ.get("AI_MAN_CLAUDE_QUOTA_COMMAND", "/usage")),
        },
    }
    process_limits = _pure_process_limits(resolve_backend=include_health)
    for policy in process_limits.values():
        warnings.extend(policy.get("warnings", []))

    health = _config_health(all_settings, warnings)
    health["mode"] = "health" if include_health else "fast"
    health["live_checks"] = bool(include_health)
    payload = {
        "ok": True,
        "profile_roots": {
            "agy": by_key["paths.agy_home"]["value"],
            "codex": by_key["paths.codex_home"]["value"],
            "claude": by_key["paths.claude_home"]["value"],
        },
        "metadata_dir": by_key["paths.metadata_dir"]["value"],
        "sync_roots": _pure_sync_roots(by_key),
        "quota": quota,
        "process_limits": process_limits,
        "environment": [_env_item(setting) for setting in settings if setting["aliases"]],
        "settings": settings if include_sources else [
            {key: value for key, value in setting.items() if key not in ("source", "source_name", "raw_value", "aliases", "deprecated_aliases")}
            for setting in settings
        ],
        "settings_by_key": visible_by_key,
        "config_health": health,
        "warnings": warnings,
    }
    return payload


def config_health_payload():
    payload = effective_config_payload(include_sources=True, include_internal=True, include_health=True)
    return {
        "health": payload["config_health"],
        "settings": payload["settings_by_key"],
        "process_limits": payload["process_limits"],
        "sync_roots": payload["sync_roots"],
    }
