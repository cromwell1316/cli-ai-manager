import sys
import types
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_tmux_quota_warm_path_polls_short_capture_until_markers(monkeypatch, tmp_path):
    import cli_profile_manager.quota as quota

    calls = []
    sleeps = []
    captures = [
        "Antigravity CLI 1.1.1\n>\n? for shortcuts\n",
        "Antigravity CLI 1.1.1\nDaily quota 94% remaining\n>\n",
    ]

    def fake_run(args, text=True, capture_output=True, timeout=5, check=False):
        calls.append(args)
        if "capture-pane" in args:
            return types.SimpleNamespace(returncode=0, stdout=captures.pop(0), stderr="")
        return types.SimpleNamespace(returncode=0, stdout="", stderr="")

    real_sleep = quota.time.sleep

    def fake_sleep(seconds):
        sleeps.append(seconds)
        real_sleep(seconds)

    monkeypatch.setattr(quota.shutil, "which", lambda name: f"/usr/bin/{name}" if name in ("tmux", "agy") else None)
    monkeypatch.setattr(quota.subprocess, "run", fake_run)
    monkeypatch.setattr(quota.time, "sleep", fake_sleep)
    monkeypatch.setenv("AI_MAN_QUOTA_POST_COMMAND_SECONDS", "1")
    monkeypatch.setenv("AI_MAN_TMUX_QUOTA_POLL_INTERVAL_SECONDS", "0.01")
    monkeypatch.setenv("AI_MAN_TMUX_QUOTA_SHORT_CAPTURE_LINES", "20")

    session = quota.TmuxQuotaSession("agy", ["agy"], {"HOME": str(tmp_path / "p1")}, str(tmp_path))
    session.ready = True
    session._cache_liveness(True)

    snapshot = session.snapshot(timeout_seconds=1)

    assert "Daily quota 94% remaining" in snapshot
    assert sleeps == [0.01]
    assert any("capture-pane" in call and "-20" in call for call in calls)
    assert not any("capture-pane" in call and "-240" in call for call in calls)
    assert not any("has-session" in call for call in calls)
    assert session.last_snapshot_metrics["capture_kind"] == "short"
    assert session.last_snapshot_metrics["marker_ready"] is True
    assert session.last_snapshot_metrics["captures"] == 2


def test_tmux_quota_warm_path_uses_long_capture_on_parser_miss(monkeypatch, tmp_path):
    import cli_profile_manager.quota as quota

    calls = []

    def fake_run(args, text=True, capture_output=True, timeout=5, check=False):
        calls.append(args)
        if "capture-pane" in args and "-240" in args:
            return types.SimpleNamespace(returncode=0, stdout="Antigravity layout without quota rows\n", stderr="")
        if "capture-pane" in args:
            return types.SimpleNamespace(returncode=0, stdout="Antigravity CLI 1.1.1\n>\n", stderr="")
        return types.SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(quota.shutil, "which", lambda name: f"/usr/bin/{name}" if name in ("tmux", "agy") else None)
    monkeypatch.setattr(quota.subprocess, "run", fake_run)
    monkeypatch.setenv("AI_MAN_QUOTA_POST_COMMAND_SECONDS", "0")

    session = quota.TmuxQuotaSession("agy", ["agy"], {"HOME": str(tmp_path / "p1")}, str(tmp_path))
    session.ready = True
    session._cache_liveness(True)

    snapshot = session.snapshot(timeout_seconds=1)

    assert snapshot == "Antigravity layout without quota rows\n"
    assert any("capture-pane" in call and "-80" in call for call in calls)
    assert any("capture-pane" in call and "-240" in call for call in calls)
    assert session.last_snapshot_metrics["capture_kind"] == "long"
    assert session.last_snapshot_metrics["marker_ready"] is False


def test_tmux_liveness_cache_reuses_recent_has_session_result(monkeypatch, tmp_path):
    import cli_profile_manager.quota as quota

    calls = []

    def fake_run(args, text=True, capture_output=True, timeout=5, check=False):
        calls.append(args)
        return types.SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(quota.shutil, "which", lambda name: f"/usr/bin/{name}" if name == "tmux" else None)
    monkeypatch.setattr(quota.subprocess, "run", fake_run)
    monkeypatch.setenv("AI_MAN_TMUX_QUOTA_LIVENESS_CACHE_SECONDS", "10")

    session = quota.TmuxQuotaSession("agy", ["agy"], {"HOME": str(tmp_path / "p1")}, str(tmp_path))

    assert session.is_alive() is True
    assert session.is_alive() is True
    assert sum(1 for call in calls if "has-session" in call) == 1


def test_persistent_session_snapshot_includes_warm_path_metrics(monkeypatch, tmp_path):
    import cli_profile_manager.quota as quota

    quota.close_persistent_quota_sessions()
    monkeypatch.setattr(quota, "resolve_quota_backend", lambda tool_key: "tmux")

    class FakeTmuxSession:
        backend = "tmux"

        def __init__(self, tool_key, command, env, cwd):
            self.tool_key = tool_key
            self.command = list(command)
            self.env = env.copy()
            self.cwd = cwd
            self.created_at = quota.time.time()
            self.last_used_at = self.created_at
            self.session_name = "ai_man_quota_agy_p1_fake"
            self.last_snapshot_metrics = {}

        def snapshot(self, timeout_seconds=quota.DEFAULT_TIMEOUT_SECONDS, idle_seconds=quota.DEFAULT_IDLE_SECONDS):
            self.last_snapshot_metrics = {"warm": True, "latency_ms": 12.5, "capture_kind": "short"}
            return "Usage 94% remaining"

        def is_alive(self):
            return True

        def close(self):
            pass

    monkeypatch.setattr(quota, "TmuxQuotaSession", FakeTmuxSession)

    quota.run_persistent_cli_quota_snapshot("agy", ["agy"], {"HOME": str(tmp_path / "p1")}, str(tmp_path))
    snapshot = quota.persistent_quota_sessions_snapshot("agy")

    assert snapshot["sessions"][0]["last_snapshot_metrics"] == {
        "warm": True,
        "latency_ms": 12.5,
        "capture_kind": "short",
    }
    quota.close_persistent_quota_sessions()
