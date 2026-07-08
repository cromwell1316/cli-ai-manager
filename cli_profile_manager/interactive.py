import glob
import logging
import os
import queue
import re
import select
import sys
import termios
import threading
import time
import tty
from concurrent.futures import Future

from .cli import (
    CLR_BG_CYAN,
    CLR_BLACK_TEXT,
    CLR_BLUE,
    CLR_BOLD,
    CLR_CYAN,
    CLR_GREEN,
    CLR_MAGENTA,
    CLR_RED,
    CLR_RESET,
    CLR_WHITE,
    CLR_YELLOW,
    EXIT_OK,
    TOOLS,
    account_email_from_google_accounts,
    build_windows_agy_credential,
    credential_path,
    clear_profile_data,
    core_find_windows_user,
    default_export_dir,
    export_credential_file,
    find_windows_user,
    agy_quota_entries,
    first_free_profile,
    get_display_profiles,
    get_profile_status,
    get_profiles,
    import_credential_file,
    label_profile,
    load_metadata,
    normalize_credential_path,
    parse_profile,
    profile_home,
    read_wsl_agy_oauth,
    resolve_sync_bases,
    run_cli_tool,
    save_metadata,
    quota_payload,
    status_payload,
    sync_profiles_noninteractive,
    quota_summary,
    write_json_atomic,
)
from .quota import close_persistent_quota_sessions

AGY_DEFAULT_QUOTA_COLUMNS = ["FM", "FH", "FL", "PL", "PH", "CS", "CO"]
INTERACTIVE_QUOTA_CACHE = {}
INTERACTIVE_QUOTA_LOCK = threading.Lock()
QUOTA_FRESH_SECONDS = 300
QUOTA_STALE_SECONDS = 3600
QUOTA_RETRY_BACKOFF_SECONDS = (10, 30, 60)
QUOTA_ACTIVE_JOB_STATES = ("queued", "running")
INTERACTIVE_QUOTA_SCHEDULER = None
INTERACTIVE_QUOTA_SCHEDULER_LOCK = threading.Lock()
ANSI_RE = re.compile(
    r"(?:\x1b\[[0-?]*[ -/]*[@-~]|\x1b\][^\x07]*(?:\x07|\x1b\\)|\x1b[@-_])"
)


def visible_len(text):
    return len(ANSI_RE.sub("", str(text)))


def visible_ljust(text, width):
    text = str(text)
    return text + (" " * max(0, width - visible_len(text)))


def visible_fit(text, width):
    text = str(text)
    if visible_len(text) <= width:
        return visible_ljust(text, width)
    plain = ANSI_RE.sub("", text)
    if width <= 3:
        return plain[:width]
    return plain[:width - 3] + "..."


def interactive_quota_enabled():
    return os.environ.get("AI_MAN_INTERACTIVE_QUOTA", "1").lower() not in ("0", "false", "no", "off")


def interactive_quota_timeout(tool_key=None):
    if tool_key == "agy":
        raw = os.environ.get("AI_MAN_INTERACTIVE_AGY_QUOTA_TIMEOUT", os.environ.get("AI_MAN_INTERACTIVE_QUOTA_TIMEOUT", "40"))
        fallback = 40.0
    else:
        raw = os.environ.get("AI_MAN_INTERACTIVE_QUOTA_TIMEOUT", "12")
        fallback = 12.0
    try:
        return max(1.0, float(raw))
    except ValueError:
        return fallback


def interactive_agy_quota_concurrency():
    raw = os.environ.get("AI_MAN_INTERACTIVE_AGY_QUOTA_CONCURRENCY", "2")
    try:
        return max(1, int(raw))
    except ValueError:
        return 2


def interactive_quota_fresh_seconds():
    raw = os.environ.get("AI_MAN_INTERACTIVE_QUOTA_FRESH_SECONDS", "600")
    try:
        return max(1.0, float(raw))
    except ValueError:
        return 600.0


