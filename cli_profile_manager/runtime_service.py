import contextlib
import io
import json
import os
import signal
import socket
import stat
import sys
import time
from pathlib import Path

from . import metadata, paths
from . import audit


PROTOCOL_VERSION = 1
DEFAULT_CLIENT_TIMEOUT_SECONDS = 0.75
MAX_REQUEST_BYTES = 1024 * 1024
RUNTIME_DIR_NAME = "runtime"
SOCKET_NAME = "service.sock"
PID_NAME = "service.pid"
LOG_NAME = "service.log"
LAST_INVALIDATION_NAME = "last_invalidation.json"
READ_ONLY_COMMANDS = {"config", "diagnostics", "list", "status"}
MUTATING_COMMANDS = {"audit", "clear", "export", "import", "label", "login", "sync"}
INELIGIBLE_COMMANDS = sorted(MUTATING_COMMANDS | {"launch", "quota", "service"})
RUNTIME_STATE_OWNERSHIP = {
    "metadata": "profiles_metadata.json labels and profile annotations",
    "paths": "environment-resolved profile roots and metadata directory",
    "profiles": "filesystem profile discovery and credential presence",
    "diagnostics": "safe runtime diagnostics assembled per request",
    "command_snapshot": "per-command read model for list/status/config/diagnostics",
    "audit": "local audit event backends and retention state",
}
NEVER_CACHE_STATE = (
    "raw credential contents",
    "raw PTY buffers",
    "unredacted accounts",
    "safety decisions for future commands",
)
MUTATION_INVALIDATION_CONTRACT = {
    "import": ("credentials", "profiles", "command_snapshot", "diagnostics"),
    "export": ("audit", "diagnostics"),
    "label": ("metadata", "command_snapshot", "diagnostics"),
    "clear": ("credentials", "profiles", "metadata", "command_snapshot", "quota", "diagnostics"),
    "login": ("credentials", "profiles", "command_snapshot", "quota", "diagnostics"),
    "sync": ("credentials", "profiles", "metadata", "command_snapshot", "quota", "diagnostics"),
    "audit:purge": ("audit", "diagnostics"),
    "audit:compact": ("audit", "diagnostics"),
}


class ServiceError(RuntimeError):
    pass


def runtime_dir():
    return Path(metadata.METADATA_DIR) / RUNTIME_DIR_NAME


def socket_path():
    return runtime_dir() / SOCKET_NAME


def pid_path():
    return runtime_dir() / PID_NAME


def log_path():
    return runtime_dir() / LOG_NAME


def last_invalidation_path():
    return runtime_dir() / LAST_INVALIDATION_NAME


def ensure_runtime_dir():
    directory = runtime_dir()
    directory.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(directory, 0o700)
    except OSError:
        pass
    return directory


def _user_only_mode(path):
    try:
        mode = stat.S_IMODE(os.stat(path).st_mode)
    except OSError:
        return None
    return oct(mode)


