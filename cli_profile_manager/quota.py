import os
import re
import select
import shutil
import signal
import subprocess
import fcntl
import struct
import termios
import time


DEFAULT_COLS = 120
DEFAULT_ROWS = 40
DEFAULT_TIMEOUT_SECONDS = 20
DEFAULT_IDLE_SECONDS = 0.8
DEFAULT_STARTUP_SECONDS = 3.0


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


def agy_model_name_from_line(line):
    if "quota pools" in line.lower() or "," in line or len(line) > 72:
        return None
    match = re.search(r"\b(?:Gemini|Claude|GPT)\s+[A-Za-z0-9 .()/-]+", line)
    if not match:
        return None
    return match.group(0).strip()


def parse_codex_quota(screen_text):
    text = "\n".join(compact_lines(screen_text))
    quota = {
        "state": "available",
        "source_command": "/status",
        "limits": {},
        "raw_summary": text,
    }
    five_hour = parse_percent_limit(text, (
        r"5\s*h(?:our)?\s+limit\b.*?(\d{1,3})\s*%\s*(?:left|remaining)?",
        r"(\d{1,3})\s*%\s*(?:left|remaining).*?5\s*h(?:our)?\s+limit\b",
    ))
    weekly = parse_percent_limit(text, (
        r"(?:7\s*day|weekly)\b.*?(\d{1,3})\s*%\s*(?:left|remaining)?",
        r"(\d{1,3})\s*%\s*(?:left|remaining).*?(?:7\s*day|weekly)\b",
    ))
    reset = parse_reset_text(text)
    if five_hour is not None:
        quota["limits"]["five_hour"] = {"percent_left": five_hour}
        if reset:
            quota["limits"]["five_hour"]["resets"] = reset
    if weekly is not None:
        quota["limits"]["weekly"] = {"percent_left": weekly}
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
        model_name = agy_model_name_from_line(line)
        if model_name:
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
        r"(?:daily|today|gemini)\b.*?(\d{1,3})\s*%\s*(?:left|remaining|used)?",
        r"(\d{1,3})\s*%\s*(?:left|remaining).*?(?:daily|today|gemini)\b",
    ))
    reset = parse_reset_text(text)
    if daily is not None:
        quota["limits"]["daily"] = {"percent": daily}
        if reset:
            quota["limits"]["daily"]["resets"] = reset
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
        startup_seconds = float(os.environ.get("AI_MAN_QUOTA_STARTUP_SECONDS", DEFAULT_STARTUP_SECONDS))
        wait_for_startup(master_fd, output, max(0.0, startup_seconds))
        wait_for_idle(master_fd, output, idle_seconds, timeout_seconds)
        slash_command = quota_command_for(tool_key)
        if not slash_command:
            raise QuotaProbeError("unsupported", f"quota command is not configured for {tool_key}")
        os.write(master_fd, f"{slash_command}\r".encode("utf-8"))
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
        result["state"] = "unknown"
        result["warnings"] = ["quota output was captured but no known quota fields matched"]
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
    return {
        "tool": tool_key,
        "profile": profile_name,
        "quota": quota,
    }
