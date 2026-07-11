import glob
import logging
import os
import queue
import re
import select
import signal
import sys
import termios
import threading
import time
import tty
from concurrent.futures import Future
from itertools import count

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
    agy_quota_entries,
    run_cli_tool,
    quota_summary,
)
from .operations import (
    TOOLS,
    credential_path,
    clear_profile_data,
    default_export_dir,
    export_credential_file,
    find_windows_user as core_find_windows_user,
    first_free_profile,
    get_display_profiles,
    get_occupied_profiles as get_profiles,
    import_credential_file,
    label_profile,
    load_metadata,
    normalize_credential_path,
    parse_profile,
    profile_home,
    quota_payload,
    resolve_sync_bases,
    status_payload,
    sync_profiles_noninteractive,
)
from .metadata import save_metadata
from .quota import close_persistent_quota_sessions
from .terminal_rendering import (
    ANSI_RE,
    TerminalFrameRenderer,
    terminal_size,
    visible_fit,
    visible_len,
    visible_ljust,
)


def _audit():
    from . import audit

    return audit

def _safety():
    from . import safety

    return safety


def configure_interactive_logging():
    if logging.getLogger().handlers:
        return
    log_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ai-man.log")
    logging.basicConfig(
        filename=log_file,
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def safety_decision(operation, command=None, tool=None, profile=None, target=None, facts=None, yes=False, dry_run=False):
    descriptor = _safety().operation_descriptor(
        operation,
        command=command,
        tool=tool,
        profile=profile,
        target=target,
        facts=facts,
    )
    decision = _safety().evaluate(descriptor, yes=yes, dry_run=dry_run)
    _safety().audit_decision(_audit(), decision)
    return decision

AGY_DEFAULT_QUOTA_COLUMNS = ["FM", "FH", "FL", "PL", "PH", "CS", "CO", "GPT"]
AGY_QUOTA_COLUMN_GROUPS = (
    ("Flash", ("FM", "FH", "FL")),
    ("Pro", ("PL", "PH")),
    ("Claude", ("CS", "CO")),
    ("GPT", ("GPT",)),
)
SETTINGS_METADATA_KEY = "_settings"
QUOTA_REFRESH_SETTING_KEY = "quota_refresh_seconds"
DEVELOPER_MODE_SETTING_KEY = "developer_mode"
INTERACTIVE_QUOTA_CACHE = {}
INTERACTIVE_QUOTA_LOCK = threading.Lock()
INTERACTIVE_QUOTA_RENDER_GENERATION = 0
INTERACTIVE_SETTINGS_CACHE = None
LOG_TAIL_CACHE = {}
LOG_TAIL_MAX_BYTES = 256 * 1024
LOG_TAIL_MAX_LINES = 400
LOG_TAIL_PATTERN = re.compile(r"\b(error|fail|failed|timeout|exception|resource_exhausted|account_ineligible|missing_cli|quota|agy\d*)\b", re.I)
QUOTA_FRESH_SECONDS = 300
QUOTA_STALE_SECONDS = 3600
QUOTA_RETRY_BACKOFF_SECONDS = (10, 30, 60)
QUOTA_ACTIVE_JOB_STATES = ("queued", "running")
QUOTA_TERMINAL_FAILURE_STATES = {
    "account_ineligible",
    "auth_required",
    "missing_cli",
    "resource_exhausted",
    "timeout",
    "unsupported",
}
QUOTA_PROGRESS_SPINNER = "|/-\\"
QUOTA_PIPELINE_STATES = (
    "empty",
    "queued",
    "running",
    "available",
    "stale_refreshing",
    "retry_wait",
    "failed",
    "auth_required",
    "disabled",
)
QUOTA_FAILURE_STATES = (
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
)
QUOTA_LEGAL_TRANSITIONS = {
    None: {"empty", "queued", "disabled"},
    "empty": {"queued", "disabled"},
    "queued": {"running", "available", "retry_wait", "failed", "auth_required", "disabled"},
    "running": {"available", "retry_wait", "failed", "auth_required", "disabled"},
    "available": {"queued", "stale_refreshing", "disabled"},
    "stale_refreshing": {"available", "retry_wait", "failed", "auth_required", "disabled"},
    "retry_wait": {"queued", "stale_refreshing", "disabled"},
    "failed": {"queued", "disabled"},
    "auth_required": {"queued", "disabled"},
    "disabled": {"queued"},
}
INTERACTIVE_QUOTA_SCHEDULER = None
INTERACTIVE_QUOTA_SCHEDULER_LOCK = threading.Lock()
INTERACTIVE_SHUTTING_DOWN = False
STATUS_RENDERER = TerminalFrameRenderer(cache_key="status")
STATUS_SCREEN_RENDER_CACHE = {}
STATUS_ROW_RENDER_CACHE = {}
STATUS_QUOTA_CELL_RENDER_CACHE = {}
STATUS_RENDER_CACHE_LIMIT = 512


def bump_status_render_generation():
    global INTERACTIVE_QUOTA_RENDER_GENERATION
    INTERACTIVE_QUOTA_RENDER_GENERATION += 1


def interactive_quota_enabled():
    return os.environ.get("AI_MAN_INTERACTIVE_QUOTA", "1").lower() not in ("0", "false", "no", "off")


def interactive_quota_timeout(tool_key=None):
    if tool_key == "agy":
        raw = os.environ.get("AI_MAN_INTERACTIVE_AGY_QUOTA_TIMEOUT", os.environ.get("AI_MAN_INTERACTIVE_QUOTA_TIMEOUT", "120"))
        fallback = 120.0
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
    raw = os.environ.get("AI_MAN_INTERACTIVE_QUOTA_FRESH_SECONDS")
    if raw is None:
        raw = load_interactive_setting(QUOTA_REFRESH_SETTING_KEY, "600")
    try:
        return max(1.0, float(raw))
    except ValueError:
        return 600.0


def interactive_developer_mode_enabled():
    raw = os.environ.get("AI_MAN_DEVELOPER_MODE")
    if raw is None:
        raw = load_interactive_setting(DEVELOPER_MODE_SETTING_KEY, False)
    return str(raw).strip().lower() in ("1", "true", "yes", "on", "enabled")


def load_interactive_settings():
    global INTERACTIVE_SETTINGS_CACHE
    if INTERACTIVE_SETTINGS_CACHE is None:
        metadata = load_metadata()
        settings = metadata.get(SETTINGS_METADATA_KEY, {})
        INTERACTIVE_SETTINGS_CACHE = settings if isinstance(settings, dict) else {}
    return dict(INTERACTIVE_SETTINGS_CACHE)


def load_interactive_setting(key, default=None):
    return load_interactive_settings().get(key, default)


def save_interactive_setting(key, value):
    global INTERACTIVE_SETTINGS_CACHE
    metadata = load_metadata()
    settings = metadata.setdefault(SETTINGS_METADATA_KEY, {})
    if not isinstance(settings, dict):
        settings = {}
        metadata[SETTINGS_METADATA_KEY] = settings
    settings[key] = value
    save_metadata(metadata)
    INTERACTIVE_SETTINGS_CACHE = dict(settings)


def interactive_log_path():
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "ai-man.log")


def log_file_fingerprint(path=None):
    path = interactive_log_path() if path is None else path
    try:
        stat = os.stat(path)
    except OSError:
        return None
    return (
        getattr(stat, "st_dev", None),
        getattr(stat, "st_ino", None),
        stat.st_mtime_ns,
        stat.st_size,
    )


