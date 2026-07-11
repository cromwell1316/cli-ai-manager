import os
import subprocess

from .executable_lookup import executable_path


DEFAULTS = {
    "launch": {
        "enabled": True,
        "memory_mb": 4096,
        "cpu_percent": 300,
        "max_processes": 256,
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


BOOL_FALSE = {"0", "false", "no", "off", "disabled"}
BOOL_TRUE = {"1", "true", "yes", "on", "enabled"}
SYSTEMD_USER_SCOPE_PROBE_COMMAND = ("systemd-run", "--user", "--scope", "--quiet", "true")
SYSTEMD_USER_SCOPE_CACHE = {}


class ProcessPolicyError(RuntimeError):
    pass


def reset_process_policy_cache():
    SYSTEMD_USER_SCOPE_CACHE.clear()


def systemd_user_scope_cache_key(environ=None):
    environ = os.environ if environ is None else environ
    return (
        os.name,
        SYSTEMD_USER_SCOPE_PROBE_COMMAND,
        environ.get("PATH"),
        environ.get("XDG_RUNTIME_DIR"),
        environ.get("AI_MAN_PROCESS_SYSTEMD"),
    )


def _bool_env(name, default, warnings):
    raw = os.environ.get(name)
    if raw is None:
        return default
    value = raw.strip().lower()
    if value in BOOL_FALSE:
        return False
    if value in BOOL_TRUE:
        return True
    warnings.append(f"{name}={raw!r} is invalid; using {default}")
    return default


def _int_env(name, default, minimum, maximum, warnings):
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        warnings.append(f"{name}={raw!r} is invalid; using {default}")
        return default
    if value < minimum or (maximum is not None and value > maximum):
        upper = f"..{maximum}" if maximum is not None else "+"
        warnings.append(f"{name}={raw!r} is outside {minimum}{upper}; using {default}")
        return default
    return value


def _tier_env_name(tier, suffix):
    if tier == "quota":
        primary = f"AI_MAN_QUOTA_PROCESS_{suffix}"
    elif tier == "validation":
        primary = f"AI_MAN_VALIDATION_PROCESS_{suffix}"
    else:
        primary = f"AI_MAN_PROCESS_{suffix}"
    return primary


def _tier_int(tier, suffix, default, minimum, maximum, warnings):
    primary = _tier_env_name(tier, suffix)
    if primary in os.environ:
        return _int_env(primary, default, minimum, maximum, warnings)
    generic = f"AI_MAN_PROCESS_{suffix}"
    if tier != "launch" and generic in os.environ:
        return _int_env(generic, default, minimum, maximum, warnings)
    return default


def process_policy(tier="launch", resolve_backend=True):
    if tier not in DEFAULTS:
        raise ValueError(f"unknown process policy tier: {tier}")
    defaults = DEFAULTS[tier]
    warnings = []
    enabled = _bool_env("AI_MAN_PROCESS_LIMITS", defaults["enabled"], warnings)
    if tier == "quota":
        enabled = _bool_env("AI_MAN_QUOTA_PROCESS_LIMITS", enabled, warnings)
    elif tier == "validation":
        enabled = _bool_env("AI_MAN_VALIDATION_PROCESS_LIMITS", enabled, warnings)
    policy = {
        "tier": tier,
        "enabled": enabled,
        "memory_mb": _tier_int(tier, "MEMORY_MB", defaults["memory_mb"], 128, 262144, warnings),
        "cpu_percent": _tier_int(tier, "CPU_PERCENT", defaults["cpu_percent"], 10, 10000, warnings),
        "max_processes": _tier_int(tier, "MAX_PROCESSES", defaults["max_processes"], 1, 100000, warnings),
        "nice": _tier_int(tier, "NICE", defaults["nice"], -20, 19, warnings),
        "ionice_class": _tier_int(tier, "IONICE_CLASS", defaults["ionice_class"], 0, 3, warnings),
        "ionice_level": _tier_int(tier, "IONICE_LEVEL", defaults["ionice_level"], 0, 7, warnings),
        "prefer_systemd": _bool_env("AI_MAN_PROCESS_SYSTEMD", defaults["prefer_systemd"], warnings),
        "warnings": warnings,
    }
    policy["backend"] = select_backend(policy, needs_pty=(tier == "quota")) if resolve_backend else "deferred"
    return policy


def _systemd_user_scope_available_uncached():
    if os.name == "nt":
        return False
    if executable_path("systemd-run") is None:
        return False
    if os.environ.get("XDG_RUNTIME_DIR") is None:
        return False
    try:
        completed = subprocess.run(
            ["systemd-run", "--user", "--scope", "--quiet", "true"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=2,
            check=False,
        )
    except Exception:
        return False
    return completed.returncode == 0


def systemd_user_scope_available():
    key = systemd_user_scope_cache_key()
    if key not in SYSTEMD_USER_SCOPE_CACHE:
        SYSTEMD_USER_SCOPE_CACHE[key] = _systemd_user_scope_available_uncached()
    return SYSTEMD_USER_SCOPE_CACHE[key]


def select_backend(policy, needs_pty=False):
    if not policy["enabled"]:
        return "disabled"
    if os.name == "nt":
        return "unsupported"
    if policy.get("prefer_systemd") and not needs_pty and systemd_user_scope_available():
        return "systemd-run"
    try:
        import resource  # noqa: F401
    except ImportError:
        return "priority-only"
    return "setrlimit"


def systemd_scope_command(command, policy, unit_name=None):
    if not policy.get("enabled") or policy.get("backend") != "systemd-run":
        return list(command)
    args = ["systemd-run", "--user", "--scope", "--quiet"]
    if unit_name:
        args.extend(["--unit", unit_name])
    args.extend([
        "-p",
        f"MemoryMax={int(policy['memory_mb'])}M",
        "-p",
        f"CPUQuota={int(policy['cpu_percent'])}%",
        "-p",
        f"TasksMax={int(policy['max_processes'])}",
    ])
    return args + list(command)


def preexec_for_policy(policy):
    if not policy.get("enabled") or os.name == "nt":
        return None
    backend = policy.get("backend")
    if backend not in ("setrlimit", "priority-only"):
        return None

    def apply_limits():
        if policy.get("nice") is not None:
            try:
                os.nice(int(policy["nice"]))
            except OSError:
                pass
        if backend == "setrlimit":
            try:
                import resource

                memory_bytes = int(policy["memory_mb"]) * 1024 * 1024
                resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
                resource.setrlimit(resource.RLIMIT_NPROC, (int(policy["max_processes"]), int(policy["max_processes"])))
                cpu_seconds = max(1, int(policy["cpu_percent"]) // 100 * 3600)
                resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds))
            except Exception:
                os._exit(125)

    return apply_limits


def ionice_command(command, policy):
    if not policy.get("enabled") or os.name == "nt" or executable_path("ionice") is None:
        return list(command)
    ionice_class = int(policy.get("ionice_class", 0))
    if ionice_class <= 0:
        return list(command)
    args = ["ionice", "-c", str(ionice_class)]
    if ionice_class in (2, 3):
        args.extend(["-n", str(int(policy.get("ionice_level", 7)))])
    return args + list(command)


def prepare_popen(command, tier="launch", needs_pty=False, unit_name=None):
    policy = process_policy(tier)
    prepared = list(command)
    preexec = None
    if policy["enabled"]:
        if policy["backend"] == "systemd-run" and not needs_pty:
            prepared = systemd_scope_command(prepared, policy, unit_name=unit_name)
        else:
            prepared = ionice_command(prepared, policy)
            preexec = preexec_for_policy(policy)
    return prepared, preexec, policy


def diagnostics_payload():
    policies = {tier: process_policy(tier) for tier in ("launch", "quota", "validation")}
    return {
        "supported": os.name != "nt",
        "systemd_user_scope_available": systemd_user_scope_available(),
        "policies": policies,
    }
