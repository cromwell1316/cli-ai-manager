import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def config_env(tmp_path):
    env = os.environ.copy()
    env.update({
        "AI_MAN_AGY_HOME": str(tmp_path / "agy-homes"),
        "AI_MAN_CODEX_HOME": str(tmp_path / "codex-homes"),
        "AI_MAN_CLAUDE_HOME": str(tmp_path / "claude-homes"),
        "AI_MAN_METADATA_DIR": str(tmp_path / "metadata"),
        "AI_MAN_WSL_HOME": str(tmp_path / "wsl"),
        "AI_MAN_WINDOWS_HOME": str(tmp_path / "windows"),
    })
    return env


def test_effective_config_fast_path_does_not_resolve_live_process_backend(monkeypatch, tmp_path):
    from cli_profile_manager import config, process_policy

    monkeypatch.setenv("AI_MAN_AGY_HOME", str(tmp_path / "agy-homes"))
    monkeypatch.setenv("AI_MAN_CODEX_HOME", str(tmp_path / "codex-homes"))
    monkeypatch.setenv("AI_MAN_CLAUDE_HOME", str(tmp_path / "claude-homes"))
    monkeypatch.setenv("AI_MAN_METADATA_DIR", str(tmp_path / "metadata"))
    monkeypatch.setenv("AI_MAN_WSL_HOME", str(tmp_path / "wsl"))
    monkeypatch.setenv("AI_MAN_WINDOWS_HOME", str(tmp_path / "windows"))
    monkeypatch.setenv("AI_MAN_PROCESS_MEMORY_MB", "bad")

    def fail_select_backend(*args, **kwargs):
        raise AssertionError("config fast path must not resolve live process backend")

    monkeypatch.setattr(process_policy, "select_backend", fail_select_backend)

    payload = config.effective_config_payload(include_sources=True)

    assert payload["profile_roots"]["agy"] == str(tmp_path / "agy-homes")
    assert payload["process_limits"]["launch"]["backend"] == "deferred"
    assert payload["config_health"]["mode"] == "fast"
    assert payload["config_health"]["live_checks"] is False
    assert any("AI_MAN_PROCESS_MEMORY_MB" in warning for warning in payload["warnings"])


def test_config_health_payload_resolves_live_process_backend(monkeypatch, tmp_path):
    from cli_profile_manager import config, process_policy

    monkeypatch.setenv("AI_MAN_AGY_HOME", str(tmp_path / "agy-homes"))
    monkeypatch.setenv("AI_MAN_CODEX_HOME", str(tmp_path / "codex-homes"))
    monkeypatch.setenv("AI_MAN_CLAUDE_HOME", str(tmp_path / "claude-homes"))
    monkeypatch.setenv("AI_MAN_METADATA_DIR", str(tmp_path / "metadata"))
    monkeypatch.setenv("AI_MAN_WSL_HOME", str(tmp_path / "wsl"))
    monkeypatch.setenv("AI_MAN_WINDOWS_HOME", str(tmp_path / "windows"))
    monkeypatch.setattr(process_policy, "select_backend", lambda policy, needs_pty=False: "live-test-backend")

    payload = config.config_health_payload()

    assert payload["health"]["mode"] == "health"
    assert payload["health"]["live_checks"] is True
    assert payload["process_limits"]["launch"]["backend"] == "live-test-backend"
    assert payload["process_limits"]["quota"]["backend"] == "live-test-backend"


def test_fast_diagnostics_does_not_resolve_live_process_backend(monkeypatch, tmp_path):
    from cli_profile_manager import diagnostics, process_policy

    monkeypatch.setenv("AI_MAN_AGY_HOME", str(tmp_path / "agy-homes"))
    monkeypatch.setenv("AI_MAN_CODEX_HOME", str(tmp_path / "codex-homes"))
    monkeypatch.setenv("AI_MAN_CLAUDE_HOME", str(tmp_path / "claude-homes"))
    monkeypatch.setenv("AI_MAN_METADATA_DIR", str(tmp_path / "metadata"))
    monkeypatch.setenv("AI_MAN_WSL_HOME", str(tmp_path / "wsl"))
    monkeypatch.setenv("AI_MAN_WINDOWS_HOME", str(tmp_path / "windows"))

    def fail_select_backend(*args, **kwargs):
        raise AssertionError("fast diagnostics must not resolve live process backend")

    monkeypatch.setattr(process_policy, "select_backend", fail_select_backend)

    payload = diagnostics.diagnostics_payload(
        "agy",
        status_provider=lambda tool, num: None,
        profile_index_provider=lambda tool: {
            "occupied_profiles": [],
            "display_profiles": [1],
        },
        mode="fast",
    )

    assert payload["mode"] == "fast"
    assert payload["config_health"]["mode"] == "fast"
    assert payload["config_health"]["live_checks"] is False
    assert payload["process_limits"]["systemd_user_scope_check"] == "skipped_fast_diagnostics"
    assert payload["process_limits"]["policies"]["launch"]["backend"] == "systemd-run-check-skipped"