def reset_live_log_cache(path=None):
    if path is None:
        LOG_TAIL_CACHE.clear()
    else:
        LOG_TAIL_CACHE.pop(str(path), None)


def _read_log_tail(path, size):
    with open(path, "rb") as fh:
        if size > LOG_TAIL_MAX_BYTES:
            fh.seek(max(0, size - LOG_TAIL_MAX_BYTES))
        data = fh.read(LOG_TAIL_MAX_BYTES)
    text = data.decode("utf-8", errors="replace")
    return text.splitlines()[-LOG_TAIL_MAX_LINES:]


def _selected_log_lines(lines, width):
    selected = []
    for line in lines:
        cleaned = line.strip()
        if cleaned and LOG_TAIL_PATTERN.search(cleaned):
            selected.append(visible_fit(cleaned, width))
    return selected


def live_log_lines(limit=8, width=118):
    path = interactive_log_path()
    fingerprint = log_file_fingerprint(path)
    if fingerprint is None:
        reset_live_log_cache(path)
        return [f"log file not found: {path}"]
    dev, inode, _mtime_ns, size = fingerprint
    cache = LOG_TAIL_CACHE.get(path)
    if (
        cache is None
        or cache.get("dev") != dev
        or cache.get("inode") != inode
        or size < cache.get("offset", 0)
    ):
        lines = _read_log_tail(path, size)
        selected = _selected_log_lines(lines, width)[-LOG_TAIL_MAX_LINES:]
        LOG_TAIL_CACHE[path] = {
            "dev": dev,
            "inode": inode,
            "offset": size,
            "partial": "",
            "selected": selected,
        }
        return selected[-limit:]
    if size == cache.get("offset"):
        return list(cache.get("selected", [])[-limit:])

    try:
        with open(path, "rb") as fh:
            fh.seek(cache.get("offset", 0))
            data = fh.read(max(0, size - cache.get("offset", 0)))
    except OSError:
        reset_live_log_cache(path)
        return [f"log file not found: {path}"]

    text = cache.get("partial", "") + data.decode("utf-8", errors="replace")
    if text.endswith(("\n", "\r")):
        lines = text.splitlines()
        partial = ""
    else:
        parts = text.splitlines()
        lines = parts[:-1]
        partial = parts[-1] if parts else text
    selected = list(cache.get("selected", []))
    selected.extend(_selected_log_lines(lines, width))
    cache.update({
        "offset": size,
        "partial": partial,
        "selected": selected[-LOG_TAIL_MAX_LINES:],
    })
    return selected[-limit:]


class InteractiveQuotaScheduler:
    def __init__(self, agy_concurrency=None):
        self.agy_concurrency = agy_concurrency or interactive_agy_quota_concurrency()
        self.queue = queue.PriorityQueue()
        self.closed = False
        self.workers = []
        self.sequence = count()
        self.metrics_lock = threading.Lock()
        self.metrics = {
            "submitted": 0,
            "queued": 0,
            "coalesced": 0,
            "started": 0,
            "completed": 0,
            "failed": 0,
            "cancelled": 0,
        }
        for idx in range(self.agy_concurrency):
            worker = threading.Thread(
                target=self._worker,
                name=f"ai-man-quota-{idx + 1}",
                daemon=True,
            )
            worker.start()
            self.workers.append(worker)

    def increment_metric(self, name, amount=1):
        with self.metrics_lock:
            self.metrics[name] = self.metrics.get(name, 0) + amount

    def metrics_snapshot(self):
        with self.metrics_lock:
            return dict(self.metrics)

    def submit(self, tool_key, profile_num, priority=10):
        future = Future()
        if self.closed:
            future.cancel()
            return future
        self.increment_metric("submitted")
        self.increment_metric("queued")
        self.queue.put((priority, next(self.sequence), tool_key, profile_num, future, time.time()))
        return future

    def _worker(self):
        while True:
            item = self.queue.get()
            _priority, _seq, tool_key, profile_num, future, _submitted_at = item
            if future is None:
                self.queue.task_done()
                return
            try:
                if future.set_running_or_notify_cancel():
                    self.increment_metric("started")
                    load_quota_background(tool_key, profile_num)
                    future.set_result(True)
                    self.increment_metric("completed")
                else:
                    self.increment_metric("cancelled")
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
                self.increment_metric("failed")
                future.set_exception(e)
            finally:
                self.queue.task_done()

    def shutdown(self, wait=False, timeout=2.0):
        if self.closed:
            return
        self.closed = True
        while True:
            try:
                _priority, _seq, _tool_key, _profile_num, future, _submitted_at = self.queue.get_nowait()
            except queue.Empty:
                break
            try:
                if future is not None:
                    future.cancel()
                    self.increment_metric("cancelled")
            finally:
                self.queue.task_done()
        for _ in self.workers:
            self.queue.put((9999, next(self.sequence), None, None, None, time.time()))
        if wait:
            self.wait(timeout)

    def wait(self, timeout=2.0):
        deadline = time.monotonic() + timeout
        for worker in self.workers:
            remaining = max(0.0, deadline - time.monotonic())
            worker.join(remaining)


def quota_scheduler():
    global INTERACTIVE_QUOTA_SCHEDULER
    if INTERACTIVE_SHUTTING_DOWN:
        raise RuntimeError("interactive runtime is shutting down")
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


def shutdown_interactive_runtime(wait=False):
    global INTERACTIVE_QUOTA_SCHEDULER, INTERACTIVE_SHUTTING_DOWN
    INTERACTIVE_SHUTTING_DOWN = True
    with INTERACTIVE_QUOTA_SCHEDULER_LOCK:
        scheduler = INTERACTIVE_QUOTA_SCHEDULER
        INTERACTIVE_QUOTA_SCHEDULER = None
    if scheduler is not None:
        scheduler.shutdown(wait=False)
    close_persistent_quota_sessions()
    if scheduler is not None and wait:
        scheduler.wait(2.0)


def install_interactive_signal_handlers():
    previous_handlers = {}

    def handle_signal(signum, frame):
        shutdown_interactive_runtime(wait=True)
        raise SystemExit(128 + signum)

    for signum in (signal.SIGINT, signal.SIGTERM):
        previous_handlers[signum] = signal.getsignal(signum)
        signal.signal(signum, handle_signal)
    return previous_handlers


def restore_interactive_signal_handlers(previous_handlers):
    for signum, handler in previous_handlers.items():
        signal.signal(signum, handler)


def record_quota_job_coalesced():
    scheduler = INTERACTIVE_QUOTA_SCHEDULER
    if scheduler is not None:
        scheduler.increment_metric("coalesced")


def quota_cache_key(tool_key, profile_num):
    return (tool_key, profile_num)


def validate_quota_transition(previous_state, next_state):
    if next_state not in QUOTA_PIPELINE_STATES:
        raise ValueError(f"unknown quota pipeline state: {next_state}")
    allowed = QUOTA_LEGAL_TRANSITIONS.get(previous_state)
    if allowed is None or next_state not in allowed:
        raise ValueError(f"illegal quota pipeline transition: {previous_state} -> {next_state}")
    return True


