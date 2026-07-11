import os
import atexit
import hashlib
import re
import select
import shutil
import signal
import subprocess
import fcntl
import logging
import struct
import termios
import threading
import time

from .process_policy import prepare_popen
from . import audit


DEFAULT_COLS = 120
DEFAULT_ROWS = 40
DEFAULT_TMUX_QUOTA_COLS = 120
DEFAULT_TMUX_QUOTA_ROWS = 80
DEFAULT_TIMEOUT_SECONDS = 20
DEFAULT_IDLE_SECONDS = 0.8
DEFAULT_STARTUP_SECONDS = 3.0
DEFAULT_POST_COMMAND_SECONDS = 4.0
DEFAULT_KEY_DELAY_SECONDS = 0.04
DEFAULT_AGY_KEY_DELAY_SECONDS = 0.0
DEFAULT_AGY_STARTUP_SECONDS = 30.0
DEFAULT_AGY_POST_COMMAND_SECONDS = 8.0
DEFAULT_TMUX_LIVENESS_CACHE_SECONDS = 1.0
DEFAULT_TMUX_SHORT_CAPTURE_LINES = 80
DEFAULT_TMUX_LONG_CAPTURE_LINES = 240
DEFAULT_TMUX_POLL_INTERVAL_SECONDS = 0.1
DEFAULT_TMUX_COLD_START_CONCURRENCY = 2
DEFAULT_TMUX_WARM_SNAPSHOT_CONCURRENCY = 4
DIRECT_AGY_PROMPT_SUCCESS_MARKER = "__AI_MAN_DIRECT_AGY_PROMPT_SUCCEEDED__"
PARSER_MISS_SESSION_INVALIDATION_THRESHOLD = 3
DEFAULT_PERSISTENT_SESSION_TTL_SECONDS = 1800.0
DEFAULT_PERSISTENT_SESSION_MAX = 24
TMUX_QUOTA_SESSION_PREFIX = "ai_man_quota_"
AGY_QUOTA_BACKEND_ENV = "AI_MAN_AGY_QUOTA_BACKEND"
AGY_COMPLETE_MODEL_LABELS = ("FM", "FH", "FL", "PL", "PH", "CS", "CO")


QUOTA_COMMANDS = {
    "agy": "/usage",
    "codex": "/status",
    "claude": "/usage",
}

AUTH_PATTERNS = (
    re.compile(r"\b(sign in|login required|not authenticated|please log in|please sign in)\b", re.I),
    re.compile(r"\bauthentication required\b", re.I),
    re.compile(r"\byou are not logged into antigravity\b", re.I),
)

AGY_READY_PATTERNS = (
    re.compile(r"\bCLI ready for user input\b", re.I),
    re.compile(r"\bready for user input\b", re.I),
    re.compile(r"\btype\s+/help\b", re.I),
    re.compile(r"\?\s+for\s+shortcuts\b", re.I),
)

AGY_PROMPT_PATTERNS = (
    re.compile(r"(?:^|\n)\s*(?:[^\n]*\s)?[~>]\s*$"),
    re.compile(r"(?:^|\n)\s*>\s*$"),
)

AGY_FAILURE_PATTERNS = (
    (
        "resource_limited",
        "AGY CLI was stopped by local quota process resource limits",
        (
            re.compile(r"\bMmapAligned\(\) failed\b", re.I),
            re.compile(r"\btcmalloc\b.*\bunable to allocate\b", re.I | re.S),
            re.compile(r"\bfailed - unable to allocate\b", re.I),
            re.compile(r"\bpthread_create failed\b", re.I),
            re.compile(r"\bResource temporarily unavailable\b", re.I),
        ),
    ),
    (
        "tty_unavailable",
        "AGY CLI could not open a controlling terminal",
        (
            re.compile(r"\berror opening TTY\b", re.I),
            re.compile(r"\bcould not open TTY\b", re.I),
            re.compile(r"\bopen /dev/tty\b", re.I),
            re.compile(r"\bbubbletea:.*TTY\b", re.I),
        ),
    ),
    (
        "auth_required",
        "AGY CLI reported that authentication is required",
        (
            re.compile(r"\byou are not logged into antigravity\b", re.I),
            re.compile(r"\bplease log in\b", re.I),
            re.compile(r"\bplease sign in\b", re.I),
        ),
    ),
    (
        "resource_exhausted",
        "AGY CLI reported that quota or resources are exhausted",
        (
            re.compile(r"\bRESOURCE_EXHAUSTED\b", re.I),
            re.compile(r"\bresource exhausted\b", re.I),
            re.compile(r"\bexhausted your capacity\b", re.I),
            re.compile(r"\bquota will reset\b", re.I),
        ),
    ),
    (
        "account_ineligible",
        "AGY CLI reported an account eligibility warning",
        (
            re.compile(r"\baccount ineligible\b", re.I),
            re.compile(r"\bineligible\b.*\baccount\b", re.I),
            re.compile(r"\baccount\b.*\bnot eligible\b", re.I),
            re.compile(r"\bnot eligible for Antigravity\b", re.I),
            re.compile(r"\bnot currently available in your location\b", re.I),
        ),
    ),
)
AGY_NONFATAL_WARNING_STATES = {"account_ineligible"}
AGY_STARTUP_PENDING_PATTERN = re.compile(r"\bAntigravity CLI\b|\bSigning in\b|\bcurrently not signed in\b", re.I)

ANSI_RE = re.compile(
    r"(?:\x1b\[[0-?]*[ -/]*[@-~]|\x1b\][^\x07]*(?:\x07|\x1b\\)|\x1b[@-_])"
)

SPINNER_CHARS = set("⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏")


class QuotaProbeError(RuntimeError):
    def __init__(self, state, message, raw_output=""):
        super().__init__(message)
        self.state = state
        self.raw_output = raw_output


def quota_command_for(tool_key):
    override = os.environ.get(f"AI_MAN_{tool_key.upper()}_QUOTA_COMMAND")
    return override or QUOTA_COMMANDS.get(tool_key)