class InteractiveQuotaScheduler:
    def __init__(self, agy_concurrency=None):
        self.agy_concurrency = agy_concurrency or interactive_agy_quota_concurrency()
        self.queue = queue.Queue()
        self.closed = False
        self.workers = []
        for idx in range(self.agy_concurrency):
            worker = threading.Thread(
                target=self._worker,
                name=f"ai-man-quota-{idx + 1}",
                daemon=True,
            )
            worker.start()
            self.workers.append(worker)

    def submit(self, tool_key, profile_num):
        future = Future()
        self.queue.put((tool_key, profile_num, future))
        return future

    def _worker(self):
        while True:
            item = self.queue.get()
            if item is None:
                self.queue.task_done()
                return
            tool_key, profile_num, future = item
            try:
                if future.set_running_or_notify_cancel():
                    load_quota_background(tool_key, profile_num)
                    future.set_result(True)
            except Exception as e:
                finish_quota_refresh(
                    tool_key,
                    profile_num,
                    {
                        "state": "exception",
                        "limits": {},
                        "warnings": [str(e)],
                    },
                    time.time(),
                )
                future.set_exception(e)
            finally:
                self.queue.task_done()

    def shutdown(self):
        if self.closed:
            return
        self.closed = True
        for _ in self.workers:
            self.queue.put(None)


def quota_scheduler():
    global INTERACTIVE_QUOTA_SCHEDULER
    concurrency = interactive_agy_quota_concurrency()
    with INTERACTIVE_QUOTA_SCHEDULER_LOCK:
        if (
            INTERACTIVE_QUOTA_SCHEDULER is None
            or INTERACTIVE_QUOTA_SCHEDULER.agy_concurrency != concurrency
        ):
            if INTERACTIVE_QUOTA_SCHEDULER is not None:
                INTERACTIVE_QUOTA_SCHEDULER.shutdown()
            INTERACTIVE_QUOTA_SCHEDULER = InteractiveQuotaScheduler(concurrency)
        return INTERACTIVE_QUOTA_SCHEDULER


def quota_cache_key(tool_key, profile_num):
    return (tool_key, profile_num)


def quota_cache_entry(tool_key, profile_num):
    with INTERACTIVE_QUOTA_LOCK:
        return INTERACTIVE_QUOTA_CACHE.get(quota_cache_key(tool_key, profile_num))


def store_quota_cache(tool_key, profile_num, entry):
    with INTERACTIVE_QUOTA_LOCK:
        INTERACTIVE_QUOTA_CACHE[quota_cache_key(tool_key, profile_num)] = entry


def quota_entry_fresh(entry, now=None):
    now = time.time() if now is None else now
    fetched_at = entry.get("fetched_at")
    return fetched_at is not None and now - fetched_at <= interactive_quota_fresh_seconds()


def quota_entry_stale_usable(entry, now=None):
    now = time.time() if now is None else now
    fetched_at = entry.get("fetched_at")
    quota = entry.get("quota") or {}
    return (
        fetched_at is not None
        and quota.get("state") == "available"
        and now - fetched_at <= QUOTA_STALE_SECONDS
    )


def retry_delay_for_attempts(attempts):
    if attempts <= 0:
        return QUOTA_RETRY_BACKOFF_SECONDS[0]
    index = min(attempts - 1, len(QUOTA_RETRY_BACKOFF_SECONDS) - 1)
    return QUOTA_RETRY_BACKOFF_SECONDS[index]


def retry_allowed(entry, now=None):
    now = time.time() if now is None else now
    return now >= (entry.get("next_retry_at") or 0)


def loading_quota(job_state="queued"):
    return {
        "state": "loading",
        "job_state": job_state,
        "limits": {},
        "warnings": ["quota is loading"],
    }


def diagnostic_text(quota):
    warnings = quota.get("warnings") or []
    if warnings:
        return str(warnings[0])
    return quota.get("state", "unknown")


