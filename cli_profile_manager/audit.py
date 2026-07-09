import contextlib
import contextvars
import json
import os
import re
import stat
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from . import metadata


SCHEMA_VERSION = 1
AUDIT_DIR_NAME = "audit"
JSONL_NAME = "audit.jsonl"
SQLITE_NAME = "audit.sqlite3"
TOKEN_RE = re.compile(
    r"(?i)(sk-[a-z0-9_-]+|xox[a-z]-[a-z0-9-]+|gh[pousr]_[a-z0-9_]+|ya29\.[a-z0-9._-]+|refresh_token|access_token|id_token|authorization)"
)
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@([A-Z0-9.-]+\.[A-Z]{2,})\b", re.I)
PATH_RE = re.compile(r"(?:(?:/[\w .@+-]+){2,}|[A-Za-z]:\\[^\s]+)")
SECRET_KEYS = {
    "token",
    "refresh_token",
    "access_token",
    "id_token",
    "authorization",
    "password",
    "secret",
    "credential",
    "credentials",
    "env",
    "environment",
    "raw_output",
    "screen",
    "screen_text",
    "stdout",
    "stderr",
}
BOOL_TRUE = {"1", "true", "yes", "on", "enabled"}
BOOL_FALSE = {"0", "false", "no", "off", "disabled"}

CURRENT_CORRELATION_ID = contextvars.ContextVar("audit_correlation_id", default=None)
CURRENT_PARENT_ID = contextvars.ContextVar("audit_parent_id", default=None)


def _bool_env(name, default):
    raw = os.environ.get(name)
    if raw is None:
        return default
    value = raw.strip().lower()
    if value in BOOL_TRUE:
        return True
    if value in BOOL_FALSE:
        return False
    return default


def audit_enabled():
    return _bool_env("AI_MAN_AUDIT", True)


def strict_mode():
    return _bool_env("AI_MAN_AUDIT_STRICT", False)


def show_accounts():
    return _bool_env("AI_MAN_AUDIT_SHOW_ACCOUNTS", False)


def show_paths():
    return _bool_env("AI_MAN_AUDIT_SHOW_PATHS", False)


def backend_name():
    raw = os.environ.get("AI_MAN_AUDIT_BACKEND", "jsonl").strip().lower()
    return raw if raw in ("jsonl", "sqlite") else "jsonl"


def retention_days():
    raw = os.environ.get("AI_MAN_AUDIT_RETENTION_DAYS", "90")
    try:
        return max(1, int(raw))
    except ValueError:
        return 90


def max_bytes():
    raw = os.environ.get("AI_MAN_AUDIT_MAX_BYTES", str(10 * 1024 * 1024))
    try:
        return max(4096, int(raw))
    except ValueError:
        return 10 * 1024 * 1024


def audit_dir():
    return Path(metadata.METADATA_DIR) / AUDIT_DIR_NAME


def jsonl_path():
    return audit_dir() / JSONL_NAME


def sqlite_path():
    return audit_dir() / SQLITE_NAME


def ensure_audit_dir():
    path = audit_dir()
    path.mkdir(parents=True, exist_ok=True)
    with contextlib.suppress(OSError):
        os.chmod(path, 0o700)
    return path


def user_only_mode(path):
    try:
        return oct(stat.S_IMODE(os.stat(path).st_mode))
    except OSError:
        return None


def redact_string(value):
    text = str(value)
    text = TOKEN_RE.sub("[redacted-token]", text)
    if not show_accounts():
        text = EMAIL_RE.sub(lambda match: f"redacted:{stable_hash(match.group(0))}@{match.group(1).lower()}", text)
    if not show_paths():
        text = PATH_RE.sub("[redacted-path]", text)
    return text


def stable_hash(value):
    import hashlib

    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:12]


def redact(value, key=None):
    lowered = str(key or "").lower()
    if lowered in SECRET_KEYS or any(part in lowered for part in ("token", "secret", "password", "credential")):
        return "[redacted]"
    if isinstance(value, dict):
        return {str(k): redact(v, k) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact(item, key) for item in value]
    if isinstance(value, str):
        return redact_string(value)
    return value