def strip_terminal_sequences(text):
    text = ANSI_RE.sub("", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    return text


def compact_lines(text):
    lines = []
    for line in strip_terminal_sequences(text).splitlines():
        cleaned = re.sub(r"[ \t]+", " ", line).strip()
        if cleaned:
            lines.append(cleaned)
    return lines


def parse_reset_text(text):
    reset = re.search(r"\breset(?:s|ting)?(?:\s+in|\s+at)?\s+([^\n,;|]+)", text, re.I)
    return reset.group(1).strip() if reset else None


def parse_percent_limit(text, label_patterns):
    for pattern in label_patterns:
        match = re.search(pattern, text, re.I | re.S)
        if match:
            return int(match.group(1))
    return None


def parse_percent_value(text):
    match = re.search(r"(\d{1,3}(?:\.\d+)?)\s*%", text)
    if not match:
        return None
    value = float(match.group(1))
    return int(value) if value.is_integer() else value


def limit_reset_from_line(line):
    match = re.search(r"\b(?:reset|resets|refresh|refreshes)(?:\s+in|\s+at|:)?\s+(.+)$", line, re.I)
    if not match:
        return None
    return match.group(1).strip(" .;|")


def add_percent_limit(quota, key, line, value=None, label=None):
    value = parse_percent_value(line) if value is None else value
    if value is None:
        return False
    percent_key = "percent_left" if re.search(r"\b(left|remaining|available)\b", line, re.I) else "percent"
    data = {percent_key: value}
    if label:
        data["model"] = label
    reset = limit_reset_from_line(line)
    if reset:
        data["resets"] = reset
    quota["limits"][key] = data
    return True


def stable_limit_key(label):
    return re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_") or "usage"


def generic_quota_key_and_label(line, fallback_index=1):
    lowered = line.lower()
    specs = (
        ("daily", "day", (r"\bdaily\b", r"\btoday\b")),
        ("local_messages", "local", (r"\blocal\b.*\bmessages?\b", r"\bmessages?\b.*\blocal\b")),
        ("cloud_tasks", "cloud", (r"\bcloud\b.*\btasks?\b", r"\btasks?\b.*\bcloud\b")),
        ("requests", "req", (r"\brequests?\b",)),
        ("messages", "msg", (r"\bmessages?\b",)),
        ("tasks", "tasks", (r"\btasks?\b",)),
        ("tokens", "tokens", (r"\btokens?\b",)),
    )
    for key, label, patterns in specs:
        if any(re.search(pattern, lowered, re.I) for pattern in patterns):
            return key, label

    model = agy_model_name_from_line(line)
    if model:
        return stable_limit_key(model), model

    before_percent = re.split(r"\d{1,3}(?:\.\d+)?\s*%", line, 1)[0]
    before_percent = re.sub(r"^[^\w]*(?:quota|usage|limit|pool|model)?[^\w]*", "", before_percent, flags=re.I)
    before_percent = before_percent.strip(" :-|•·")
    if before_percent:
        label = before_percent[-36:].strip()
        return stable_limit_key(label), label
    return None, None


def parse_fraction_value(line):
    match = re.search(r"\b(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)\b", line)
    if not match:
        return None
    used = float(match.group(1))
    total = float(match.group(2))
    if total <= 0:
        return None
    value = max(0.0, min(100.0, (used / total) * 100.0))
    return int(value) if value.is_integer() else round(value, 1)


def add_agy_line_limit(quota, line, fallback_index=1):
    if not re.search(r"\b(quota|limit|usage|remaining|left|available|used|refresh|reset|messages?|tasks?|requests?|tokens?|daily|today|local|cloud|gemini|claude|gpt)\b", line, re.I):
        return False
    key, label = generic_quota_key_and_label(line, fallback_index)
    if key is None:
        return False
    if key in quota["limits"]:
        return False
    percent = parse_percent_value(line)
    if percent is not None:
        return add_percent_limit(quota, key, line, value=percent, label=label)
    fraction = parse_fraction_value(line)
    if fraction is None:
        return False
    quota["limits"][key] = {"percent": fraction, "model": label}
    reset = limit_reset_from_line(line)
    if reset:
        quota["limits"][key]["resets"] = reset
    return True


def parse_labeled_percent_lines(lines, specs):
    matches = {}
    for line in lines:
        if "%" not in line:
            continue
        for key, label, patterns in specs:
            if any(re.search(pattern, line, re.I) for pattern in patterns):
                matches.setdefault(key, (line, label))
                break
    return matches


def codex_status_limit_line(line):
    return bool(re.search(
        r"\b(?:context\s+window|5\s*[- ]?\s*h(?:our)?\s+limit|five\s*[- ]?\s*hour\s+limit|weekly\s+limit|7\s*[- ]?\s*day\s+limit)\s*:",
        line,
        re.I,
    ))


def agy_model_name_from_line(line):
    if "quota pools" in line.lower() or "," in line or len(line) > 72:
        return None
    match = re.search(r"\b(?:Gemini|Claude|GPT)\s+[A-Za-z0-9 .()/-]+", line)
    if not match:
        return None
    return match.group(0).strip()


def parse_codex_quota(screen_text):
    lines = compact_lines(screen_text)
    text = "\n".join(lines)
    quota = {
        "state": "available",
        "source_command": "/status",
        "limits": {},
        "raw_summary": text,
    }
    five_hour = parse_percent_limit(text, (
        r"5\s*h(?:our)?\s+limit\s*:.*?(\d{1,3})\s*%\s*(?:left|remaining)?",
        r"five\s*[- ]?\s*hour\s+limit\s*:.*?(\d{1,3})\s*%\s*(?:left|remaining)?",
    ))
    weekly = parse_percent_limit(text, (
        r"(?:7\s*day|weekly)\s+limit\s*:.*?(\d{1,3})\s*%\s*(?:left|remaining|available)?",
    ))
    reset = parse_reset_text(text)
    if five_hour is not None:
        quota["limits"]["five_hour"] = {"percent_left": five_hour}
        if reset:
            quota["limits"]["five_hour"]["resets"] = reset
    if weekly is not None:
        quota["limits"]["weekly"] = {"percent_left": weekly}
    status_lines = [line for line in lines if codex_status_limit_line(line)]
    labeled = parse_labeled_percent_lines(status_lines, (
        ("five_hour", "5h", (r"\b5\s*[- ]?\s*h(?:our)?\b", r"\bfive\s*[- ]?\s*hour\b")),
        ("weekly", "weekly", (r"\bweekly\b", r"\b7\s*[- ]?\s*day\b", r"\bweek\b")),
        ("context", "context", (r"\bcontext\b",)),
    ))
    for key, (line, label) in labeled.items():
        if key not in quota["limits"]:
            add_percent_limit(quota, key, line, label=label)
    if "five_hour" not in quota["limits"] and "weekly" not in quota["limits"]:
        quota["limits"].clear()
        return quota
    for line in lines:
        if "%" not in line or not re.search(r"\b(rate|usage|message|task|limit|remaining|left|available)\b", line, re.I):
            continue
        if re.search(r"\b(gpt|model|context)\b", line, re.I):
            continue
        if not quota["limits"]:
            add_percent_limit(quota, "usage", line, label="usage")
    return quota


def parse_claude_quota(screen_text):
    text = "\n".join(compact_lines(screen_text))
    quota = {
        "state": "available",
        "source_command": "/usage",
        "limits": {},
        "raw_summary": text,
    }
    session = parse_percent_limit(text, (
        r"(?:session|5\s*h(?:our)?|usage)\b.*?(\d{1,3})\s*%\s*(?:left|remaining|used)?",
        r"(\d{1,3})\s*%\s*(?:left|remaining).*?(?:session|5\s*h(?:our)?|usage)\b",
    ))
    weekly = parse_percent_limit(text, (
        r"(?:weekly|7\s*day)\b.*?(\d{1,3})\s*%\s*(?:left|remaining|used)?",
        r"(\d{1,3})\s*%\s*(?:left|remaining).*?(?:weekly|7\s*day)\b",
    ))
    reset = parse_reset_text(text)
    if session is not None:
        quota["limits"]["session"] = {"percent": session}
        if reset:
            quota["limits"]["session"]["resets"] = reset
    if weekly is not None:
        quota["limits"]["weekly"] = {"percent": weekly}
    return quota


def parse_agy_quota(screen_text):
    lines = compact_lines(screen_text)
    text = "\n".join(lines)
    quota = {
        "state": "available",
        "source_command": "/usage",
        "limits": {},
        "raw_summary": text,
    }
    account_match = re.search(r"\bAccount:\s*([^\s│]+@[^\s│]+)", text, re.I)
    if not account_match:
        account_match = re.search(r"\b([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})\b", text, re.I)
    if account_match:
        quota["account"] = account_match.group(1)
    current_model = None
    for line in lines:
        if line.startswith("└ Models & Quota"):
            break
        model_name = agy_model_name_from_line(line)
        if model_name:
            current_model = model_name
            quota["current_model"] = current_model
            break
    for idx, line in enumerate(lines):
        if "%" in line:
            continue
        model_name = agy_model_name_from_line(line)
        if model_name:
            if current_model is None:
                current_model = model_name
                quota["current_model"] = current_model
            percent = None
            refresh = None
            search_lines = lines[idx:idx + 4]
            for search_line in search_lines:
                percent_match = re.search(r"(\d{1,3}(?:\.\d+)?)\s*%", search_line)
                if percent_match:
                    percent = float(percent_match.group(1))
                refresh_match = re.search(r"Refresh(?:es)?\s+in\s+([^·]+)$", search_line, re.I)
                if refresh_match:
                    refresh = refresh_match.group(1).strip()
            if percent is not None:
                key = re.sub(r"[^a-z0-9]+", "_", model_name.lower()).strip("_")
                quota["limits"][key] = {
                    "model": model_name,
                    "percent": percent,
                }
                if refresh:
                    quota["limits"][key]["refreshes_in"] = refresh
                if current_model and model_name == current_model:
                    quota["current_limit"] = key
    daily = parse_percent_limit(text, (
        r"(?:daily|today)\b.*?(\d{1,3})\s*%\s*(?:left|remaining|used)?",
        r"(\d{1,3})\s*%\s*(?:left|remaining).*?(?:daily|today)\b",
    ))
    reset = parse_reset_text(text)
    if daily is not None:
        quota["limits"]["daily"] = {"percent": daily}
        if reset:
            quota["limits"]["daily"]["resets"] = reset
    fallback_index = 1
    for line in lines:
        if "%" not in line and not re.search(r"\b\d+(?:\.\d+)?\s*/\s*\d+(?:\.\d+)?\b", line):
            continue
        before_count = len(quota["limits"])
        add_agy_line_limit(quota, line, fallback_index)
        if len(quota["limits"]) > before_count:
            fallback_index += 1
    return quota


PARSERS = {
    "agy": parse_agy_quota,
    "codex": parse_codex_quota,
    "claude": parse_claude_quota,
}


def detect_auth_required(text):
    return any(pattern.search(text) for pattern in AUTH_PATTERNS)


def classify_agy_failure(text, fatal_only=False):
    if not text:
        return None
    for state, message, patterns in AGY_FAILURE_PATTERNS:
        if fatal_only and state in AGY_NONFATAL_WARNING_STATES:
            continue
        if any(pattern.search(text) for pattern in patterns):
            return state, message
    return None


def classify_agy_probe_error(state, text):
    classified = classify_agy_failure(text)
    if classified and state in ("startup_pending", "timeout") and classified[0] in AGY_NONFATAL_WARNING_STATES:
        classified = None
    if classified:
        return classified
    sign_in_stalled = (
        re.search(r"\bcurrently not signed in\b", text, re.I)
        and re.search(r"\bsigning in\b", text, re.I)
    )
    if state == "startup_pending" and sign_in_stalled:
        return "startup_pending", "AGY CLI is still signing in; keeping the session warm"
    if state == "timeout" and sign_in_stalled:
        return "auth_required", "AGY CLI could not complete sign-in for this profile; /usage was not sent"
    if state == "startup_pending":
        return "startup_pending", "AGY CLI is still starting; keeping the session warm"
    return None


def agy_diagnostic_summary(text, state=None, limit=240):
    lines = compact_lines(text)
    if state == "account_ineligible":
        selected = [
            line for line in lines
            if re.search(r"\beligib|not currently available in your location", line, re.I)
        ]
        if selected:
            return "\n".join(selected)[-limit:]
    if state in ("auth_required", "startup_pending"):
        selected = [
            line for line in lines
            if re.search(r"\bcurrently not signed in\b|\bsigning in\b|\bsign in\b|\blogin\b", line, re.I)
        ]
        if selected:
            return "\n".join(selected)[-limit:]
    return "\n".join(lines)[:limit]


def agy_eligibility_warning(text):
    classified = classify_agy_failure(text)
    if classified and classified[0] == "account_ineligible":
        return classified[1]
    return None


def quota_startup_seconds(tool_key):
    default = DEFAULT_AGY_STARTUP_SECONDS if tool_key == "agy" else DEFAULT_STARTUP_SECONDS
    if tool_key == "agy":
        raw = os.environ.get("AI_MAN_AGY_QUOTA_STARTUP_SECONDS", os.environ.get("AI_MAN_QUOTA_STARTUP_SECONDS", default))
    else:
        raw = os.environ.get("AI_MAN_QUOTA_STARTUP_SECONDS", default)
    try:
        return max(0.0, float(raw))
    except (TypeError, ValueError):
        return default


def agy_cli_ready(text):
    return any(pattern.search(text) for pattern in AGY_READY_PATTERNS)


def agy_prompt_ready(text):
    summary = "\n".join(compact_lines(text))
    if not re.search(r"\bAntigravity CLI\b", summary, re.I):
        return False
    if re.search(r"\b(signing in|loading|checking|authenticating)\b", summary, re.I):
        return False
    return any(pattern.search(summary) for pattern in AGY_PROMPT_PATTERNS)


def has_spinner_frame(text):
    return any(char in text[-200:] for char in SPINNER_CHARS)


def output_text(output):
    parts = []
    for part in output:
        if isinstance(part, bytes):
            parts.append(part.decode("utf-8", errors="replace"))
        elif part is None:
            continue
        else:
            parts.append(str(part))
    return "".join(parts)


def fd_readable(fd, timeout=0):
    try:
        ready, _, _ = select.select([fd], [], [], timeout)
    except (OSError, ValueError):
        return False
    return bool(ready)


def read_available(fd):
    chunks = []
    while True:
        if not fd_readable(fd, 0):
            break
        try:
            data = os.read(fd, 4096)
        except OSError:
            break
        if not data:
            break
        chunks.append(data.decode("utf-8", errors="replace"))
    return "".join(chunks)


def wait_for_idle(fd, output, idle_seconds, timeout_seconds):
    start = time.monotonic()
    stable_since = None
    last_len = -1
    while True:
        if fd_readable(fd, 0.1):
            output.append(read_available(fd))
        current = output_text(output)
        current_len = len(current)
        if current_len == last_len and not has_spinner_frame(current):
            if stable_since is None:
                stable_since = time.monotonic()
            if time.monotonic() - stable_since >= idle_seconds:
                return current
        else:
            last_len = current_len
            stable_since = None
        if time.monotonic() - start > timeout_seconds:
            raise QuotaProbeError("timeout", "timeout waiting for CLI output", current)


def wait_for_startup(fd, output, startup_seconds):
    deadline = time.monotonic() + startup_seconds
    while time.monotonic() < deadline:
        if fd_readable(fd, 0.1):
            output.append(read_available(fd))


def wait_for_agy_readiness(fd, output, startup_seconds, idle_seconds):
    deadline = time.monotonic() + startup_seconds
    while time.monotonic() < deadline:
        if fd_readable(fd, 0.1):
            output.append(read_available(fd))
        current = output_text(output)
        classified = classify_agy_failure(current, fatal_only=True)
        if classified:
            state, message = classified
            raise QuotaProbeError(state, message, current)
        if agy_cli_ready(current) or agy_prompt_ready(current):
            return current
    current = output_text(output)
    if AGY_STARTUP_PENDING_PATTERN.search(current):
        raise QuotaProbeError("startup_pending", "AGY CLI is still starting", current)
    raise QuotaProbeError("timeout", "timeout waiting for AGY CLI readiness", current)


def wait_for_cli_startup(tool_key, fd, output, startup_seconds, idle_seconds, timeout_seconds):
    if tool_key == "agy":
        wait_for_agy_readiness(fd, output, startup_seconds, idle_seconds)
        return
    wait_for_startup(fd, output, startup_seconds)
    wait_for_idle(fd, output, idle_seconds, timeout_seconds)


def wait_after_command(fd, output, minimum_seconds):
    deadline = time.monotonic() + minimum_seconds
    while time.monotonic() < deadline:
        if fd_readable(fd, 0.1):
            output.append(read_available(fd))


def send_interactive_command(fd, command, key_delay_seconds=DEFAULT_KEY_DELAY_SECONDS):
    text = f"\x15{command}\r"
    if key_delay_seconds <= 0:
        os.write(fd, text.encode("utf-8"))
        return
    for ch in text:
        os.write(fd, ch.encode("utf-8"))
        if key_delay_seconds > 0:
            time.sleep(key_delay_seconds)


def quota_key_delay_seconds(tool_key):
    default = DEFAULT_AGY_KEY_DELAY_SECONDS if tool_key == "agy" else DEFAULT_KEY_DELAY_SECONDS
    return max(0.0, float(os.environ.get("AI_MAN_QUOTA_KEY_DELAY_SECONDS", default)))


def quota_post_command_seconds(tool_key):
    default = DEFAULT_AGY_POST_COMMAND_SECONDS if tool_key == "agy" else DEFAULT_POST_COMMAND_SECONDS
    try:
        return max(0.0, float(os.environ.get("AI_MAN_QUOTA_POST_COMMAND_SECONDS", default)))
    except ValueError:
        return default


def tmux_liveness_cache_seconds():
    try:
        return max(0.0, float(os.environ.get("AI_MAN_TMUX_QUOTA_LIVENESS_CACHE_SECONDS", DEFAULT_TMUX_LIVENESS_CACHE_SECONDS)))
    except ValueError:
        return DEFAULT_TMUX_LIVENESS_CACHE_SECONDS


def tmux_capture_lines(kind):
    env_name = "AI_MAN_TMUX_QUOTA_LONG_CAPTURE_LINES" if kind == "long" else "AI_MAN_TMUX_QUOTA_SHORT_CAPTURE_LINES"
    default = DEFAULT_TMUX_LONG_CAPTURE_LINES if kind == "long" else DEFAULT_TMUX_SHORT_CAPTURE_LINES
    try:
        return max(20, int(os.environ.get(env_name, default)))
    except ValueError:
        return default


def tmux_quota_cols():
    try:
        return max(80, int(os.environ.get("AI_MAN_TMUX_QUOTA_COLS", DEFAULT_TMUX_QUOTA_COLS)))
    except ValueError:
        return DEFAULT_TMUX_QUOTA_COLS


def tmux_quota_rows():
    try:
        return max(40, int(os.environ.get("AI_MAN_TMUX_QUOTA_ROWS", DEFAULT_TMUX_QUOTA_ROWS)))
    except ValueError:
        return DEFAULT_TMUX_QUOTA_ROWS


def tmux_poll_interval_seconds():
    try:
        return max(0.01, float(os.environ.get("AI_MAN_TMUX_QUOTA_POLL_INTERVAL_SECONDS", DEFAULT_TMUX_POLL_INTERVAL_SECONDS)))
    except ValueError:
        return DEFAULT_TMUX_POLL_INTERVAL_SECONDS


def tmux_cold_start_concurrency():
    try:
        return max(1, int(os.environ.get("AI_MAN_TMUX_QUOTA_COLD_START_CONCURRENCY", DEFAULT_TMUX_COLD_START_CONCURRENCY)))
    except ValueError:
        return DEFAULT_TMUX_COLD_START_CONCURRENCY


def tmux_warm_snapshot_concurrency():
    try:
        return max(1, int(os.environ.get("AI_MAN_TMUX_QUOTA_WARM_SNAPSHOT_CONCURRENCY", DEFAULT_TMUX_WARM_SNAPSHOT_CONCURRENCY)))
    except ValueError:
        return DEFAULT_TMUX_WARM_SNAPSHOT_CONCURRENCY


def agy_model_quota_label(model):
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
        return None

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


def agy_model_quota_labels(quota):
    labels = set()
    for name, data in quota.get("limits", {}).items():
        model = data.get("model", name)
        label = agy_model_quota_label(model)
        if label:
            labels.add(label)
    return labels


def agy_full_model_quota_ready(screen_text, quota):
    if not re.search(r"\bALL MODELS\b|Models\s*&\s*Quota", screen_text, re.I):
        return True
    labels = agy_model_quota_labels(quota)
    if not labels:
        return False
    return all(label in labels for label in AGY_COMPLETE_MODEL_LABELS)


def quota_snapshot_ready(tool_key, screen_text):
    quota = parse_quota(tool_key, screen_text)
    if tool_key == "agy" and quota.get("state") == "available" and not agy_full_model_quota_ready(screen_text, quota):
        return False
    return quota.get("state") not in ("empty_output", "parser_miss")


def terminate_process(proc, master_fd, output):
    if proc.poll() is not None:
        return
    try:
        os.write(master_fd, b"/exit\r")
    except OSError:
        pass
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            return
        output.append(read_available(master_fd))
        time.sleep(0.1)
    try:
        proc.terminate()
    except OSError:
        pass
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            return
        time.sleep(0.1)
    if proc.poll() is None:
        try:
            proc.kill()
        except OSError:
            pass


def quota_pty_preexec(slave_fd, policy_preexec):
    def preexec():
        try:
            os.setsid()
            fcntl.ioctl(slave_fd, termios.TIOCSCTTY, 0)
        except Exception:
            os._exit(126)
        if policy_preexec is not None:
            policy_preexec()

    return preexec


def start_quota_pty_process(tool_key, command, env, cwd, backend):
    if os.name == "nt":
        raise QuotaProbeError("unsupported", "PTY quota probing is not supported on Windows yet")
    try:
        import pty
    except ImportError as e:
        raise QuotaProbeError("unsupported", "PTY support is not available") from e
    if shutil.which(command[0]) is None:
        raise QuotaProbeError("missing_cli", f"{command[0]} CLI is not installed or not in PATH")

    master_fd, slave_fd = pty.openpty()
    try:
        fcntl.ioctl(slave_fd, termios.TIOCSWINSZ, struct.pack("HHHH", DEFAULT_ROWS, DEFAULT_COLS, 0, 0))
        popen_env = env.copy()
        popen_env.setdefault("TERM", "xterm-256color")
        prepared_command, policy_preexec, policy = prepare_popen(command, tier="quota", needs_pty=True)
        audit.record(
            "subprocess",
            "decision",
            command="quota",
            tool=tool_key,
            backend=policy.get("backend"),
            details={"process_policy": {key: policy.get(key) for key in ("enabled", "backend", "tier", "memory_mb", "cpu_percent", "max_processes")}},
        )
        proc = subprocess.Popen(
            prepared_command,
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            cwd=cwd,
            env=popen_env,
            close_fds=True,
            preexec_fn=quota_pty_preexec(slave_fd, policy_preexec),
        )
    except Exception as e:
        try:
            os.close(master_fd)
        except OSError:
            pass
        try:
            os.close(slave_fd)
        except OSError:
            pass
        if isinstance(e, QuotaProbeError):
            raise
        raise QuotaProbeError("pty_failure", f"failed to start PTY quota probe: {e}") from e
    os.close(slave_fd)
    audit.record("quota", "started", tool=tool_key, backend=backend, details={"cwd": cwd, "command": command, "pid": proc.pid})
    return proc, master_fd, policy


def agy_quota_backend_configured():
    raw = os.environ.get(AGY_QUOTA_BACKEND_ENV, "auto").strip().lower()
    if raw not in ("auto", "tmux", "pty"):
        logging.warning("%s=%r is invalid; using auto", AGY_QUOTA_BACKEND_ENV, raw)
        return "auto"
    return raw


def tmux_path():
    return shutil.which("tmux")


def resolve_quota_backend(tool_key):
    if tool_key != "agy":
        return "persistent_pty"
    configured = agy_quota_backend_configured()
    found_tmux = tmux_path()
    if configured == "pty":
        return "persistent_pty"
    if configured == "tmux":
        if not found_tmux:
            raise QuotaProbeError("missing_backend", "tmux quota backend was requested but tmux is not installed or not in PATH")
        return "tmux"
    if found_tmux:
        return "tmux"
    logging.warning("AGY quota backend auto falling back to persistent_pty because tmux is unavailable")
    return "persistent_pty"


def tmux_quota_session_name(tool_key, command, env, cwd):
    home = os.path.abspath(env.get("HOME") or "")
    absolute_cwd = os.path.abspath(cwd)
    identity = "\0".join([tool_key, "\0".join(command), absolute_cwd, home])
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:12]
    profile = os.path.basename(home) or "unknown"
    safe_profile = re.sub(r"[^A-Za-z0-9_-]+", "_", profile).strip("_") or "profile"
    return f"{TMUX_QUOTA_SESSION_PREFIX}{tool_key}_{safe_profile}_{digest}"