def finish_quota_refresh(tool_key, profile_num, quota, now):
    state = quota.get("state", "unknown")
    with INTERACTIVE_QUOTA_LOCK:
        key = quota_cache_key(tool_key, profile_num)
        current = INTERACTIVE_QUOTA_CACHE.get(key) or {}
        attempts = current.get("attempts", 0) + 1
        previous_quota = current.get("quota") or {}
        had_previous = previous_quota.get("state") == "available" and previous_quota.get("limits")
        if state == "available":
            quota["fetched_at"] = now
            quota["job_state"] = "ready"
            entry = {
                "state": "ready",
                "job_state": "ready",
                "quota": quota,
                "fetched_at": now,
                "started_at": current.get("started_at"),
                "attempts": 0,
                "last_error": None,
                "next_retry_at": None,
            }
        else:
            last_error = {
                "state": state,
                "message": diagnostic_text(quota),
                "warnings": list(quota.get("warnings") or []),
            }
            delay = retry_delay_for_attempts(attempts)
            if had_previous:
                preserved = dict(previous_quota)
                preserved["job_state"] = "retryable"
                preserved["last_error"] = last_error
                preserved["warnings"] = list(previous_quota.get("warnings") or [])
                if last_error["message"] and last_error["message"] not in preserved["warnings"]:
                    preserved["warnings"].append(last_error["message"])
                entry_quota = preserved
            else:
                quota["job_state"] = "retryable"
                entry_quota = quota
            entry = {
                "state": "retryable",
                "job_state": "retryable",
                "quota": entry_quota,
                "fetched_at": current.get("fetched_at"),
                "started_at": current.get("started_at"),
                "attempts": attempts,
                "last_error": last_error,
                "next_retry_at": now + delay,
            }
        INTERACTIVE_QUOTA_CACHE[key] = entry
        return entry


def load_quota_background(tool_key, profile_num):
    now = time.time()
    with INTERACTIVE_QUOTA_LOCK:
        entry = INTERACTIVE_QUOTA_CACHE.get(quota_cache_key(tool_key, profile_num))
        if entry is not None:
            entry["state"] = "running"
            entry["job_state"] = "running"
            entry["started_at"] = now
            if (entry.get("quota") or {}).get("state") == "loading":
                entry["quota"]["job_state"] = "running"
    monotonic = getattr(time, "monotonic", time.time)
    started = monotonic()
    logging.debug("quota job start tool=%s profile=p%s", tool_key, profile_num)
    try:
        quota = quota_payload(tool_key, profile_num, interactive_quota_timeout(tool_key))["quota"]
    except Exception as e:
        quota = {
            "state": "exception",
            "limits": {},
            "warnings": [str(e)],
        }
    finish_quota_refresh(tool_key, profile_num, quota, time.time())
    logging.debug(
        "quota job finish tool=%s profile=p%s state=%s elapsed=%.3fs",
        tool_key,
        profile_num,
        quota.get("state", "unknown"),
        monotonic() - started,
    )


def ensure_quota_loading(tool_key, profile_num):
    now = time.time()
    should_submit = False
    with INTERACTIVE_QUOTA_LOCK:
        key = quota_cache_key(tool_key, profile_num)
        entry = INTERACTIVE_QUOTA_CACHE.get(key)
        if entry is None:
            entry = {
                "state": "queued",
                "job_state": "queued",
                "quota": loading_quota("queued"),
                "fetched_at": None,
                "started_at": None,
                "attempts": 0,
                "last_error": None,
                "next_retry_at": None,
            }
            INTERACTIVE_QUOTA_CACHE[key] = entry
            should_submit = True
        elif entry.get("job_state") in QUOTA_ACTIVE_JOB_STATES:
            return entry
        elif quota_entry_fresh(entry, now):
            entry["state"] = "ready"
            entry["job_state"] = "ready"
            entry["quota"]["job_state"] = "ready"
            return entry
        elif entry.get("state") == "retryable" and not retry_allowed(entry, now):
            return entry
        elif quota_entry_stale_usable(entry, now) or entry.get("state") in ("retryable", "failed", "ready"):
            entry["state"] = "queued"
            entry["job_state"] = "queued"
            entry["started_at"] = None
            if entry.get("quota"):
                entry["quota"]["job_state"] = "queued"
            else:
                entry["quota"] = loading_quota("queued")
            should_submit = True
        else:
            return entry
    if should_submit:
        logging.debug("quota job enqueue tool=%s profile=p%s", tool_key, profile_num)
        future = quota_scheduler().submit(tool_key, profile_num)
        with INTERACTIVE_QUOTA_LOCK:
            current = INTERACTIVE_QUOTA_CACHE.get(quota_cache_key(tool_key, profile_num))
            if current is not None:
                current["future"] = future
            return current
    return quota_cache_entry(tool_key, profile_num)