def transition_quota_entry(entry, next_state, tool_key=None, profile_num=None, reason=None, now=None):
    previous = entry.get("machine_state")
    validate_quota_transition(previous, next_state)
    entry["machine_state"] = next_state
    entry["state_machine"] = {
        "state": next_state,
        "previous_state": previous,
        "reason": reason,
        "transitioned_at": time.time() if now is None else now,
    }
    quota = entry.get("quota")
    if isinstance(quota, dict):
        quota["pipeline_state"] = next_state
    if tool_key is not None and profile_num is not None:
        _audit().record(
            "quota",
            "transitioned",
            tool=tool_key,
            profile=f"p{profile_num}",
            result=next_state,
            details={"from": previous, "to": next_state, "reason": reason},
        )
    return entry


def quota_entry_machine_state(entry):
    state = entry.get("machine_state")
    if state:
        return state
    legacy = entry.get("state")
    job_state = entry.get("job_state")
    quota = entry.get("quota") or {}
    quota_state = quota.get("state")
    if legacy == "ready" and quota_state == "available":
        return "available"
    if legacy == "queued" and quota_state == "available":
        return "stale_refreshing"
    if job_state == "queued":
        return "queued"
    if job_state == "running":
        return "running"
    if legacy == "retryable":
        return "auth_required" if quota_state == "auth_required" else "retry_wait"
    if legacy == "failed":
        return "failed"
    return "empty"


def quota_cache_entry(tool_key, profile_num):
    with INTERACTIVE_QUOTA_LOCK:
        return INTERACTIVE_QUOTA_CACHE.get(quota_cache_key(tool_key, profile_num))


def store_quota_cache(tool_key, profile_num, entry):
    with INTERACTIVE_QUOTA_LOCK:
        entry.setdefault("machine_state", quota_entry_machine_state(entry))
        INTERACTIVE_QUOTA_CACHE[quota_cache_key(tool_key, profile_num)] = entry
    bump_status_render_generation()


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


def terminal_quota_failure_state(state):
    return state in QUOTA_TERMINAL_FAILURE_STATES


def loading_quota(job_state="queued"):
    return {
        "state": "loading",
        "job_state": job_state,
        "pipeline_state": job_state,
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
            quota["pipeline_state"] = "available"
            entry = {
                "state": "ready",
                "job_state": "ready",
                "machine_state": current.get("machine_state", "running"),
                "quota": quota,
                "fetched_at": now,
                "started_at": current.get("started_at"),
                "attempts": 0,
                "last_error": None,
                "next_retry_at": None,
            }
            transition_quota_entry(entry, "available", tool_key, profile_num, "probe_succeeded", now)
        else:
            last_error = {
                "state": state,
                "message": diagnostic_text(quota),
                "warnings": list(quota.get("warnings") or []),
            }
            terminal_failure = terminal_quota_failure_state(state) and not had_previous
            delay = None if terminal_failure else retry_delay_for_attempts(attempts)
            machine_state = "auth_required" if state == "auth_required" else ("failed" if terminal_failure else "retry_wait")
            job_state = "failed" if terminal_failure else "retryable"
            if had_previous:
                preserved = dict(previous_quota)
                preserved["job_state"] = job_state
                preserved["pipeline_state"] = machine_state
                preserved["last_error"] = last_error
                preserved["warnings"] = list(previous_quota.get("warnings") or [])
                if last_error["message"] and last_error["message"] not in preserved["warnings"]:
                    preserved["warnings"].append(last_error["message"])
                entry_quota = preserved
            else:
                quota["job_state"] = job_state
                quota["pipeline_state"] = machine_state
                entry_quota = quota
            entry = {
                "state": job_state,
                "job_state": job_state,
                "machine_state": current.get("machine_state", "running"),
                "quota": entry_quota,
                "fetched_at": current.get("fetched_at"),
                "started_at": current.get("started_at"),
                "attempts": attempts,
                "last_error": last_error,
                "next_retry_at": None if delay is None else now + delay,
            }
            transition_quota_entry(entry, machine_state, tool_key, profile_num, state, now)
        INTERACTIVE_QUOTA_CACHE[key] = entry
    bump_status_render_generation()
    details = {
        "state": state,
        "attempts": entry.get("attempts"),
        "had_previous_available": had_previous,
        "machine_state": entry.get("machine_state"),
        "job_state": entry.get("job_state"),
        "fetched_at": entry.get("fetched_at"),
        "next_retry_at": entry.get("next_retry_at"),
        "limits": list((entry.get("quota") or {}).get("limits", {})),
        "warnings": list(quota.get("warnings") or []),
        "diagnostic_summary": quota.get("diagnostic_summary"),
    }
    _audit().record(
        "quota",
        "refresh_finished",
        tool=tool_key,
        profile=f"p{profile_num}",
        result=state,
        details=details,
    )
    logging.info(
        "quota refresh finished tool=%s profile=p%s state=%s machine=%s attempts=%s warnings=%s diagnostic=%s",
        tool_key,
        profile_num,
        state,
        entry.get("machine_state"),
        entry.get("attempts"),
        details["warnings"],
        details["diagnostic_summary"],
    )
    return entry


def load_quota_background(tool_key, profile_num):
    now = time.time()
    with INTERACTIVE_QUOTA_LOCK:
        entry = INTERACTIVE_QUOTA_CACHE.get(quota_cache_key(tool_key, profile_num))
        if entry is not None:
            if entry.get("machine_state") not in ("running", "stale_refreshing"):
                transition_quota_entry(entry, "running", tool_key, profile_num, "worker_started", now)
            entry["state"] = "running"
            entry["job_state"] = "running"
            entry["started_at"] = now
            if (entry.get("quota") or {}).get("state") == "loading":
                entry["quota"]["job_state"] = "running"
                entry["quota"]["pipeline_state"] = "running"
    bump_status_render_generation()
    _audit().record(
        "quota",
        "refresh_started",
        tool=tool_key,
        profile=f"p{profile_num}",
        details={"timeout_seconds": interactive_quota_timeout(tool_key)},
    )
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
                "machine_state": "empty",
                "quota": loading_quota("queued"),
                "fetched_at": None,
                "started_at": None,
                "attempts": 0,
                "last_error": None,
                "next_retry_at": None,
            }
            transition_quota_entry(entry, "queued", tool_key, profile_num, "cache_miss", now)
            INTERACTIVE_QUOTA_CACHE[key] = entry
            should_submit = True
            bump_status_render_generation()
        elif entry.get("job_state") in QUOTA_ACTIVE_JOB_STATES:
            record_quota_job_coalesced()
            return entry
        elif quota_entry_fresh(entry, now):
            entry["state"] = "ready"
            entry["job_state"] = "ready"
            entry["quota"]["job_state"] = "ready"
            entry["machine_state"] = "available"
            entry["quota"]["pipeline_state"] = "available"
            return entry
        elif entry.get("state") == "retryable" and not retry_allowed(entry, now):
            return entry
        elif quota_entry_stale_usable(entry, now) or entry.get("state") in ("retryable", "failed", "ready"):
            previous_machine = quota_entry_machine_state(entry)
            entry["state"] = "queued"
            entry["job_state"] = "queued"
            entry["started_at"] = None
            if entry.get("quota"):
                entry["quota"]["job_state"] = "queued"
            else:
                entry["quota"] = loading_quota("queued")
            target_state = "stale_refreshing" if quota_entry_stale_usable(entry, now) else "queued"
            if previous_machine != target_state:
                transition_quota_entry(entry, target_state, tool_key, profile_num, "refresh_due", now)
            should_submit = True
            bump_status_render_generation()
        else:
            return entry
    if should_submit:
        logging.debug("quota job enqueue tool=%s profile=p%s", tool_key, profile_num)
        _audit().record(
            "quota",
            "refresh_queued",
            tool=tool_key,
            profile=f"p{profile_num}",
            details={"reason": "ensure_quota_loading", "priority": 10},
        )
        future = quota_scheduler().submit(tool_key, profile_num, priority=10)
        with INTERACTIVE_QUOTA_LOCK:
            current = INTERACTIVE_QUOTA_CACHE.get(quota_cache_key(tool_key, profile_num))
            if current is not None:
                current["future"] = future
            return current
    return quota_cache_entry(tool_key, profile_num)


