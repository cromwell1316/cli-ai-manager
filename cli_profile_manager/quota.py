import os
import atexit
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


DEFAULT_COLS = 120
DEFAULT_ROWS = 40
DEFAULT_TIMEOUT_SECONDS = 20
DEFAULT_IDLE_SECONDS = 0.8
DEFAULT_STARTUP_SECONDS = 3.0
DEFAULT_POST_COMMAND_SECONDS = 4.0
DEFAULT_KEY_DELAY_SECONDS = 0.04
DEFAULT_AGY_STARTUP_SECONDS = 8.0
DEFAULT_AGY_POST_COMMAND_SECONDS = 8.0
PARSER_MISS_SESSION_INVALIDATION_THRESHOLD = 3


QUOTA_COMMANDS = {
    "agy": "/usage",
    "codex": "/status",
    "claude": "/usage",
}

AUTH_PATTERNS = (
    re.compile(r"\b(sign in|login required|not authenticated|please log in|please sign in)\b", re.I),
    re.compile(r"\bauthentication required\b", re.I),
)

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


def has_spinner_frame(text):
    return any(char in text[-200:] for char in SPINNER_CHARS)


def read_available(fd):
    chunks = []
    while True:
        ready, _, _ = select.select([fd], [], [], 0)
        if not ready:
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
        ready, _, _ = select.select([fd], [], [], 0.1)
        if ready:
            output.append(read_available(fd))
        current = "".join(output)
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
        ready, _, _ = select.select([fd], [], [], 0.1)
        if ready:
            output.append(read_available(fd))


def wait_after_command(fd, output, minimum_seconds):
    deadline = time.monotonic() + minimum_seconds
    while time.monotonic() < deadline:
        ready, _, _ = select.select([fd], [], [], 0.1)
        if ready:
            output.append(read_available(fd))


def send_interactive_command(fd, command, key_delay_seconds=DEFAULT_KEY_DELAY_SECONDS):
    text = f"\x15{command}\r"
    for ch in text:
        os.write(fd, ch.encode("utf-8"))
        if key_delay_seconds > 0:
            time.sleep(key_delay_seconds)


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


class PersistentQuotaSession:
    def __init__(self, tool_key, command, env, cwd):
        self.tool_key = tool_key
        self.command = list(command)
        self.env = env.copy()
        self.cwd = cwd
        self.proc = None
        self.master_fd = None
        self.lock = threading.Lock()

    def start(self, timeout_seconds=DEFAULT_TIMEOUT_SECONDS, idle_seconds=DEFAULT_IDLE_SECONDS):
        if os.name == "nt":
            raise QuotaProbeError("unsupported", "PTY quota probing is not supported on Windows yet")
        try:
            import pty
        except ImportError as e:
            raise QuotaProbeError("unsupported", "PTY support is not available") from e
        if shutil.which(self.command[0]) is None:
            raise QuotaProbeError("missing_cli", f"{self.command[0]} CLI is not installed or not in PATH")

        master_fd, slave_fd = pty.openpty()
        fcntl.ioctl(slave_fd, termios.TIOCSWINSZ, struct.pack("HHHH", DEFAULT_ROWS, DEFAULT_COLS, 0, 0))
        env = self.env.copy()
        env.setdefault("TERM", "xterm-256color")
        proc = subprocess.Popen(
            self.command,
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            cwd=self.cwd,
            env=env,
            start_new_session=True,
            close_fds=True,
        )
        os.close(slave_fd)
        output = []
        try:
            startup_default = DEFAULT_AGY_STARTUP_SECONDS if self.tool_key == "agy" else DEFAULT_STARTUP_SECONDS
            startup_seconds = float(os.environ.get("AI_MAN_QUOTA_STARTUP_SECONDS", startup_default))
            wait_for_startup(master_fd, output, max(0.0, startup_seconds))
            wait_for_idle(master_fd, output, idle_seconds, timeout_seconds)
            if proc.poll() is not None:
                raise QuotaProbeError("process_exit", "CLI process exited during startup", "".join(output))
        except Exception:
            terminate_process(proc, master_fd, output)
            try:
                os.close(master_fd)
            except OSError:
                pass
            raise
        self.proc = proc
        self.master_fd = master_fd

    def is_alive(self):
        return self.proc is not None and self.proc.poll() is None and self.master_fd is not None

    def snapshot(self, timeout_seconds=DEFAULT_TIMEOUT_SECONDS, idle_seconds=DEFAULT_IDLE_SECONDS):
        with self.lock:
            if not self.is_alive():
                self.close()
                self.start(timeout_seconds=timeout_seconds, idle_seconds=idle_seconds)
            read_available(self.master_fd)
            slash_command = quota_command_for(self.tool_key)
            if not slash_command:
                raise QuotaProbeError("unsupported", f"quota command is not configured for {self.tool_key}")
            key_delay_seconds = float(os.environ.get("AI_MAN_QUOTA_KEY_DELAY_SECONDS", DEFAULT_KEY_DELAY_SECONDS))
            output = []
            send_interactive_command(self.master_fd, slash_command, max(0.0, key_delay_seconds))
            post_command_default = DEFAULT_AGY_POST_COMMAND_SECONDS if self.tool_key == "agy" else DEFAULT_POST_COMMAND_SECONDS
            post_command_seconds = float(os.environ.get("AI_MAN_QUOTA_POST_COMMAND_SECONDS", post_command_default))
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
        if proc is None or master_fd is None:
            return
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
INVALIDATING_QUOTA_STATES = {"timeout", "process_exit"}