class TmuxQuotaSession:
    def __init__(self, tool_key, command, env, cwd):
        self.tool_key = tool_key
        self.command = list(command)
        self.env = env.copy()
        self.cwd = cwd
        self.session_name = tmux_quota_session_name(tool_key, self.command, self.env, cwd)
        self.lock = threading.Lock()
        self.created_at = time.time()
        self.last_used_at = self.created_at
        self.ready = False
        self.starting = False
        self.last_alive_check_at = 0.0
        self.last_alive_result = None
        self.last_snapshot_metrics = {}
        self.lifecycle_metrics = {
            "startup_count": 0,
            "snapshot_count": 0,
            "warm_snapshot_count": 0,
            "cold_snapshot_count": 0,
            "close_count": 0,
            "evict_count": 0,
            "external_death_count": 0,
        }

    @property
    def backend(self):
        return "tmux"

    def _run_tmux(self, args, check=True, timeout=5):
        tmux = tmux_path()
        if not tmux:
            raise QuotaProbeError("missing_backend", "tmux quota backend was requested but tmux is not installed or not in PATH")
        try:
            completed = subprocess.run(
                [tmux, *args],
                text=True,
                capture_output=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as e:
            raw_output = "".join(part for part in (e.stdout, e.stderr) if part)
            raise QuotaProbeError("timeout", "timeout waiting for tmux quota backend", raw_output) from e
        output = "".join(part for part in (completed.stdout, completed.stderr) if part)
        if check and completed.returncode != 0:
            if re.search(r"\b(can't find session|no server running|session not found)\b", output, re.I):
                raise QuotaProbeError("process_exit", "tmux quota session is not running", output)
            raise QuotaProbeError("tmux_failure", f"tmux command failed with code {completed.returncode}", output)
        return completed

    def _cache_liveness(self, alive):
        self.last_alive_check_at = time.monotonic()
        self.last_alive_result = bool(alive)
        return bool(alive)

    def _clear_liveness_cache(self):
        self.last_alive_check_at = 0.0
        self.last_alive_result = None

    def start(self, timeout_seconds=DEFAULT_TIMEOUT_SECONDS, idle_seconds=DEFAULT_IDLE_SECONDS):
        if shutil.which(self.command[0]) is None:
            raise QuotaProbeError("missing_cli", f"{self.command[0]} CLI is not installed or not in PATH")
        self.starting = True
        started_at = time.monotonic()
        home = self.env.get("HOME")
        tmux_command = [
            "new-session",
            "-d",
            "-x",
            str(tmux_quota_cols()),
            "-y",
            str(tmux_quota_rows()),
            "-s",
            self.session_name,
            "-c",
            self.cwd,
        ]
        if home:
            tmux_command.extend(["env", f"HOME={home}"])
        tmux_command.extend(self.command)
        try:
            with tmux_cold_start_slot():
                self._run_tmux(tmux_command)
                self.resize_for_quota()
                self._cache_liveness(True)
                self.lifecycle_metrics["startup_count"] += 1
                audit.record(
                    "quota",
                    "started",
                    tool=self.tool_key,
                    backend="tmux",
                    details={
                        "session": self.session_name,
                        "cwd": self.cwd,
                        "home": home,
                        "command": self.command,
                        "cold_start_concurrency": tmux_cold_start_concurrency(),
                    },
                )
                logging.debug(
                    "quota session create tool=%s backend=tmux session=%s cwd=%s home=%s",
                    self.tool_key,
                    self.session_name,
                    self.cwd,
                    home,
                )
                ready_started_at = time.monotonic()
                self.wait_for_ready(timeout_seconds=timeout_seconds)
                self.lifecycle_metrics["last_ready_ms"] = round((time.monotonic() - ready_started_at) * 1000, 3)
        except QuotaProbeError as e:
            if self.tool_key == "agy" and e.state == "startup_pending" and self.is_alive():
                self.starting = False
                self.lifecycle_metrics["last_startup_ms"] = round((time.monotonic() - started_at) * 1000, 3)
                audit.record(
                    "quota",
                    "completed",
                    tool=self.tool_key,
                    backend="tmux",
                    result="startup_pending",
                    details={"session": self.session_name},
                )
                raise
            self.starting = False
            if self.is_alive():
                self.close()
            raise
        except Exception:
            self.starting = False
            if self.is_alive():
                self.close()
            raise
        self.ready = True
        self.starting = False
        self.lifecycle_metrics["last_startup_ms"] = round((time.monotonic() - started_at) * 1000, 3)
        audit.record(
            "quota",
            "completed",
            tool=self.tool_key,
            backend="tmux",
            result="succeeded",
            details={"session": self.session_name, "startup_ms": self.lifecycle_metrics["last_startup_ms"]},
        )
        logging.debug(
            "quota session ready tool=%s backend=tmux session=%s cwd=%s home=%s",
            self.tool_key,
            self.session_name,
            self.cwd,
            home,
        )

    def is_alive(self, use_cache=True):
        if not manager_owned_tmux_session_name(self.session_name):
            return False
        if use_cache and self.last_alive_result is not None:
            cache_age = time.monotonic() - self.last_alive_check_at
            if cache_age <= tmux_liveness_cache_seconds():
                return self.last_alive_result
        try:
            completed = self._run_tmux(["has-session", "-t", self.session_name], check=False)
        except QuotaProbeError:
            return self._cache_liveness(False)
        alive = completed.returncode == 0
        if not alive and self.last_alive_result is True:
            self.lifecycle_metrics["external_death_count"] += 1
        return self._cache_liveness(alive)

    def capture(self, start="-200"):
        completed = self._run_tmux(["capture-pane", "-pt", self.session_name, "-S", str(start)])
        return completed.stdout or ""

    def capture_recent(self, kind="short"):
        return self.capture(start=f"-{tmux_capture_lines(kind)}")

    def resize_for_quota(self):
        self._run_tmux(
            [
                "resize-window",
                "-t",
                self.session_name,
                "-x",
                str(tmux_quota_cols()),
                "-y",
                str(tmux_quota_rows()),
            ],
            check=False,
        )

    def wait_for_ready(self, timeout_seconds=DEFAULT_TIMEOUT_SECONDS):
        startup_seconds = quota_startup_seconds(self.tool_key)
        deadline = time.monotonic() + min(max(startup_seconds, 0.0), max(timeout_seconds, startup_seconds, 0.0))
        last_snapshot = ""
        while time.monotonic() <= deadline:
            if not self.is_alive(use_cache=False):
                raise QuotaProbeError("process_exit", "tmux quota session exited during startup", last_snapshot)
            last_snapshot = self.capture()
            classified = classify_agy_failure(last_snapshot, fatal_only=True) if self.tool_key == "agy" else None
            if classified:
                state, message = classified
                raise QuotaProbeError(state, message, last_snapshot)
            if self.tool_key == "agy" and (agy_cli_ready(last_snapshot) or agy_prompt_ready(last_snapshot)):
                return last_snapshot
            time.sleep(0.1)
        if self.tool_key == "agy" and AGY_STARTUP_PENDING_PATTERN.search(last_snapshot):
            raise QuotaProbeError("startup_pending", "AGY CLI is still starting", last_snapshot)
        raise QuotaProbeError("timeout", "timeout waiting for AGY CLI readiness", last_snapshot)

    def snapshot(self, timeout_seconds=DEFAULT_TIMEOUT_SECONDS, idle_seconds=DEFAULT_IDLE_SECONDS):
        with self.lock:
            self.last_used_at = time.time()
            reused_session = True
            if not self.is_alive():
                self.close()
                self.start(timeout_seconds=timeout_seconds, idle_seconds=idle_seconds)
                reused_session = False
            elif not self.ready:
                audit.record("quota", "retried", tool=self.tool_key, backend="tmux", details={"reuse": True, "session": self.session_name})
                self.wait_for_ready(timeout_seconds=timeout_seconds)
                self.ready = True
            else:
                audit.record("quota", "retried", tool=self.tool_key, backend="tmux", details={"reuse": True, "session": self.session_name})
                logging.debug(
                    "quota session reuse tool=%s backend=tmux session=%s cwd=%s home=%s",
                    self.tool_key,
                    self.session_name,
                    self.cwd,
                    self.env.get("HOME"),
                )
            slash_command = quota_command_for(self.tool_key)
            if not slash_command:
                raise QuotaProbeError("unsupported", f"quota command is not configured for {self.tool_key}")
            started_at = time.monotonic()
            was_warm = reused_session and self.ready
            with tmux_warm_snapshot_slot():
                self.resize_for_quota()
                self._run_tmux(["send-keys", "-t", self.session_name, slash_command, "Enter"])
                logging.debug(
                    "quota command sent tool=%s backend=tmux session=%s command=%s",
                    self.tool_key,
                    self.session_name,
                    slash_command,
                )
                post_command_seconds = quota_post_command_seconds(self.tool_key)
                poll_interval = tmux_poll_interval_seconds()
                deadline = time.monotonic() + post_command_seconds
                snapshot = ""
                ready = False
                captures = 0
                while True:
                    snapshot = self.capture_recent("short")
                    captures += 1
                    if quota_snapshot_ready(self.tool_key, snapshot):
                        ready = True
                        break
                    if time.monotonic() >= deadline:
                        break
                    time.sleep(min(poll_interval, max(0.0, deadline - time.monotonic())))
                capture_kind = "short"
                if not ready:
                    snapshot = self.capture_recent("long")
                    captures += 1
                    capture_kind = "long"
                self._run_tmux(["send-keys", "-t", self.session_name, "Escape"], check=False)
                if not self.is_alive():
                    raise QuotaProbeError("process_exit", "tmux quota session exited during quota probe", snapshot)
            self.last_snapshot_metrics = {
                "warm": was_warm,
                "latency_ms": round((time.monotonic() - started_at) * 1000, 3),
                "capture_kind": capture_kind,
                "captures": captures,
                "bytes": len(snapshot),
                "marker_ready": ready,
                "warm_snapshot_concurrency": tmux_warm_snapshot_concurrency(),
            }
            self.lifecycle_metrics["snapshot_count"] += 1
            if was_warm:
                self.lifecycle_metrics["warm_snapshot_count"] += 1
            else:
                self.lifecycle_metrics["cold_snapshot_count"] += 1
            self.lifecycle_metrics["last_snapshot_ms"] = self.last_snapshot_metrics["latency_ms"]
            audit.record(
                "quota",
                "completed",
                tool=self.tool_key,
                backend="tmux",
                result="warm_snapshot" if was_warm else "cold_snapshot",
                details={"session": self.session_name, **self.last_snapshot_metrics},
            )
            return snapshot

    def close(self):
        started_at = time.monotonic()
        self.ready = False
        self.starting = False
        self._clear_liveness_cache()
        if not manager_owned_tmux_session_name(self.session_name):
            return
        try:
            self._run_tmux(["kill-session", "-t", self.session_name], check=False)
        except QuotaProbeError:
            pass
        self.lifecycle_metrics["close_count"] += 1
        self.lifecycle_metrics["last_close_ms"] = round((time.monotonic() - started_at) * 1000, 3)
        audit.record("quota", "completed", tool=self.tool_key, backend="tmux", result="closed", details={"session": self.session_name, "close_ms": self.lifecycle_metrics["last_close_ms"]})
        logging.debug(
            "quota session close tool=%s backend=tmux session=%s cwd=%s home=%s",
            self.tool_key,
            self.session_name,
            self.cwd,
            self.env.get("HOME"),
        )


class PersistentQuotaSession:
    def __init__(self, tool_key, command, env, cwd):
        self.tool_key = tool_key
        self.command = list(command)
        self.env = env.copy()
        self.cwd = cwd
        self.proc = None
        self.master_fd = None
        self.lock = threading.Lock()
        self.created_at = time.time()
        self.last_used_at = self.created_at
        self.ready = False
        self.starting = False

    @property
    def backend(self):
        return "persistent_pty"

    def start(self, timeout_seconds=DEFAULT_TIMEOUT_SECONDS, idle_seconds=DEFAULT_IDLE_SECONDS):
        self.starting = True
        try:
            proc, master_fd, policy = start_quota_pty_process(
                self.tool_key,
                self.command,
                self.env,
                self.cwd,
                "persistent_pty",
            )
        except Exception:
            self.starting = False
            raise
        self.proc = proc
        self.master_fd = master_fd
        output = []
        try:
            startup_seconds = quota_startup_seconds(self.tool_key)
            wait_for_cli_startup(
                self.tool_key,
                master_fd,
                output,
                startup_seconds,
                idle_seconds,
                timeout_seconds,
            )
            if proc.poll() is not None:
                if proc.returncode in (125, 126):
                    state = "resource_limited" if proc.returncode == 125 else "pty_failure"
                    message = (
                        f"failed to apply quota process limits with backend {policy.get('backend')}"
                        if proc.returncode == 125
                        else "failed to assign controlling terminal for quota process"
                    )
                    raise QuotaProbeError(
                        state,
                        message,
                        output_text(output),
                )
                raise QuotaProbeError("process_exit", "CLI process exited during startup", output_text(output))
        except QuotaProbeError as e:
            if self.tool_key == "agy" and e.state == "startup_pending" and proc.poll() is None:
                self.starting = False
                audit.record(
                    "quota",
                    "completed",
                    tool=self.tool_key,
                    backend="persistent_pty",
                    result="startup_pending",
                    details={"pid": proc.pid},
                )
                raise
            terminate_process(proc, master_fd, output)
            self.proc = None
            self.master_fd = None
            self.starting = False
            try:
                os.close(master_fd)
            except OSError:
                pass
            raise
        except Exception:
            terminate_process(proc, master_fd, output)
            self.proc = None
            self.master_fd = None
            self.starting = False
            try:
                os.close(master_fd)
            except OSError:
                pass
            raise
        self.ready = True
        self.starting = False
        audit.record("quota", "completed", tool=self.tool_key, backend="persistent_pty", result="succeeded", details={"pid": proc.pid})

    def is_alive(self):
        return (
            (self.starting and self.master_fd is not None)
            or (self.proc is not None and self.proc.poll() is None and self.master_fd is not None)
        )

    def snapshot(self, timeout_seconds=DEFAULT_TIMEOUT_SECONDS, idle_seconds=DEFAULT_IDLE_SECONDS):
        with self.lock:
            self.last_used_at = time.time()
            if not self.is_alive():
                self.close()
                self.start(timeout_seconds=timeout_seconds, idle_seconds=idle_seconds)
            else:
                audit.record("quota", "retried", tool=self.tool_key, backend="persistent_pty", details={"reuse": True})
                if self.tool_key == "agy" and not self.ready:
                    output = []
                    startup_seconds = quota_startup_seconds(self.tool_key)
                    wait_for_agy_readiness(
                        self.master_fd,
                        output,
                        startup_seconds,
                        idle_seconds,
                    )
                    self.ready = True
            read_available(self.master_fd)
            slash_command = quota_command_for(self.tool_key)
            if not slash_command:
                raise QuotaProbeError("unsupported", f"quota command is not configured for {self.tool_key}")
            output = []
            send_interactive_command(self.master_fd, slash_command, quota_key_delay_seconds(self.tool_key))
            post_command_seconds = quota_post_command_seconds(self.tool_key)
            wait_after_command(self.master_fd, output, max(0.0, post_command_seconds))
            snapshot = wait_for_idle(self.master_fd, output, idle_seconds, timeout_seconds)
            if not self.is_alive():
                raise QuotaProbeError("process_exit", "CLI process exited during quota probe", snapshot)
            return snapshot

    def close(self):
        proc = self.proc
        master_fd = self.master_fd
        self.proc = None
        self.master_fd = None
        self.ready = False
        self.starting = False
        if proc is None or master_fd is None:
            return
        audit.record("quota", "completed", tool=self.tool_key, backend="persistent_pty", result="closed")
        output = []
        terminate_process(proc, master_fd, output)
        try:
            os.close(master_fd)
        except OSError:
            pass
        if proc.poll() is None:
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except OSError:
                pass


PERSISTENT_QUOTA_SESSIONS = {}
PERSISTENT_QUOTA_PARSER_MISSES = {}
PERSISTENT_QUOTA_LOCK = threading.Lock()
TMUX_POOL_LOCK = threading.Lock()
TMUX_POOL_SEMAPHORES = {}
INVALIDATING_QUOTA_STATES = {"timeout", "process_exit", "resource_limited"}


class PoolSlot:
    def __init__(self, semaphore):
        self.semaphore = semaphore

    def __enter__(self):
        self.semaphore.acquire()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.semaphore.release()
        return False


def tmux_pool_semaphore(name, limit):
    key = (name, int(limit))
    with TMUX_POOL_LOCK:
        semaphore = TMUX_POOL_SEMAPHORES.get(key)
        if semaphore is None:
            semaphore = threading.BoundedSemaphore(int(limit))
            TMUX_POOL_SEMAPHORES[key] = semaphore
        return semaphore


def tmux_cold_start_slot():
    return PoolSlot(tmux_pool_semaphore("tmux_cold_start", tmux_cold_start_concurrency()))


def tmux_warm_snapshot_slot():
    return PoolSlot(tmux_pool_semaphore("tmux_warm_snapshot", tmux_warm_snapshot_concurrency()))


def manager_owned_tmux_session_name(session_name):
    return isinstance(session_name, str) and session_name.startswith(TMUX_QUOTA_SESSION_PREFIX)


def persistent_session_ttl_seconds():
    raw = os.environ.get("AI_MAN_QUOTA_SESSION_TTL_SECONDS", str(DEFAULT_PERSISTENT_SESSION_TTL_SECONDS))
    try:
        return max(1.0, float(raw))
    except ValueError:
        return DEFAULT_PERSISTENT_SESSION_TTL_SECONDS


def persistent_session_max_count():
    raw = os.environ.get("AI_MAN_QUOTA_SESSION_MAX", str(DEFAULT_PERSISTENT_SESSION_MAX))
    try:
        return max(1, int(raw))
    except ValueError:
        return DEFAULT_PERSISTENT_SESSION_MAX


def persistent_quota_session_key(tool_key, command, env, cwd, backend="persistent_pty"):
    home = env.get("HOME")
    return (
        tool_key,
        tuple(command),
        os.path.abspath(cwd),
        os.path.abspath(home) if home else None,
        env.get("CODEX_HOME"),
        env.get("CLAUDE_CONFIG_DIR"),
        backend,
    )


def close_persistent_quota_sessions(tool_key=None, home=None):
    with PERSISTENT_QUOTA_LOCK:
        sessions = []
        for key, session in list(PERSISTENT_QUOTA_SESSIONS.items()):
            if tool_key is not None and key[0] != tool_key:
                continue
            if home is not None and key[3] != os.path.abspath(home):
                continue
            sessions.append(session)
            del PERSISTENT_QUOTA_SESSIONS[key]
            PERSISTENT_QUOTA_PARSER_MISSES.pop(key, None)
    for session in sessions:
        logging.debug(
            "quota session close tool=%s cwd=%s home=%s",
            getattr(session, "tool_key", None),
            getattr(session, "cwd", None),
            getattr(session, "env", {}).get("HOME"),
        )
        session.close()


def evict_persistent_quota_sessions(now=None):
    now = time.time() if now is None else now
    ttl = persistent_session_ttl_seconds()
    max_count = persistent_session_max_count()
    with PERSISTENT_QUOTA_LOCK:
        evicted = []
        for key, session in list(PERSISTENT_QUOTA_SESSIONS.items()):
            if getattr(session, "starting", False):
                continue
            if not session.is_alive() or now - getattr(session, "last_used_at", now) > ttl:
                evicted.append(session)
                del PERSISTENT_QUOTA_SESSIONS[key]
                PERSISTENT_QUOTA_PARSER_MISSES.pop(key, None)
        if len(PERSISTENT_QUOTA_SESSIONS) > max_count:
            by_idle = sorted(
                (
                    item for item in PERSISTENT_QUOTA_SESSIONS.items()
                    if not getattr(item[1], "starting", False)
                ),
                key=lambda item: getattr(item[1], "last_used_at", 0),
            )
            for key, session in by_idle[:max(0, len(PERSISTENT_QUOTA_SESSIONS) - max_count)]:
                evicted.append(session)
                del PERSISTENT_QUOTA_SESSIONS[key]
                PERSISTENT_QUOTA_PARSER_MISSES.pop(key, None)
    for session in evicted:
        backend = getattr(session, "backend", "persistent_pty")
        lifecycle = getattr(session, "lifecycle_metrics", None)
        if isinstance(lifecycle, dict):
            lifecycle["evict_count"] = lifecycle.get("evict_count", 0) + 1
            lifecycle["last_evict_at"] = now
        audit.record("quota", "skipped", tool=getattr(session, "tool_key", None), backend=backend, result="evicted")
        logging.debug(
            "quota session evict tool=%s backend=%s cwd=%s home=%s",
            getattr(session, "tool_key", None),
            backend,
            getattr(session, "cwd", None),
            getattr(session, "env", {}).get("HOME"),
        )
        session.close()
    return len(evicted)


def persistent_quota_sessions_snapshot(tool_key=None):
    with PERSISTENT_QUOTA_LOCK:
        sessions = []
        by_backend = {}
        starting_count = 0
        ready_count = 0
        for key, session in PERSISTENT_QUOTA_SESSIONS.items():
            if tool_key is not None and key[0] != tool_key:
                continue
            backend = key[6] if len(key) > 6 else getattr(session, "backend", "persistent_pty")
            by_backend[backend] = by_backend.get(backend, 0) + 1
            if getattr(session, "starting", False):
                starting_count += 1
            if getattr(session, "ready", False):
                ready_count += 1
            sessions.append({
                "tool": key[0],
                "command": list(key[1]),
                "cwd": key[2],
                "home": key[3],
                "codex_home": key[4],
                "claude_config_dir": key[5],
                "backend": backend,
                "session_name": getattr(session, "session_name", None),
                "manager_owned": manager_owned_tmux_session_name(getattr(session, "session_name", None)) if backend == "tmux" else True,
                "starting": bool(getattr(session, "starting", False)),
                "ready": bool(getattr(session, "ready", False)),
                "alive": session.is_alive(),
                "parser_misses": PERSISTENT_QUOTA_PARSER_MISSES.get(key, 0),
                "last_snapshot_metrics": dict(getattr(session, "last_snapshot_metrics", {}) or {}),
                "lifecycle_metrics": dict(getattr(session, "lifecycle_metrics", {}) or {}),
                "created_age_seconds": round(time.time() - getattr(session, "created_at", time.time()), 3),
                "idle_age_seconds": round(time.time() - getattr(session, "last_used_at", time.time()), 3),
            })
    return {
        "count": len(sessions),
        "pool": {
            "ttl_seconds": persistent_session_ttl_seconds(),
            "max_count": persistent_session_max_count(),
            "tmux_cold_start_concurrency": tmux_cold_start_concurrency(),
            "tmux_warm_snapshot_concurrency": tmux_warm_snapshot_concurrency(),
            "by_backend": by_backend,
            "starting": starting_count,
            "ready": ready_count,
        },
        "sessions": sessions,
    }


atexit.register(close_persistent_quota_sessions)


def run_persistent_cli_quota_snapshot(tool_key, command, env, cwd, timeout_seconds=DEFAULT_TIMEOUT_SECONDS, idle_seconds=DEFAULT_IDLE_SECONDS):
    backend = resolve_quota_backend(tool_key)
    key = persistent_quota_session_key(tool_key, command, env, cwd, backend)
    evict_persistent_quota_sessions()
    with PERSISTENT_QUOTA_LOCK:
        session = PERSISTENT_QUOTA_SESSIONS.get(key)
        if session is None:
            session_class = TmuxQuotaSession if backend == "tmux" else PersistentQuotaSession
            session = session_class(tool_key, command, env, cwd)
            PERSISTENT_QUOTA_SESSIONS[key] = session
            logging.debug("quota session create tool=%s backend=%s cwd=%s home=%s", tool_key, backend, cwd, env.get("HOME"))
    try:
        return session.snapshot(timeout_seconds=timeout_seconds, idle_seconds=idle_seconds)
    except Exception as e:
        invalidating = isinstance(e, QuotaProbeError) and e.state in INVALIDATING_QUOTA_STATES
        if invalidating or not session.is_alive():
            with PERSISTENT_QUOTA_LOCK:
                if PERSISTENT_QUOTA_SESSIONS.get(key) is session:
                    del PERSISTENT_QUOTA_SESSIONS[key]
                    PERSISTENT_QUOTA_PARSER_MISSES.pop(key, None)
            logging.debug(
                "quota session invalidate tool=%s backend=%s cwd=%s home=%s reason=%s",
                tool_key,
                backend,
                cwd,
                env.get("HOME"),
                getattr(e, "state", type(e).__name__),
            )
            session.close()
        raise


def record_persistent_parser_result(tool_key, command, env, cwd, quota):
    try:
        backend = resolve_quota_backend(tool_key)
    except QuotaProbeError:
        return
    key = persistent_quota_session_key(tool_key, command, env, cwd, backend)
    state = quota.get("state")
    with PERSISTENT_QUOTA_LOCK:
        if key not in PERSISTENT_QUOTA_SESSIONS:
            return
        if state != "parser_miss":
            PERSISTENT_QUOTA_PARSER_MISSES.pop(key, None)
            return
        misses = PERSISTENT_QUOTA_PARSER_MISSES.get(key, 0) + 1
        if misses < PARSER_MISS_SESSION_INVALIDATION_THRESHOLD:
            PERSISTENT_QUOTA_PARSER_MISSES[key] = misses
            return
        session = PERSISTENT_QUOTA_SESSIONS.pop(key)
        PERSISTENT_QUOTA_PARSER_MISSES.pop(key, None)
    logging.debug("quota session invalidate tool=%s backend=%s cwd=%s home=%s reason=parser_miss", tool_key, backend, cwd, env.get("HOME"))
    session.close()


def run_cli_quota_snapshot(tool_key, command, env, cwd, timeout_seconds=DEFAULT_TIMEOUT_SECONDS, idle_seconds=DEFAULT_IDLE_SECONDS):
    proc, master_fd, policy = start_quota_pty_process(tool_key, command, env, cwd, "pty")
    output = []
    try:
        startup_seconds = quota_startup_seconds(tool_key)
        wait_for_cli_startup(
            tool_key,
            master_fd,
            output,
            startup_seconds,
            idle_seconds,
            timeout_seconds,
        )
        if proc.poll() in (125, 126):
            state = "resource_limited" if proc.returncode == 125 else "pty_failure"
            message = (
                f"failed to apply quota process limits with backend {policy.get('backend')}"
                if proc.returncode == 125
                else "failed to assign controlling terminal for quota process"
            )
            raise QuotaProbeError(
                state,
                message,
                output_text(output),
            )
        slash_command = quota_command_for(tool_key)
        if not slash_command:
            raise QuotaProbeError("unsupported", f"quota command is not configured for {tool_key}")
        send_interactive_command(master_fd, slash_command, quota_key_delay_seconds(tool_key))
        post_command_seconds = quota_post_command_seconds(tool_key)
        wait_after_command(master_fd, output, max(0.0, post_command_seconds))
        snapshot = wait_for_idle(master_fd, output, idle_seconds, timeout_seconds)
        audit.record("quota", "completed", tool=tool_key, backend="pty", result="succeeded", details={"bytes": len(snapshot)})
        return snapshot
    finally:
        terminate_process(proc, master_fd, output)
        try:
            os.close(master_fd)
        except OSError:
            pass
        if proc.poll() is None:
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except OSError:
                pass


def parse_quota(tool_key, screen_text):
    normalized = strip_terminal_sequences(screen_text)
    summary = "\n".join(compact_lines(normalized))
    if not summary.strip():
        return {
            "state": "empty_output",
            "source_command": quota_command_for(tool_key),
            "limits": {},
            "warnings": ["quota command returned no readable output"],
        }
    if tool_key == "agy":
        classified = classify_agy_failure(normalized)
        if classified and classified[0] not in AGY_NONFATAL_WARNING_STATES:
            state, message = classified
            result = {
                "state": state,
                "source_command": quota_command_for(tool_key),
                "limits": {},
                "warnings": [message],
            }
            diagnostic = agy_diagnostic_summary(normalized, state)
            if diagnostic:
                result["diagnostic_summary"] = diagnostic
            return result
        if DIRECT_AGY_PROMPT_SUCCESS_MARKER in normalized:
            clean_summary = summary.replace(DIRECT_AGY_PROMPT_SUCCESS_MARKER, "").strip()
            result = {
                "state": "available",
                "source_command": "agy-profile-prompt",
                "limits": {},
                "raw_summary": clean_summary,
                "warnings": ["AGY profile prompt completed; quota percentages are not available from this probe"],
            }
            if clean_summary:
                result["diagnostic_summary"] = clean_summary[:240]
            return result
    if detect_auth_required(normalized):
        return {
            "state": "auth_required",
            "source_command": quota_command_for(tool_key),
            "limits": {},
            "warnings": ["CLI reported that authentication is required"],
        }
    parser = PARSERS.get(tool_key)
    if parser is None:
        return {
            "state": "unsupported",
            "source_command": quota_command_for(tool_key),
            "limits": {},
            "warnings": [f"quota parsing is not configured for {tool_key}"],
        }
    result = parser(normalized)
    result["source_command"] = quota_command_for(tool_key)
    if not result.get("limits"):
        result["state"] = "parser_miss"
        diagnostic = summary[:240]
        result["warnings"] = ["quota output was captured but no known quota fields matched"]
        eligibility_warning = agy_eligibility_warning(normalized) if tool_key == "agy" else None
        if eligibility_warning:
            result["warnings"].append(eligibility_warning)
        if diagnostic:
            result["diagnostic_summary"] = diagnostic
    return result


def run_direct_cli_prompt_snapshot(tool_key, command, env, cwd, timeout_seconds=DEFAULT_TIMEOUT_SECONDS, idle_seconds=DEFAULT_IDLE_SECONDS):
    if shutil.which(command[0]) is None:
        raise QuotaProbeError("missing_cli", f"{command[0]} CLI is not installed or not in PATH")
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as e:
        raw_output = "".join(part for part in (e.stdout, e.stderr) if part)
        raise QuotaProbeError("timeout", f"timeout waiting for {command[0]} prompt output", raw_output) from e
    output = "".join(part for part in (completed.stdout, completed.stderr) if part)
    if completed.returncode != 0:
        raise QuotaProbeError("process_exit", f"{command[0]} exited with code {completed.returncode}", output)
    if tool_key == "agy":
        output = f"{output}\n{DIRECT_AGY_PROMPT_SUCCESS_MARKER}\n"
    return output


def source_command_for_payload(tool_key, command):
    if tool_key == "agy" and command and re.fullmatch(r"agy\d+", str(command[0])):
        return " ".join(str(part) for part in command)
    return quota_command_for(tool_key)


def quota_payload(tool_key, profile_name, command, env, cwd, timeout_seconds=DEFAULT_TIMEOUT_SECONDS, runner=run_cli_quota_snapshot):
    audit.record("quota", "attempted", tool=tool_key, profile=profile_name, details={"runner": getattr(runner, "__name__", "runner")})
    try:
        screen_text = runner(tool_key, command, env, cwd, timeout_seconds=timeout_seconds)
        quota = parse_quota(tool_key, screen_text)
    except QuotaProbeError as e:
        state = e.state
        message = str(e)
        diagnostic = None
        if tool_key == "agy":
            classified = classify_agy_probe_error(state, e.raw_output)
            if classified:
                state, message = classified
            diagnostic = agy_diagnostic_summary(e.raw_output, state)
        audit.record(
            "quota",
            "failed",
            tool=tool_key,
            profile=profile_name,
            result="failed",
            error_class=state,
            details={"message": message, "diagnostic_summary": diagnostic},
        )
        quota = {
            "state": state,
            "source_command": source_command_for_payload(tool_key, command),
            "limits": {},
            "warnings": [message],
        }
        if diagnostic:
            quota["diagnostic_summary"] = diagnostic
    if runner is run_persistent_cli_quota_snapshot:
        record_persistent_parser_result(tool_key, command, env, cwd, quota)
    audit.record(
        "quota",
        "completed",
        tool=tool_key,
        profile=profile_name,
        result=quota.get("state"),
        details={
            "source_command": quota.get("source_command"),
            "limits": list(quota.get("limits", {})),
            "warnings": list(quota.get("warnings") or []),
            "diagnostic_summary": quota.get("diagnostic_summary"),
        },
    )
    return {
        "tool": tool_key,
        "profile": profile_name,
        "quota": quota,
    }