def status_with_auto_quota(tool_key, profile_num, metadata):
    status = status_payload(tool_key, profile_num, metadata)
    if not interactive_quota_enabled():
        return status
    if not status["has_token"]:
        status["quota"] = {
            "state": "no_token",
            "limits": {},
            "warnings": ["profile has no token"],
        }
        return status
    entry = ensure_quota_loading(tool_key, profile_num)
    status["quota"] = entry["quota"]
    return status


def color_quota_text(text, status):
    quota = status.get("quota") or {}
    state = quota.get("state")
    if state == "loading":
        return f"{CLR_YELLOW}{text}{CLR_RESET}"
    fetched_at = quota.get("fetched_at")
    if fetched_at is None:
        return f"{CLR_RED}{text}{CLR_RESET}" if state not in ("available", "loading") else text
    color = CLR_GREEN if time.time() - fetched_at <= interactive_quota_fresh_seconds() else CLR_WHITE
    return f"{color}{text}{CLR_RESET}"


def quota_text(status, color=True, width=24):
    summary = quota_summary(status)
    if summary == "unknown":
        summary = "retrying"
    text = summary or "quota pending"
    if len(text) > width:
        text = f"{text[:max(0, width - 3)]}..."
    return color_quota_text(text, status) if color else text


def agy_quota_cell_map(status):
    quota = status.get("quota") or {}
    if quota.get("state") != "available":
        return {}
    return dict(agy_quota_entries(quota))


def agy_status_quota_columns(statuses):
    columns = list(AGY_DEFAULT_QUOTA_COLUMNS)
    for status in statuses:
        for label in agy_quota_cell_map(status):
            if label not in columns:
                columns.append(label)
    return columns


def agy_quota_cells(status, columns):
    cells = agy_quota_cell_map(status)
    quota = status.get("quota") or {}
    job_state = quota.get("job_state") or status.get("job_state")
    if cells:
        marker = "~" if job_state in QUOTA_ACTIVE_JOB_STATES else ""
        values = [cells.get(column, "") for column in columns]
        if marker and values:
            for idx, value in enumerate(values):
                if value:
                    values[idx] = f"{value}{marker}"
                    break
        return values
    state = quota.get("state")
    marker = ""
    if state == "no_token":
        marker = ""
    elif job_state in QUOTA_ACTIVE_JOB_STATES or state == "loading":
        marker = "..."
    elif job_state in ("retryable", "failed") or state in (
        "unknown",
        "error",
        "timeout",
        "exception",
        "auth_required",
        "missing_cli",
        "empty_output",
        "parser_miss",
        "process_exit",
    ):
        marker = "!"
    return [marker if idx == 0 else "" for idx, _ in enumerate(columns)]


def agy_quota_fresh(status, now=None):
    quota = status.get("quota") or {}
    fetched_at = quota.get("fetched_at")
    if fetched_at is None:
        return True
    now = time.time() if now is None else now
    return now - fetched_at <= interactive_quota_fresh_seconds()


def quota_cell_percent(cell):
    match = re.search(r"(\d{1,3}(?:\.\d+)?)\s*%", str(cell))
    if not match:
        return None
    return float(match.group(1))


def color_agy_quota_cell(cell, status):
    if not cell:
        return cell
    if cell == "...":
        return f"{CLR_YELLOW}{cell}{CLR_RESET}"
    if cell == "!":
        return f"{CLR_RED}{cell}{CLR_RESET}"
    value = quota_cell_percent(cell)
    if value is None:
        return cell
    if not agy_quota_fresh(status):
        return f"{CLR_WHITE}{cell}{CLR_RESET}"
    if value <= 20:
        color = CLR_RED
    elif value <= 40:
        color = CLR_YELLOW
    else:
        color = CLR_GREEN
    return f"{color}{cell}{CLR_RESET}"


