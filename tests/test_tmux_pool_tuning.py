import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_tmux_pool_concurrency_settings(monkeypatch):
    import cli_profile_manager.quota as quota

    monkeypatch.setenv("AI_MAN_TMUX_QUOTA_COLD_START_CONCURRENCY", "3")
    monkeypatch.setenv("AI_MAN_TMUX_QUOTA_WARM_SNAPSHOT_CONCURRENCY", "7")

    assert quota.tmux_cold_start_concurrency() == 3
    assert quota.tmux_warm_snapshot_concurrency() == 7

    monkeypatch.setenv("AI_MAN_TMUX_QUOTA_COLD_START_CONCURRENCY", "bad")
    monkeypatch.setenv("AI_MAN_TMUX_QUOTA_WARM_SNAPSHOT_CONCURRENCY", "0")

    assert quota.tmux_cold_start_concurrency() == quota.DEFAULT_TMUX_COLD_START_CONCURRENCY
    assert quota.tmux_warm_snapshot_concurrency() == 1


def test_evict_skips_starting_dead_tmux_session(monkeypatch, tmp_path):
    import cli_profile_manager.quota as quota

    quota.close_persistent_quota_sessions()
    monkeypatch.setenv("AI_MAN_QUOTA_SESSION_TTL_SECONDS", "1")
    session = quota.TmuxQuotaSession("agy", ["agy"], {"HOME": str(tmp_path / "p1")}, str(tmp_path))
    session.starting = True
    session.last_used_at = 1.0
    session.last_alive_result = False
    key = quota.persistent_quota_session_key("agy", ["agy"], session.env, session.cwd, "tmux")

    with quota.PERSISTENT_QUOTA_LOCK:
        quota.PERSISTENT_QUOTA_SESSIONS[key] = session

    assert quota.evict_persistent_quota_sessions(now=100.0) == 0
    assert quota.persistent_quota_sessions_snapshot("agy")["count"] == 1
    quota.close_persistent_quota_sessions()


def test_tmux_close_refuses_non_manager_owned_session(monkeypatch, tmp_path):
    import cli_profile_manager.quota as quota

    calls = []
    session = quota.TmuxQuotaSession("agy", ["agy"], {"HOME": str(tmp_path / "p1")}, str(tmp_path))
    session.session_name = "user-owned-session"
    monkeypatch.setattr(session, "_run_tmux", lambda args, check=True, timeout=5: calls.append(args))

    session.close()

    assert calls == []
    assert session.lifecycle_metrics["close_count"] == 0


def test_external_tmux_kill_invalidates_pooled_session(monkeypatch, tmp_path):
    import cli_profile_manager.quota as quota

    quota.close_persistent_quota_sessions()
    monkeypatch.setattr(quota, "resolve_quota_backend", lambda tool_key: "tmux")

    created = []

    class ExternallyKilledSession:
        backend = "tmux"

        def __init__(self, tool_key, command, env, cwd):
            self.tool_key = tool_key
            self.command = list(command)
            self.env = env.copy()
            self.cwd = cwd
            self.created_at = quota.time.time()
            self.last_used_at = self.created_at
            self.session_name = f"{quota.TMUX_QUOTA_SESSION_PREFIX}agy_p1_fake"
            self.starting = False
            self.ready = True
            self.closed = False
            created.append(self)

        def snapshot(self, timeout_seconds=quota.DEFAULT_TIMEOUT_SECONDS, idle_seconds=quota.DEFAULT_IDLE_SECONDS):
            raise quota.QuotaProbeError("process_exit", "tmux quota session exited during quota probe")

        def is_alive(self):
            return False

        def close(self):
            self.closed = True

    monkeypatch.setattr(quota, "TmuxQuotaSession", ExternallyKilledSession)
    env = {"HOME": str(tmp_path / "p1")}

    try:
        quota.run_persistent_cli_quota_snapshot("agy", ["agy"], env, str(tmp_path))
    except quota.QuotaProbeError as exc:
        assert exc.state == "process_exit"
    else:
        raise AssertionError("expected process_exit")

    assert created[0].closed is True
    assert quota.persistent_quota_sessions_snapshot("agy")["count"] == 0


def test_persistent_snapshot_reports_pool_and_lifecycle_metrics(monkeypatch, tmp_path):
    import cli_profile_manager.quota as quota

    quota.close_persistent_quota_sessions()
    monkeypatch.setenv("AI_MAN_TMUX_QUOTA_COLD_START_CONCURRENCY", "2")
    monkeypatch.setenv("AI_MAN_TMUX_QUOTA_WARM_SNAPSHOT_CONCURRENCY", "5")

    session = quota.TmuxQuotaSession("agy", ["agy"], {"HOME": str(tmp_path / "p1")}, str(tmp_path))
    session.ready = True
    session.lifecycle_metrics["startup_count"] = 1
    session.last_snapshot_metrics = {"warm": True, "latency_ms": 10.5}
    session._cache_liveness(True)
    key = quota.persistent_quota_session_key("agy", ["agy"], session.env, session.cwd, "tmux")

    with quota.PERSISTENT_QUOTA_LOCK:
        quota.PERSISTENT_QUOTA_SESSIONS[key] = session

    snapshot = quota.persistent_quota_sessions_snapshot("agy")

    assert snapshot["pool"]["tmux_cold_start_concurrency"] == 2
    assert snapshot["pool"]["tmux_warm_snapshot_concurrency"] == 5
    assert snapshot["pool"]["by_backend"] == {"tmux": 1}
    assert snapshot["pool"]["ready"] == 1
    assert snapshot["sessions"][0]["manager_owned"] is True
    assert snapshot["sessions"][0]["lifecycle_metrics"]["startup_count"] == 1
    assert snapshot["sessions"][0]["last_snapshot_metrics"]["warm"] is True
    quota.close_persistent_quota_sessions()
