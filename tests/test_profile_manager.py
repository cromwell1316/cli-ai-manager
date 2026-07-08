import base64
import importlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def load_pm(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_MAN_AGY_HOME", str(tmp_path / "agy-homes"))
    monkeypatch.setenv("AI_MAN_CODEX_HOME", str(tmp_path / "codex-homes"))
    monkeypatch.setenv("AI_MAN_CLAUDE_HOME", str(tmp_path / "claude-homes"))
    monkeypatch.setenv("AI_MAN_METADATA_DIR", str(tmp_path / "metadata"))
    monkeypatch.setenv("AI_MAN_WSL_HOME", str(tmp_path / "wsl"))
    monkeypatch.setenv("AI_MAN_WINDOWS_HOME", str(tmp_path / "windows"))
    sys.path.insert(0, str(ROOT))
    import profile_manager

    return importlib.reload(profile_manager)


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def make_id_token(email):
    header = base64.urlsafe_b64encode(b'{"alg":"none"}').decode().rstrip("=")
    payload = base64.urlsafe_b64encode(json.dumps({"email": email}).encode()).decode().rstrip("=")
    return f"{header}.{payload}.sig"


def test_parse_profile_accepts_p_prefix_and_rejects_invalid(monkeypatch, tmp_path):
    pm = load_pm(monkeypatch, tmp_path)

    assert pm.parse_profile("p12") == 12
    assert pm.parse_profile("12") == 12

    with pytest.raises(ValueError):
        pm.parse_profile("p0")
    with pytest.raises(ValueError):
        pm.parse_profile("abc")


def test_first_free_profile_uses_env_home(monkeypatch, tmp_path):
    pm = load_pm(monkeypatch, tmp_path)
    (tmp_path / "codex-homes" / "p1").mkdir(parents=True)
    (tmp_path / "codex-homes" / "p3").mkdir(parents=True)

    assert pm.first_free_profile("codex") == 2


def test_status_detection_reports_source_state_account_and_warnings(monkeypatch, tmp_path):
    pm = load_pm(monkeypatch, tmp_path)
    codex_auth = tmp_path / "codex-homes" / "p1" / "auth.json"
    write_json(codex_auth, {"tokens": {"id_token": make_id_token("user@example.com")}})
    agy_token = tmp_path / "agy-homes" / "p2" / ".gemini" / "oauth_creds.json"
    write_json(agy_token, {"refresh_token": "r"})
    write_json(tmp_path / "agy-homes" / "p2" / ".gemini" / "google_accounts.json", {"active": "agy@example.com"})
    agy_cli_token = tmp_path / "agy-homes" / "p3" / ".gemini" / "antigravity-cli" / "antigravity-oauth-token"
    write_json(agy_cli_token, {"auth_method": "oauth", "token": "synthetic"})
    invalid_claude = tmp_path / "claude-homes" / "p1" / ".credentials.json"
    invalid_claude.parent.mkdir(parents=True)
    invalid_claude.write_text("{bad", encoding="utf-8")

    codex = pm.status_payload("codex", 1, {})
    agy = pm.status_payload("agy", 2, {})
    agy_cli = pm.status_payload("agy", 3, {})
    claude = pm.status_payload("claude", 1, {})

    assert codex["token_state"] == "valid"
    assert codex["credential_source"] == "codex-auth"
    assert codex["account"] == "user@example.com"
    assert agy["token_state"] == "valid"
    assert agy["credential_source"] == "wsl-oauth"
    assert agy["account"] == "agy@example.com"
    assert agy_cli["token_state"] == "valid"
    assert agy_cli["credential_source"] == "agy-cli-token"
    assert agy_cli["account"] == "logged in"
    assert claude["token_state"] == "invalid"
    assert claude["credential_source"] == "claude-credentials"
    assert claude["warnings"]


def test_quota_parsers_extract_agent_specific_limits():
    from cli_profile_manager.quota import parse_quota

    codex = parse_quota("codex", "5h limit: [###] 82% left resets 03:12\nWeekly limit: 64% left")
    claude = parse_quota("claude", "Claude Code /usage\nSession usage 41% remaining resets in 2h\nWeekly 77%")
    agy = parse_quota("agy", "Gemini usage\nDaily limit 35% remaining resets tomorrow")

    assert codex["state"] == "available"
    assert codex["limits"]["five_hour"]["percent_left"] == 82
    assert codex["limits"]["weekly"]["percent_left"] == 64
    assert claude["state"] == "available"
    assert claude["limits"]["session"]["percent"] == 41
    assert claude["limits"]["weekly"]["percent"] == 77
    assert agy["state"] == "available"
    assert agy["limits"]["daily"]["percent"] == 35


def test_agy_quota_parser_extracts_common_usage_variants():
    from cli_profile_manager.cli import quota_summary
    from cli_profile_manager.quota import parse_quota

    quota = parse_quota(
        "agy",
        """
        Antigravity usage
        Local messages: 73% remaining, refreshes in 4h
        Cloud tasks: 6/10 used, resets tomorrow
        Gemini 2.5 Pro quota: 41% left
        """,
    )

    assert quota["state"] == "available"
    assert quota["limits"]["local_messages"]["percent_left"] == 73
    assert quota["limits"]["cloud_tasks"]["percent"] == 60
    assert quota["limits"]["gemini_2_5_pro_quota"]["percent_left"] == 41
    assert quota_summary({"quota": quota}) == "local:73%, cloud:60%, Gemini 2.5 Pro quota:41%"


def test_codex_quota_parser_extracts_status_limit_variants():
    from cli_profile_manager.quota import parse_quota

    quota = parse_quota(
        "codex",
        """
        /status
        Model: gpt-5.5 medium
        5h limit: 71% remaining, resets in 2h 14m
        Weekly limit: 42% available, resets Monday
        Context window: 18% used
        """,
    )

    assert quota["state"] == "available"
    assert quota["limits"]["five_hour"]["percent_left"] == 71
    assert quota["limits"]["weekly"]["percent_left"] == 42
    assert quota["limits"]["context"]["percent"] == 18


def test_codex_quota_parser_extracts_boxed_status_output():
    from cli_profile_manager.cli import quota_summary
    from cli_profile_manager.quota import parse_quota

    quota = parse_quota(
        "codex",
        """
        ╭─────────────────────────────────────────────────────────────────────────────────╮
        │  >_ OpenAI Codex (v0.142.3)                                                     │
        │  Context window:       81% left (58.6K used / 258K)                             │
        │  5h limit:             [██████████████████░░] 89% left (resets 16:24)           │
        │  Weekly limit:         [█████████████████░░░] 83% left (resets 20:22 on 14 Jul) │
        ╰─────────────────────────────────────────────────────────────────────────────────╯
        """,
    )

    assert quota["state"] == "available"
    assert quota["limits"]["context"]["percent_left"] == 81
    assert quota["limits"]["five_hour"]["percent_left"] == 89
    assert quota["limits"]["weekly"]["percent_left"] == 83
    assert quota_summary({"quota": quota}) == "5h:89%, week:83%, ctx:81%"


def test_codex_quota_parser_ignores_generic_non_limit_usage():
    from cli_profile_manager.quota import parse_quota

    quota = parse_quota(
        "codex",
        "Usage limits\nMessages remaining: 63%\nRate limit resets at 18:30",
    )

    assert quota["state"] == "unknown"
    assert quota["limits"] == {}


def test_codex_quota_parser_ignores_warning_without_status_breakdown():
    from cli_profile_manager.quota import parse_quota

    quota = parse_quota(
        "codex",
        "Heads up, you have less than 10% of your weekly limit left. Run /status for a breakdown.",
    )

    assert quota["state"] == "unknown"
    assert quota["limits"] == {}


def test_status_payload_can_include_quota_without_real_cli(monkeypatch, tmp_path):
    pm = load_pm(monkeypatch, tmp_path)
    codex_auth = tmp_path / "codex-homes" / "p1" / "auth.json"
    write_json(codex_auth, {"OPENAI_API_KEY": "sk-test"})

    def fake_quota(tool_key, profile_name, command, env, cwd, timeout_seconds=20):
        assert tool_key == "codex"
        assert profile_name == "p1"
        assert command == ["codex"]
        assert env["CODEX_HOME"] == str(tmp_path / "codex-homes" / "p1")
        return {
            "tool": tool_key,
            "profile": profile_name,
            "quota": {
                "state": "available",
                "limits": {"five_hour": {"percent_left": 82}},
            },
        }

    import cli_profile_manager.cli as cli

    monkeypatch.setattr(cli, "core_quota_payload", fake_quota)

    status = pm.status_payload_with_quota("codex", 1, {})

    assert status["quota"]["state"] == "available"
    assert status["quota"]["limits"]["five_hour"]["percent_left"] == 82


def test_interactive_visible_padding_ignores_ansi_codes():
    sys.path.insert(0, str(ROOT))
    import cli_profile_manager.interactive as interactive

    text = f"{interactive.CLR_GREEN}Active{interactive.CLR_RESET}"

    assert interactive.visible_len(text) == len("Active")
    assert interactive.visible_len(interactive.visible_ljust(text, 12)) == 12
    assert interactive.visible_len(interactive.visible_fit(f"{interactive.CLR_RED}invalid token: Antigravity CLI token is missing token{interactive.CLR_RESET}", 34)) == 34


def test_interactive_quota_text_does_not_show_unknown_state():
    sys.path.insert(0, str(ROOT))
    import cli_profile_manager.interactive as interactive

    status = {"quota": {"state": "unknown", "limits": {}}}

    assert interactive.quota_text(status, color=False) == "not parsed"


@pytest.mark.parametrize("sequence", ["\x1b[A", "\x1bOA", "\x1b[1;2A", "\x1b[1;5A"])
def test_interactive_get_key_reads_up_arrow_sequences(monkeypatch, sequence):
    sys.path.insert(0, str(ROOT))
    import cli_profile_manager.interactive as interactive

    class FakeStdin:
        def fileno(self):
            return 0

    data = [ch.encode() for ch in sequence]

    monkeypatch.setattr(interactive.sys, "stdin", FakeStdin())
    monkeypatch.setattr(interactive.os, "read", lambda _fd, _size: data.pop(0))
    monkeypatch.setattr(interactive.termios, "tcgetattr", lambda _fd: object())
    monkeypatch.setattr(interactive.termios, "tcsetattr", lambda *_args: None)
    monkeypatch.setattr(interactive.tty, "setraw", lambda _fd: None)
    monkeypatch.setattr(interactive.select, "select", lambda r, _w, _e, _t: (r if data else [], [], []))

    assert interactive.get_key() == "up"


@pytest.mark.parametrize("sequence", ["\x1b[B", "\x1bOB", "\x1b[1;2B", "\x1b[1;5B"])
def test_interactive_get_key_reads_down_arrow_sequences(monkeypatch, sequence):
    sys.path.insert(0, str(ROOT))
    import cli_profile_manager.interactive as interactive

    class FakeStdin:
        def fileno(self):
            return 0

    data = [ch.encode() for ch in sequence]

    monkeypatch.setattr(interactive.sys, "stdin", FakeStdin())
    monkeypatch.setattr(interactive.os, "read", lambda _fd, _size: data.pop(0))
    monkeypatch.setattr(interactive.termios, "tcgetattr", lambda _fd: object())
    monkeypatch.setattr(interactive.termios, "tcsetattr", lambda *_args: None)
    monkeypatch.setattr(interactive.tty, "setraw", lambda _fd: None)
    monkeypatch.setattr(interactive.select, "select", lambda r, _w, _e, _t: (r if data else [], [], []))

    assert interactive.get_key() == "down"


def test_agy_windows_wsl_conversion_round_trips(monkeypatch, tmp_path):
    pm = load_pm(monkeypatch, tmp_path)
    token = {"refresh_token": "secret", "scope": "email"}
    win_cred = pm.build_windows_agy_credential(token, "a@example.com")
    win_path = tmp_path / "cred-p1.json"
    write_json(win_path, win_cred)

    decoded, account = pm.decode_windows_agy_credential(str(win_path))

    assert decoded == token
    assert account == "a@example.com"

    pm.import_windows_agy_credential(str(win_path), 1)
    assert json.loads((tmp_path / "agy-homes" / "p1" / ".gemini" / "oauth_creds.json").read_text()) == token


def test_import_export_use_atomic_destination_without_tmp_leftovers(monkeypatch, tmp_path):
    pm = load_pm(monkeypatch, tmp_path)
    source = tmp_path / "source-auth.json"
    write_json(source, {"OPENAI_API_KEY": "sk-test"})

    profile_num, dest = pm.import_credential_file("codex", str(source), 1)
    exported = pm.export_credential_file("codex", profile_num, str(tmp_path / "out" / "auth.json"))

    assert Path(dest).exists()
    assert Path(exported).exists()
    assert list((tmp_path / "codex-homes" / "p1").glob("*.tmp-*")) == []
    assert list((tmp_path / "out").glob("*.tmp-*")) == []


def test_sync_dry_run_json_shape_and_hard_delete_preflight(monkeypatch, tmp_path):
    pm = load_pm(monkeypatch, tmp_path)
    wsl = tmp_path / "wsl"
    windows = tmp_path / "windows"
    write_json(wsl / "codex-homes" / "p1" / "auth.json", {"OPENAI_API_KEY": "new"})
    write_json(wsl / "agy-homes" / "p1" / ".gemini" / "oauth_creds.json", {"refresh_token": "r"})
    write_json(windows / "codex-homes" / "p9" / "auth.json", {"OPENAI_API_KEY": "old"})

    result = pm.sync_profiles_noninteractive("wsl", "hard", dry_run=True, yes=False)

    assert result["dry_run"] is True
    assert result["copied"] == 2
    assert result["converted"] == 1
    assert result["invalid"] == 0
    assert result["would_delete"] == 1
    assert str(windows / "codex-homes" / "p9" / "auth.json") in result["delete_paths"]
    assert not (windows / "agy-homes" / "cred-p1.json").exists()

    with pytest.raises(PermissionError):
        pm.sync_profiles_noninteractive("wsl", "hard", dry_run=False, yes=False)


def test_direct_command_exit_codes_and_json_errors(monkeypatch, tmp_path):
    env = os.environ.copy()
    env.update({
        "AI_MAN_AGY_HOME": str(tmp_path / "agy-homes"),
        "AI_MAN_CODEX_HOME": str(tmp_path / "codex-homes"),
        "AI_MAN_CLAUDE_HOME": str(tmp_path / "claude-homes"),
        "AI_MAN_METADATA_DIR": str(tmp_path / "metadata"),
    })

    completed = subprocess.run(
        [sys.executable, str(ROOT / "profile_manager.py"), "status", "codex", "bad", "--json"],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 2
    payload = json.loads(completed.stdout)
    assert payload["ok"] is False
    assert payload["error"]["code"] == 2


def test_import_export_dry_run_json_does_not_write(monkeypatch, tmp_path):
    env = os.environ.copy()
    env.update({
        "AI_MAN_AGY_HOME": str(tmp_path / "agy-homes"),
        "AI_MAN_CODEX_HOME": str(tmp_path / "codex-homes"),
        "AI_MAN_CLAUDE_HOME": str(tmp_path / "claude-homes"),
        "AI_MAN_METADATA_DIR": str(tmp_path / "metadata"),
    })
    source = tmp_path / "source-auth.json"
    write_json(source, {"OPENAI_API_KEY": "sk-test"})

    imported = subprocess.run(
        [
            sys.executable,
            str(ROOT / "profile_manager.py"),
            "import",
            "codex",
            str(source),
            "p1",
            "--dry-run",
            "--json",
        ],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert imported.returncode == 0
    import_payload = json.loads(imported.stdout)
    assert import_payload["ok"] is True
    assert import_payload["dry_run"] is True
    assert import_payload["would_import"] is True
    assert not (tmp_path / "codex-homes" / "p1" / "auth.json").exists()

    write_json(tmp_path / "codex-homes" / "p1" / "auth.json", {"OPENAI_API_KEY": "sk-test"})
    export_path = tmp_path / "out" / "auth.json"
    exported = subprocess.run(
        [
            sys.executable,
            str(ROOT / "profile_manager.py"),
            "export",
            "codex",
            "p1",
            "--to",
            str(export_path),
            "--dry-run",
            "--json",
        ],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert exported.returncode == 0
    export_payload = json.loads(exported.stdout)
    assert export_payload["ok"] is True
    assert export_payload["dry_run"] is True
    assert export_payload["would_export"] is True
    assert not export_path.exists()


def test_core_modules_are_importable_without_terminal_helpers():
    from cli_profile_manager import metadata, paths, sync
    from cli_profile_manager.credentials import agy, claude, codex

    assert paths.parse_profile("p1") == 1
    assert metadata.load_metadata() == {}
    assert sync.profile_number_from_dir_name("p2") == 2
    assert agy.WINDOWS_TARGET == "gemini:antigravity"
    assert callable(codex.account_from_auth)
    assert callable(claude.account_summary)


def test_launch_flags_after_profile_are_normalized_before_tool_args(monkeypatch, tmp_path):
    pm = load_pm(monkeypatch, tmp_path)

    normalized = pm.normalize_launch_argv([
        "launch",
        "codex",
        "p1",
        "--dry-run",
        "--json",
        "--platform",
        "windows",
        "--",
        "--help",
    ])

    assert normalized == [
        "launch",
        "--dry-run",
        "--json",
        "--platform",
        "windows",
        "codex",
        "p1",
        "--",
        "--help",
    ]