def status_with_auto_quota(tool_key, profile_num, metadata):
    status = status_payload(tool_key, profile_num, metadata)
    return status_with_auto_quota_snapshot(tool_key, status)


def status_with_auto_quota_snapshot(tool_key, status):
    status = dict(status)
    if not interactive_quota_enabled():
        return status
    if not status["has_token"]:
        status["quota"] = {
            "state": "no_token",
            "pipeline_state": "disabled",
            "limits": {},
            "warnings": ["profile has no token"],
        }
        return status
    entry = ensure_quota_loading(tool_key, status["num"])
    status["quota"] = entry["quota"]
    return status


def collect_status_snapshot(tool_key):
    metadata = load_metadata()
    profiles = get_display_profiles(tool_key)
    return [status_payload(tool_key, n, metadata) for n in profiles]


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


def quota_expired(status, now=None):
    quota = status.get("quota") or {}
    fetched_at = quota.get("fetched_at")
    if fetched_at is None or quota.get("state") != "available":
        return False
    now = time.time() if now is None else now
    return now - fetched_at > interactive_quota_fresh_seconds()


def quota_text(status, color=True, width=24):
    summary = quota_summary(status)
    if summary == "unknown":
        summary = "retrying"
    text = summary or "quota pending"
    if len(text) > width:
        text = f"{text[:max(0, width - 3)]}..."
    return color_quota_text(text, status) if color else text


def bounded_cache_get(cache, key):
    return cache.get(key)


def bounded_cache_set(cache, key, value, limit=STATUS_RENDER_CACHE_LIMIT):
    if len(cache) >= limit:
        cache.clear()
    cache[key] = value
    return value


def freeze_render_value(value):
    if isinstance(value, dict):
        return tuple((key, freeze_render_value(value[key])) for key in sorted(value))
    if isinstance(value, (list, tuple)):
        return tuple(freeze_render_value(item) for item in value)
    if isinstance(value, set):
        return tuple(sorted(freeze_render_value(item) for item in value))
    return value


def quota_progress_snapshot(statuses):
    total = 0
    completed = 0
    queued = 0
    running = 0
    warming = 0
    failed = 0
    pending = 0
    for status in statuses:
        if not status.get("has_token"):
            continue
        total += 1
        quota = status.get("quota") or {}
        state = quota.get("state")
        job_state = quota.get("job_state") or status.get("job_state")
        if job_state == "queued":
            queued += 1
        elif job_state == "running":
            running += 1
        elif state == "available" and quota.get("limits") and job_state in (None, "ready"):
            completed += 1
        elif state == "startup_pending":
            warming += 1
        elif state == "loading":
            queued += 1
        else:
            failed += 1
    pending = max(0, total - completed - queued - running - warming - failed)
    return {
        "total": total,
        "completed": completed,
        "queued": queued,
        "running": running,
        "warming": warming,
        "failed": failed,
        "pending": pending,
        "active": queued + running + warming,
    }


def quota_progress_bar(done, total, width=24):
    if total <= 0:
        filled = 0
    else:
        filled = min(width, max(0, int((done / total) * width)))
    return f"[{'#' * filled}{'-' * (width - filled)}]"


def quota_progress_line(statuses, now=None):
    progress = quota_progress_snapshot(statuses)
    total = progress["total"]
    if total <= 0 or progress["active"] <= 0:
        return None
    now = time.time() if now is None else now
    spinner = QUOTA_PROGRESS_SPINNER[int(now * 4) % len(QUOTA_PROGRESS_SPINNER)]
    done = progress["completed"]
    percent = int((done / total) * 100) if total else 0
    bar = quota_progress_bar(done, total)
    details = (
        f"{done}/{total} {percent}% "
        f"running {progress['running']}, queued {progress['queued']}"
    )
    if progress["warming"]:
        details += f", warming {progress['warming']}"
    if progress["failed"]:
        details += f", failed {progress['failed']}"
    if progress["pending"]:
        details += f", pending {progress['pending']}"
    return f"Quota refresh {spinner} {CLR_CYAN}{bar}{CLR_RESET} {details}"


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
        return [cells.get(column, "") for column in columns]
    state = quota.get("state")
    marker = ""
    if state == "no_token":
        marker = ""
    elif job_state in QUOTA_ACTIVE_JOB_STATES or state in ("loading", "startup_pending"):
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
        "tty_unavailable",
        "account_ineligible",
        "resource_exhausted",
        "pty_failure",
        "resource_limited",
    ):
        marker = "!"
    return [marker if idx == 0 else "" for idx, _ in enumerate(columns)]


def agy_quota_cells_cached(status, columns):
    quota = status.get("quota") or {}
    key = (
        tuple(columns),
        quota.get("state"),
        quota.get("job_state") or status.get("job_state"),
        freeze_render_value(quota.get("limits") or {}),
    )
    cached = bounded_cache_get(STATUS_QUOTA_CELL_RENDER_CACHE, key)
    if cached is not None:
        return cached
    return bounded_cache_set(STATUS_QUOTA_CELL_RENDER_CACHE, key, agy_quota_cells(status, columns))


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


def agy_quota_header_lines(columns, quota_width):
    column_groups = []
    used = set()
    for title, group_columns in AGY_QUOTA_COLUMN_GROUPS:
        present = [column for column in group_columns if column in columns]
        if not present:
            continue
        used.update(present)
        span_width = (quota_width * len(present)) + max(0, len(present) - 1)
        column_groups.append((title, span_width))
    other_columns = [column for column in columns if column not in used]
    if other_columns:
        span_width = (quota_width * len(other_columns)) + max(0, len(other_columns) - 1)
        column_groups.append(("Other", span_width))
    group_header = " ".join(visible_fit(title.center(width), width) for title, width in column_groups)
    column_header = " ".join(visible_fit(column, quota_width) for column in columns)
    return group_header, column_header


def status_has_issue(status):
    email = str(status.get("email") or "")
    token_state = status.get("token_state")
    return (
        not status.get("has_token")
        or token_state in ("invalid", "missing", "error")
        or email.startswith("invalid token:")
    )


def status_profile_text(status):
    profile = f"p{status['num']}"
    if not status_has_issue(status):
        return profile
    return f"{CLR_RED}{profile}!{CLR_RESET}"


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


def status_row_render_key(tool_key, status, quota_columns, widths, now=None):
    quota = status.get("quota") or {}
    now = time.time() if now is None else now
    fetched_at = quota.get("fetched_at")
    fresh = None
    if fetched_at is not None:
        fresh = now - fetched_at <= interactive_quota_fresh_seconds()
    return (
        tool_key,
        tuple(quota_columns),
        tuple(sorted(widths.items())),
        status.get("num"),
        status.get("email"),
        status.get("has_token"),
        status.get("label"),
        status.get("job_state"),
        quota.get("state"),
        quota.get("job_state"),
        quota.get("pipeline_state"),
        quota.get("account"),
        quota.get("fetched_at"),
        fresh,
        freeze_render_value(quota.get("limits") or {}),
        freeze_render_value(quota.get("warnings") or []),
    )