def utc_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def make_event(
    category,
    action,
    command=None,
    tool=None,
    profile=None,
    backend=None,
    result=None,
    exit_code=None,
    error_class=None,
    details=None,
    correlation_id=None,
    parent_id=None,
):
    event_id = uuid.uuid4().hex
    corr = correlation_id or CURRENT_CORRELATION_ID.get() or event_id
    event = {
        "schema_version": SCHEMA_VERSION,
        "event_id": event_id,
        "correlation_id": corr,
        "parent_id": parent_id if parent_id is not None else CURRENT_PARENT_ID.get(),
        "timestamp": utc_now(),
        "monotonic_ms": round(time.monotonic() * 1000, 3),
        "pid": os.getpid(),
        "category": category,
        "action": action,
        "command": command,
        "tool": tool,
        "profile": profile,
        "backend": backend,
        "result": result,
        "exit_code": exit_code,
        "error_class": error_class,
        "details": redact(details or {}),
    }
    return event


def _write_jsonl(event):
    ensure_audit_dir()
    path = jsonl_path()
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")
    with contextlib.suppress(OSError):
        os.chmod(path, 0o600)


def _sqlite_connect():
    import sqlite3

    ensure_audit_dir()
    conn = sqlite3.connect(str(sqlite_path()))
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_events (
            event_id TEXT PRIMARY KEY,
            correlation_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            category TEXT NOT NULL,
            action TEXT NOT NULL,
            command TEXT,
            tool TEXT,
            profile TEXT,
            result TEXT,
            event_json TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_correlation ON audit_events(correlation_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_filters ON audit_events(category, command, tool, profile, result)")
    with contextlib.suppress(OSError):
        os.chmod(sqlite_path(), 0o600)
    return conn


def _write_sqlite(event):
    with _sqlite_connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO audit_events
            (event_id, correlation_id, timestamp, category, action, command, tool, profile, result, event_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event["event_id"],
                event["correlation_id"],
                event["timestamp"],
                event["category"],
                event["action"],
                event.get("command"),
                event.get("tool"),
                str(event.get("profile")) if event.get("profile") is not None else None,
                event.get("result"),
                json.dumps(event, sort_keys=True),
            ),
        )


def write_event(event):
    if not audit_enabled():
        return None
    try:
        if backend_name() == "sqlite":
            _write_sqlite(event)
        else:
            _write_jsonl(event)
        return event
    except Exception:
        if strict_mode():
            raise
        return None


def record(category, action, **kwargs):
    return write_event(make_event(category, action, **kwargs))


@contextlib.contextmanager
def span(category, action, **kwargs):
    started = make_event(category, "started", **kwargs)
    write_event(started)
    corr_token = CURRENT_CORRELATION_ID.set(started["correlation_id"])
    parent_token = CURRENT_PARENT_ID.set(started["event_id"])
    start_time = time.monotonic()
    try:
        yield started
    except Exception as exc:
        details = dict(kwargs.get("details") or {})
        details["elapsed_ms"] = round((time.monotonic() - start_time) * 1000, 3)
        write_event(make_event(category, "failed", error_class=type(exc).__name__, result="failed", details=details, **_span_kwargs(kwargs)))
        raise
    finally:
        CURRENT_PARENT_ID.reset(parent_token)
        CURRENT_CORRELATION_ID.reset(corr_token)


def complete_span(started_event, result="succeeded", exit_code=None, details=None, error_class=None):
    event = make_event(
        started_event["category"],
        "completed",
        command=started_event.get("command"),
        tool=started_event.get("tool"),
        profile=started_event.get("profile"),
        backend=started_event.get("backend"),
        result=result,
        exit_code=exit_code,
        error_class=error_class,
        details={
            **(details or {}),
            "elapsed_ms": round(time.monotonic() * 1000 - started_event["monotonic_ms"], 3),
        },
        correlation_id=started_event["correlation_id"],
        parent_id=started_event["event_id"],
    )
    return write_event(event)


def _span_kwargs(kwargs):
    return {
        "command": kwargs.get("command"),
        "tool": kwargs.get("tool"),
        "profile": kwargs.get("profile"),
        "backend": kwargs.get("backend"),
    }


def read_jsonl_events(path=None):
    path = Path(path or jsonl_path())
    events = []
    if not path.exists():
        return events
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(event, dict):
                events.append(event)
    return events


def read_sqlite_events():
    if not sqlite_path().exists():
        return []
    with _sqlite_connect() as conn:
        rows = conn.execute("SELECT event_json FROM audit_events ORDER BY timestamp, event_id").fetchall()
    events = []
    for (raw,) in rows:
        with contextlib.suppress(json.JSONDecodeError):
            events.append(json.loads(raw))
    return events


def all_events():
    return read_sqlite_events() if backend_name() == "sqlite" else read_jsonl_events()


def _matches(event, filters):
    since = filters.pop("since", None)
    until = filters.pop("until", None)
    if since or until:
        timestamp = event.get("timestamp", "")
        if since and timestamp < since:
            return False
        if until and timestamp > until:
            return False
    for key, expected in filters.items():
        if expected is None:
            continue
        if key == "profile":
            actual = event.get("profile")
            if actual not in (expected, str(expected), f"p{expected}"):
                return False
        elif event.get(key) != expected:
            return False
    return True


def query_events(limit=50, **filters):
    events = [event for event in all_events() if _matches(event, dict(filters))]
    events.sort(key=lambda event: (event.get("timestamp", ""), event.get("event_id", "")), reverse=True)
    if limit is not None:
        events = events[: max(0, int(limit))]
    return events


def show_events(identifier):
    return [
        event for event in all_events()
        if event.get("event_id") == identifier or event.get("correlation_id") == identifier
    ]


def purge_all():
    removed = 0
    for path in (jsonl_path(), sqlite_path()):
        if path.exists():
            try:
                if path == jsonl_path():
                    removed += len(read_jsonl_events(path))
                else:
                    removed += len(read_sqlite_events())
                path.unlink()
            except OSError:
                pass
    return removed


def compact_retention(days=None, maximum_bytes=None):
    days = retention_days() if days is None else int(days)
    maximum_bytes = max_bytes() if maximum_bytes is None else int(maximum_bytes)
    cutoff = time.time() - (days * 86400)
    kept = []
    removed = 0
    for event in all_events():
        try:
            event_time = datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00")).timestamp()
        except Exception:
            event_time = time.time()
        if event_time < cutoff:
            removed += 1
        else:
            kept.append(event)
    encoded = [json.dumps(event, sort_keys=True) for event in kept]
    while sum(len(item) + 1 for item in encoded) > maximum_bytes and encoded:
        encoded.pop(0)
        kept.pop(0)
        removed += 1
    if backend_name() == "sqlite":
        if sqlite_path().exists():
            sqlite_path().unlink()
        for event in kept:
            _write_sqlite(event)
    else:
        ensure_audit_dir()
        with open(jsonl_path(), "w", encoding="utf-8") as handle:
            for raw in encoded:
                handle.write(raw + "\n")
        with contextlib.suppress(OSError):
            os.chmod(jsonl_path(), 0o600)
    return {"removed": removed, "kept": len(kept)}


def status_payload():
    ensure_audit_dir()
    events = all_events()
    selected_path = sqlite_path() if backend_name() == "sqlite" else jsonl_path()
    return {
        "ok": True,
        "enabled": audit_enabled(),
        "strict": strict_mode(),
        "backend": backend_name(),
        "path": str(selected_path),
        "audit_dir": str(audit_dir()),
        "audit_dir_mode": user_only_mode(audit_dir()),
        "path_mode": user_only_mode(selected_path),
        "record_count": len(events),
        "retention_days": retention_days(),
        "max_bytes": max_bytes(),
        "last_event": events[-1] if events else None,
    }


def diagnostics_payload():
    payload = status_payload()
    payload.pop("last_event", None)
    return payload