def color_email_parts(value):
    text = str(value)
    match = re.fullmatch(r"([^@\s]+)(@[^@\s]+)", text)
    if not match:
        return text
    local, domain = match.groups()
    pieces = []
    for char in local:
        if char.isalpha():
            pieces.append(f"{CLR_CYAN}{char}{CLR_RESET}")
        elif char.isdigit():
            pieces.append(f"{CLR_YELLOW}{char}{CLR_RESET}")
        else:
            pieces.append(f"{CLR_WHITE}{char}{CLR_RESET}")
    pieces.append(f"{CLR_MAGENTA}{domain}{CLR_RESET}")
    return "".join(pieces)


def invalidate_quota_cache(tool_key=None, profile_num=None):
    with INTERACTIVE_QUOTA_LOCK:
        if tool_key is None:
            INTERACTIVE_QUOTA_CACHE.clear()
            close_args = [(None, None)]
        elif profile_num is None:
            close_args = [(tool_key, None)]
            for key in list(INTERACTIVE_QUOTA_CACHE):
                if key[0] == tool_key:
                    del INTERACTIVE_QUOTA_CACHE[key]
        else:
            INTERACTIVE_QUOTA_CACHE.pop(quota_cache_key(tool_key, profile_num), None)
            close_args = [(tool_key, profile_home(tool_key, profile_num))]
    for close_tool, close_home in close_args:
        close_persistent_quota_sessions(close_tool, close_home)


def force_quota_refresh(tool_key=None):
    submissions = []
    with INTERACTIVE_QUOTA_LOCK:
        for key, entry in list(INTERACTIVE_QUOTA_CACHE.items()):
            entry_tool, profile_num = key
            if tool_key is not None and entry_tool != tool_key:
                continue
            if entry.get("job_state") in QUOTA_ACTIVE_JOB_STATES:
                continue
            entry["state"] = "queued"
            entry["job_state"] = "queued"
            entry["started_at"] = None
            entry["next_retry_at"] = None
            quota = entry.get("quota") or {}
            if quota:
                quota["job_state"] = "queued"
                entry["quota"] = quota
            else:
                entry["quota"] = loading_quota("queued")
            submissions.append((entry_tool, profile_num))
    for entry_tool, profile_num in submissions:
        future = quota_scheduler().submit(entry_tool, profile_num)
        with INTERACTIVE_QUOTA_LOCK:
            entry = INTERACTIVE_QUOTA_CACHE.get(quota_cache_key(entry_tool, profile_num))
            if entry is not None:
                entry["future"] = future
    return len(submissions)


def any_quota_loading(tool_key=None):
    with INTERACTIVE_QUOTA_LOCK:
        for (entry_tool, _), entry in INTERACTIVE_QUOTA_CACHE.items():
            if tool_key is not None and entry_tool != tool_key:
                continue
            if entry.get("job_state") in QUOTA_ACTIVE_JOB_STATES:
                return True
    return False


def next_quota_wake_timeout(tool_key=None, now=None, active_timeout=0.5, max_retry_timeout=0.5):
    now = time.time() if now is None else now
    next_retry_at = None
    next_refresh_at = None
    with INTERACTIVE_QUOTA_LOCK:
        for (entry_tool, _), entry in INTERACTIVE_QUOTA_CACHE.items():
            if tool_key is not None and entry_tool != tool_key:
                continue
            if entry.get("job_state") in QUOTA_ACTIVE_JOB_STATES:
                return active_timeout
            fetched_at = entry.get("fetched_at")
            quota = entry.get("quota") or {}
            if fetched_at is not None and quota.get("state") == "available":
                refresh_at = fetched_at + interactive_quota_fresh_seconds()
                if next_refresh_at is None or refresh_at < next_refresh_at:
                    next_refresh_at = refresh_at
            retry_at = entry.get("next_retry_at")
            if retry_at is None:
                continue
            if entry.get("state") != "retryable" and entry.get("job_state") != "retryable":
                continue
            if next_retry_at is None or retry_at < next_retry_at:
                next_retry_at = retry_at
    candidates = [value for value in (next_retry_at, next_refresh_at) if value is not None]
    if not candidates:
        return None
    next_wake_at = min(candidates)
    return max(0.0, min(max_retry_timeout, next_wake_at - now))