def render_status_row(tool_key, status, quota_columns, widths, now=None):
    key = status_row_render_key(tool_key, status, quota_columns, widths, now)
    cached = bounded_cache_get(STATUS_ROW_RENDER_CACHE, key)
    if cached is not None:
        return cached

    stat_str = f"{CLR_GREEN}Active{CLR_RESET}" if status["has_token"] else f"{CLR_RED}No Token{CLR_RESET}"
    lbl_str = f"({status['label']})" if status["label"] else ""
    email_color = CLR_CYAN if status["has_token"] else CLR_RED
    profile = status_profile_text(status)
    display_email = status["email"]
    quota_account = (status.get("quota") or {}).get("account")
    if quota_account and (tool_key == "agy" or display_email in ("logged in", "(no login)")):
        display_email = quota_account
    email = color_email_parts(display_email) if status["has_token"] else f"{email_color}{display_email}{CLR_RESET}"
    label = f"{CLR_YELLOW}{lbl_str}{CLR_RESET}" if lbl_str else ""
    if tool_key == "agy":
        quota = " ".join(
            visible_fit(color_agy_quota_cell(cell, status), widths["quota"])
            for cell in agy_quota_cells_cached(status, quota_columns)
        )
    else:
        quota = visible_fit(quota_text(status, width=widths["quota"]), widths["quota"])
    row = (
        f"{visible_fit(profile, widths['profile'])} "
        f"{visible_fit(email, widths['account'])} "
        f"{visible_fit(stat_str, widths['status'])} "
        f"{quota} "
        f"{visible_fit(label, widths['label'])}"
    )
    return bounded_cache_set(STATUS_ROW_RENDER_CACHE, key, row)


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
    bump_status_render_generation()
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
                record_quota_job_coalesced()
                continue
            previous_machine = quota_entry_machine_state(entry)
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
            target_state = "stale_refreshing" if (quota.get("state") == "available" and quota.get("limits")) else "queued"
            if previous_machine != target_state:
                transition_quota_entry(entry, target_state, entry_tool, profile_num, "forced_refresh")
            submissions.append((entry_tool, profile_num))
        if submissions:
            bump_status_render_generation()
    for entry_tool, profile_num in submissions:
        future = quota_scheduler().submit(entry_tool, profile_num, priority=0)
        with INTERACTIVE_QUOTA_LOCK:
            entry = INTERACTIVE_QUOTA_CACHE.get(quota_cache_key(entry_tool, profile_num))
            if entry is not None:
                entry["future"] = future
    return len(submissions)


