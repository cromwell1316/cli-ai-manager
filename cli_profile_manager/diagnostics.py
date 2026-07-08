import hashlib
import os
import re
import shutil
import time

from .paths import DISPLAY_SLOT_COUNT, TOOLS, get_display_profiles, get_occupied_profiles, profile_home
from .quota import persistent_quota_sessions_snapshot, quota_command_for


TOKEN_LIKE_RE = re.compile(
    r"(?i)(sk-[a-z0-9_-]+|xox[a-z]-[a-z0-9-]+|gh[pousr]_[a-z0-9_]+|ya29\.[a-z0-9._-]+|refresh_token)"
)
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@([A-Z0-9.-]+\.[A-Z]{2,})\b", re.I)


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
        "AI_MAN_QUOTA_POST_COMMAND_SECONDS",
        "AI_MAN_QUOTA_KEY_DELAY_SECONDS",
    ]
    return {key: os.environ.get(key) for key in keys if key in os.environ}


def tool_diagnostics(tool_key, status_provider=None, show_accounts=False):
    tool = TOOLS[tool_key]
    occupied = get_occupied_profiles(tool_key)
    display = get_display_profiles(tool_key)
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
    cli_path = shutil.which(tool["cmd"])
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


def diagnostics_payload(tool_key=None, status_provider=None, show_accounts=False):
    from .interactive import quota_runtime_snapshot

    selected_tools = [tool_key] if tool_key else list(TOOLS)
    payload = {
        "ok": True,
        "generated_at": int(time.time()),
        "tools": {
            key: tool_diagnostics(key, status_provider=status_provider, show_accounts=show_accounts)
            for key in selected_tools
        },
        "environment": relevant_env_snapshot(),
        "quota_runtime": quota_runtime_snapshot(tool_key),
        "persistent_sessions": persistent_quota_sessions_snapshot(tool_key),
    }
    return redact_sensitive(payload, show_accounts)