def format_countdown(seconds):
    seconds = max(0, int(seconds + 0.999))
    minutes, secs = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h{minutes:02d}m"
    if minutes:
        return f"{minutes}m{secs:02d}s"
    return f"{secs}s"


def quota_refresh_countdown(tool_key=None, now=None):
    now = time.time() if now is None else now
    next_refresh_at = None
    with INTERACTIVE_QUOTA_LOCK:
        for (entry_tool, _), entry in INTERACTIVE_QUOTA_CACHE.items():
            if tool_key is not None and entry_tool != tool_key:
                continue
            if entry.get("job_state") in QUOTA_ACTIVE_JOB_STATES:
                return "updating now"
            fetched_at = entry.get("fetched_at")
            quota = entry.get("quota") or {}
            if fetched_at is None or quota.get("state") != "available":
                continue
            refresh_at = fetched_at + interactive_quota_fresh_seconds()
            if next_refresh_at is None or refresh_at < next_refresh_at:
                next_refresh_at = refresh_at
    if next_refresh_at is None:
        return "pending"
    remaining = next_refresh_at - now
    if remaining <= 0:
        return "now"
    return format_countdown(remaining)


def quota_runtime_snapshot(tool_key=None):
    now = time.time()
    with INTERACTIVE_QUOTA_LOCK:
        cache_entries = []
        for (entry_tool, profile_num), entry in sorted(INTERACTIVE_QUOTA_CACHE.items()):
            if tool_key is not None and entry_tool != tool_key:
                continue
            quota = entry.get("quota") or {}
            cache_entries.append({
                "tool": entry_tool,
                "profile": f"p{profile_num}",
                "state": entry.get("state"),
                "job_state": entry.get("job_state"),
                "quota_state": quota.get("state"),
                "has_limits": bool(quota.get("limits")),
                "fetched_age_seconds": None if entry.get("fetched_at") is None else round(now - entry["fetched_at"], 3),
                "started_age_seconds": None if entry.get("started_at") is None else round(now - entry["started_at"], 3),
                "attempts": entry.get("attempts", 0),
                "next_retry_in_seconds": None if entry.get("next_retry_at") is None else max(0.0, round(entry["next_retry_at"] - now, 3)),
                "last_error": entry.get("last_error"),
            })
        scheduler = INTERACTIVE_QUOTA_SCHEDULER
        scheduler_payload = None
        if scheduler is not None:
            scheduler_payload = {
                "agy_concurrency": scheduler.agy_concurrency,
                "worker_count": len(scheduler.workers),
                "queue_size": scheduler.queue.qsize(),
                "closed": scheduler.closed,
            }
    return {
        "enabled": interactive_quota_enabled(),
        "next_wake_timeout": next_quota_wake_timeout(tool_key),
        "active_jobs": any_quota_loading(tool_key),
        "scheduler": scheduler_payload,
        "cache": cache_entries,
    }


def read_key_byte(fd=None, timeout=None):
    fd = sys.stdin.fileno() if fd is None else fd
    if timeout is not None:
        ready, _, _ = select.select([fd], [], [], timeout)
        if not ready:
            return None
    first = os.read(fd, 1)
    if not first:
        return None
    first_byte = first[0]
    if first_byte < 0x80:
        return first.decode(errors="ignore")
    if 0xC0 <= first_byte < 0xE0:
        remaining = 1
    elif 0xE0 <= first_byte < 0xF0:
        remaining = 2
    elif 0xF0 <= first_byte < 0xF8:
        remaining = 3
    else:
        return first.decode(errors="ignore")
    data = bytearray(first)
    deadline = time.monotonic() + 0.05
    while remaining > 0 and time.monotonic() < deadline:
        ready, _, _ = select.select([fd], [], [], max(0.0, deadline - time.monotonic()))
        if not ready:
            break
        data.extend(os.read(fd, 1))
        remaining -= 1
    return bytes(data).decode(errors="ignore")