def _read_pid():
    try:
        return int(pid_path().read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None


def _process_alive(pid):
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def cleanup_stale_files():
    pid = _read_pid()
    if pid and _process_alive(pid):
        return False
    removed = False
    for path in (socket_path(), pid_path()):
        try:
            path.unlink()
            removed = True
        except FileNotFoundError:
            pass
        except OSError:
            pass
    if removed:
        audit.record("runtime_service", "completed", command="service", result="stale_cleaned", details={"action": "cleanup_stale"})
    return removed


def _read_last_invalidation():
    try:
        payload = json.loads(last_invalidation_path().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _write_last_invalidation(payload):
    ensure_runtime_dir()
    path = last_invalidation_path()
    tmp_path = path.with_name(f"{path.name}.tmp-{os.getpid()}")
    tmp_path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    os.replace(tmp_path, path)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def invalidation_payload(reason, domains, command=None, generation=None):
    payload = {
        "reason": reason or "mutation",
        "domains": sorted(set(domains or ())),
        "command": command,
        "generation": generation,
        "time": time.time(),
    }
    return payload


def mutation_invalidation(argv):
    if not argv:
        return None
    command = argv[0]
    if "--dry-run" in argv:
        return None
    if command == "audit":
        action = argv[1] if len(argv) > 1 else "status"
        key = f"audit:{action}"
    else:
        key = command
    domains = MUTATION_INVALIDATION_CONTRACT.get(key)
    if not domains:
        return None
    return {
        "reason": key,
        "domains": list(domains),
        "command": command,
    }


def runtime_contract_payload():
    return {
        "state_ownership": dict(RUNTIME_STATE_OWNERSHIP),
        "never_cache": list(NEVER_CACHE_STATE),
        "eligible_commands": sorted(READ_ONLY_COMMANDS),
        "ineligible_commands": list(INELIGIBLE_COMMANDS),
        "mutation_invalidation": {key: list(value) for key, value in MUTATION_INVALIDATION_CONTRACT.items()},
    }


def service_status():
    ensure_runtime_dir()
    pid = _read_pid()
    socket_exists = socket_path().exists()
    alive = _process_alive(pid)
    stale = bool((pid or socket_exists) and not alive)
    last_invalidation = _read_last_invalidation()
    return {
        "enabled_env": service_mode_enabled(),
        "running": bool(alive and socket_exists),
        "pid": pid,
        "stale": stale,
        "available": bool(alive and socket_exists and not stale),
        "unavailable_reason": None if alive and socket_exists and not stale else ("stale_runtime_files" if stale else "not_running"),
        "recovery_hint": "run service restart or service stop to clean stale runtime files" if stale else None,
        "socket_path": str(socket_path()),
        "pid_path": str(pid_path()),
        "log_path": str(log_path()),
        "runtime_dir": str(runtime_dir()),
        "runtime_dir_mode": _user_only_mode(runtime_dir()),
        "socket_mode": _user_only_mode(socket_path()) if socket_exists else None,
        "protocol_version": PROTOCOL_VERSION,
        "last_invalidation": last_invalidation,
        "contract": runtime_contract_payload(),
    }


def service_mode_enabled(env=None):
    env = os.environ if env is None else env
    return str(env.get("AI_MAN_SERVICE", "")).lower() in ("1", "true", "yes", "on")


def eligible_argv(argv):
    if not argv:
        return False
    command = argv[0]
    if command not in READ_ONLY_COMMANDS:
        return False
    if command == "service":
        return False
    if command in ("list", "status") and "--quota" in argv:
        return False
    return True


def mutates_runtime_state(argv):
    return mutation_invalidation(argv) is not None


def encode_message(payload):
    return (json.dumps(payload, separators=(",", ":")) + "\n").encode("utf-8")


def read_message(stream):
    data = stream.readline(MAX_REQUEST_BYTES + 1)
    if len(data) > MAX_REQUEST_BYTES:
        raise ServiceError("request too large")
    if not data:
        raise ServiceError("empty request")
    try:
        payload = json.loads(data.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise ServiceError(f"invalid json: {exc}") from exc
    if not isinstance(payload, dict):
        raise ServiceError("request must be a JSON object")
    return payload


def request(payload, timeout_seconds=DEFAULT_CLIENT_TIMEOUT_SECONDS):
    sock_path = socket_path()
    if not sock_path.exists():
        raise ServiceError("service socket is not present")
    audit.record("runtime_service", "attempted", command="service", details={"action": payload.get("action")})
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.settimeout(timeout_seconds)
        client.connect(str(sock_path))
        client.sendall(encode_message(payload))
        with client.makefile("rb") as stream:
            response = read_message(stream)
    audit.record(
        "runtime_service",
        "completed" if response.get("ok") else "failed",
        command="service",
        result="succeeded" if response.get("ok") else "failed",
        details={"action": payload.get("action"), "error": response.get("error")},
    )
    return response


def execute_argv(argv):
    from . import cli

    stdout = io.StringIO()
    stderr = io.StringIO()
    old_service = os.environ.get("AI_MAN_SERVICE")
    os.environ["AI_MAN_SERVICE"] = "0"
    try:
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            rc = cli.run_cli(list(argv))
        return {
            "ok": True,
            "returncode": 0 if rc is None else rc,
            "stdout": stdout.getvalue(),
            "stderr": stderr.getvalue(),
        }
    finally:
        if old_service is None:
            os.environ.pop("AI_MAN_SERVICE", None)
        else:
            os.environ["AI_MAN_SERVICE"] = old_service


class RuntimeState:
    def __init__(self):
        self.started_at = time.time()
        self.generation = 0
        self.requests = 0
        self.last_invalidation = _read_last_invalidation()

    def invalidate(self, reason=None, domains=None, command=None):
        self.generation += 1
        self.last_invalidation = invalidation_payload(reason, domains, command, self.generation)
        _write_last_invalidation(self.last_invalidation)
        audit.record(
            "runtime_service",
            "completed",
            command="service",
            result="invalidated",
            details={
                "action": "invalidate",
                "generation": self.generation,
                "reason": self.last_invalidation["reason"],
                "domains": self.last_invalidation["domains"],
                "source_command": command,
            },
        )

    def health(self):
        return {
            "ok": True,
            "pid": os.getpid(),
            "started_at": self.started_at,
            "uptime_seconds": round(time.time() - self.started_at, 3),
            "generation": self.generation,
            "requests": self.requests,
            "last_invalidation": self.last_invalidation,
            "contract": runtime_contract_payload(),
        }


def _validate_peer(sock):
    if not hasattr(socket, "SO_PEERCRED"):
        return True
    try:
        creds = sock.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12)
    except OSError:
        return False
    pid = int.from_bytes(creds[0:4], sys.byteorder)
    uid = int.from_bytes(creds[4:8], sys.byteorder)
    return pid > 0 and uid == os.getuid()


def handle_payload(payload, state):
    state.requests += 1
    audit.record("runtime_service", "attempted", command="service", details={"action": payload.get("action"), "request_count": state.requests})
    if payload.get("version") != PROTOCOL_VERSION:
        return {"ok": False, "error": {"type": "protocol_error", "message": "unsupported protocol version"}}
    action = payload.get("action")
    if action == "health":
        return state.health()
    if action == "invalidate":
        domains = payload.get("domains") or []
        if not isinstance(domains, list) or not all(isinstance(item, str) for item in domains):
            return {"ok": False, "error": {"type": "usage_error", "message": "domains must be a string list"}}
        reason = payload.get("reason")
        command = payload.get("command")
        state.invalidate(
            reason=reason if isinstance(reason, str) else None,
            domains=domains,
            command=command if isinstance(command, str) else None,
        )
        return {"ok": True, "generation": state.generation, "last_invalidation": state.last_invalidation}
    if action == "shutdown":
        return {"ok": True, "shutdown": True}
    if action == "run":
        argv = payload.get("argv")
        if not isinstance(argv, list) or not all(isinstance(item, str) for item in argv):
            return {"ok": False, "error": {"type": "usage_error", "message": "argv must be a string list"}}
        if not eligible_argv(argv):
            return {"ok": False, "error": {"type": "not_eligible", "message": "command is not service eligible"}}
        result = execute_argv(argv)
        result["generation"] = state.generation
        return result
    return {"ok": False, "error": {"type": "usage_error", "message": "unknown action"}}


def serve_forever():
    ensure_runtime_dir()
    cleanup_stale_files()
    if socket_path().exists():
        raise ServiceError(f"service socket already exists: {socket_path()}")
    state = RuntimeState()
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        old_umask = os.umask(0o177)
        try:
            server.bind(str(socket_path()))
        finally:
            os.umask(old_umask)
        try:
            os.chmod(socket_path(), 0o600)
        except OSError:
            pass
        server.listen(16)
        pid_path().write_text(str(os.getpid()), encoding="utf-8")
        try:
            os.chmod(pid_path(), 0o600)
        except OSError:
            pass
        running = True
        while running:
            conn, _ = server.accept()
            with conn:
                with conn.makefile("rb") as stream:
                    try:
                        if not _validate_peer(conn):
                            response = {"ok": False, "error": {"type": "permission_denied", "message": "unexpected peer user"}}
                        else:
                            response = handle_payload(read_message(stream), state)
                    except Exception as exc:
                        response = {"ok": False, "error": {"type": "runtime_error", "message": str(exc)}}
                    if response.get("shutdown"):
                        running = False
                    conn.sendall(encode_message(response))
    finally:
        server.close()
        for path in (socket_path(), pid_path()):
            try:
                path.unlink()
            except FileNotFoundError:
                pass
            except OSError:
                pass


def start_service(script_path):
    ensure_runtime_dir()
    cleanup_stale_files()
    current = service_status()
    if current["running"]:
        audit.record("runtime_service", "skipped", command="service", result="already_running", details={"action": "start"})
        return {**current, "ok": True, "started": False}
    log_file = open(log_path(), "ab", buffering=0)
    try:
        proc = __import__("subprocess").Popen(
            [sys.executable, str(script_path), "service", "run"],
            stdin=__import__("subprocess").DEVNULL,
            stdout=log_file,
            stderr=log_file,
            close_fds=True,
            start_new_session=True,
        )
    finally:
        log_file.close()
    deadline = time.time() + 5.0
    while time.time() < deadline:
        status = service_status()
        if status["running"]:
            audit.record("runtime_service", "completed", command="service", result="succeeded", details={"action": "start", "pid": status.get("pid")})
            return {**status, "ok": True, "started": True}
        if proc.poll() is not None:
            break
        time.sleep(0.05)
    audit.record("runtime_service", "failed", command="service", result="failed", error_class="startup_timeout", details={"action": "start"})
    return {**service_status(), "ok": False, "started": False, "error": "service did not become ready"}


def stop_service(timeout_seconds=3.0):
    status = service_status()
    if not status["pid"] and not socket_path().exists():
        cleanup_stale_files()
        audit.record("runtime_service", "skipped", command="service", result="not_running", details={"action": "stop"})
        return {**service_status(), "ok": True, "stopped": False}
    if status["running"]:
        try:
            request({"version": PROTOCOL_VERSION, "action": "shutdown"}, timeout_seconds=0.5)
        except Exception:
            pass
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            if not _process_alive(status["pid"]):
                cleanup_stale_files()
                return {**service_status(), "ok": True, "stopped": True}
            time.sleep(0.05)
        try:
            os.kill(status["pid"], signal.SIGTERM)
        except OSError:
            pass
    cleanup_stale_files()
    return {**service_status(), "ok": True, "stopped": True}


def service_health():
    response = request({"version": PROTOCOL_VERSION, "action": "health"}, timeout_seconds=0.5)
    return response if response.get("ok") else None


def invalidate_service():
    return invalidate_service_for(reason="mutation", domains=(), command=None)


def invalidate_service_for(reason=None, domains=(), command=None):
    payload = invalidation_payload(reason, domains, command, generation=None)
    try:
        _write_last_invalidation(payload)
    except OSError as exc:
        audit.record(
            "runtime_service",
            "skipped",
            command=command or "service",
            result="diagnostic_write_failed",
            error_class=type(exc).__name__,
            details={"action": "invalidate", "reason": payload["reason"], "domains": payload["domains"]},
        )
    audit.record(
        "runtime_service",
        "attempted",
        command=command or "service",
        details={"action": "invalidate", "reason": payload["reason"], "domains": payload["domains"]},
    )
    try:
        response = request(
            {
                "version": PROTOCOL_VERSION,
                "action": "invalidate",
                "reason": payload["reason"],
                "domains": payload["domains"],
                "command": command,
            },
            timeout_seconds=0.25,
        )
    except Exception as exc:
        audit.record(
            "runtime_service",
            "skipped",
            command=command or "service",
            result="unavailable",
            error_class=type(exc).__name__,
            details={"action": "invalidate", "reason": payload["reason"], "domains": payload["domains"]},
        )
        return None
    return response


def run_via_service(argv, timeout_seconds=DEFAULT_CLIENT_TIMEOUT_SECONDS):
    return request({"version": PROTOCOL_VERSION, "action": "run", "argv": list(argv)}, timeout_seconds=timeout_seconds)