def schedule_due_quota_refresh(tool_key=None, now=None):
    now = time.time() if now is None else now
    submissions = []
    with INTERACTIVE_QUOTA_LOCK:
        for key, entry in list(INTERACTIVE_QUOTA_CACHE.items()):
            entry_tool, profile_num = key
            if tool_key is not None and entry_tool != tool_key:
                continue
            if entry.get("job_state") in QUOTA_ACTIVE_JOB_STATES:
                record_quota_job_coalesced()
                continue
            quota = entry.get("quota") or {}
            fetched_at = entry.get("fetched_at")
            reasons = []
            machine_state = quota_entry_machine_state(entry)
            retryable = (
                machine_state != "auth_required"
                and (entry.get("state") == "retryable" or entry.get("job_state") == "retryable")
            )
            retry_at = entry.get("next_retry_at")
            if retryable and retry_at is not None and now < retry_at:
                continue
            if fetched_at is not None and quota.get("state") == "available":
                age = now - fetched_at
                if age >= interactive_quota_fresh_seconds():
                    reasons.append("freshness_expired")
            if retryable:
                if retry_at is None or now >= retry_at:
                    reasons.append("retry_due")
            if not reasons:
                continue
            previous_machine = quota_entry_machine_state(entry)
            entry["state"] = "queued"
            entry["job_state"] = "queued"
            entry["started_at"] = None
            entry["next_retry_at"] = None
            if quota:
                quota["job_state"] = "queued"
                entry["quota"] = quota
            else:
                entry["quota"] = loading_quota("queued")
            target_state = "stale_refreshing" if (quota.get("state") == "available" and quota.get("limits")) else "queued"
            if previous_machine != target_state:
                transition_quota_entry(entry, target_state, entry_tool, profile_num, ",".join(reasons), now)
            submissions.append((entry_tool, profile_num, reasons, fetched_at))
        if submissions:
            bump_status_render_generation()
    for entry_tool, profile_num, reasons, fetched_at in submissions:
        age = None if fetched_at is None else round(now - fetched_at, 3)
        _audit().record(
            "quota",
            "auto_refresh_queued",
            tool=entry_tool,
            profile=f"p{profile_num}",
            details={
                "reasons": reasons,
                "priority": 5,
                "age_seconds": age,
                "fresh_seconds": interactive_quota_fresh_seconds(),
            },
        )
        logging.info(
            "quota auto refresh queued tool=%s profile=p%s reasons=%s age=%s",
            entry_tool,
            profile_num,
            reasons,
            age,
        )
        future = quota_scheduler().submit(entry_tool, profile_num, priority=5)
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
                "machine_state": quota_entry_machine_state(entry),
                "state_machine": entry.get("state_machine"),
                "quota_state": quota.get("state"),
                "quota_pipeline_state": quota.get("pipeline_state"),
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
                "metrics": scheduler.metrics_snapshot(),
            }
    return {
        "enabled": interactive_quota_enabled(),
        "states": list(QUOTA_PIPELINE_STATES),
        "failure_states": list(QUOTA_FAILURE_STATES),
        "legal_transitions": {key or "start": sorted(value) for key, value in QUOTA_LEGAL_TRANSITIONS.items()},
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


def header_lines(title=""):
    width = 62
    border = "═" * (width - 2)
    lines = [f"{CLR_BOLD}{CLR_CYAN}╔{border}╗{CLR_RESET}"]
    if title:
        padding = (width - 2 - len(title)) // 2
        pad_str = " " * padding
        extra = " " if (width - 2 - len(title)) % 2 != 0 else ""
        lines.append(
            f"{CLR_BOLD}{CLR_CYAN}║{CLR_RESET}{pad_str}"
            f"{CLR_BOLD}{CLR_WHITE}{title}{CLR_RESET}{pad_str}{extra}"
            f"{CLR_BOLD}{CLR_CYAN}║{CLR_RESET}"
        )
    lines.append(f"{CLR_BOLD}{CLR_CYAN}╚{border}╝{CLR_RESET}")
    return lines


def reset_status_screen_render():
    STATUS_SCREEN_RENDER_CACHE.clear()
    STATUS_ROW_RENDER_CACHE.clear()
    STATUS_QUOTA_CELL_RENDER_CACHE.clear()
    reset_live_log_cache()
    STATUS_RENDERER.reset()


def paint_terminal_frame(lines, cache_key="status"):
    global STATUS_RENDERER
    if STATUS_RENDERER.stdout is not sys.stdout or STATUS_RENDERER.cache_key != cache_key:
        STATUS_RENDERER = TerminalFrameRenderer(stdout=sys.stdout, cache_key=cache_key)
    if cache_key not in STATUS_SCREEN_RENDER_CACHE:
        STATUS_RENDERER.previous_lines = None
    STATUS_RENDERER.paint(lines)
    STATUS_SCREEN_RENDER_CACHE[cache_key] = list(STATUS_RENDERER.previous_lines or [])


def status_screen_snapshot_key(
    tool_key,
    status_message,
    statuses,
    layout_key,
    progress_line,
    countdown,
    developer_mode,
    live_logs,
):
    return (
        tool_key,
        status_message,
        layout_key,
        tuple(status_row_render_key(tool_key, status, (), {}, None) for status in statuses),
        progress_line,
        countdown,
        developer_mode,
        tuple(live_logs),
    )


def status_screen_width():
    columns, _ = terminal_size(fallback=(120, 24))
    return max(60, columns)


def status_screen_fast_key(tool_key, status_message, base_statuses):
    if base_statuses is None:
        return None
    now = time.time()
    active = any_quota_loading(tool_key)
    developer_mode = interactive_developer_mode_enabled()
    log_fingerprint = log_file_fingerprint() if developer_mode else None
    return (
        tool_key,
        status_message,
        id(base_statuses),
        len(base_statuses),
        INTERACTIVE_QUOTA_RENDER_GENERATION,
        int(now * 4) if active else None,
        quota_refresh_countdown(tool_key, now),
        developer_mode,
        log_fingerprint,
        status_screen_width(),
    )


def status_screen_layout(tool_key, statuses, max_width=None):
    max_width = max_width or status_screen_width()
    if tool_key == "agy":
        quota_columns = agy_status_quota_columns(statuses)
        quota_width = 4
        profile_width = 7
        status_width = 8
        label_width = 12
        quota_block_width = (quota_width * len(quota_columns)) + max(0, len(quota_columns) - 1)
        fixed_width = profile_width + status_width + label_width + quota_block_width + 4
        account_width = min(38, max(18, max_width - fixed_width))
        if fixed_width + account_width > max_width:
            label_width = max(0, label_width - ((fixed_width + account_width) - max_width))
            fixed_width = profile_width + status_width + label_width + quota_block_width + 4
            account_width = max(18, max_width - fixed_width)
        if fixed_width + account_width > max_width:
            account_width = max(7, max_width - fixed_width)
        widths = {
            "profile": profile_width,
            "account": account_width,
            "status": status_width,
            "quota": quota_width,
            "label": label_width,
        }
        quota_header = agy_quota_header_lines(quota_columns, widths["quota"])
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
    return quota_columns, widths, quota_header, total_width


def render_status_screen_frame(tool_key, status_message=None, base_statuses=None):
    now = time.time()
    tool_name = TOOLS[tool_key]["name"]
    lines = header_lines(f"STATUS: {tool_name.upper()}")
    lines.append("")

    if base_statuses is None:
        base_statuses = collect_status_snapshot(tool_key)
    statuses = [status_with_auto_quota_snapshot(tool_key, status) for status in base_statuses]
    screen_width = status_screen_width()
    quota_columns, widths, quota_header, total_width = status_screen_layout(tool_key, statuses, screen_width)
    layout_key = (screen_width, tuple(quota_columns), tuple(sorted(widths.items())), total_width)
    progress_line = quota_progress_line(statuses, now)
    developer_mode = interactive_developer_mode_enabled()
    log_lines = live_log_lines() if developer_mode else []
    countdown = quota_refresh_countdown(tool_key, now)
    snapshot_key = status_screen_snapshot_key(
        tool_key,
        status_message,
        statuses,
        layout_key,
        progress_line,
        countdown,
        developer_mode,
        log_lines,
    )

    if isinstance(quota_header, tuple):
        quota_group_header, quota_column_header = quota_header
        lines.append(
            f"{CLR_BOLD}{CLR_WHITE}"
            f"{visible_fit('Profile', widths['profile'])} "
            f"{visible_fit('Active Account / Tier', widths['account'])} "
            f"{visible_fit('Status', widths['status'])} "
            f"{quota_group_header} "
            f"{visible_fit('Label', widths['label'])}"
            f"{CLR_RESET}"
        )
        lines.append(
            f"{CLR_BOLD}{CLR_WHITE}"
            f"{visible_fit('', widths['profile'])} "
            f"{visible_fit('', widths['account'])} "
            f"{visible_fit('', widths['status'])} "
            f"{quota_column_header} "
            f"{visible_fit('', widths['label'])}"
            f"{CLR_RESET}"
        )
    else:
        lines.append(
            f"{CLR_BOLD}{CLR_WHITE}"
            f"{visible_fit('Profile', widths['profile'])} "
            f"{visible_fit('Active Account / Tier', widths['account'])} "
            f"{visible_fit('Status', widths['status'])} "
            f"{quota_header} "
            f"{visible_fit('Label', widths['label'])}"
            f"{CLR_RESET}"
        )
    lines.append("-" * total_width)

    for status in statuses:
        lines.append(render_status_row(tool_key, status, quota_columns, widths, now))
    lines.append("")
    if status_message:
        lines.append(f"{CLR_YELLOW}{status_message}{CLR_RESET}")
    if progress_line:
        lines.append(progress_line)
    if developer_mode:
        lines.append("")
        lines.append(f"{CLR_BOLD}{CLR_YELLOW}Live logs{CLR_RESET}")
        for log_line in log_lines:
            lines.append(f"  {CLR_WHITE}{log_line}{CLR_RESET}")
    lines.append(
        f"Next auto refresh: {CLR_CYAN}{countdown}{CLR_RESET}. "
        "Press Enter/q to return, r to refresh quota now..."
    )
    return snapshot_key, lines


def render_status_screen_lines(tool_key, status_message=None, base_statuses=None):
    return render_status_screen_frame(tool_key, status_message, base_statuses)[1]


def render_status_screen(tool_key, status_message=None, base_statuses=None):
    fast_key = status_screen_fast_key(tool_key, status_message, base_statuses)
    if fast_key is not None and STATUS_SCREEN_RENDER_CACHE.get("status_fast_key") == fast_key:
        return False
    snapshot_key, lines = render_status_screen_frame(tool_key, status_message, base_statuses)
    if fast_key is not None:
        STATUS_SCREEN_RENDER_CACHE["status_fast_key"] = fast_key
    if STATUS_SCREEN_RENDER_CACHE.get("status_snapshot_key") == snapshot_key:
        return False
    paint_terminal_frame(lines)
    STATUS_SCREEN_RENDER_CACHE["status_snapshot_key"] = snapshot_key
    return True


def view_status(tool_key):
    status_message = None
    base_statuses = collect_status_snapshot(tool_key)
    STATUS_SCREEN_RENDER_CACHE.clear()
    _audit().record("interactive", "started", command="status", tool=tool_key, details={"workflow": "view_status"})
    try:
        while True:
            render_status_screen(tool_key, status_message, base_statuses)
            status_message = None
            key = get_key(timeout=next_quota_wake_timeout(tool_key))
            if key is None:
                count = schedule_due_quota_refresh(tool_key)
                if count:
                    _audit().record(
                        "interactive",
                        "retried",
                        command="status",
                        tool=tool_key,
                        details={"workflow": "auto_quota_refresh", "profiles": count},
                    )
                continue
            if key in ("enter", "esc", "q"):
                _audit().record("interactive", "completed", command="status", tool=tool_key, result="succeeded", details={"workflow": "view_status", "key": key})
                return
            elif key in ("r", "R", "ctrl+r", "к", "К"):
                count = force_quota_refresh(tool_key)
                _audit().record("interactive", "retried", command="status", tool=tool_key, details={"workflow": "quota_refresh", "profiles": count})
                if count:
                    status_message = f"Refreshing quota now for {count} profiles..."
                else:
                    status_message = "Quota refresh is already running..."
                continue
            elif key == "ctrl+c":
                _audit().record("interactive", "failed", command="status", tool=tool_key, result="failed", error_class="KeyboardInterrupt")
                sys.exit(0)
    finally:
        reset_status_screen_render()


def clear_screen():
    STATUS_SCREEN_RENDER_CACHE.clear()
    STATUS_RENDERER.previous_lines = None
    STATUS_RENDERER.previous_size = None
    STATUS_RENDERER.cursor_hidden = False
    sys.stdout.write("\033[?25h\033[H\033[2J\033[3J")
    sys.stdout.flush()


def print_header(title=""):
    for line in header_lines(title):
        print(line)


def render_menu_lines(options, title="", selected_idx=0, pre_lines=None):
    lines = header_lines(title)
    lines.append("")
    if pre_lines:
        lines.extend(str(line) for line in pre_lines)
    for idx, option in enumerate(options):
        if idx == selected_idx:
            lines.append(f"  {CLR_BOLD}{CLR_CYAN}--> \033[40m\033[1;37m{option}{CLR_RESET}")
        else:
            lines.append(f"      \033[90m{option}{CLR_RESET}")
    lines.append("")
    lines.append(
        f"{CLR_WHITE}Use {CLR_BOLD}↑/↓{CLR_RESET}{CLR_WHITE}, digits/shortcuts, "
        f"{CLR_BOLD}Enter{CLR_RESET}{CLR_WHITE} to confirm, "
        f"{CLR_BOLD}Esc/q{CLR_RESET}{CLR_WHITE} to go back.{CLR_RESET}"
    )
    return lines


def run_menu(options, title="", shortcuts=None, pre_lines=None):
    shortcuts = shortcuts or {}
    selected_idx = 0
    renderer = TerminalFrameRenderer(cache_key="menu")
    _audit().record("interactive", "started", details={"workflow": "menu", "title": title, "options": len(options)})
    try:
        while True:
            renderer.paint(render_menu_lines(options, title, selected_idx, pre_lines=pre_lines))
            key = get_key()
            if key == 'up':
                selected_idx = (selected_idx - 1) % len(options)
            elif key == 'down':
                selected_idx = (selected_idx + 1) % len(options)
            elif key == 'enter':
                _audit().record("interactive", "completed", result="succeeded", details={"workflow": "menu", "title": title, "selected": selected_idx})
                return selected_idx
            elif key.isdigit() and key != "0":
                idx = int(key) - 1
                if 0 <= idx < len(options):
                    _audit().record("interactive", "completed", result="succeeded", details={"workflow": "menu", "title": title, "selected": idx, "key": key})
                    return idx
            elif key in shortcuts:
                _audit().record("interactive", "completed", result="succeeded", details={"workflow": "menu", "title": title, "shortcut": key})
                return shortcuts[key]
            elif key in ('esc', 'q'):
                _audit().record("interactive", "completed", result="cancelled", details={"workflow": "menu", "title": title, "key": key})
                return -1
            elif key == 'ctrl+c':
                _audit().record("interactive", "failed", result="failed", error_class="KeyboardInterrupt", details={"workflow": "menu", "title": title})
                sys.exit(0)
    finally:
        renderer.clear()
        renderer.reset()


def launch_account_table(tool_key, statuses):
    if tool_key == "agy":
        quota_columns = agy_status_quota_columns(statuses)
        widths = {
            "profile": 6,
            "account": 30,
            "status": 10,
            "quota": 5,
            "label": 14,
        }
        quota_header = agy_quota_header_lines(quota_columns, widths["quota"])
        total_width = widths["profile"] + widths["account"] + widths["status"] + widths["label"]
        total_width += (widths["quota"] * len(quota_columns)) + len(quota_columns) + 3
    else:
        quota_columns = []
        widths = {
            "profile": 6,
            "account": 30,
            "status": 10,
            "quota": 28,
            "label": 14,
        }
        quota_header = f"{'Quota':<{widths['quota']}}"
        total_width = sum(widths.values()) + len(widths) - 1

    prefix = "      "
    if isinstance(quota_header, tuple):
        quota_group_header, quota_column_header = quota_header
        headers = [
            (
                f"{prefix}{CLR_BOLD}{CLR_WHITE}"
                f"{'Profile':<{widths['profile']}} "
                f"{'Account':<{widths['account']}} "
                f"{'Status':<{widths['status']}} "
                f"{quota_group_header} "
                f"{'Label':<{widths['label']}}"
                f"{CLR_RESET}"
            ),
            (
                f"{prefix}{CLR_BOLD}{CLR_WHITE}"
                f"{'':<{widths['profile']}} "
                f"{'':<{widths['account']}} "
                f"{'':<{widths['status']}} "
                f"{quota_column_header} "
                f"{'':<{widths['label']}}"
                f"{CLR_RESET}"
            ),
        ]
    else:
        headers = [
            (
                f"{prefix}{CLR_BOLD}{CLR_WHITE}"
                f"{'Profile':<{widths['profile']}} "
                f"{'Account':<{widths['account']}} "
                f"{'Status':<{widths['status']}} "
                f"{quota_header} "
                f"{'Label':<{widths['label']}}"
                f"{CLR_RESET}"
            )
        ]
    separator = f"{prefix}{'-' * total_width}"
    rows = []
    for status in statuses:
        label_text = f"({status['label']})" if status["label"] else ""
        state_text = f"{CLR_GREEN}Active{CLR_RESET}" if status["has_token"] else f"{CLR_RED}No Token{CLR_RESET}"
        display_account = status.get("email", "")
        quota_account = (status.get("quota") or {}).get("account")
        if quota_account and (tool_key == "agy" or display_account in ("logged in", "(no login)")):
            display_account = quota_account
        account = color_email_parts(display_account) if status["has_token"] else f"{CLR_RED}{display_account}{CLR_RESET}"
        if tool_key == "agy":
            quota_text_value = " ".join(
                visible_fit(color_agy_quota_cell(cell, status), widths["quota"])
                for cell in agy_quota_cells(status, quota_columns)
            )
        else:
            quota_text_value = visible_fit(quota_text(status, width=widths["quota"]), widths["quota"])
        profile_text = status_profile_text(status)
        label = f"{CLR_YELLOW}{label_text}{CLR_RESET}" if label_text else ""
        rows.append(
            f"{visible_fit(profile_text, widths['profile'])} "
            f"{visible_fit(account, widths['account'])} "
            f"{visible_fit(state_text, widths['status'])} "
            f"{quota_text_value} "
            f"{visible_fit(label, widths['label'])}"
        )
    return headers + [separator], rows

def launch_account(tool_key):
    tool = TOOLS[tool_key]
    metadata = load_metadata()
    while True:
        profiles = get_display_profiles(tool_key)
        statuses = [status_with_auto_quota(tool_key, n, metadata) for n in profiles]
        pre_lines, options = launch_account_table(tool_key, statuses)

        sel = run_menu(options, f"LAUNCH {tool['name'].upper()}", pre_lines=pre_lines)
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

        safety_decision(
            "label",
            command="label",
            tool=tool_key,
            profile=f"p{profile_num}",
            target=profile_home(tool_key, profile_num),
            facts={"label": new_lbl},
        )
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
        safety_decision(
            "import",
            command="import",
            tool=tool_key,
            profile=f"p{next_p}",
            target=credential_path(tool_key, next_p),
            facts={"source": cred_file, "destination": credential_path(tool_key, next_p)},
        )
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
            export_dir = default_export_dir()
            if tool_key == "agy":
                planned_dest = os.path.join(export_dir, f"cred-p{profile_num}-exported.json")
            else:
                planned_dest = os.path.join(export_dir, f"{tool_key}-p{profile_num}-exported.json")
            safety_decision(
                "export",
                command="export",
                tool=tool_key,
                profile=f"p{profile_num}",
                target=planned_dest,
                facts={"source": credential_path(tool_key, profile_num), "destination": planned_dest},
            )
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
        decision = safety_decision(
            "clear",
            command="clear",
            tool=tool_key,
            profile=f"p{profile_num}",
            target=home,
            facts={"exists": os.path.exists(home), "delete_paths": [home] if os.path.exists(home) else []},
            yes=(confirm == "yes"),
        )
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
            print(f"\nOperation cancelled. {decision['message'] or ''}".rstrip())

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
        safety_decision(
            "import",
            command="import",
            tool=tool_key,
            profile=f"p{next_p}",
            target=credential_path(tool_key, next_p),
            facts={"source": cred_file, "destination": credential_path(tool_key, next_p)},
        )
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
            safety_decision(
                "sync-hard",
                command="sync",
                target=str(dst_base),
                facts={
                    "source": direction,
                    "mode": mode,
                    "source_base": str(src_base),
                    "destination_base": str(dst_base),
                    "would_delete": preflight["would_delete"],
                },
                dry_run=True,
            )
            print(f"Hard-delete preflight: {preflight['would_delete']} destination paths would be removed.")
            for path in preflight["delete_paths"]:
                print(f"  {path}")
        except Exception as e:
            print(f"{CLR_RED}Preflight failed: {e}{CLR_RESET}")
            input("\nPress Enter to return...")
            return
        print(f"{CLR_RED}WARNING: Hard sync will DELETE extra files in Dest that are not in Source.{CLR_RESET}")
        confirm = input("Type 'yes' to proceed: ").strip().lower()
        decision = safety_decision(
            "sync-hard",
            command="sync",
            target=str(dst_base),
            facts={
                "source": direction,
                "mode": mode,
                "source_base": str(src_base),
                "destination_base": str(dst_base),
                "would_delete": preflight["would_delete"],
            },
            yes=(confirm == "yes"),
        )
        if confirm != 'yes':
            print(f"Operation cancelled. {decision['message'] or ''}".rstrip())
            input("\nPress Enter to return...")
            return
    else:
        safety_decision(
            "sync-soft",
            command="sync",
            target=str(dst_base),
            facts={
                "source": direction,
                "mode": mode,
                "source_base": str(src_base),
                "destination_base": str(dst_base),
            },
        )

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


def format_duration(seconds):
    try:
        seconds = int(float(seconds))
    except (TypeError, ValueError):
        seconds = 0
    if seconds >= 3600 and seconds % 3600 == 0:
        return f"{seconds // 3600}h"
    if seconds >= 60 and seconds % 60 == 0:
        return f"{seconds // 60}m"
    return f"{seconds}s"


def parse_duration_seconds(value):
    raw = str(value).strip().lower()
    if not raw:
        raise ValueError("empty duration")
    multiplier = 1.0
    if raw.endswith("ms"):
        multiplier = 0.001
        raw = raw[:-2].strip()
    elif raw.endswith("s"):
        raw = raw[:-1].strip()
    elif raw.endswith("m"):
        multiplier = 60.0
        raw = raw[:-1].strip()
    elif raw.endswith("h"):
        multiplier = 3600.0
        raw = raw[:-1].strip()
    seconds = float(raw) * multiplier
    if seconds < 1:
        raise ValueError("duration must be at least 1 second")
    return seconds


def settings_menu_lines():
    current = interactive_quota_fresh_seconds()
    source = "environment" if "AI_MAN_INTERACTIVE_QUOTA_FRESH_SECONDS" in os.environ else "saved/default"
    dev_mode = "on" if interactive_developer_mode_enabled() else "off"
    return [
        f"      Quota refresh interval: {CLR_CYAN}{format_duration(current)}{CLR_RESET} ({current:g}s, {source})",
        f"      Env: AI_MAN_INTERACTIVE_QUOTA_FRESH_SECONDS",
        f"      Developer mode: {CLR_CYAN}{dev_mode}{CLR_RESET} (shows live logs on status screens)",
        f"      Env: AI_MAN_DEVELOPER_MODE",
        "",
    ]


def edit_quota_refresh_interval():
    clear_screen()
    print_header("SET QUOTA REFRESH INTERVAL")
    current = interactive_quota_fresh_seconds()
    print(f"\nCurrent value: {CLR_CYAN}{format_duration(current)}{CLR_RESET} ({current:g} seconds)")
    print("Enter seconds, or use suffix: 30s, 10m, 1h.")
    value = input("\nNew value (empty to cancel): ").strip()
    if not value:
        return
    try:
        seconds = parse_duration_seconds(value)
    except ValueError as e:
        print(f"\n{CLR_RED}Invalid interval: {e}{CLR_RESET}")
        input("\nPress Enter to return...")
        return
    save_interactive_setting(QUOTA_REFRESH_SETTING_KEY, seconds)
    os.environ["AI_MAN_INTERACTIVE_QUOTA_FRESH_SECONDS"] = str(seconds)
    invalidate_quota_cache()
    print(f"\n{CLR_GREEN}Quota refresh interval updated to {format_duration(seconds)}.{CLR_RESET}")
    input("Press Enter to return...")


def toggle_developer_mode():
    enabled = not interactive_developer_mode_enabled()
    save_interactive_setting(DEVELOPER_MODE_SETTING_KEY, enabled)
    os.environ["AI_MAN_DEVELOPER_MODE"] = "1" if enabled else "0"
    print(f"\n{CLR_GREEN}Developer mode {'enabled' if enabled else 'disabled'}.{CLR_RESET}")
    input("Press Enter to return...")


def settings_menu():
    options = [
        "[1] Quota refresh interval",
        "[2] Toggle developer mode",
        "[x] Back to main menu",
    ]
    while True:
        sel = run_menu(options, "SETTINGS", shortcuts={"x": 2}, pre_lines=settings_menu_lines())
        if sel == 0:
            edit_quota_refresh_interval()
        elif sel == 1:
            toggle_developer_mode()
        elif sel in (2, -1):
            break


def run_interactive_main():
    global INTERACTIVE_SHUTTING_DOWN
    configure_interactive_logging()
    INTERACTIVE_SHUTTING_DOWN = False
    previous_handlers = install_interactive_signal_handlers()
    try:
        while True:
            options = [
                "[1] Antigravity CLI (agy)",
                "[2] OpenAI Codex CLI",
                "[3] Anthropic Claude CLI",
                "[4] Sync Profiles (WSL <-> Windows)",
                "[5] Settings",
                "[x] Exit",
            ]
            sel = run_menu(options, "UNIFIED PROFILE MANAGER", shortcuts={"x": 5})
            if sel == 0:
                run_tool_manager("agy")
            elif sel == 1:
                run_tool_manager("codex")
            elif sel == 2:
                run_tool_manager("claude")
            elif sel == 3:
                sync_profiles()
            elif sel == 4:
                settings_menu()
            elif sel in (5, -1):
                clear_screen()
                print("Exiting Profile Manager. Goodbye!")
                break
        return EXIT_OK
    finally:
        shutdown_interactive_runtime(wait=True)
        restore_interactive_signal_handlers(previous_handlers)