def key_from_escape_sequence(fd):
    sequence = ""
    deadline = time.monotonic() + 0.5
    while time.monotonic() < deadline:
        ch = read_key_byte(fd, max(0.0, deadline - time.monotonic()))
        if ch is None:
            return None
        sequence += ch
        if ch.isalpha() or ch == "~":
            break

    final = sequence[-1:] if sequence else ""
    if final == 'A':
        return 'up'
    if final == 'B':
        return 'down'
    if final == 'C':
        return 'right'
    if final == 'D':
        return 'left'
    return 'esc'


def get_key(timeout=None):
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = read_key_byte(fd, timeout)
        if ch is None:
            return None
        if ch == '\x1b':
            ch2 = read_key_byte(fd, 0.5)
            if ch2 is None:
                return 'esc'
            if ch2 in ('[', 'O'):
                key = key_from_escape_sequence(fd)
                return key or 'esc'
            return 'esc'
        elif ch in ('\n', '\r'):
            return 'enter'
        elif ch == '\x03': # Ctrl+C
            return 'ctrl+c'
        elif ch == '\x12': # Ctrl+R
            return 'ctrl+r'
        else:
            return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def render_status_screen(tool_key, status_message=None):
    clear_screen()
    tool_name = TOOLS[tool_key]["name"]
    print_header(f"STATUS: {tool_name.upper()}")
    print()

    metadata = load_metadata()
    profiles = get_display_profiles(tool_key)
    statuses = [status_with_auto_quota(tool_key, n, metadata) for n in profiles]

    if tool_key == "agy":
        quota_columns = agy_status_quota_columns(statuses)
        widths = {
            "profile": 8,
            "account": 38,
            "status": 10,
            "quota": 5,
            "label": 14,
        }
        quota_header = " ".join(f"{column:<{widths['quota']}}" for column in quota_columns)
        total_width = widths["profile"] + widths["account"] + widths["status"] + widths["label"]
        total_width += (widths["quota"] * len(quota_columns)) + len(quota_columns) + 3
    else:
        quota_columns = []
        widths = {
            "profile": 8,
            "account": 32,
            "status": 10,
            "quota": 52,
            "label": 14,
        }
        quota_header = f"{'Quota':<{widths['quota']}}"
        total_width = sum(widths.values()) + len(widths) - 1
    print(
        f"{CLR_BOLD}{CLR_WHITE}"
        f"{'Profile':<{widths['profile']}} "
        f"{'Active Account / Tier':<{widths['account']}} "
        f"{'Status':<{widths['status']}} "
        f"{quota_header} "
        f"{'Label':<{widths['label']}}"
        f"{CLR_RESET}"
    )
    print("-" * total_width)

    for status in statuses:
        stat_str = f"{CLR_GREEN}Active{CLR_RESET}" if status["has_token"] else f"{CLR_RED}No Token{CLR_RESET}"
        lbl_str = f"({status['label']})" if status["label"] else ""
        email_color = CLR_CYAN if status["has_token"] else CLR_RESET
        profile = f"p{status['num']}"
        display_email = status["email"]
        quota_account = (status.get("quota") or {}).get("account")
        if quota_account and (tool_key == "agy" or display_email in ("logged in", "(no login)")):
            display_email = quota_account
        email = color_email_parts(display_email) if status["has_token"] else f"{email_color}{display_email}{CLR_RESET}"
        label = f"{CLR_YELLOW}{lbl_str}{CLR_RESET}" if lbl_str else ""
        if tool_key == "agy":
            quota = " ".join(
                visible_fit(color_agy_quota_cell(cell, status), widths["quota"])
                for cell in agy_quota_cells(status, quota_columns)
            )
        else:
            quota = visible_fit(quota_text(status, width=widths["quota"]), widths["quota"])
        print(
            f"{visible_fit(profile, widths['profile'])} "
            f"{visible_fit(email, widths['account'])} "
            f"{visible_fit(stat_str, widths['status'])} "
            f"{quota} "
            f"{visible_fit(label, widths['label'])}"
        )
    print()
    if status_message:
        print(f"{CLR_YELLOW}{status_message}{CLR_RESET}")
    print(
        f"Next auto refresh: {CLR_CYAN}{quota_refresh_countdown(tool_key)}{CLR_RESET}. "
        "Press Enter/q to return, r to refresh quota now..."
    )