def test_deep_diagnostics_keeps_live_config_health(monkeypatch, tmp_path):
    from cli_profile_manager import diagnostics, process_policy

    monkeypatch.setenv("AI_MAN_AGY_HOME", str(tmp_path / "agy-homes"))
    monkeypatch.setenv("AI_MAN_CODEX_HOME", str(tmp_path / "codex-homes"))
    monkeypatch.setenv("AI_MAN_CLAUDE_HOME", str(tmp_path / "claude-homes"))
    monkeypatch.setenv("AI_MAN_METADATA_DIR", str(tmp_path / "metadata"))
    monkeypatch.setenv("AI_MAN_WSL_HOME", str(tmp_path / "wsl"))
    monkeypatch.setenv("AI_MAN_WINDOWS_HOME", str(tmp_path / "windows"))
    monkeypatch.setattr(process_policy, "select_backend", lambda policy, needs_pty=False: "live-test-backend")

    payload = diagnostics.diagnostics_payload(
        "agy",
        status_provider=lambda tool, num: None,
        profile_index_provider=lambda tool: {
            "occupied_profiles": [],
            "display_profiles": [1],
        },
        mode="deep",
    )

    assert payload["mode"] == "deep"
    assert payload["config_health"]["mode"] == "health"
    assert payload["config_health"]["live_checks"] is True
    assert payload["process_limits"]["policies"]["launch"]["backend"] == "live-test-backend"


def test_config_show_json_stays_fast_and_redacted(monkeypatch, tmp_path):
    env = config_env(tmp_path)
    env.update({
        "AI_MAN_AGY_QUOTA_COMMAND": "sk-test-secret",
        "AI_MAN_INTERACTIVE_QUOTA_TIMEOUT": "0",
    })

    completed = subprocess.run(
        [sys.executable, str(ROOT / "profile_manager.py"), "config", "show", "--json"],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["ok"] is True
    assert payload["config_health"]["mode"] == "fast"
    assert payload["process_limits"]["launch"]["backend"] == "deferred"
    assert payload["quota"]["commands"]["agy"] == "[redacted-token]"
    assert "sk-test-secret" not in completed.stdout
    assert any("AI_MAN_INTERACTIVE_QUOTA_TIMEOUT" in warning for warning in payload["warnings"])


def test_config_show_json_does_not_import_live_process_policy(tmp_path):
    code = r"""
import contextlib
import io
import json
import sys
import profile_manager

with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    rc = profile_manager.main(["config", "show", "--json"])
if rc != 0:
    raise SystemExit(rc)

print(json.dumps({
    "process_policy_imported": "cli_profile_manager.process_policy" in sys.modules,
}))
"""
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(ROOT),
        env=config_env(tmp_path),
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload == {"process_policy_imported": False}


def test_effective_config_payload_schema_is_stable(monkeypatch, tmp_path):
    from cli_profile_manager import config

    monkeypatch.setenv("AI_MAN_AGY_HOME", str(tmp_path / "agy-homes"))
    monkeypatch.setenv("AI_MAN_CODEX_HOME", str(tmp_path / "codex-homes"))
    monkeypatch.setenv("AI_MAN_CLAUDE_HOME", str(tmp_path / "claude-homes"))
    monkeypatch.setenv("AI_MAN_METADATA_DIR", str(tmp_path / "metadata"))
    monkeypatch.setenv("AI_MAN_WSL_HOME", str(tmp_path / "wsl"))
    monkeypatch.setenv("AI_MAN_WINDOWS_HOME", str(tmp_path / "windows"))

    payload = config.effective_config_payload(include_sources=True)
    assert list(payload.keys()) == [
        "ok",
        "profile_roots",
        "metadata_dir",
        "sync_roots",
        "quota",
        "process_limits",
        "environment",
        "settings",
        "settings_by_key",
        "config_health",
        "warnings",
    ]
    assert payload["settings_by_key"] == {setting["key"]: setting for setting in payload["settings"]}
    first_setting = payload["settings"][0]
    assert list(first_setting.keys()) == [
        "key",
        "name",
        "category",
        "description",
        "type",
        "default",
        "value",
        "raw_value",
        "source",
        "source_name",
        "aliases",
        "deprecated_aliases",
        "redacted",
        "internal",
        "warnings",
    ]

    slim_payload = config.effective_config_payload(include_sources=False)
    slim_setting = slim_payload["settings_by_key"]["paths.agy_home"]
    assert "source" in slim_setting
    assert "source" not in slim_payload["settings"][0]
    assert "aliases" not in slim_payload["settings"][0]


def test_config_health_command_json_exposes_health_split(tmp_path):
    completed = subprocess.run(
        [sys.executable, str(ROOT / "profile_manager.py"), "config", "health", "--json"],
        env=config_env(tmp_path),
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["ok"] is True
    assert payload["health"]["mode"] == "health"
    assert payload["health"]["live_checks"] is True
    assert "process_limits" in payload