def persistent_quota_session_key(tool_key, command, env, cwd):
    home = env.get("HOME")
    return (
        tool_key,
        tuple(command),
        os.path.abspath(cwd),
        os.path.abspath(home) if home else None,
        env.get("CODEX_HOME"),
        env.get("CLAUDE_CONFIG_DIR"),
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


def persistent_quota_sessions_snapshot(tool_key=None):
    with PERSISTENT_QUOTA_LOCK:
        sessions = []
        for key, session in PERSISTENT_QUOTA_SESSIONS.items():
            if tool_key is not None and key[0] != tool_key:
                continue
            sessions.append({
                "tool": key[0],
                "command": list(key[1]),
                "cwd": key[2],
                "home": key[3],
                "codex_home": key[4],
                "claude_config_dir": key[5],
                "alive": session.is_alive(),
                "parser_misses": PERSISTENT_QUOTA_PARSER_MISSES.get(key, 0),
            })
    return {
        "count": len(sessions),
        "sessions": sessions,
    }


atexit.register(close_persistent_quota_sessions)


def run_persistent_cli_quota_snapshot(tool_key, command, env, cwd, timeout_seconds=DEFAULT_TIMEOUT_SECONDS, idle_seconds=DEFAULT_IDLE_SECONDS):
    key = persistent_quota_session_key(tool_key, command, env, cwd)
    with PERSISTENT_QUOTA_LOCK:
        session = PERSISTENT_QUOTA_SESSIONS.get(key)
        if session is None:
            session = PersistentQuotaSession(tool_key, command, env, cwd)
            PERSISTENT_QUOTA_SESSIONS[key] = session
            logging.debug("quota session create tool=%s cwd=%s home=%s", tool_key, cwd, env.get("HOME"))
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
                "quota session invalidate tool=%s cwd=%s home=%s reason=%s",
                tool_key,
                cwd,
                env.get("HOME"),
                getattr(e, "state", type(e).__name__),
            )
            session.close()
        raise


def record_persistent_parser_result(tool_key, command, env, cwd, quota):
    key = persistent_quota_session_key(tool_key, command, env, cwd)
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
    logging.debug("quota session invalidate tool=%s cwd=%s home=%s reason=parser_miss", tool_key, cwd, env.get("HOME"))
    session.close()


def run_cli_quota_snapshot(tool_key, command, env, cwd, timeout_seconds=DEFAULT_TIMEOUT_SECONDS, idle_seconds=DEFAULT_IDLE_SECONDS):
    if os.name == "nt":
        raise QuotaProbeError("unsupported", "PTY quota probing is not supported on Windows yet")
    try:
        import pty
    except ImportError as e:
        raise QuotaProbeError("unsupported", "PTY support is not available") from e
    if shutil.which(command[0]) is None:
        raise QuotaProbeError("missing_cli", f"{command[0]} CLI is not installed or not in PATH")

    master_fd, slave_fd = pty.openpty()
    fcntl.ioctl(slave_fd, termios.TIOCSWINSZ, struct.pack("HHHH", DEFAULT_ROWS, DEFAULT_COLS, 0, 0))
    env = env.copy()
    env.setdefault("TERM", "xterm-256color")
    proc = subprocess.Popen(
        command,
        stdin=slave_fd,
        stdout=slave_fd,
        stderr=slave_fd,
        cwd=cwd,
        env=env,
        start_new_session=True,
        close_fds=True,
    )
    os.close(slave_fd)
    output = []
    try:
        startup_default = DEFAULT_AGY_STARTUP_SECONDS if tool_key == "agy" else DEFAULT_STARTUP_SECONDS
        startup_seconds = float(os.environ.get("AI_MAN_QUOTA_STARTUP_SECONDS", startup_default))
        wait_for_startup(master_fd, output, max(0.0, startup_seconds))
        wait_for_idle(master_fd, output, idle_seconds, timeout_seconds)
        slash_command = quota_command_for(tool_key)
        if not slash_command:
            raise QuotaProbeError("unsupported", f"quota command is not configured for {tool_key}")
        key_delay_seconds = float(os.environ.get("AI_MAN_QUOTA_KEY_DELAY_SECONDS", DEFAULT_KEY_DELAY_SECONDS))
        send_interactive_command(master_fd, slash_command, max(0.0, key_delay_seconds))
        post_command_default = DEFAULT_AGY_POST_COMMAND_SECONDS if tool_key == "agy" else DEFAULT_POST_COMMAND_SECONDS
        post_command_seconds = float(os.environ.get("AI_MAN_QUOTA_POST_COMMAND_SECONDS", post_command_default))
        wait_after_command(master_fd, output, max(0.0, post_command_seconds))
        return wait_for_idle(master_fd, output, idle_seconds, timeout_seconds)
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
        if diagnostic:
            result["diagnostic_summary"] = diagnostic
    return result


def quota_payload(tool_key, profile_name, command, env, cwd, timeout_seconds=DEFAULT_TIMEOUT_SECONDS, runner=run_cli_quota_snapshot):
    try:
        screen_text = runner(tool_key, command, env, cwd, timeout_seconds=timeout_seconds)
        quota = parse_quota(tool_key, screen_text)
    except QuotaProbeError as e:
        quota = {
            "state": e.state,
            "source_command": quota_command_for(tool_key),
            "limits": {},
            "warnings": [str(e)],
        }
    if runner is run_persistent_cli_quota_snapshot:
        record_persistent_parser_result(tool_key, command, env, cwd, quota)
    return {
        "tool": tool_key,
        "profile": profile_name,
        "quota": quota,
    }