def view_status(tool_key):
    status_message = None
    while True:
        render_status_screen(tool_key, status_message)
        status_message = None
        key = get_key(timeout=next_quota_wake_timeout(tool_key))
        if key is None:
            continue
        if key in ("enter", "esc", "q"):
            return
        elif key in ("r", "R", "ctrl+r", "к", "К"):
            count = force_quota_refresh(tool_key)
            if count:
                status_message = f"Refreshing quota now for {count} profiles..."
            else:
                status_message = "Quota refresh is already running..."
            continue
        elif key == "ctrl+c":
            sys.exit(0)


def clear_screen():
    sys.stdout.write("\033[H\033[J")
    sys.stdout.flush()


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

def launch_account(tool_key):
    tool = TOOLS[tool_key]
    metadata = load_metadata()
    while True:
        profiles = get_display_profiles(tool_key)
        options = []
        for n in profiles:
            status = status_with_auto_quota(tool_key, n, metadata)
            lbl = f" ({status['label']})" if status['label'] else ""
            tok = f"{CLR_GREEN}[Active]{CLR_RESET}" if status['has_token'] else f"{CLR_RED}[No Token]{CLR_RESET}"
            quota = quota_text(status)
            options.append(f"p{status['num']:<3} | {status['email']:<28} {tok} {quota:<24}{CLR_YELLOW}{lbl}{CLR_RESET}")

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
        invalidate_quota_cache(tool_key, profile_num)
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
    invalidate_quota_cache(tool_key, next_p)
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
            status = status_with_auto_quota(tool_key, n, metadata)
            lbl = f" ({status['label']})" if status['label'] else " (no label)"
            quota = quota_text(status)
            options.append(f"p{status['num']:<3} | {status['email']:<28} {quota:<24} {CLR_YELLOW}{lbl}{CLR_RESET}")

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
    return core_find_windows_user()

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
        invalidate_quota_cache(tool_key, next_p)
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
            status = status_with_auto_quota(tool_key, n, metadata)
            if status['has_token']:
                lbl = f" ({status['label']})" if status['label'] else ""
                quota = quota_text(status)
                options.append(f"p{status['num']:<3} | {status['email']:<28} {CLR_GREEN}[Active]{CLR_RESET} {quota:<24}{CLR_YELLOW}{lbl}{CLR_RESET}")
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
            status = status_with_auto_quota(tool_key, n, metadata)
            lbl = f" ({status['label']})" if status['label'] else ""
            tok = f"{CLR_GREEN}[Active]{CLR_RESET}" if status['has_token'] else f"{CLR_RED}[No Token]{CLR_RESET}"
            quota = quota_text(status)
            options.append(f"p{status['num']:<3} | {status['email']:<28} {tok} {quota:<24}{CLR_YELLOW}{lbl}{CLR_RESET}")

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
                invalidate_quota_cache(tool_key, profile_num)
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
        invalidate_quota_cache(tool_key, next_p)
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
    invalidate_quota_cache()
    print(
        f"{CLR_GREEN}Updated {result['copied']} files, skipped {result['skipped']}, "
        f"converted {result['converted']} agy credentials, invalid {result['invalid']}.{CLR_RESET}"
    )
    print(f"\n{CLR_CYAN}Sync Complete!{CLR_RESET}")
    input("\nPress Enter to return...")


def run_interactive_main():
    while True:
        options = [
            "[1] Antigravity CLI (agy)",
            "[2] OpenAI Codex CLI",
            "[3] Anthropic Claude CLI",
            "[4] Sync Profiles (WSL <-> Windows)",
            "[x] Exit",
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
