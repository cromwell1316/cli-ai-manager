import base64
import contextlib
import io
import importlib
import json
import os
import shutil
import subprocess
import sys
import threading
import time
import types
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


def run_in_process_command(pm, argv):
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        rc = pm.run_cli(argv)
    return rc, stdout.getvalue(), stderr.getvalue()


def test_parse_profile_accepts_p_prefix_and_rejects_invalid(monkeypatch, tmp_path):
    pm = load_pm(monkeypatch, tmp_path)

    assert pm.parse_profile("p12") == 12
    assert pm.parse_profile("12") == 12

    with pytest.raises(ValueError):
        pm.parse_profile("p0")
    with pytest.raises(ValueError):
        pm.parse_profile("abc")


def test_help_and_config_show_do_not_import_quota_module(tmp_path):
    env = os.environ.copy()
    env.update(
        {
            "AI_MAN_AGY_HOME": str(tmp_path / "agy-homes"),
            "AI_MAN_CODEX_HOME": str(tmp_path / "codex-homes"),
            "AI_MAN_CLAUDE_HOME": str(tmp_path / "claude-homes"),
            "AI_MAN_METADATA_DIR": str(tmp_path / "metadata"),
            "AI_MAN_WSL_HOME": str(tmp_path / "wsl"),
            "AI_MAN_WINDOWS_HOME": str(tmp_path / "windows"),
        }
    )
    code = r"""
import contextlib
import io
import json
import sys
import profile_manager

with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    try:
        profile_manager.main(["--help"])
    except SystemExit as exc:
        if exc.code != 0:
            raise
help_imported = "cli_profile_manager.quota" in sys.modules

with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    rc = profile_manager.main(["config", "show", "--json"])
if rc != 0:
    raise SystemExit(rc)

print(json.dumps({
    "help_imported_quota": help_imported,
    "config_imported_quota": "cli_profile_manager.quota" in sys.modules,
    "config_imported_interactive": "cli_profile_manager.interactive" in sys.modules,
}))
"""
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(ROOT),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    payload = json.loads(completed.stdout)

    assert payload == {
        "help_imported_quota": False,
        "config_imported_quota": False,
        "config_imported_interactive": False,
    }


def test_parser_help_detection_ignores_launch_passthrough_help(monkeypatch, tmp_path):
    pm = load_pm(monkeypatch, tmp_path)

    assert pm.is_parser_help_request(["--help"]) is True
    assert pm.is_parser_help_request(["launch", "agy", "p1", "--help"]) is True
    assert pm.is_parser_help_request(["launch", "agy", "p1", "--", "-h"]) is False
    assert pm.is_parser_help_request(["launch", "agy", "p1", "--", "--help"]) is False


def test_in_process_command_perf_budgets(monkeypatch, tmp_path):
    pm = load_pm(monkeypatch, tmp_path)
    agy_token = tmp_path / "agy-homes" / "p1" / ".gemini" / "oauth_creds.json"
    write_json(agy_token, {"refresh_token": "synthetic"})
    write_json(tmp_path / "agy-homes" / "p1" / ".gemini" / "google_accounts.json", {"active": "bench@example.com"})
    write_json(tmp_path / "metadata" / "profiles_metadata.json", {"agy": {"p1": {"label": "bench"}}})

    commands = {
        "config show --json": ["config", "show", "--json"],
        "list agy --json": ["list", "agy", "--json"],
        "status agy p1 --json": ["status", "agy", "p1", "--json"],
        "diagnostics agy --json": ["diagnostics", "agy", "--json"],
    }
    budgets_ms = {
        "config show --json": 60.0,
        "list agy --json": 100.0,
        "status agy p1 --json": 80.0,
        "diagnostics agy --json": 180.0,
    }
    failures = []

    for name, argv in commands.items():
        values = []
        for _ in range(5):
            started = time.perf_counter()
            rc, stdout, stderr = run_in_process_command(pm, argv)
            elapsed_ms = (time.perf_counter() - started) * 1000
            values.append(elapsed_ms)
            assert rc == 0, stderr
            assert stdout.strip()
        median_ms = sorted(values)[len(values) // 2]
        if median_ms > budgets_ms[name]:
            failures.append(f"{name}: median {median_ms:.3f}ms > budget {budgets_ms[name]:.3f}ms")

    assert not failures, "; ".join(failures)


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


def test_agy_status_uses_recent_auth_log_when_google_account_is_placeholder(monkeypatch, tmp_path):
    pm = load_pm(monkeypatch, tmp_path)
    profile_home = tmp_path / "agy-homes" / "p4"
    write_json(profile_home / ".gemini" / "oauth_creds.json", {"refresh_token": "r"})
    write_json(profile_home / ".gemini" / "google_accounts.json", {"active": "logged in"})
    log_path = profile_home / ".gemini" / "antigravity-cli" / "log" / "cli-20260708_133455.log"
    log_path.parent.mkdir(parents=True)
    log_path.write_text(
        "applyAuthResult: email=resolved@example.com, authMethod=consumer, quotaProject=\n",
        encoding="utf-8",
    )

    status = pm.status_payload("agy", 4, {})

    assert status["token_state"] == "valid"
    assert status["email"] == "resolved@example.com"
    assert status["account"] == "resolved@example.com"


def test_command_snapshot_reuses_profile_discovery_and_status(monkeypatch, tmp_path):
    pm = load_pm(monkeypatch, tmp_path)
    import cli_profile_manager.operations as operations

    calls = []

    monkeypatch.setattr(operations.ProfileIndex, "_scan_base", lambda self: calls.append(self.tool_key) or setattr(self, "_occupied_profiles", [1]))
    monkeypatch.setattr(operations, "get_profile_status", lambda tool, n, metadata, account_email_provider=None, profile_fact=None: {
        "num": n,
        "profile": f"p{n}",
        "email": "(no login)",
        "has_token": False,
        "token_state": "missing",
        "credential_source": None,
        "account": None,
        "warnings": [],
        "label": "",
        "home": str(tmp_path / f"{tool}-homes" / f"p{n}"),
    })

    snapshot = pm.command_snapshot()

    assert snapshot.display_profiles("codex")[:2] == [1, 2]
    assert snapshot.first_free_profile("codex") == 2
    assert snapshot.status("codex", 1) is snapshot.status("codex", 1)
    assert calls == ["codex"]


def test_command_snapshot_profile_index_uses_file_facts(monkeypatch, tmp_path):
    pm = load_pm(monkeypatch, tmp_path)
    import cli_profile_manager.operations as operations

    auth_path = tmp_path / "codex-homes" / "p1" / "auth.json"
    write_json(auth_path, {"tokens": {"id_token": make_id_token("user@example.com")}})
    snapshot = pm.command_snapshot()

    index = snapshot.profile_index("codex")
    fact = index.fact(1)
    status = snapshot.status("codex", 1)

    assert fact.credential.path == str(auth_path)
    assert fact.credential.exists is True
    assert isinstance(fact.credential.mtime_ns, int)
    assert status["token_state"] == "valid"
    assert status["account"] == "user@example.com"
    assert not hasattr(fact, "content")
    assert not isinstance(fact.credential, dict)
    assert isinstance(operations.ProfileIndex("codex").fingerprint(), tuple)


def test_command_snapshot_reuses_agy_account_lookup(monkeypatch, tmp_path):
    pm = load_pm(monkeypatch, tmp_path)
    import cli_profile_manager.operations as operations

    token = tmp_path / "agy-homes" / "p1" / ".gemini" / "oauth_creds.json"
    write_json(token, {"refresh_token": "r"})
    calls = []

    monkeypatch.setattr(
        operations,
        "account_email_from_google_accounts",
        lambda home: calls.append(home) or "agy@example.com",
    )

    snapshot = pm.command_snapshot()
    first = snapshot.status("agy", 1)
    second = snapshot.status("agy", 1)

    assert first is second
    assert first["account"] == "agy@example.com"
    assert calls == [str(tmp_path / "agy-homes" / "p1")]


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
    assert quota_summary({"quota": quota}) == "P:41% local:73% cloud:60%"


def test_agy_quota_parser_extracts_models_and_quota_output():
    from cli_profile_manager.cli import quota_summary
    from cli_profile_manager.quota import parse_quota

    quota = parse_quota(
        "agy",
        """
        └ Models & Quota
        Account: user@example.com
        ALL MODELS
        Gemini 3.5 Flash (Medium)
        [░░░░░░░░░░] 0.00%
        Refreshes in 100h 47m
        Gemini 3.1 Pro (Low)
        [███░░░░░░░] 5.00%
        5% remaining · Refreshes in 76h 48m
        Claude Sonnet 4.6 (Thinking)
        [██████████] 100.00%
        Quota available
        """,
    )

    assert quota["state"] == "available"
    assert quota["account"] == "user@example.com"
    assert quota["current_limit"] == "gemini_3_5_flash_medium"
    assert quota["limits"]["gemini_3_5_flash_medium"]["percent"] == 0
    assert quota["limits"]["gemini_3_1_pro_low"]["percent"] == 5
    assert quota["limits"]["claude_sonnet_4_6_thinking"]["percent"] == 100
    assert "usage_1" not in quota["limits"]
    assert quota_summary({"quota": quota}) == "FM:0% PL:5% CS:100%"


def test_agy_quota_parser_extracts_all_model_rows_from_usage_output():
    from cli_profile_manager.cli import quota_summary
    from cli_profile_manager.quota import parse_quota

    quota = parse_quota(
        "agy",
        """
        Account: nikitosz1357@gmail.com
        ALL MODELS
        Gemini 3.5 Flash (Medium)
        [░░░░░░░░░░] 0.00%
        Refreshes in 100h 18m
        Gemini 3.5 Flash (High)
        [░░░░░░░░░░] 0.00%
        Refreshes in 100h 18m
        Gemini 3.5 Flash (Low)
        [░░░░░░░░░░] 0.00%
        Refreshes in 100h 18m
        Gemini 3.1 Pro (Low)
        [███░░░░░░░] 5.00%
        5% remaining · Refreshes in 76h 19m
        Gemini 3.1 Pro (High)
        [███░░░░░░░] 5.00%
        5% remaining · Refreshes in 76h 19m
        """,
    )

    assert quota["account"] == "nikitosz1357@gmail.com"
    assert quota["limits"]["gemini_3_5_flash_medium"]["percent"] == 0
    assert quota["limits"]["gemini_3_5_flash_high"]["percent"] == 0
    assert quota["limits"]["gemini_3_5_flash_low"]["percent"] == 0
    assert quota["limits"]["gemini_3_1_pro_low"]["percent"] == 5
    assert quota["limits"]["gemini_3_1_pro_high"]["percent"] == 5
    assert quota_summary({"quota": quota}) == "FM:0% FH:0% FL:0% PL:5% PH:5%"


def test_interactive_agy_quota_columns_split_model_limits():
    from cli_profile_manager.interactive import agy_quota_cells, agy_status_quota_columns

    status = {
        "quota": {
            "state": "available",
            "limits": {
                "gemini_3_5_flash_medium": {"model": "Gemini 3.5 Flash (Medium)", "percent": 0},
                "gemini_3_5_flash_high": {"model": "Gemini 3.5 Flash (High)", "percent": 94},
                "gemini_3_1_pro_low": {"model": "Gemini 3.1 Pro (Low)", "percent": 5},
                "claude_sonnet_4_6_thinking": {"model": "Claude Sonnet 4.6 (Thinking)", "percent": 100},
                "claude_opus_4_1": {"model": "Claude Opus 4.1", "percent": 100},
            },
        },
    }

    columns = agy_status_quota_columns([status])

    assert columns[:7] == ["FM", "FH", "FL", "PL", "PH", "CS", "CO"]
    assert agy_quota_cells(status, columns)[:7] == ["0%", "94%", "", "5%", "", "100%", "100%"]


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

    assert quota["state"] == "parser_miss"
    assert quota["limits"] == {}


def test_codex_quota_parser_ignores_warning_without_status_breakdown():
    from cli_profile_manager.quota import parse_quota

    quota = parse_quota(
        "codex",
        "Heads up, you have less than 10% of your weekly limit left. Run /status for a breakdown.",
    )

    assert quota["state"] == "parser_miss"
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

    import cli_profile_manager.operations as operations

    monkeypatch.setattr(operations, "core_quota_payload", fake_quota)

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


def test_interactive_quota_text_marks_unknown_state_as_retrying():
    sys.path.insert(0, str(ROOT))
    import cli_profile_manager.interactive as interactive

    status = {"quota": {"state": "unknown", "limits": {}}}

    assert interactive.quota_text(status, color=False) == "retrying"


def test_interactive_quota_text_uses_color_for_expired_available_quota(monkeypatch):
    import cli_profile_manager.interactive as interactive

    monkeypatch.setenv("AI_MAN_INTERACTIVE_QUOTA_FRESH_SECONDS", "600")
    status = {
        "quota": {
            "state": "available",
            "limits": {"daily": {"percent": 77}},
            "fetched_at": interactive.time.time() - 601,
        },
    }

    assert interactive.quota_text(status, color=False) == "day:77%"
    assert interactive.quota_text(status).startswith(interactive.CLR_WHITE)


def test_interactive_quota_progress_line_tracks_active_refresh():
    import cli_profile_manager.interactive as interactive

    statuses = [
        {
            "has_token": True,
            "quota": {"state": "available", "job_state": "ready", "limits": {"daily": {"percent": 77}}},
        },
        {
            "has_token": True,
            "quota": {"state": "loading", "job_state": "running", "limits": {}},
        },
        {
            "has_token": True,
            "quota": {"state": "loading", "job_state": "queued", "limits": {}},
        },
        {
            "has_token": True,
            "quota": {"state": "parser_miss", "job_state": "retryable", "limits": {}},
        },
        {
            "has_token": False,
            "quota": {"state": "no_token", "limits": {}},
        },
    ]

    progress = interactive.quota_progress_snapshot(statuses)
    line = interactive.quota_progress_line(statuses, now=0.0)

    assert progress == {
        "total": 4,
        "completed": 1,
        "queued": 1,
        "running": 1,
        "warming": 0,
        "failed": 1,
        "pending": 0,
        "active": 2,
    }
    assert "Quota refresh |" in line
    assert "1/4 25%" in line
    assert "running 1, queued 1, failed 1" in line


def test_interactive_quota_progress_line_hidden_when_idle():
    import cli_profile_manager.interactive as interactive

    statuses = [
        {
            "has_token": True,
            "quota": {"state": "available", "job_state": "ready", "limits": {"daily": {"percent": 77}}},
        },
    ]

    assert interactive.quota_progress_line(statuses, now=0.0) is None


def test_interactive_quota_progress_counts_only_obtained_quota_values():
    import cli_profile_manager.interactive as interactive

    statuses = [
        {
            "has_token": True,
            "quota": {
                "state": "available",
                "job_state": "retryable",
                "limits": {"daily": {"percent": 77}},
            },
        },
        {
            "has_token": True,
            "quota": {
                "state": "startup_pending",
                "job_state": "retryable",
                "limits": {},
            },
        },
        {
            "has_token": True,
            "quota": {
                "state": "available",
                "job_state": "ready",
                "limits": {"daily": {"percent": 88}},
            },
        },
    ]

    progress = interactive.quota_progress_snapshot(statuses)
    line = interactive.quota_progress_line(statuses, now=0.0)

    assert progress["completed"] == 1
    assert progress["failed"] == 1
    assert progress["warming"] == 1
    assert "1/3 33%" in line
    assert "warming 1" in line


def test_interactive_status_screen_renders_quota_progress(monkeypatch):
    import cli_profile_manager.interactive as interactive

    monkeypatch.setenv("AI_MAN_INTERACTIVE_QUOTA_FRESH_SECONDS", "600")
    interactive.invalidate_quota_cache()
    now = interactive.time.time()
    interactive.store_quota_cache("agy", 1, {
        "state": "ready",
        "job_state": "ready",
        "machine_state": "available",
        "quota": {
            "state": "available",
            "job_state": "ready",
            "limits": {"daily": {"percent": 77}},
            "fetched_at": now,
        },
        "fetched_at": now,
        "started_at": None,
        "attempts": 0,
        "last_error": None,
        "next_retry_at": None,
    })
    interactive.store_quota_cache("agy", 2, {
        "state": "running",
        "job_state": "running",
        "machine_state": "running",
        "quota": {"state": "loading", "job_state": "running", "limits": {}},
        "fetched_at": None,
        "started_at": now,
        "attempts": 0,
        "last_error": None,
        "next_retry_at": None,
    })
    base_statuses = [
        {"num": 1, "email": "one@example.com", "has_token": True, "label": ""},
        {"num": 2, "email": "two@example.com", "has_token": True, "label": ""},
    ]

    lines = interactive.render_status_screen_lines("agy", base_statuses=base_statuses)
    plain = "\n".join(interactive.ANSI_RE.sub("", line) for line in lines)

    assert "Quota refresh" in plain
    assert "1/2 50%" in plain
    assert "running 1, queued 0" in plain
    interactive.invalidate_quota_cache()


def test_quota_state_machine_rejects_illegal_transitions():
    import cli_profile_manager.interactive as interactive

    assert interactive.validate_quota_transition("queued", "running") is True

    with pytest.raises(ValueError, match="illegal quota pipeline transition"):
        interactive.validate_quota_transition("available", "running")

    with pytest.raises(ValueError, match="unknown quota pipeline state"):
        interactive.validate_quota_transition("queued", "mystery")


def test_quota_parser_classifies_empty_parser_miss_and_auth_output():
    from cli_profile_manager.quota import parse_quota

    empty = parse_quota("agy", " \r\n\t ")
    miss = parse_quota("agy", "Antigravity changed this screen\nNo quota rows here")
    auth = parse_quota("agy", "Please sign in to continue")

    assert empty["state"] == "empty_output"
    assert empty["warnings"] == ["quota command returned no readable output"]
    assert miss["state"] == "parser_miss"
    assert "no known quota fields matched" in miss["warnings"][0]
    assert miss["diagnostic_summary"] == "Antigravity changed this screen\nNo quota rows here"
    assert auth["state"] == "auth_required"


def test_agy_quota_parser_classifies_native_failure_output():
    from cli_profile_manager.quota import parse_quota

    tty = parse_quota("agy", "CLI error: bubbletea: error opening TTY: open /dev/tty: no such device")
    ineligible = parse_quota("agy", "Account ineligible for Antigravity")
    location_ineligible = parse_quota(
        "agy",
        "Eligibility check failed: Your current account is not eligible for Antigravity, "
        "because it is not currently available in your location.",
    )
    exhausted = parse_quota("agy", "RESOURCE_EXHAUSTED: quota exceeded")
    capacity_exhausted = parse_quota("agy", "Error: You have exhausted your capacity on this model. Your quota will reset after 50h10m11s.")
    warning_then_capacity = parse_quota(
        "agy",
        "Eligibility check failed: Your current account is not eligible for Antigravity, "
        "because it is not currently available in your location.\n"
        "Error: You have exhausted your capacity on this model. Your quota will reset after 44h24m59s.",
    )
    limited = parse_quota("agy", "runtime/cgo: pthread_create failed: Resource temporarily unavailable")

    assert tty["state"] == "tty_unavailable"
    assert ineligible["state"] == "parser_miss"
    assert "eligibility warning" in ineligible["warnings"][1]
    assert location_ineligible["state"] == "parser_miss"
    assert "eligibility warning" in location_ineligible["warnings"][1]
    assert exhausted["state"] == "resource_exhausted"
    assert capacity_exhausted["state"] == "resource_exhausted"
    assert warning_then_capacity["state"] == "resource_exhausted"
    assert limited["state"] == "resource_limited"
    assert "diagnostic_summary" in tty


def test_quota_payload_preserves_missing_cli_diagnostic():
    from cli_profile_manager.quota import QuotaProbeError, quota_payload

    def fake_runner(tool_key, command, env, cwd, timeout_seconds=20):
        raise QuotaProbeError("missing_cli", "agy CLI is not installed or not in PATH")

    payload = quota_payload("agy", "p1", ["agy"], {}, ".", runner=fake_runner)

    assert payload["quota"]["state"] == "missing_cli"
    assert payload["quota"]["warnings"] == ["agy CLI is not installed or not in PATH"]


def test_quota_payload_refines_agy_process_exit_from_raw_output():
    from cli_profile_manager.quota import QuotaProbeError, quota_payload

    def fake_runner(tool_key, command, env, cwd, timeout_seconds=20):
        raise QuotaProbeError("process_exit", "CLI process exited during startup", "Account ineligible")

    payload = quota_payload("agy", "p1", ["agy"], {}, ".", runner=fake_runner)

    assert payload["quota"]["state"] == "account_ineligible"
    assert payload["quota"]["warnings"] == ["AGY CLI reported an account eligibility warning"]
    assert payload["quota"]["diagnostic_summary"] == "Account ineligible"


def test_quota_payload_refines_agy_location_ineligible_from_raw_output():
    from cli_profile_manager.quota import QuotaProbeError, quota_payload

    def fake_runner(tool_key, command, env, cwd, timeout_seconds=20):
        raise QuotaProbeError(
            "startup_pending",
            "AGY CLI is still starting",
            "Eligibility check failed: Your current account is not eligible for Antigravity, "
            "because it is not currently available in your location.",
        )

    payload = quota_payload("agy", "p1", ["agy"], {}, ".", runner=fake_runner)

    assert payload["quota"]["state"] == "startup_pending"
    assert payload["quota"]["warnings"] == ["AGY CLI is still starting; keeping the session warm"]


def test_quota_payload_refines_agy_thread_exhaustion_from_raw_output():
    from cli_profile_manager.quota import QuotaProbeError, quota_payload

    def fake_runner(tool_key, command, env, cwd, timeout_seconds=20):
        raise QuotaProbeError(
            "process_exit",
            "CLI process exited during startup",
            "runtime/cgo: pthread_create failed: Resource temporarily unavailable",
        )

    payload = quota_payload("agy", "p1", ["agy"], {}, ".", runner=fake_runner)

    assert payload["quota"]["state"] == "resource_limited"
    assert payload["quota"]["warnings"] == ["AGY CLI was stopped by local quota process resource limits"]


def test_quota_payload_refines_agy_sign_in_timeout_from_raw_output():
    from cli_profile_manager.quota import QuotaProbeError, quota_payload

    def fake_runner(tool_key, command, env, cwd, timeout_seconds=20):
        raise QuotaProbeError(
            "timeout",
            "timeout waiting for AGY CLI readiness",
            "Welcome to the Antigravity CLI. You are currently not signed in.\nSigning in...",
        )

    payload = quota_payload("agy", "p1", ["agy"], {}, ".", runner=fake_runner)

    assert payload["quota"]["state"] == "auth_required"
    assert payload["quota"]["warnings"] == ["AGY CLI could not complete sign-in for this profile; /usage was not sent"]


def test_quota_payload_refines_agy_sign_in_startup_pending_from_raw_output():
    from cli_profile_manager.quota import QuotaProbeError, quota_payload

    def fake_runner(tool_key, command, env, cwd, timeout_seconds=20):
        raise QuotaProbeError(
            "startup_pending",
            "AGY CLI is still starting",
            "Welcome to the Antigravity CLI. You are currently not signed in.\nSigning in...",
        )

    payload = quota_payload("agy", "p1", ["agy"], {}, ".", runner=fake_runner)

    assert payload["quota"]["state"] == "startup_pending"
    assert payload["quota"]["warnings"] == ["AGY CLI is still signing in; keeping the session warm"]


def test_agy_quota_startup_seconds_uses_specific_override(monkeypatch):
    import cli_profile_manager.quota as quota

    monkeypatch.delenv("AI_MAN_QUOTA_STARTUP_SECONDS", raising=False)
    monkeypatch.delenv("AI_MAN_AGY_QUOTA_STARTUP_SECONDS", raising=False)
    assert quota.quota_startup_seconds("agy") == 30.0
    assert quota.quota_startup_seconds("codex") == 3.0

    monkeypatch.setenv("AI_MAN_QUOTA_STARTUP_SECONDS", "11")
    assert quota.quota_startup_seconds("agy") == 11.0
    assert quota.quota_startup_seconds("codex") == 11.0

    monkeypatch.setenv("AI_MAN_AGY_QUOTA_STARTUP_SECONDS", "77")
    assert quota.quota_startup_seconds("agy") == 77.0
    assert quota.quota_startup_seconds("codex") == 11.0


def test_agy_quota_uses_profile_pty_command(monkeypatch, tmp_path):
    import cli_profile_manager.operations as operations

    captured = {}

    def fake_core_quota_payload(tool_key, profile_name, command, env, cwd, **kwargs):
        captured.update({
            "tool_key": tool_key,
            "profile_name": profile_name,
            "command": command,
            "env": env,
            "cwd": cwd,
            "runner": kwargs.get("runner"),
        })
        return {"tool": tool_key, "profile": profile_name, "quota": {"state": "available", "limits": {}}}

    def fake_runner(*args, **kwargs):
        return "ok"

    monkeypatch.setattr(operations, "core_quota_payload", fake_core_quota_payload)
    monkeypatch.setattr(operations, "run_persistent_cli_quota_snapshot", fake_runner)
    monkeypatch.chdir(tmp_path)

    payload = operations.quota_payload("agy", 2, timeout_seconds=12)

    assert payload["quota"]["state"] == "available"
    assert captured["command"] == ["agy"]
    assert captured["cwd"] == str(tmp_path)
    assert captured["runner"] is fake_runner
    assert captured["env"]["HOME"].endswith(os.path.join("agy-homes", "p2"))


def test_agy_quota_pty_default_timeout(monkeypatch, tmp_path):
    import cli_profile_manager.operations as operations

    captured = {}

    def fake_core_quota_payload(tool_key, profile_name, command, env, cwd, **kwargs):
        captured["timeout_seconds"] = kwargs.get("timeout_seconds")
        return {"tool": tool_key, "profile": profile_name, "quota": {"state": "available", "limits": {}}}

    monkeypatch.setattr(operations, "core_quota_payload", fake_core_quota_payload)
    monkeypatch.setattr(operations, "run_persistent_cli_quota_snapshot", lambda *args, **kwargs: "ok")
    monkeypatch.chdir(tmp_path)

    operations.quota_payload("agy", 1)

    assert captured["timeout_seconds"] == 120


def test_agy_quota_backend_selection_auto_prefers_tmux(monkeypatch):
    import cli_profile_manager.quota as quota

    monkeypatch.delenv("AI_MAN_AGY_QUOTA_BACKEND", raising=False)
    monkeypatch.setattr(quota.shutil, "which", lambda name: "/usr/bin/tmux" if name == "tmux" else None)

    assert quota.resolve_quota_backend("agy") == "tmux"
    assert quota.resolve_quota_backend("codex") == "persistent_pty"


def test_agy_quota_backend_selection_auto_falls_back_to_pty(monkeypatch):
    import cli_profile_manager.quota as quota

    monkeypatch.setenv("AI_MAN_AGY_QUOTA_BACKEND", "auto")
    monkeypatch.setattr(quota.shutil, "which", lambda name: None)

    assert quota.resolve_quota_backend("agy") == "persistent_pty"


def test_agy_quota_backend_selection_forced_pty(monkeypatch):
    import cli_profile_manager.quota as quota

    monkeypatch.setenv("AI_MAN_AGY_QUOTA_BACKEND", "pty")
    monkeypatch.setattr(quota.shutil, "which", lambda name: "/usr/bin/tmux")

    assert quota.resolve_quota_backend("agy") == "persistent_pty"


def test_agy_quota_backend_selection_forced_tmux_missing(monkeypatch):
    import cli_profile_manager.quota as quota

    monkeypatch.setenv("AI_MAN_AGY_QUOTA_BACKEND", "tmux")
    monkeypatch.setattr(quota.shutil, "which", lambda name: None)

    with pytest.raises(quota.QuotaProbeError) as exc_info:
        quota.resolve_quota_backend("agy")
    assert exc_info.value.state == "missing_backend"


def test_direct_prompt_runner_marks_success(monkeypatch, tmp_path):
    import cli_profile_manager.quota as quota

    fake_cli = tmp_path / "agy1"
    fake_cli.write_text(
        "\n".join([
            "#!/usr/bin/env python3",
            "import sys",
            "print('reviewed: ok')",
            "assert sys.argv[1:] == ['-p', 'review this code in one sentence']",
        ]),
        encoding="utf-8",
    )
    fake_cli.chmod(0o755)
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ.get('PATH', '')}")

    screen = quota.run_direct_cli_prompt_snapshot(
        "agy",
        ["agy1", "-p", "review this code in one sentence"],
        os.environ.copy(),
        str(tmp_path),
        timeout_seconds=2,
    )
    parsed = quota.parse_quota("agy", screen)

    assert parsed["state"] == "available"
    assert parsed["source_command"] == "agy-profile-prompt"
    assert "quota percentages are not available" in parsed["warnings"][0]


def test_direct_prompt_runner_classifies_capacity_exhausted(monkeypatch, tmp_path):
    import cli_profile_manager.quota as quota

    fake_cli = tmp_path / "agy1"
    fake_cli.write_text(
        "\n".join([
            "#!/usr/bin/env python3",
            "import sys",
            "print('Error: You have exhausted your capacity on this model. Your quota will reset after 50h10m11s.', file=sys.stderr)",
            "raise SystemExit(1)",
        ]),
        encoding="utf-8",
    )
    fake_cli.chmod(0o755)
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ.get('PATH', '')}")

    payload = quota.quota_payload(
        "agy",
        "p1",
        ["agy1", "-p", "review this code in one sentence"],
        os.environ.copy(),
        str(tmp_path),
        timeout_seconds=2,
        runner=quota.run_direct_cli_prompt_snapshot,
    )

    assert payload["quota"]["state"] == "resource_exhausted"
    assert payload["quota"]["source_command"] == "agy1 -p review this code in one sentence"
    assert "quota or resources are exhausted" in payload["quota"]["warnings"][0]


def test_interactive_uses_longer_agy_quota_timeout(monkeypatch):
    import cli_profile_manager.interactive as interactive

    monkeypatch.delenv("AI_MAN_INTERACTIVE_QUOTA_TIMEOUT", raising=False)
    monkeypatch.delenv("AI_MAN_INTERACTIVE_AGY_QUOTA_TIMEOUT", raising=False)

    assert interactive.interactive_quota_timeout("agy") == 120.0
    assert interactive.interactive_quota_timeout("codex") == 12.0


def test_interactive_unknown_quota_cache_is_retryable(monkeypatch):
    import cli_profile_manager.interactive as interactive

    calls = []

    def fake_quota_payload(tool_key, profile_num, timeout_seconds):
        calls.append((tool_key, profile_num, timeout_seconds))
        return {
            "quota": {
                "state": "unknown",
                "limits": {},
            },
        }

    monkeypatch.setattr(interactive, "quota_payload", fake_quota_payload)
    monkeypatch.setattr(interactive, "time", type("FakeTime", (), {"time": staticmethod(lambda: 100.0)})())
    interactive.invalidate_quota_cache()

    interactive.load_quota_background("agy", 1)
    entry = interactive.quota_cache_entry("agy", 1)

    assert entry["state"] == "retryable"
    assert calls == [("agy", 1, 120.0)]


def test_interactive_agy_quota_cache_is_per_profile(monkeypatch):
    import cli_profile_manager.interactive as interactive

    calls = []

    def fake_quota_payload(tool_key, profile_num, timeout_seconds):
        calls.append((tool_key, profile_num, timeout_seconds))
        return {
            "quota": {
                "state": "available",
                "limits": {"daily": {"percent": 40 + profile_num}},
            },
        }

    monkeypatch.setattr(interactive, "quota_payload", fake_quota_payload)
    interactive.invalidate_quota_cache()

    first = interactive.ensure_quota_loading("agy", 1)
    second = interactive.ensure_quota_loading("agy", 2)
    first["future"].result(timeout=1)
    second["future"].result(timeout=1)

    assert sorted(calls) == [("agy", 1, 120.0), ("agy", 2, 120.0)]
    assert interactive.quota_cache_key("agy", 1) != interactive.quota_cache_key("agy", 2)
    assert interactive.quota_cache_entry("agy", 1)["quota"]["limits"]["daily"]["percent"] == 41
    assert interactive.quota_cache_entry("agy", 2)["quota"]["limits"]["daily"]["percent"] == 42


def test_interactive_quota_loads_are_not_serialized(monkeypatch):
    import cli_profile_manager.interactive as interactive

    calls = []
    entered = threading.Event()
    release = threading.Event()

    def fake_quota_payload(tool_key, profile_num, timeout_seconds):
        calls.append(profile_num)
        if len(calls) == 2:
            entered.set()
        release.wait(1)
        return {
            "quota": {
                "state": "available",
                "limits": {"daily": {"percent": 40 + profile_num}},
            },
        }

    monkeypatch.setattr(interactive, "quota_payload", fake_quota_payload)
    interactive.invalidate_quota_cache()

    first = interactive.ensure_quota_loading("agy", 1)
    second = interactive.ensure_quota_loading("agy", 2)

    assert entered.wait(0.5)
    release.set()
    first["future"].result(timeout=1)
    second["future"].result(timeout=1)
    assert sorted(calls) == [1, 2]


def test_interactive_agy_quota_scheduler_respects_configured_concurrency(monkeypatch):
    import cli_profile_manager.interactive as interactive

    active = 0
    max_active = 0
    lock = threading.Lock()
    entered = threading.Event()
    release = threading.Event()

    def fake_quota_payload(tool_key, profile_num, timeout_seconds):
        nonlocal active, max_active
        with lock:
            active += 1
            max_active = max(max_active, active)
            if active == 2:
                entered.set()
        release.wait(1)
        with lock:
            active -= 1
        return {
            "quota": {
                "state": "available",
                "limits": {"daily": {"percent": profile_num}},
            },
        }

    monkeypatch.setenv("AI_MAN_INTERACTIVE_AGY_QUOTA_CONCURRENCY", "2")
    monkeypatch.setattr(interactive, "quota_payload", fake_quota_payload)
    interactive.invalidate_quota_cache()

    entries = [interactive.ensure_quota_loading("agy", n) for n in range(1, 12)]
    assert entered.wait(0.5)
    assert max_active == 2
    release.set()
    for entry in entries:
        entry["future"].result(timeout=1)


def test_interactive_duplicate_quota_schedule_reuses_one_job(monkeypatch):
    import cli_profile_manager.interactive as interactive

    calls = []
    release = threading.Event()

    def fake_quota_payload(tool_key, profile_num, timeout_seconds):
        calls.append(profile_num)
        release.wait(1)
        return {
            "quota": {
                "state": "available",
                "limits": {"daily": {"percent": 90}},
            },
        }

    monkeypatch.setattr(interactive, "quota_payload", fake_quota_payload)
    interactive.invalidate_quota_cache()

    first = interactive.ensure_quota_loading("agy", 1)
    second = interactive.ensure_quota_loading("agy", 1)

    assert first is second
    release.set()
    first["future"].result(timeout=1)
    assert calls == [1]


def test_interactive_quota_scheduler_reports_coalesced_jobs(monkeypatch):
    import cli_profile_manager.interactive as interactive

    release = threading.Event()

    def fake_quota_payload(tool_key, profile_num, timeout_seconds):
        release.wait(1)
        return {
            "quota": {
                "state": "available",
                "limits": {"daily": {"percent": 90}},
            },
        }

    monkeypatch.setattr(interactive, "quota_payload", fake_quota_payload)
    interactive.invalidate_quota_cache()

    scheduler = interactive.quota_scheduler()
    before = scheduler.metrics_snapshot()
    first = interactive.ensure_quota_loading("agy", 1)
    second = interactive.ensure_quota_loading("agy", 1)

    assert first is second
    release.set()
    first["future"].result(timeout=1)
    metrics = scheduler.metrics_snapshot()
    assert metrics["submitted"] == before["submitted"] + 1
    assert metrics["queued"] == before["queued"] + 1
    assert metrics["coalesced"] == before["coalesced"] + 1
    assert metrics["started"] >= before["started"] + 1
    assert metrics["completed"] >= before["completed"] + 1


def test_interactive_status_collection_does_not_wait_for_quota_worker(monkeypatch, tmp_path):
    pm = load_pm(monkeypatch, tmp_path)
    agy_token = tmp_path / "agy-homes" / "p1" / ".gemini" / "oauth_creds.json"
    write_json(agy_token, {"refresh_token": "r"})

    import cli_profile_manager.interactive as interactive

    release = threading.Event()

    def fake_quota_payload(tool_key, profile_num, timeout_seconds):
        release.wait(1)
        return {
            "quota": {
                "state": "available",
                "limits": {"daily": {"percent": 50}},
            },
        }

    monkeypatch.setattr(interactive, "quota_payload", fake_quota_payload)
    interactive.invalidate_quota_cache()

    status = interactive.status_with_auto_quota("agy", 1, {})

    assert status["has_token"] is True
    assert status["quota"]["state"] == "loading"
    release.set()
    interactive.quota_cache_entry("agy", 1)["future"].result(timeout=1)


@pytest.mark.parametrize(
    ("state", "warning"),
    [
        ("timeout", "timeout waiting for CLI output"),
        ("resource_limited", "failed to apply quota process limits with backend setrlimit"),
    ],
)
def test_interactive_stale_quota_survives_failed_refresh(monkeypatch, state, warning):
    import cli_profile_manager.interactive as interactive

    def fake_quota_payload(tool_key, profile_num, timeout_seconds):
        return {
            "quota": {
                "state": state,
                "limits": {},
                "warnings": [warning],
            },
        }

    monkeypatch.setattr(interactive, "quota_payload", fake_quota_payload)
    monkeypatch.setenv("AI_MAN_INTERACTIVE_QUOTA_FRESH_SECONDS", "600")
    interactive.invalidate_quota_cache()
    stale_fetched_at = interactive.time.time() - interactive.interactive_quota_fresh_seconds() - 1
    interactive.store_quota_cache("agy", 1, {
        "state": "ready",
        "job_state": "ready",
        "quota": {
            "state": "available",
            "limits": {"daily": {"percent": 77}},
            "fetched_at": 100.0,
        },
        "fetched_at": stale_fetched_at,
        "started_at": None,
        "attempts": 0,
        "last_error": None,
        "next_retry_at": None,
    })

    entry = interactive.ensure_quota_loading("agy", 1)
    entry["future"].result(timeout=1)
    refreshed = interactive.quota_cache_entry("agy", 1)

    assert stale_fetched_at
    assert refreshed["state"] == "retryable"
    assert refreshed["quota"]["state"] == "available"
    assert refreshed["quota"]["limits"]["daily"]["percent"] == 77
    assert refreshed["last_error"]["state"] == state
    assert warning in refreshed["quota"]["warnings"]


def test_interactive_retry_backoff_prevents_tight_retry_loop(monkeypatch):
    import cli_profile_manager.interactive as interactive

    calls = []

    def fake_quota_payload(tool_key, profile_num, timeout_seconds):
        calls.append(profile_num)
        return {
            "quota": {
                "state": "unknown",
                "limits": {},
                "warnings": ["quota output was captured but no known quota fields matched"],
            },
        }

    monkeypatch.setattr(interactive, "quota_payload", fake_quota_payload)
    interactive.invalidate_quota_cache()

    first = interactive.ensure_quota_loading("agy", 1)
    first["future"].result(timeout=1)
    second = interactive.ensure_quota_loading("agy", 1)

    assert second["job_state"] == "retryable"
    assert calls == [1]


def test_interactive_auth_required_maps_to_terminal_state(monkeypatch):
    import cli_profile_manager.interactive as interactive

    def fake_quota_payload(tool_key, profile_num, timeout_seconds):
        return {
            "quota": {
                "state": "auth_required",
                "limits": {},
                "warnings": ["CLI reported that authentication is required"],
            },
        }

    monkeypatch.setattr(interactive, "quota_payload", fake_quota_payload)
    interactive.invalidate_quota_cache()

    entry = interactive.ensure_quota_loading("agy", 1)
    entry["future"].result(timeout=1)
    refreshed = interactive.quota_cache_entry("agy", 1)

    assert refreshed["machine_state"] == "auth_required"
    assert refreshed["quota"]["pipeline_state"] == "auth_required"
    assert refreshed["last_error"]["state"] == "auth_required"
    assert refreshed["next_retry_at"] is None
    assert interactive.schedule_due_quota_refresh("agy", now=interactive.time.time() + 3600) == 0


@pytest.mark.parametrize("state", ["resource_exhausted", "account_ineligible", "timeout"])
def test_interactive_terminal_quota_failures_do_not_auto_retry(monkeypatch, state):
    import cli_profile_manager.interactive as interactive

    def fake_quota_payload(tool_key, profile_num, timeout_seconds):
        return {
            "quota": {
                "state": state,
                "limits": {},
                "warnings": [f"{state} warning"],
            },
        }

    monkeypatch.setattr(interactive, "quota_payload", fake_quota_payload)
    interactive.invalidate_quota_cache()

    entry = interactive.ensure_quota_loading("agy", 1)
    entry["future"].result(timeout=1)
    refreshed = interactive.quota_cache_entry("agy", 1)

    assert refreshed["machine_state"] == "failed"
    assert refreshed["job_state"] == "failed"
    assert refreshed["last_error"]["state"] == state
    assert refreshed["next_retry_at"] is None
    assert interactive.schedule_due_quota_refresh("agy", now=interactive.time.time() + 3600) == 0


def test_interactive_next_quota_wake_timeout_for_active_retryable_and_idle():
    import cli_profile_manager.interactive as interactive

    interactive.invalidate_quota_cache()

    assert interactive.next_quota_wake_timeout("agy", now=100.0) is None

    interactive.store_quota_cache("agy", 1, {
        "state": "queued",
        "job_state": "queued",
        "quota": {"state": "loading", "limits": {}},
        "next_retry_at": None,
    })
    assert interactive.next_quota_wake_timeout("agy", now=100.0) == 0.5

    interactive.invalidate_quota_cache()
    interactive.store_quota_cache("agy", 1, {
        "state": "retryable",
        "job_state": "retryable",
        "quota": {"state": "parser_miss", "limits": {}},
        "next_retry_at": 100.2,
    })
    assert interactive.next_quota_wake_timeout("agy", now=100.0) == pytest.approx(0.2)
    assert interactive.next_quota_wake_timeout("agy", now=100.3) == 0.0

    interactive.invalidate_quota_cache()


def test_interactive_retry_wait_stale_quota_can_refresh(monkeypatch):
    import cli_profile_manager.interactive as interactive

    submitted = []

    class FakeScheduler:
        def submit(self, tool_key, profile_num, priority=10):
            submitted.append((tool_key, profile_num, priority))
            return object()

    monkeypatch.setattr(interactive, "quota_scheduler", lambda: FakeScheduler())
    monkeypatch.setenv("AI_MAN_INTERACTIVE_QUOTA_FRESH_SECONDS", "600")
    interactive.invalidate_quota_cache()
    stale_fetched_at = interactive.time.time() - interactive.interactive_quota_fresh_seconds() - 1
    interactive.store_quota_cache("agy", 1, {
        "state": "retryable",
        "job_state": "retryable",
        "machine_state": "retry_wait",
        "quota": {
            "state": "available",
            "limits": {"daily": {"percent": 77}},
            "fetched_at": stale_fetched_at,
            "pipeline_state": "retry_wait",
        },
        "fetched_at": stale_fetched_at,
        "started_at": None,
        "attempts": 1,
        "last_error": {"state": "process_exit", "message": "previous failure"},
        "next_retry_at": 700.0,
    })

    entry = interactive.ensure_quota_loading("agy", 1)

    assert submitted == [("agy", 1, 10)]
    assert entry["machine_state"] == "stale_refreshing"
    assert entry["quota"]["state"] == "available"
    assert entry["quota"]["limits"]["daily"]["percent"] == 77
    assert entry["quota"]["job_state"] == "queued"
    interactive.invalidate_quota_cache()


def test_interactive_next_quota_wake_timeout_tracks_auto_refresh(monkeypatch):
    import cli_profile_manager.interactive as interactive

    monkeypatch.setenv("AI_MAN_INTERACTIVE_QUOTA_FRESH_SECONDS", "600")
    interactive.invalidate_quota_cache()
    interactive.store_quota_cache("agy", 1, {
        "state": "ready",
        "job_state": "ready",
        "quota": {
            "state": "available",
            "limits": {"daily": {"percent": 77}},
            "fetched_at": 100.0,
        },
        "fetched_at": 100.0,
        "started_at": None,
        "attempts": 0,
        "last_error": None,
        "next_retry_at": None,
    })

    assert interactive.next_quota_wake_timeout("agy", now=699.8) == pytest.approx(0.2)
    assert interactive.next_quota_wake_timeout("agy", now=700.0) == 0.0
    assert interactive.quota_refresh_countdown("agy", now=640.0) == "1m00s"
    assert interactive.quota_refresh_countdown("agy", now=700.0) == "now"
    interactive.invalidate_quota_cache()


def test_interactive_schedule_due_quota_refresh_enqueues_expired_available_quota(monkeypatch):
    import cli_profile_manager.interactive as interactive

    submitted = []

    class FakeScheduler:
        def submit(self, tool_key, profile_num, priority=10):
            submitted.append((tool_key, profile_num, priority))
            return object()

    monkeypatch.setenv("AI_MAN_INTERACTIVE_QUOTA_FRESH_SECONDS", "600")
    monkeypatch.setattr(interactive, "quota_scheduler", lambda: FakeScheduler())
    interactive.invalidate_quota_cache()
    interactive.store_quota_cache("agy", 1, {
        "state": "ready",
        "job_state": "ready",
        "machine_state": "available",
        "quota": {
            "state": "available",
            "limits": {"daily": {"percent": 77}},
            "fetched_at": 100.0,
        },
        "fetched_at": 100.0,
        "started_at": None,
        "attempts": 0,
        "last_error": None,
        "next_retry_at": None,
    })

    assert interactive.schedule_due_quota_refresh("agy", now=700.0) == 1
    entry = interactive.quota_cache_entry("agy", 1)

    assert submitted == [("agy", 1, 5)]
    assert entry["machine_state"] == "stale_refreshing"
    assert entry["job_state"] == "queued"
    assert entry["quota"]["job_state"] == "queued"
    assert interactive.schedule_due_quota_refresh("agy", now=700.0) == 0
    interactive.invalidate_quota_cache()


def test_interactive_schedule_due_quota_refresh_respects_retry_backoff(monkeypatch):
    import cli_profile_manager.interactive as interactive

    submitted = []

    class FakeScheduler:
        def submit(self, tool_key, profile_num, priority=10):
            submitted.append((tool_key, profile_num, priority))
            return object()

    monkeypatch.setenv("AI_MAN_INTERACTIVE_QUOTA_FRESH_SECONDS", "600")
    monkeypatch.setattr(interactive, "quota_scheduler", lambda: FakeScheduler())
    interactive.invalidate_quota_cache()
    interactive.store_quota_cache("agy", 1, {
        "state": "retryable",
        "job_state": "retryable",
        "machine_state": "retry_wait",
        "quota": {
            "state": "available",
            "limits": {"daily": {"percent": 77}},
            "fetched_at": 100.0,
        },
        "fetched_at": 100.0,
        "started_at": None,
        "attempts": 5,
        "last_error": {"state": "empty_output", "message": "quota command returned no readable output"},
        "next_retry_at": 760.0,
    })

    assert interactive.schedule_due_quota_refresh("agy", now=700.0) == 0
    assert submitted == []
    assert interactive.schedule_due_quota_refresh("agy", now=760.0) == 1
    assert submitted == [("agy", 1, 5)]
    interactive.invalidate_quota_cache()


def test_interactive_force_refresh_preserves_stale_quota(monkeypatch):
    import cli_profile_manager.interactive as interactive

    submitted = []

    class FakeScheduler:
        def submit(self, tool_key, profile_num, priority=10):
            submitted.append((tool_key, profile_num, priority))
            return object()

    monkeypatch.setattr(interactive, "quota_scheduler", lambda: FakeScheduler())
    interactive.invalidate_quota_cache()
    interactive.store_quota_cache("agy", 1, {
        "state": "ready",
        "job_state": "ready",
        "quota": {
            "state": "available",
            "limits": {"daily": {"percent": 77}},
            "fetched_at": 100.0,
        },
        "fetched_at": 100.0,
        "started_at": None,
        "attempts": 0,
        "last_error": None,
        "next_retry_at": None,
    })

    assert interactive.force_quota_refresh("agy") == 1
    entry = interactive.quota_cache_entry("agy", 1)

    assert submitted == [("agy", 1, 0)]
    assert entry["job_state"] == "queued"
    assert entry["quota"]["limits"]["daily"]["percent"] == 77
    assert entry["quota"]["job_state"] == "queued"
    interactive.invalidate_quota_cache()


def test_persistent_quota_runner_reuses_session(monkeypatch, tmp_path):
    import cli_profile_manager.quota as quota

    monkeypatch.setenv("AI_MAN_AGY_QUOTA_BACKEND", "pty")
    created = []

    class FakeSession:
        def __init__(self, tool_key, command, env, cwd):
            self.tool_key = tool_key
            self.command = command
            self.env = env
            self.cwd = cwd
            self.closed = False
            created.append(self)

        def snapshot(self, timeout_seconds=quota.DEFAULT_TIMEOUT_SECONDS, idle_seconds=quota.DEFAULT_IDLE_SECONDS):
            return "Daily limit 50% remaining"

        def is_alive(self):
            return not self.closed

        def close(self):
            self.closed = True

    quota.close_persistent_quota_sessions()
    monkeypatch.setattr(quota, "PersistentQuotaSession", FakeSession)

    env = {"HOME": str(tmp_path / "p1")}
    first = quota.run_persistent_cli_quota_snapshot("agy", ["agy"], env, str(tmp_path))
    second = quota.run_persistent_cli_quota_snapshot("agy", ["agy"], env, str(tmp_path))

    assert first == "Daily limit 50% remaining"
    assert second == "Daily limit 50% remaining"
    assert len(created) == 1
    quota.close_persistent_quota_sessions()


def test_persistent_quota_runner_uses_separate_sessions_per_profile(monkeypatch, tmp_path):
    import cli_profile_manager.quota as quota

    monkeypatch.setenv("AI_MAN_AGY_QUOTA_BACKEND", "pty")
    created = []

    class FakeSession:
        def __init__(self, tool_key, command, env, cwd):
            self.env = env
            self.closed = False
            created.append(self)

        def snapshot(self, timeout_seconds=quota.DEFAULT_TIMEOUT_SECONDS, idle_seconds=quota.DEFAULT_IDLE_SECONDS):
            return "Daily limit 50% remaining"

        def is_alive(self):
            return not self.closed

        def close(self):
            self.closed = True

    quota.close_persistent_quota_sessions()
    monkeypatch.setattr(quota, "PersistentQuotaSession", FakeSession)

    quota.run_persistent_cli_quota_snapshot("agy", ["agy"], {"HOME": str(tmp_path / "p1")}, str(tmp_path / "p1"))
    quota.run_persistent_cli_quota_snapshot("agy", ["agy"], {"HOME": str(tmp_path / "p2")}, str(tmp_path / "p2"))

    assert len(created) == 2
    quota.close_persistent_quota_sessions()


def test_persistent_quota_runner_replaces_dead_session(monkeypatch, tmp_path):
    import cli_profile_manager.quota as quota

    monkeypatch.setenv("AI_MAN_AGY_QUOTA_BACKEND", "pty")
    created = []

    class FakeSession:
        def __init__(self, tool_key, command, env, cwd):
            self.closed = False
            created.append(self)

        def snapshot(self, timeout_seconds=quota.DEFAULT_TIMEOUT_SECONDS, idle_seconds=quota.DEFAULT_IDLE_SECONDS):
            if len(created) == 1:
                self.closed = True
                raise quota.QuotaProbeError("process_exit", "process exited")
            return "Daily limit 55% remaining"

        def is_alive(self):
            return not self.closed

        def close(self):
            self.closed = True

    quota.close_persistent_quota_sessions()
    monkeypatch.setattr(quota, "PersistentQuotaSession", FakeSession)
    env = {"HOME": str(tmp_path / "p1")}

    with pytest.raises(quota.QuotaProbeError):
        quota.run_persistent_cli_quota_snapshot("agy", ["agy"], env, str(tmp_path / "p1"))
    assert quota.run_persistent_cli_quota_snapshot("agy", ["agy"], env, str(tmp_path / "p1")) == "Daily limit 55% remaining"
    assert len(created) == 2
    quota.close_persistent_quota_sessions()


def test_persistent_quota_runner_invalidates_timeout_session_only(monkeypatch, tmp_path):
    import cli_profile_manager.quota as quota

    monkeypatch.setenv("AI_MAN_AGY_QUOTA_BACKEND", "pty")
    created = []
    calls = {}

    class FakeSession:
        def __init__(self, tool_key, command, env, cwd):
            self.env = env
            self.cwd = cwd
            self.closed = False
            created.append(self)

        def snapshot(self, timeout_seconds=quota.DEFAULT_TIMEOUT_SECONDS, idle_seconds=quota.DEFAULT_IDLE_SECONDS):
            calls[self.cwd] = calls.get(self.cwd, 0) + 1
            if self.cwd.endswith("p1") and calls[self.cwd] == 1:
                raise quota.QuotaProbeError("timeout", "timeout waiting for CLI output")
            return "Daily limit 55% remaining"

        def is_alive(self):
            return not self.closed

        def close(self):
            self.closed = True

    quota.close_persistent_quota_sessions()
    monkeypatch.setattr(quota, "PersistentQuotaSession", FakeSession)
    home1 = str(tmp_path / "p1")
    home2 = str(tmp_path / "p2")

    quota.run_persistent_cli_quota_snapshot("agy", ["agy"], {"HOME": home2}, home2)
    with pytest.raises(quota.QuotaProbeError):
        quota.run_persistent_cli_quota_snapshot("agy", ["agy"], {"HOME": home1}, home1)
    assert created[1].closed is True
    assert created[0].closed is False

    assert quota.run_persistent_cli_quota_snapshot("agy", ["agy"], {"HOME": home1}, home1) == "Daily limit 55% remaining"
    assert len(created) == 3
    quota.close_persistent_quota_sessions()


def test_persistent_quota_runner_keeps_agy_startup_pending_session(monkeypatch, tmp_path):
    import cli_profile_manager.quota as quota

    monkeypatch.setenv("AI_MAN_AGY_QUOTA_BACKEND", "pty")
    created = []
    calls = 0

    class FakeSession:
        def __init__(self, tool_key, command, env, cwd):
            self.closed = False
            created.append(self)

        def snapshot(self, timeout_seconds=quota.DEFAULT_TIMEOUT_SECONDS, idle_seconds=quota.DEFAULT_IDLE_SECONDS):
            nonlocal calls
            calls += 1
            if calls == 1:
                raise quota.QuotaProbeError("startup_pending", "AGY CLI is still starting")
            return "Daily limit 55% remaining"

        def is_alive(self):
            return not self.closed

        def close(self):
            self.closed = True

    quota.close_persistent_quota_sessions()
    monkeypatch.setattr(quota, "PersistentQuotaSession", FakeSession)
    env = {"HOME": str(tmp_path / "p1")}

    with pytest.raises(quota.QuotaProbeError):
        quota.run_persistent_cli_quota_snapshot("agy", ["agy"], env, str(tmp_path / "p1"))

    assert created[0].closed is False
    assert quota.run_persistent_cli_quota_snapshot("agy", ["agy"], env, str(tmp_path / "p1")) == "Daily limit 55% remaining"
    assert len(created) == 1
    quota.close_persistent_quota_sessions()


def test_persistent_quota_evict_skips_starting_session(tmp_path):
    import cli_profile_manager.quota as quota

    quota.close_persistent_quota_sessions()
    home = str(tmp_path / "p1")
    session = quota.PersistentQuotaSession("agy", ["agy"], {"HOME": home}, home)
    session.starting = True
    session.master_fd = 123
    session.last_used_at = 10.0
    key = quota.persistent_quota_session_key("agy", ["agy"], {"HOME": home}, home)

    with quota.PERSISTENT_QUOTA_LOCK:
        quota.PERSISTENT_QUOTA_SESSIONS[key] = session

    assert quota.evict_persistent_quota_sessions(now=20.0) == 0
    assert quota.persistent_quota_sessions_snapshot("agy")["count"] == 1
    quota.close_persistent_quota_sessions()


def test_persistent_quota_parser_miss_threshold_invalidates_session(monkeypatch, tmp_path):
    import cli_profile_manager.quota as quota

    monkeypatch.setenv("AI_MAN_AGY_QUOTA_BACKEND", "pty")
    created = []

    class FakeSession:
        def __init__(self, tool_key, command, env, cwd):
            self.closed = False
            created.append(self)

        def snapshot(self, timeout_seconds=quota.DEFAULT_TIMEOUT_SECONDS, idle_seconds=quota.DEFAULT_IDLE_SECONDS):
            return "Antigravity layout without quota rows"

        def is_alive(self):
            return not self.closed

        def close(self):
            self.closed = True

    quota.close_persistent_quota_sessions()
    monkeypatch.setattr(quota, "PersistentQuotaSession", FakeSession)
    home = str(tmp_path / "p1")

    for _ in range(quota.PARSER_MISS_SESSION_INVALIDATION_THRESHOLD):
        payload = quota.quota_payload(
            "agy",
            "p1",
            ["agy"],
            {"HOME": home},
            home,
            runner=quota.run_persistent_cli_quota_snapshot,
        )
        assert payload["quota"]["state"] == "parser_miss"

    assert created[0].closed is True
    quota.run_persistent_cli_quota_snapshot("agy", ["agy"], {"HOME": home}, home)
    assert len(created) == 2
    quota.close_persistent_quota_sessions()


def test_persistent_quota_sessions_evict_idle_and_dead_sessions(monkeypatch, tmp_path):
    import cli_profile_manager.quota as quota

    class FakeSession:
        def __init__(self, home, last_used_at, alive=True):
            self.tool_key = "agy"
            self.command = ["agy"]
            self.env = {"HOME": home}
            self.cwd = home
            self.created_at = last_used_at
            self.last_used_at = last_used_at
            self.alive = alive
            self.closed = False

        def is_alive(self):
            return self.alive and not self.closed

        def close(self):
            self.closed = True

    quota.close_persistent_quota_sessions()
    monkeypatch.setenv("AI_MAN_QUOTA_SESSION_TTL_SECONDS", "10")
    stale_home = str(tmp_path / "stale")
    dead_home = str(tmp_path / "dead")
    fresh_home = str(tmp_path / "fresh")
    stale = FakeSession(stale_home, 80.0)
    dead = FakeSession(dead_home, 99.0, alive=False)
    fresh = FakeSession(fresh_home, 95.0)

    with quota.PERSISTENT_QUOTA_LOCK:
        quota.PERSISTENT_QUOTA_SESSIONS[quota.persistent_quota_session_key("agy", ["agy"], stale.env, stale.cwd)] = stale
        quota.PERSISTENT_QUOTA_SESSIONS[quota.persistent_quota_session_key("agy", ["agy"], dead.env, dead.cwd)] = dead
        quota.PERSISTENT_QUOTA_SESSIONS[quota.persistent_quota_session_key("agy", ["agy"], fresh.env, fresh.cwd)] = fresh

    assert quota.evict_persistent_quota_sessions(now=100.0) == 2
    assert stale.closed is True
    assert dead.closed is True
    assert fresh.closed is False

    snapshot = quota.persistent_quota_sessions_snapshot("agy")
    assert snapshot["count"] == 1
    assert snapshot["sessions"][0]["home"] == fresh_home
    assert snapshot["sessions"][0]["idle_age_seconds"] >= 0
    quota.close_persistent_quota_sessions()


def test_persistent_quota_sessions_respect_max_count(monkeypatch, tmp_path):
    import cli_profile_manager.quota as quota

    class FakeSession:
        def __init__(self, home, last_used_at):
            self.tool_key = "agy"
            self.command = ["agy"]
            self.env = {"HOME": home}
            self.cwd = home
            self.created_at = last_used_at
            self.last_used_at = last_used_at
            self.closed = False

        def is_alive(self):
            return not self.closed

        def close(self):
            self.closed = True

    quota.close_persistent_quota_sessions()
    monkeypatch.setenv("AI_MAN_QUOTA_SESSION_MAX", "1")
    older = FakeSession(str(tmp_path / "older"), 10.0)
    newer = FakeSession(str(tmp_path / "newer"), 20.0)

    with quota.PERSISTENT_QUOTA_LOCK:
        quota.PERSISTENT_QUOTA_SESSIONS[quota.persistent_quota_session_key("agy", ["agy"], older.env, older.cwd)] = older
        quota.PERSISTENT_QUOTA_SESSIONS[quota.persistent_quota_session_key("agy", ["agy"], newer.env, newer.cwd)] = newer

    assert quota.evict_persistent_quota_sessions(now=30.0) == 1
    assert older.closed is True
    assert newer.closed is False
    assert quota.persistent_quota_sessions_snapshot("agy")["count"] == 1
    quota.close_persistent_quota_sessions()


def test_tmux_quota_session_name_is_stable_and_profile_scoped(tmp_path):
    import cli_profile_manager.quota as quota

    cwd = str(tmp_path)
    p1 = {"HOME": str(tmp_path / "agy-homes" / "p1")}
    p2 = {"HOME": str(tmp_path / "agy-homes" / "p2")}

    first = quota.tmux_quota_session_name("agy", ["agy"], p1, cwd)
    second = quota.tmux_quota_session_name("agy", ["agy"], p1, cwd)
    other = quota.tmux_quota_session_name("agy", ["agy"], p2, cwd)

    assert first == second
    assert first != other
    assert first.startswith("ai_man_quota_agy_p1_")
    assert "/" not in first


def test_tmux_quota_session_uses_expected_commands(monkeypatch, tmp_path):
    import cli_profile_manager.quota as quota

    calls = []
    screen = (
        "Antigravity CLI 1.1.1\n"
        "Eligibility Check\n"
        "not currently available in your location\n"
        ">\n"
        "? for shortcuts\n"
        "Account: user@example.com\n"
        "Gemini 3.5 Flash Medium\n"
        "Usage 94% remaining\n"
    )

    def fake_which(name):
        return f"/usr/bin/{name}" if name in ("tmux", "agy") else None

    def fake_run(args, text=True, capture_output=True, timeout=5, check=False):
        calls.append(args)
        if "has-session" in args:
            return types.SimpleNamespace(returncode=0, stdout="", stderr="")
        if "capture-pane" in args:
            return types.SimpleNamespace(returncode=0, stdout=screen, stderr="")
        return types.SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(quota.shutil, "which", fake_which)
    monkeypatch.setattr(quota.subprocess, "run", fake_run)
    monkeypatch.setenv("AI_MAN_QUOTA_POST_COMMAND_SECONDS", "0")

    home = str(tmp_path / "agy-homes" / "p1")
    session = quota.TmuxQuotaSession("agy", ["agy"], {"HOME": home}, str(tmp_path))
    session.start(timeout_seconds=1)
    captured = session.snapshot(timeout_seconds=1)
    session.close()

    assert captured == screen
    assert any(call[1:5] == ["new-session", "-d", "-s", session.session_name] for call in calls)
    new_session_call = next(call for call in calls if "new-session" in call)
    assert ["-c", str(tmp_path)] == new_session_call[5:7]
    assert f"HOME={home}" in new_session_call
    assert any(call[-2:] == ["/usage", "Enter"] for call in calls)
    assert any("capture-pane" in call and "-S" in call and "-200" in call for call in calls)
    assert any(call[-1:] == ["Escape"] for call in calls)
    assert any(call[1:3] == ["kill-session", "-t"] and call[3] == session.session_name for call in calls)


def test_run_persistent_agy_uses_tmux_in_auto(monkeypatch, tmp_path):
    import cli_profile_manager.quota as quota

    created = []

    class FakeTmuxSession:
        backend = "tmux"

        def __init__(self, tool_key, command, env, cwd):
            self.tool_key = tool_key
            self.command = command
            self.env = env
            self.cwd = cwd
            self.closed = False
            self.created_at = time.time()
            self.last_used_at = self.created_at
            self.session_name = "ai_man_quota_agy_p1_fake"
            created.append(self)

        def snapshot(self, timeout_seconds=quota.DEFAULT_TIMEOUT_SECONDS, idle_seconds=quota.DEFAULT_IDLE_SECONDS):
            return "Daily limit 50% remaining"

        def is_alive(self):
            return not self.closed

        def close(self):
            self.closed = True

    quota.close_persistent_quota_sessions()
    monkeypatch.delenv("AI_MAN_AGY_QUOTA_BACKEND", raising=False)
    monkeypatch.setattr(quota.shutil, "which", lambda name: "/usr/bin/tmux" if name == "tmux" else None)
    monkeypatch.setattr(quota, "TmuxQuotaSession", FakeTmuxSession)

    payload = quota.run_persistent_cli_quota_snapshot("agy", ["agy"], {"HOME": str(tmp_path / "p1")}, str(tmp_path))
    snapshot = quota.persistent_quota_sessions_snapshot("agy")

    assert payload == "Daily limit 50% remaining"
    assert len(created) == 1
    assert snapshot["sessions"][0]["backend"] == "tmux"
    quota.close_persistent_quota_sessions()


def test_interactive_invalidate_closes_matching_persistent_session(monkeypatch, tmp_path):
    import cli_profile_manager.interactive as interactive
    import cli_profile_manager.quota as quota

    monkeypatch.setenv("AI_MAN_AGY_QUOTA_BACKEND", "pty")
    created = []

    class FakeSession:
        def __init__(self, tool_key, command, env, cwd):
            self.env = env
            self.closed = False
            created.append(self)

        def snapshot(self, timeout_seconds=quota.DEFAULT_TIMEOUT_SECONDS, idle_seconds=quota.DEFAULT_IDLE_SECONDS):
            return "Daily limit 50% remaining"

        def is_alive(self):
            return not self.closed

        def close(self):
            self.closed = True

    quota.close_persistent_quota_sessions()
    monkeypatch.setattr(quota, "PersistentQuotaSession", FakeSession)
    home1 = str(tmp_path / "agy-homes" / "p1")
    home2 = str(tmp_path / "agy-homes" / "p2")
    monkeypatch.setattr(interactive, "profile_home", lambda tool_key, n: home1 if n == 1 else home2)

    quota.run_persistent_cli_quota_snapshot("agy", ["agy"], {"HOME": home1}, home1)
    quota.run_persistent_cli_quota_snapshot("agy", ["agy"], {"HOME": home2}, home2)
    interactive.invalidate_quota_cache("agy", 1)

    assert created[0].closed is True
    assert created[1].closed is False
    quota.close_persistent_quota_sessions()


def test_interactive_agy_quota_cells_render_h05_markers():
    from cli_profile_manager.interactive import agy_quota_cells

    columns = ["FM", "FH", "FL", "PL", "PH", "CS", "CO"]

    stale = {
        "quota": {
            "state": "available",
            "job_state": "running",
            "limits": {
                "gemini_3_5_flash_medium": {"model": "Gemini 3.5 Flash (Medium)", "percent": 94},
            },
        },
    }
    failed = {"quota": {"state": "timeout", "job_state": "retryable", "limits": {}}}
    parser_miss = {"quota": {"state": "parser_miss", "limits": {}}}
    startup_pending = {"quota": {"state": "startup_pending", "job_state": "retryable", "limits": {}}}
    no_token = {"quota": {"state": "no_token", "limits": {}}}

    assert agy_quota_cells(stale, columns)[0] == "94%"
    assert agy_quota_cells(failed, columns)[0] == "!"
    assert agy_quota_cells(parser_miss, columns)[0] == "!"
    assert agy_quota_cells(startup_pending, columns)[0] == "..."
    assert agy_quota_cells(no_token, columns) == ["", "", "", "", "", "", ""]


def test_interactive_agy_quota_cells_color_by_percent_and_staleness(monkeypatch):
    import cli_profile_manager.interactive as interactive

    monkeypatch.setenv("AI_MAN_INTERACTIVE_QUOTA_FRESH_SECONDS", "600")
    fresh = {"quota": {"state": "available", "fetched_at": interactive.time.time()}}
    stale = {"quota": {"state": "available", "fetched_at": interactive.time.time() - 601}}

    assert interactive.color_agy_quota_cell("20%", fresh).startswith(interactive.CLR_RED)
    assert interactive.color_agy_quota_cell("21%", fresh).startswith(interactive.CLR_YELLOW)
    assert interactive.color_agy_quota_cell("40%", fresh).startswith(interactive.CLR_YELLOW)
    assert interactive.color_agy_quota_cell("41%", fresh).startswith(interactive.CLR_GREEN)
    assert interactive.color_agy_quota_cell("41%", stale).startswith(interactive.CLR_WHITE)
    assert interactive.color_agy_quota_cell("...", fresh).startswith(interactive.CLR_YELLOW)
    assert interactive.color_agy_quota_cell("!", fresh).startswith(interactive.CLR_RED)


def test_interactive_email_coloring_preserves_visible_width():
    import cli_profile_manager.interactive as interactive

    colored = interactive.color_email_parts("alex123@example.com")

    assert interactive.CLR_CYAN in colored
    assert interactive.CLR_YELLOW in colored
    assert interactive.CLR_MAGENTA in colored
    assert interactive.visible_len(colored) == len("alex123@example.com")


def test_terminal_frame_renderer_initial_diff_shrink_and_resize():
    from cli_profile_manager.terminal_rendering import TerminalFrameRenderer

    class FakeStdout:
        def __init__(self):
            self.writes = []

        def isatty(self):
            return True

        def write(self, value):
            self.writes.append(value)

        def flush(self):
            pass

    sizes = iter([(80, 24), (80, 24), (80, 24), (100, 24)])
    stdout = FakeStdout()
    renderer = TerminalFrameRenderer(stdout=stdout, size_provider=lambda **kwargs: next(sizes))

    renderer.paint(["one", "two", "three"])
    renderer.paint(["one", "TWO", "three"])
    renderer.paint(["one"])
    renderer.paint(["one"])

    assert "\033[H\033[Jone\ntwo\nthree" in stdout.writes[0]
    assert "\033[2;1HTWO\033[K" in stdout.writes[1]
    assert "\033[H" not in stdout.writes[1]
    assert "\033[2;1H\033[J" in stdout.writes[2]
    assert "\033[H\033[Jone" in stdout.writes[3]


def test_terminal_frame_renderer_full_repaint_clears_old_line_tails():
    from cli_profile_manager.terminal_rendering import TerminalFrameRenderer

    class FakeStdout:
        def __init__(self):
            self.writes = []

        def isatty(self):
            return True

        def write(self, value):
            self.writes.append(value)

        def flush(self):
            pass

    stdout = FakeStdout()
    renderer = TerminalFrameRenderer(stdout=stdout)

    renderer.paint(["long previous row"])
    renderer.reset()
    renderer.paint(["short"])

    assert "\033[H\033[Jshort" in stdout.writes[-1]


def test_terminal_frame_renderer_restores_cursor_after_exception():
    from cli_profile_manager.terminal_rendering import TerminalFrameRenderer

    class FakeStdout:
        def __init__(self):
            self.writes = []

        def isatty(self):
            return True

        def write(self, value):
            self.writes.append(value)

        def flush(self):
            pass

    stdout = FakeStdout()

    with pytest.raises(RuntimeError):
        with TerminalFrameRenderer(stdout=stdout) as renderer:
            renderer.paint(["frame"])
            raise RuntimeError("boom")

    assert stdout.writes[0].startswith("\033[?25l")
    assert stdout.writes[-1] == "\033[?25h"


def test_terminal_frame_renderer_non_tty_avoids_control_sequences():
    from cli_profile_manager.terminal_rendering import TerminalFrameRenderer

    class FakeStdout:
        def __init__(self):
            self.writes = []

        def isatty(self):
            return False

        def write(self, value):
            self.writes.append(value)

        def flush(self):
            pass

    stdout = FakeStdout()
    renderer = TerminalFrameRenderer(stdout=stdout)

    renderer.paint(["one", "two"])

    assert stdout.writes == ["one\ntwo\n"]


def test_interactive_status_painter_updates_changed_lines_only(monkeypatch):
    import cli_profile_manager.interactive as interactive

    class FakeStdout:
        def __init__(self):
            self.writes = []

        def isatty(self):
            return True

        def write(self, value):
            self.writes.append(value)

        def flush(self):
            pass

    stdout = FakeStdout()
    monkeypatch.setattr(interactive.sys, "stdout", stdout)
    interactive.STATUS_SCREEN_RENDER_CACHE.clear()

    interactive.paint_terminal_frame(["one", "two"])
    interactive.paint_terminal_frame(["one", "three"])

    assert "\033[H\033[Jone\ntwo" in stdout.writes[0]
    assert "\033[2;1Hthree\033[K" in stdout.writes[1]
    assert "\033[H" not in stdout.writes[1]
    assert "\033[J" not in stdout.writes[1]


def test_interactive_status_render_skips_unchanged_frame(monkeypatch):
    import cli_profile_manager.interactive as interactive

    painted = []
    base_statuses = [
        {
            "num": 1,
            "email": "one@example.com",
            "has_token": False,
            "token_state": "missing",
            "label": "",
        }
    ]

    interactive.reset_status_screen_render()
    monkeypatch.setattr(interactive, "interactive_developer_mode_enabled", lambda: False)
    monkeypatch.setattr(interactive, "interactive_quota_enabled", lambda: False)
    monkeypatch.setattr(interactive, "paint_terminal_frame", lambda lines: painted.append(lines))

    assert interactive.render_status_screen("agy", base_statuses=base_statuses) is True
    assert interactive.render_status_screen("agy", base_statuses=base_statuses) is False
    assert len(painted) == 1

    interactive.reset_status_screen_render()


def test_interactive_status_row_cache_reuses_formatted_rows(monkeypatch):
    import cli_profile_manager.interactive as interactive

    status = {
        "num": 1,
        "email": "one@example.com",
        "has_token": True,
        "label": "work",
        "quota": {
            "state": "available",
            "job_state": "ready",
            "limits": {"daily": {"percent": 77}},
            "fetched_at": interactive.time.time(),
        },
    }
    widths = {"profile": 8, "account": 38, "status": 10, "quota": 5, "label": 14}

    interactive.STATUS_ROW_RENDER_CACHE.clear()
    first = interactive.render_status_row("agy", status, ["FM"], widths, now=100.0)
    second = interactive.render_status_row("agy", status, ["FM"], widths, now=100.0)

    assert first == second
    assert len(interactive.STATUS_ROW_RENDER_CACHE) == 1


def test_interactive_menu_lines_mark_selection_and_fit_footer():
    import cli_profile_manager.interactive as interactive

    lines = interactive.render_menu_lines(["First", "Second"], "MENU", selected_idx=1)
    rendered = "\n".join(lines)

    assert "MENU" in rendered
    assert "-->" in lines[5]
    assert "First" in lines[4]
    assert "Second" in lines[5]
    assert "Enter" in rendered


def test_interactive_menu_lines_can_render_table_header():
    import cli_profile_manager.interactive as interactive

    lines = interactive.render_menu_lines(
        ["p1     account@example.com"],
        "LAUNCH",
        selected_idx=0,
        pre_lines=["      Profile Account Quota", "      ---------------------"],
    )
    rendered = "\n".join(lines)

    assert "Profile Account Quota" in rendered
    assert "p1" in rendered
    assert "-->" in rendered


def test_interactive_settings_duration_parsing_and_formatting():
    import cli_profile_manager.interactive as interactive

    assert interactive.parse_duration_seconds("10m") == 600.0
    assert interactive.parse_duration_seconds("1h") == 3600.0
    assert interactive.parse_duration_seconds("45") == 45.0
    assert interactive.format_duration(600) == "10m"
    assert interactive.format_duration(3600) == "1h"


def test_interactive_settings_menu_lines_show_quota_refresh(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_MAN_METADATA_DIR", str(tmp_path / "metadata"))
    monkeypatch.delenv("AI_MAN_INTERACTIVE_QUOTA_FRESH_SECONDS", raising=False)
    import cli_profile_manager.metadata as metadata
    import cli_profile_manager.interactive as interactive

    metadata.refresh_from_env()
    interactive.INTERACTIVE_SETTINGS_CACHE = None
    interactive.save_interactive_setting(interactive.QUOTA_REFRESH_SETTING_KEY, 900.0)

    rendered = "\n".join(interactive.settings_menu_lines())

    assert "Quota refresh interval" in rendered
    assert "15m" in rendered
    assert "AI_MAN_INTERACTIVE_QUOTA_FRESH_SECONDS" in rendered
    assert "Developer mode" in rendered
    assert "AI_MAN_DEVELOPER_MODE" in rendered


def test_interactive_status_screen_shows_live_logs_in_developer_mode(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_MAN_METADATA_DIR", str(tmp_path / "metadata"))
    monkeypatch.setenv("AI_MAN_DEVELOPER_MODE", "1")
    import cli_profile_manager.metadata as metadata
    import cli_profile_manager.interactive as interactive

    metadata.refresh_from_env()
    log_path = tmp_path / "ai-man.log"
    log_path.write_text(
        "\n".join([
            "debug noise",
            "2026-07-10 16:00:00 - INFO - quota refresh finished tool=agy profile=p1 state=resource_exhausted",
            "2026-07-10 16:00:01 - ERROR - network failed while probing agy2",
        ]),
        encoding="utf-8",
    )
    monkeypatch.setattr(interactive, "interactive_log_path", lambda: str(log_path))
    interactive.invalidate_quota_cache()

    lines = interactive.render_status_screen_lines(
        "agy",
        base_statuses=[{"num": 1, "email": "one@example.com", "has_token": True, "label": ""}],
    )
    rendered = "\n".join(interactive.ANSI_RE.sub("", line) for line in lines)

    assert "Live logs" in rendered
    assert "resource_exhausted" in rendered
    assert "network failed" in rendered


def test_live_log_lines_cache_handles_missing_growing_and_truncated_logs(monkeypatch, tmp_path):
    import cli_profile_manager.interactive as interactive

    log_path = tmp_path / "ai-man.log"
    monkeypatch.setattr(interactive, "interactive_log_path", lambda: str(log_path))
    interactive.reset_live_log_cache()

    assert "log file not found" in interactive.live_log_lines()[0]

    log_path.write_text("debug noise\nERROR first failure\n", encoding="utf-8")
    first = interactive.live_log_lines()
    assert any("first failure" in line for line in first)
    assert len(interactive.LOG_TAIL_CACHE[str(log_path)]["selected"]) == 1

    with log_path.open("a", encoding="utf-8") as handle:
        handle.write("INFO quota refresh finished\n")
    second = interactive.live_log_lines()
    assert any("first failure" in line for line in second)
    assert any("quota refresh" in line for line in second)
    assert len(interactive.LOG_TAIL_CACHE[str(log_path)]["selected"]) == 2

    log_path.write_text("ERROR after rotation\n", encoding="utf-8")
    rotated = interactive.live_log_lines()
    assert any("after rotation" in line for line in rotated)
    assert not any("first failure" in line for line in rotated)


def test_live_log_lines_uses_incremental_reads(monkeypatch, tmp_path):
    import cli_profile_manager.interactive as interactive

    log_path = tmp_path / "ai-man.log"
    log_path.write_text("ERROR first failure\n", encoding="utf-8")
    monkeypatch.setattr(interactive, "interactive_log_path", lambda: str(log_path))
    interactive.reset_live_log_cache()

    interactive.live_log_lines()
    offset = interactive.LOG_TAIL_CACHE[str(log_path)]["offset"]

    with log_path.open("a", encoding="utf-8") as handle:
        handle.write("ERROR second failure\n")
    interactive.live_log_lines()

    assert offset == len("ERROR first failure\n".encode("utf-8"))
    assert interactive.LOG_TAIL_CACHE[str(log_path)]["offset"] == log_path.stat().st_size
    assert len(interactive.LOG_TAIL_CACHE[str(log_path)]["selected"]) == 2


def test_live_log_lines_buffers_partial_appends(monkeypatch, tmp_path):
    import cli_profile_manager.interactive as interactive

    log_path = tmp_path / "ai-man.log"
    log_path.write_text("ERROR first failure\n", encoding="utf-8")
    monkeypatch.setattr(interactive, "interactive_log_path", lambda: str(log_path))
    interactive.reset_live_log_cache()

    interactive.live_log_lines()
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write("ERROR partial")
    partial = interactive.live_log_lines()
    assert not any("partial" in line for line in partial)

    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(" completed\n")
    completed = interactive.live_log_lines()
    assert any("partial completed" in line for line in completed)


def test_interactive_main_shutdown_closes_runtime(monkeypatch):
    import cli_profile_manager.interactive as interactive

    class FakeScheduler:
        def __init__(self):
            self.calls = []

        def shutdown(self, wait=False, timeout=2.0):
            self.calls.append((wait, timeout))

        def wait(self, timeout=2.0):
            self.calls.append(("wait", timeout))

    scheduler = FakeScheduler()
    closed = []
    restored = []

    monkeypatch.setattr(interactive, "INTERACTIVE_QUOTA_SCHEDULER", scheduler)
    monkeypatch.setattr(interactive, "INTERACTIVE_SHUTTING_DOWN", False)
    monkeypatch.setattr(interactive, "install_interactive_signal_handlers", lambda: {"handlers": True})
    monkeypatch.setattr(interactive, "restore_interactive_signal_handlers", lambda handlers: restored.append(handlers))
    monkeypatch.setattr(interactive, "close_persistent_quota_sessions", lambda: closed.append(True))
    monkeypatch.setattr(interactive, "run_menu", lambda *args, **kwargs: 5)
    monkeypatch.setattr(interactive, "clear_screen", lambda: None)

    assert interactive.run_interactive_main() == interactive.EXIT_OK

    assert scheduler.calls == [(False, 2.0), ("wait", 2.0)]
    assert closed == [True]
    assert restored == [{"handlers": True}]
    assert interactive.INTERACTIVE_QUOTA_SCHEDULER is None


def test_launch_account_table_renders_agy_quota_columns():
    import cli_profile_manager.interactive as interactive

    statuses = [
        {
            "num": 1,
            "email": "logged in",
            "has_token": True,
            "label": "work",
            "quota": {
                "state": "available",
                "account": "user@example.com",
                "limits": {
                    "gemini_3_5_flash_medium": {"model": "Gemini 3.5 Flash (Medium)", "percent": 12},
                    "gemini_3_5_flash_high": {"model": "Gemini 3.5 Flash (High)", "percent": 34},
                    "claude_sonnet_4_6_thinking": {"model": "Claude Sonnet 4.6 (Thinking)", "percent": 100},
                },
            },
        },
        {
            "num": 2,
            "email": "(no login)",
            "has_token": False,
            "label": "",
            "quota": {"state": "no_token", "limits": {}},
        },
    ]

    pre_lines, rows = interactive.launch_account_table("agy", statuses)
    rendered = "\n".join(pre_lines + rows)

    assert "Profile" in rendered
    assert "FM" in rendered
    assert "FH" in rendered
    assert "CS" in rendered
    assert "12%" in rendered
    assert "34%" in rendered
    assert "100%" in rendered
    assert "work" in rendered
    assert "No Token" in rendered


@pytest.mark.parametrize("refresh_key", ["r", "R", "ctrl+r", "к", "К"])
def test_interactive_status_refresh_key_invalidates_quota_cache(monkeypatch, refresh_key):
    import cli_profile_manager.interactive as interactive

    rendered = []
    refreshed = []
    keys = iter([refresh_key, "enter"])

    monkeypatch.setattr(interactive, "render_status_screen", lambda tool_key, status_message=None, base_statuses=None: rendered.append((tool_key, status_message, base_statuses)))
    monkeypatch.setattr(interactive, "collect_status_snapshot", lambda tool_key: [])
    monkeypatch.setattr(interactive, "get_key", lambda timeout=None: next(keys))
    monkeypatch.setattr(interactive, "next_quota_wake_timeout", lambda tool_key: None)
    monkeypatch.setattr(interactive, "force_quota_refresh", lambda tool_key=None: refreshed.append(tool_key) or 2)

    interactive.view_status("agy")

    assert rendered == [
        ("agy", None, []),
        ("agy", "Refreshing quota now for 2 profiles...", []),
    ]
    assert refreshed == ["agy"]


def test_interactive_status_view_reuses_base_status_snapshot(monkeypatch):
    import cli_profile_manager.interactive as interactive

    calls = []
    keys = iter([None, "enter"])

    monkeypatch.setattr(interactive, "load_metadata", lambda: {})
    monkeypatch.setattr(interactive, "get_display_profiles", lambda tool_key: [1])
    monkeypatch.setattr(interactive, "status_payload", lambda tool_key, n, metadata: calls.append((tool_key, n)) or {
        "num": n,
        "profile": f"p{n}",
        "email": "missing@example.com",
        "has_token": False,
        "token_state": "missing",
        "label": "",
        "home": "/tmp/p1",
    })
    monkeypatch.setattr(interactive, "get_key", lambda timeout=None: next(keys))
    monkeypatch.setattr(interactive, "next_quota_wake_timeout", lambda tool_key: 0)
    monkeypatch.setattr(interactive, "clear_screen", lambda: None)
    monkeypatch.setattr(interactive, "print_header", lambda title="": None)

    interactive.view_status("agy")

    assert calls == [("agy", 1)]


def test_interactive_get_key_reads_ctrl_r(monkeypatch):
    sys.path.insert(0, str(ROOT))
    import cli_profile_manager.interactive as interactive

    class FakeStdin:
        def fileno(self):
            return 0

    data = [b"\x12"]

    monkeypatch.setattr(interactive.sys, "stdin", FakeStdin())
    monkeypatch.setattr(interactive.os, "read", lambda _fd, _size: data.pop(0))
    monkeypatch.setattr(interactive.termios, "tcgetattr", lambda _fd: object())
    monkeypatch.setattr(interactive.termios, "tcsetattr", lambda *_args: None)
    monkeypatch.setattr(interactive.tty, "setraw", lambda _fd: None)
    monkeypatch.setattr(interactive.select, "select", lambda r, _w, _e, _t: (r if data else [], [], []))

    assert interactive.get_key() == "ctrl+r"


def test_interactive_get_key_reads_cyrillic_refresh_key(monkeypatch):
    sys.path.insert(0, str(ROOT))
    import cli_profile_manager.interactive as interactive

    class FakeStdin:
        def fileno(self):
            return 0

    data = [bytes([byte]) for byte in "к".encode("utf-8")]

    monkeypatch.setattr(interactive.sys, "stdin", FakeStdin())
    monkeypatch.setattr(interactive.os, "read", lambda _fd, _size: data.pop(0))
    monkeypatch.setattr(interactive.termios, "tcgetattr", lambda _fd: object())
    monkeypatch.setattr(interactive.termios, "tcsetattr", lambda *_args: None)
    monkeypatch.setattr(interactive.tty, "setraw", lambda _fd: None)
    monkeypatch.setattr(interactive.select, "select", lambda r, _w, _e, _t: (r if data else [], [], []))

    assert interactive.get_key() == "к"


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


def test_find_windows_user_prefers_profile_home_over_first_directory(monkeypatch, tmp_path):
    from cli_profile_manager import paths

    users = tmp_path / "Users"
    (users / "Admin").mkdir(parents=True)
    write_json(users / "Oliver" / "agy-homes" / "cred-p1.json", {"BlobBase64": "x"})
    write_json(users / "Oliver" / ".config" / "cli-profile-manager" / "profiles_metadata.json", {})
    monkeypatch.delenv("USERPROFILE", raising=False)

    assert paths.find_windows_user(users) == "Oliver"


def test_find_windows_user_honors_userprofile(monkeypatch, tmp_path):
    from cli_profile_manager import paths

    users = tmp_path / "Users"
    (users / "Admin").mkdir(parents=True)
    (users / "Oliver").mkdir()
    monkeypatch.setenv("USERPROFILE", r"C:\Users\Admin")

    assert paths.find_windows_user(users) == "Admin"


def test_normalize_credential_path_keeps_native_windows_path(monkeypatch):
    from cli_profile_manager import paths

    assert paths.normalize_credential_path("codex", r"C:\Users\Oliver\codex-homes\p1\auth.json", platform_name="nt") == r"C:\Users\Oliver\codex-homes\p1\auth.json"
    assert paths.normalize_credential_path("codex", r"C:\Users\Oliver\codex-homes\p1\auth.json", platform_name="posix") == "/mnt/c/Users/Oliver/codex-homes/p1/auth.json"


def test_sync_only_managed_profile_files(monkeypatch, tmp_path):
    pm = load_pm(monkeypatch, tmp_path)
    wsl = tmp_path / "wsl"
    windows = tmp_path / "windows"
    write_json(wsl / "codex-homes" / "p1" / "auth.json", {"OPENAI_API_KEY": "new"})
    write_json(wsl / "codex-homes" / "p1" / "site-packages" / "httpcore" / "__init__.py", {"ignored": True})
    write_json(wsl / "codex-homes" / "p1" / "__pycache__" / "auth.cpython-311.pyc", {"ignored": True})
    write_json(wsl / "claude-homes" / "p2" / ".credentials.json", {"claude": "token"})
    write_json(windows / "codex-homes" / "p9" / "auth.json", {"OPENAI_API_KEY": "old"})
    write_json(windows / "codex-homes" / "p9" / "node_modules" / "pkg" / "index.js", {"ignored": True})

    result = pm.sync_profiles_noninteractive("wsl", "hard", dry_run=False, yes=True)

    assert result["copied"] == 2
    assert result["would_delete"] == 1
    assert (windows / "codex-homes" / "p1" / "auth.json").exists()
    assert (windows / "claude-homes" / "p2" / ".credentials.json").exists()
    assert not (windows / "codex-homes" / "p1" / "site-packages").exists()
    assert not (windows / "codex-homes" / "p1" / "__pycache__").exists()
    assert (windows / "codex-homes" / "p9" / "node_modules" / "pkg" / "index.js").exists()
    assert not (windows / "codex-homes" / "p9" / "auth.json").exists()


def test_sync_manifest_for_managed_profile_roots_avoids_walk(monkeypatch, tmp_path):
    from cli_profile_manager import sync

    base = tmp_path / "codex-homes"
    write_json(base / "p1" / "auth.json", {"OPENAI_API_KEY": "new"})
    write_json(base / "p1" / "node_modules" / "pkg" / "index.js", {"ignored": True})

    monkeypatch.setattr(sync.os, "walk", lambda *_args, **_kwargs: pytest.fail("managed sync manifest should not walk profile trees"))

    manifest = sync.build_sync_manifest(base, "codex-homes")

    assert sorted(str(path) for path in manifest) == ["p1/auth.json"]
    assert manifest[Path("p1/auth.json")].size > 0
    assert manifest[Path("p1/auth.json")].entry_type == "file"


def test_sync_hard_uses_manifest_diff_to_skip_identical_files(monkeypatch, tmp_path):
    pm = load_pm(monkeypatch, tmp_path)
    wsl = tmp_path / "wsl"
    windows = tmp_path / "windows"
    source = wsl / "codex-homes" / "p1" / "auth.json"
    dest = windows / "codex-homes" / "p1" / "auth.json"
    write_json(source, {"OPENAI_API_KEY": "same"})
    write_json(dest, {"OPENAI_API_KEY": "same"})
    shutil.copy2(source, dest)
    write_json(windows / "codex-homes" / "p9" / "auth.json", {"OPENAI_API_KEY": "old"})

    result = pm.sync_profiles_noninteractive("wsl", "hard", dry_run=False, yes=True)

    assert result["copied"] == 0
    assert result["skipped"] == 1
    assert result["would_delete"] == 1
    assert not (windows / "codex-homes" / "p9" / "auth.json").exists()


def test_safety_policy_inventory_covers_sensitive_commands():
    from cli_profile_manager import safety

    inventory = safety.command_inventory()

    for command in (
        "clear",
        "sync-hard",
        "sync-soft",
        "import",
        "export",
        "label",
        "login",
        "launch",
        "audit-purge",
        "service-start",
        "service-stop",
        "service-restart",
    ):
        assert command in inventory
        assert inventory[command]["risk"]
    assert inventory["clear"]["requires_confirmation"] is True
    assert inventory["sync-hard"]["dry_run_supported"] is True
    assert inventory["launch"]["risk"] == safety.RISK_EXTERNAL


def test_clear_json_refuses_without_confirmation_and_audits_safety(monkeypatch, tmp_path):
    env = os.environ.copy()
    env.update({
        "AI_MAN_AGY_HOME": str(tmp_path / "agy-homes"),
        "AI_MAN_CODEX_HOME": str(tmp_path / "codex-homes"),
        "AI_MAN_CLAUDE_HOME": str(tmp_path / "claude-homes"),
        "AI_MAN_METADATA_DIR": str(tmp_path / "metadata"),
    })
    (tmp_path / "agy-homes" / "p1").mkdir(parents=True)

    completed = subprocess.run(
        [sys.executable, str(ROOT / "profile_manager.py"), "clear", "agy", "p1", "--json"],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    audit_list = subprocess.run(
        [sys.executable, str(ROOT / "profile_manager.py"), "audit", "list", "--json", "--category", "safety"],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 2
    payload = json.loads(completed.stdout)
    assert payload["ok"] is False
    assert payload["safety"]["result"] == "refused"
    assert payload["safety"]["preflight"]["risk"] == "destructive"
    assert (tmp_path / "agy-homes" / "p1").exists()
    events = json.loads(audit_list.stdout)["events"]
    assert any(event["category"] == "safety" and event["result"] == "refused" for event in events)


def test_sync_hard_json_refusal_and_dry_run_include_safety(monkeypatch, tmp_path):
    env = os.environ.copy()
    env.update({
        "AI_MAN_AGY_HOME": str(tmp_path / "agy-homes"),
        "AI_MAN_CODEX_HOME": str(tmp_path / "codex-homes"),
        "AI_MAN_CLAUDE_HOME": str(tmp_path / "claude-homes"),
        "AI_MAN_METADATA_DIR": str(tmp_path / "metadata"),
        "AI_MAN_WSL_HOME": str(tmp_path / "wsl"),
        "AI_MAN_WINDOWS_HOME": str(tmp_path / "windows"),
    })
    (tmp_path / "wsl").mkdir()
    (tmp_path / "windows").mkdir()
    write_json(tmp_path / "wsl" / "codex-homes" / "p1" / "auth.json", {"OPENAI_API_KEY": "sk-test"})
    write_json(tmp_path / "windows" / "codex-homes" / "p9" / "auth.json", {"OPENAI_API_KEY": "old"})

    refused = subprocess.run(
        [sys.executable, str(ROOT / "profile_manager.py"), "sync", "--mode", "hard", "--json"],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    dry_run = subprocess.run(
        [sys.executable, str(ROOT / "profile_manager.py"), "sync", "--mode", "hard", "--dry-run", "--json"],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert refused.returncode == 2
    refused_payload = json.loads(refused.stdout)
    assert refused_payload["safety"]["result"] == "refused"
    assert dry_run.returncode == 0
    dry_payload = json.loads(dry_run.stdout)
    assert dry_payload["safety"]["result"] == "dry_run"
    assert dry_payload["would_delete"] >= 1


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


def test_diagnostics_json_redacts_accounts_and_reports_runtime(monkeypatch, tmp_path):
    pm = load_pm(monkeypatch, tmp_path)
    write_json(
        tmp_path / "codex-homes" / "p1" / "auth.json",
        {"tokens": {"id_token": make_id_token("user@example.com")}},
    )

    payload = pm.diagnostics_payload("codex", status_provider=lambda tool, num: pm.status_payload(tool, num))
    rendered = json.dumps(payload)

    assert payload["ok"] is True
    assert payload["tools"]["codex"]["cli_available"] in (True, False)
    assert payload["quota_runtime"]["cache"] == []
    assert "queued" in payload["quota_runtime"]["states"]
    assert "timeout" in payload["quota_runtime"]["failure_states"]
    assert "running" in payload["quota_runtime"]["legal_transitions"]["queued"]
    assert "persistent_sessions" in payload
    assert "user@example.com" not in rendered
    assert "redacted:" in rendered
    assert "safety_policy" in payload
    assert payload["safety_policy"]["commands"]["clear"]["requires_confirmation"] is True


def test_diagnostics_reuses_supplied_profile_indexes(monkeypatch, tmp_path):
    load_pm(monkeypatch, tmp_path)
    import cli_profile_manager.diagnostics as diagnostics

    monkeypatch.setattr(
        diagnostics,
        "get_occupied_profiles",
        lambda tool: pytest.fail("diagnostics should reuse supplied occupied index"),
    )
    monkeypatch.setattr(
        diagnostics,
        "get_display_profiles",
        lambda tool: pytest.fail("diagnostics should reuse supplied display index"),
    )

    payload = diagnostics.diagnostics_payload(
        "codex",
        status_provider=lambda tool, num: {"has_token": False, "token_state": "missing"},
        profile_index_provider=lambda tool: {
            "occupied_profiles": [1],
            "display_profiles": [1],
        },
    )

    assert payload["tools"]["codex"]["occupied_profiles"] == ["p1"]
    assert payload["tools"]["codex"]["visible_profiles"] == ["p1"]


def test_diagnostics_command_json_does_not_print_token_like_values(monkeypatch, tmp_path):
    env = os.environ.copy()
    env.update({
        "AI_MAN_AGY_HOME": str(tmp_path / "agy-homes"),
        "AI_MAN_CODEX_HOME": str(tmp_path / "codex-homes"),
        "AI_MAN_CLAUDE_HOME": str(tmp_path / "claude-homes"),
        "AI_MAN_METADATA_DIR": str(tmp_path / "metadata"),
        "AI_MAN_QUOTA_KEY_DELAY_SECONDS": "sk-test-secret",
    })

    completed = subprocess.run(
        [sys.executable, str(ROOT / "profile_manager.py"), "diagnostics", "agy", "--json"],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert payload["ok"] is True
    assert "sk-test-secret" not in completed.stdout
    assert "[redacted-token]" in completed.stdout


def test_diagnostics_command_defaults_to_fast_mode(monkeypatch, tmp_path):
    env = os.environ.copy()
    env.update({
        "AI_MAN_AGY_HOME": str(tmp_path / "agy-homes"),
        "AI_MAN_CODEX_HOME": str(tmp_path / "codex-homes"),
        "AI_MAN_CLAUDE_HOME": str(tmp_path / "claude-homes"),
        "AI_MAN_METADATA_DIR": str(tmp_path / "metadata"),
    })

    completed = subprocess.run(
        [sys.executable, str(ROOT / "profile_manager.py"), "diagnostics", "agy", "--json"],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["mode"] == "fast"
    assert payload["quota_runtime"]["mode"] == "fast"
    assert payload["audit"]["record_count_check"] == "skipped_fast_diagnostics"
    assert payload["process_limits"]["systemd_user_scope_check"] == "skipped_fast_diagnostics"
    assert "policies" in payload["process_limits"]


def test_diagnostics_command_deep_mode_reports_full_runtime(monkeypatch, tmp_path):
    env = os.environ.copy()
    env.update({
        "AI_MAN_AGY_HOME": str(tmp_path / "agy-homes"),
        "AI_MAN_CODEX_HOME": str(tmp_path / "codex-homes"),
        "AI_MAN_CLAUDE_HOME": str(tmp_path / "claude-homes"),
        "AI_MAN_METADATA_DIR": str(tmp_path / "metadata"),
    })

    completed = subprocess.run(
        [sys.executable, str(ROOT / "profile_manager.py"), "diagnostics", "agy", "--json", "--deep"],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["mode"] == "deep"
    assert "systemd_user_scope_check" not in payload["process_limits"]
    assert "cache" in payload["quota_runtime"]


def test_config_show_json_reports_effective_values_and_invalid_env_warnings(monkeypatch, tmp_path):
    env = os.environ.copy()
    env.update({
        "AI_MAN_AGY_HOME": str(tmp_path / "agy-homes"),
        "AI_MAN_CODEX_HOME": str(tmp_path / "codex-homes"),
        "AI_MAN_CLAUDE_HOME": str(tmp_path / "claude-homes"),
        "AI_MAN_METADATA_DIR": str(tmp_path / "metadata"),
        "AI_MAN_WSL_HOME": str(tmp_path / "wsl"),
        "AI_MAN_WINDOWS_HOME": str(tmp_path / "windows"),
        "AI_MAN_INTERACTIVE_AGY_QUOTA_CONCURRENCY": "not-a-number",
        "AI_MAN_INTERACTIVE_QUOTA_TIMEOUT": "0",
        "AI_MAN_INTERACTIVE_QUOTA_FRESH_SECONDS": "900",
        "AI_MAN_QUOTA_SESSION_TTL_SECONDS": "120",
        "AI_MAN_QUOTA_SESSION_MAX": "3",
        "AI_MAN_AGY_QUOTA_STARTUP_SECONDS": "75",
        "AI_MAN_AGY_QUOTA_COMMAND": "sk-test-secret",
        "AI_MAN_PROCESS_MEMORY_MB": "bad",
        "AI_MAN_QUOTA_PROCESS_CPU_PERCENT": "5",
    })

    completed = subprocess.run(
        [sys.executable, str(ROOT / "profile_manager.py"), "config", "show", "--json"],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert payload["ok"] is True
    assert payload["profile_roots"]["agy"] == str(tmp_path / "agy-homes")
    assert payload["quota"]["interactive_agy_concurrency"] == 2
    assert payload["quota"]["interactive_timeout"] == 12.0
    assert payload["quota"]["interactive_fresh_seconds"] == 900.0
    assert payload["quota"]["agy_startup_seconds"] == 75.0
    assert payload["quota"]["session_ttl_seconds"] == 120.0
    assert payload["quota"]["session_max"] == 3
    assert any("AI_MAN_INTERACTIVE_AGY_QUOTA_CONCURRENCY" in warning for warning in payload["warnings"])
    assert any("AI_MAN_INTERACTIVE_QUOTA_TIMEOUT" in warning for warning in payload["warnings"])
    assert "sk-test-secret" not in completed.stdout
    assert payload["quota"]["commands"]["agy"] == "[redacted-token]"
    assert payload["process_limits"]["launch"]["memory_mb"] == 4096
    assert payload["process_limits"]["quota"]["cpu_percent"] == 150
    assert "backend" in payload["process_limits"]["launch"]
    assert any("AI_MAN_PROCESS_MEMORY_MB" in warning for warning in payload["warnings"])
    assert any("AI_MAN_QUOTA_PROCESS_CPU_PERCENT" in warning for warning in payload["warnings"])


def test_config_registry_covers_known_environment_knobs():
    from cli_profile_manager.config import registry

    names = {definition.name for definition in registry() if definition.env}
    expected = {
        "AI_MAN_AGY_HOME",
        "AI_MAN_CODEX_HOME",
        "AI_MAN_CLAUDE_HOME",
        "AI_MAN_METADATA_DIR",
        "AI_MAN_WSL_HOME",
        "AI_MAN_WINDOWS_HOME",
        "AI_MAN_INTERACTIVE_QUOTA",
        "AI_MAN_INTERACTIVE_QUOTA_TIMEOUT",
        "AI_MAN_INTERACTIVE_AGY_QUOTA_TIMEOUT",
        "AI_MAN_INTERACTIVE_AGY_QUOTA_CONCURRENCY",
        "AI_MAN_INTERACTIVE_QUOTA_FRESH_SECONDS",
        "AI_MAN_SERVICE",
        "AI_MAN_AUDIT",
        "AI_MAN_AUDIT_BACKEND",
        "AI_MAN_AUDIT_STRICT",
        "AI_MAN_AUDIT_RETENTION_DAYS",
        "AI_MAN_AUDIT_MAX_BYTES",
        "AI_MAN_AUDIT_SHOW_ACCOUNTS",
        "AI_MAN_AUDIT_SHOW_PATHS",
        "AI_MAN_QUOTA_STARTUP_SECONDS",
        "AI_MAN_AGY_QUOTA_STARTUP_SECONDS",
        "AI_MAN_QUOTA_POST_COMMAND_SECONDS",
        "AI_MAN_QUOTA_KEY_DELAY_SECONDS",
        "AI_MAN_QUOTA_SESSION_TTL_SECONDS",
        "AI_MAN_QUOTA_SESSION_MAX",
        "AI_MAN_AGY_QUOTA_COMMAND",
        "AI_MAN_CODEX_QUOTA_COMMAND",
        "AI_MAN_CLAUDE_QUOTA_COMMAND",
        "AI_MAN_PROCESS_LIMITS",
        "AI_MAN_PROCESS_MEMORY_MB",
        "AI_MAN_PROCESS_CPU_PERCENT",
        "AI_MAN_PROCESS_MAX_PROCESSES",
        "AI_MAN_PROCESS_NICE",
        "AI_MAN_PROCESS_IONICE_CLASS",
        "AI_MAN_PROCESS_IONICE_LEVEL",
        "AI_MAN_PROCESS_SYSTEMD",
        "AI_MAN_QUOTA_PROCESS_LIMITS",
        "AI_MAN_QUOTA_PROCESS_MEMORY_MB",
        "AI_MAN_QUOTA_PROCESS_CPU_PERCENT",
        "AI_MAN_QUOTA_PROCESS_MAX_PROCESSES",
        "AI_MAN_QUOTA_PROCESS_NICE",
        "AI_MAN_QUOTA_PROCESS_IONICE_CLASS",
        "AI_MAN_QUOTA_PROCESS_IONICE_LEVEL",
        "AI_MAN_VALIDATION_PROCESS_LIMITS",
        "AI_MAN_VALIDATION_PROCESS_MEMORY_MB",
        "AI_MAN_VALIDATION_PROCESS_CPU_PERCENT",
        "AI_MAN_VALIDATION_PROCESS_MAX_PROCESSES",
        "AI_MAN_VALIDATION_PROCESS_NICE",
        "AI_MAN_VALIDATION_PROCESS_IONICE_CLASS",
        "AI_MAN_VALIDATION_PROCESS_IONICE_LEVEL",
    }
    assert expected <= names


def test_config_show_sources_and_filter_report_effective_source(monkeypatch, tmp_path):
    env = os.environ.copy()
    env.update({
        "AI_MAN_AGY_HOME": str(tmp_path / "agy-homes"),
        "AI_MAN_CODEX_HOME": str(tmp_path / "codex-homes"),
        "AI_MAN_CLAUDE_HOME": str(tmp_path / "claude-homes"),
        "AI_MAN_METADATA_DIR": str(tmp_path / "metadata"),
        "AI_MAN_QUOTA_SESSION_MAX": "5",
    })

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "profile_manager.py"),
            "config",
            "show",
            "--json",
            "--sources",
            "--filter",
            "session_max",
        ],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert list(payload["settings_by_key"]) == ["quota.session_max"]
    setting = payload["settings_by_key"]["quota.session_max"]
    assert setting["value"] == 5
    assert setting["source"] == "environment"
    assert setting["source_name"] == "AI_MAN_QUOTA_SESSION_MAX"


def test_config_diagnostics_include_health_and_redacted_effective_settings(monkeypatch, tmp_path):
    env = os.environ.copy()
    env.update({
        "AI_MAN_AGY_HOME": str(tmp_path / "agy-homes"),
        "AI_MAN_CODEX_HOME": str(tmp_path / "codex-homes"),
        "AI_MAN_CLAUDE_HOME": str(tmp_path / "claude-homes"),
        "AI_MAN_METADATA_DIR": str(tmp_path / "metadata"),
        "AI_MAN_QUOTA_SESSION_MAX": "0",
        "AI_MAN_AGY_QUOTA_COMMAND": "sk-test-secret",
    })

    completed = subprocess.run(
        [sys.executable, str(ROOT / "profile_manager.py"), "diagnostics", "--json"],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert payload["config_health"]["ok"] is False
    assert "AI_MAN_QUOTA_SESSION_MAX" in payload["config_health"]["invalid_settings"]
    assert payload["effective_config"]["quota.session_max"]["value"] == 24
    assert "sk-test-secret" not in completed.stdout
    assert payload["effective_config"]["quota.agy_command"]["value"] == "[redacted]"


def test_process_policy_builds_systemd_scope_command(monkeypatch):
    from cli_profile_manager import process_policy

    monkeypatch.setattr(process_policy, "systemd_user_scope_available", lambda: True)
    monkeypatch.setenv("AI_MAN_PROCESS_MEMORY_MB", "2048")
    monkeypatch.setenv("AI_MAN_PROCESS_CPU_PERCENT", "250")
    monkeypatch.setenv("AI_MAN_PROCESS_MAX_PROCESSES", "64")

    command, preexec_fn, policy = process_policy.prepare_popen(
        ["agy", "--version"],
        tier="launch",
        unit_name="ai-man-test",
    )

    assert policy["backend"] == "systemd-run"
    assert preexec_fn is None
    assert command[:4] == ["systemd-run", "--user", "--scope", "--quiet"]
    assert "MemoryMax=2048M" in command
    assert "CPUQuota=250%" in command
    assert "TasksMax=64" in command
    assert command[-2:] == ["agy", "--version"]


def test_process_policy_fallback_prepares_preexec(monkeypatch):
    from cli_profile_manager import process_policy

    monkeypatch.setattr(process_policy, "systemd_user_scope_available", lambda: False)
    monkeypatch.setenv("AI_MAN_PROCESS_SYSTEMD", "0")
    monkeypatch.setenv("AI_MAN_PROCESS_LIMITS", "1")

    command, preexec_fn, policy = process_policy.prepare_popen(["codex"], tier="launch")

    assert policy["backend"] in ("setrlimit", "priority-only")
    assert command[-1] == "codex"
    assert callable(preexec_fn) or policy["backend"] == "priority-only"


def test_run_cli_tool_uses_process_policy_wrapper(monkeypatch, tmp_path):
    pm = load_pm(monkeypatch, tmp_path)
    import cli_profile_manager.cli as cli

    captured = {}

    class FakePolicy:
        @staticmethod
        def prepare_popen(command, tier, needs_pty, unit_name=None):
            captured["policy_args"] = (command, tier, needs_pty, unit_name)
            return ["wrapped"] + command, "preexec", {"backend": "test", "enabled": True}

    class FakeCompleted:
        returncode = 7

    class FakeSubprocess:
        @staticmethod
        def run(command, env=None, preexec_fn=None):
            captured["run"] = (command, env, preexec_fn)
            return FakeCompleted()

    monkeypatch.setattr(cli, "_process_policy", lambda: FakePolicy)
    monkeypatch.setattr(cli._shutil(), "which", lambda name: f"/bin/{name}")
    monkeypatch.setattr(cli, "_subprocess", lambda: FakeSubprocess)

    rc = pm.run_cli_tool("codex", 1, ["--help"])

    assert rc == 7
    assert captured["policy_args"] == (["codex", "--help"], "launch", False, "ai-man-codex-p1")
    assert captured["run"][0] == ["wrapped", "codex", "--help"]
    assert captured["run"][2] == "preexec"


def test_quota_pty_uses_quota_process_policy(monkeypatch, tmp_path):
    import cli_profile_manager.quota as quota

    captured = {}

    class FakeProc:
        pid = 123
        returncode = 0

        def poll(self):
            return self.returncode

    def fake_prepare(command, tier, needs_pty):
        captured["policy_args"] = (command, tier, needs_pty)
        return ["wrapped"] + list(command), "preexec", {"backend": "setrlimit"}

    def fake_popen(command, **kwargs):
        captured["popen"] = (command, kwargs)
        return FakeProc()

    monkeypatch.setitem(sys.modules, "pty", types.SimpleNamespace(openpty=lambda: (10, 11)))
    monkeypatch.setattr(quota.shutil, "which", lambda name: f"/bin/{name}")
    monkeypatch.setattr(quota.fcntl, "ioctl", lambda *args: None)
    monkeypatch.setattr(quota.os, "close", lambda fd: None)
    monkeypatch.setattr(quota, "prepare_popen", fake_prepare)
    monkeypatch.setattr(quota.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(quota, "wait_for_cli_startup", lambda *args: None)
    monkeypatch.setattr(quota, "wait_for_idle", lambda *args: "quota screen")
    monkeypatch.setattr(quota, "send_interactive_command", lambda *args: None)
    monkeypatch.setattr(quota, "wait_after_command", lambda *args: None)

    screen = quota.run_cli_quota_snapshot("agy", ["agy"], {}, str(tmp_path))

    assert screen == "quota screen"
    assert captured["policy_args"] == (["agy"], "quota", True)
    assert captured["popen"][0] == ["wrapped", "agy"]
    assert callable(captured["popen"][1]["preexec_fn"])
    assert "start_new_session" not in captured["popen"][1]


def test_agy_quota_pty_assigns_controlling_tty_and_waits_for_readiness(monkeypatch, tmp_path):
    import cli_profile_manager.quota as quota

    fake_cli = tmp_path / "fake_agy_cli.py"
    fake_cli.write_text(
        "\n".join([
            "import os",
            "import select",
            "import sys",
            "import time",
            "tty = open('/dev/tty', 'rb+', buffering=0)",
            "print('booting agy', flush=True)",
            "if select.select([sys.stdin], [], [], 0.15)[0]:",
            "    print('EARLY_COMMAND', flush=True)",
            "print('CLI ready for user input', flush=True)",
            "for line in sys.stdin:",
            "    command = line.strip()",
            "    if command == '/exit':",
            "        break",
            "    if command == '/usage':",
            "        print('Gemini 3.5 Flash (Medium)', flush=True)",
            "        print('Usage 94% remaining', flush=True)",
            "    else:",
            "        print('unexpected command ' + command, flush=True)",
            "    time.sleep(0.05)",
        ]),
        encoding="utf-8",
    )

    monkeypatch.setenv("AI_MAN_PROCESS_LIMITS", "0")
    monkeypatch.setenv("AI_MAN_QUOTA_KEY_DELAY_SECONDS", "0")
    monkeypatch.setenv("AI_MAN_QUOTA_POST_COMMAND_SECONDS", "0.1")

    screen = quota.run_cli_quota_snapshot(
        "agy",
        [sys.executable, str(fake_cli)],
        {"HOME": str(tmp_path)},
        str(tmp_path),
        timeout_seconds=2,
        idle_seconds=0.1,
    )
    parsed = quota.parse_quota("agy", screen)

    assert "EARLY_COMMAND" not in screen
    assert parsed["state"] == "available"
    assert parsed["limits"]["gemini_3_5_flash_medium"]["percent"] == 94


def test_agy_quota_pty_accepts_stable_prompt_as_readiness(monkeypatch, tmp_path):
    import cli_profile_manager.quota as quota

    fake_cli = tmp_path / "fake_agy_prompt_cli.py"
    fake_cli.write_text(
        "\n".join([
            "import sys",
            "import time",
            "open('/dev/tty', 'rb+', buffering=0)",
            "print('Antigravity CLI 1.1.0', flush=True)",
            "print('user@example.com', flush=True)",
            "print('Gemini 3.5 Flash (Medium)', flush=True)",
            "print('~', flush=True)",
            "for line in sys.stdin:",
            "    command = line.strip()",
            "    if command == '/exit':",
            "        break",
            "    if command == '/usage':",
            "        print('Gemini 3.5 Flash (Medium)', flush=True)",
            "        print('Usage 94% remaining', flush=True)",
            "    time.sleep(0.05)",
        ]),
        encoding="utf-8",
    )

    monkeypatch.setenv("AI_MAN_PROCESS_LIMITS", "0")
    monkeypatch.setenv("AI_MAN_QUOTA_KEY_DELAY_SECONDS", "0")
    monkeypatch.setenv("AI_MAN_QUOTA_POST_COMMAND_SECONDS", "0.1")

    screen = quota.run_cli_quota_snapshot(
        "agy",
        [sys.executable, str(fake_cli)],
        {"HOME": str(tmp_path)},
        str(tmp_path),
        timeout_seconds=2,
        idle_seconds=0.1,
    )
    parsed = quota.parse_quota("agy", screen)

    assert parsed["state"] == "available"
    assert parsed["limits"]["gemini_3_5_flash_medium"]["percent"] == 94


def test_agy_readiness_does_not_accept_idle_splash_without_prompt():
    import os
    import cli_profile_manager.quota as quota

    read_fd, write_fd = os.pipe()
    try:
        os.write(write_fd, b"Antigravity CLI 1.1.0\nSigning in...\n")
        with pytest.raises(quota.QuotaProbeError, match="AGY CLI is still starting") as exc_info:
            quota.wait_for_agy_readiness(read_fd, [], startup_seconds=0.2, idle_seconds=0.05)
        assert exc_info.value.state == "startup_pending"
    finally:
        os.close(read_fd)
        os.close(write_fd)


def test_agy_readiness_accepts_prompt_after_eligibility_warning():
    import os
    import cli_profile_manager.quota as quota

    read_fd, write_fd = os.pipe()
    try:
        os.write(
            write_fd,
            (
                "Antigravity CLI 1.1.1\n"
                "Eligibility check failed: Your current account is not eligible for Antigravity, "
                "because it is not currently available in your location.\n"
                ">\n"
            ).encode("utf-8"),
        )
        screen = quota.wait_for_agy_readiness(read_fd, [], startup_seconds=0.2, idle_seconds=0.05)
        assert "Eligibility check failed" in screen
    finally:
        os.close(read_fd)
        os.close(write_fd)


def test_quota_output_text_accepts_bytes_from_pty_buffers():
    import cli_profile_manager.quota as quota

    assert quota.output_text([b"Daily quota ", "55% ", bytes("осталось", "utf-8")]) == "Daily quota 55% осталось"


def test_quota_read_available_treats_bad_fd_as_empty():
    import cli_profile_manager.quota as quota

    assert quota.read_available(-1) == ""


def test_persistent_agy_quota_session_uses_readiness_gated_fake_cli(monkeypatch, tmp_path):
    import cli_profile_manager.quota as quota

    monkeypatch.setenv("AI_MAN_AGY_QUOTA_BACKEND", "pty")
    fake_cli = tmp_path / "fake_persistent_agy_cli.py"
    fake_cli.write_text(
        "\n".join([
            "import sys",
            "import time",
            "open('/dev/tty', 'rb+', buffering=0)",
            "print('CLI ready for user input', flush=True)",
            "for line in sys.stdin:",
            "    command = line.strip()",
            "    if command == '/exit':",
            "        break",
            "    if command == '/usage':",
            "        print('Daily quota 55% remaining', flush=True)",
            "    time.sleep(0.05)",
        ]),
        encoding="utf-8",
    )

    monkeypatch.setenv("AI_MAN_PROCESS_LIMITS", "0")
    monkeypatch.setenv("AI_MAN_QUOTA_KEY_DELAY_SECONDS", "0")
    monkeypatch.setenv("AI_MAN_QUOTA_POST_COMMAND_SECONDS", "0.1")
    quota.close_persistent_quota_sessions()

    try:
        screen = quota.run_persistent_cli_quota_snapshot(
            "agy",
            [sys.executable, str(fake_cli)],
            {"HOME": str(tmp_path)},
            str(tmp_path),
            timeout_seconds=2,
            idle_seconds=0.1,
        )
        parsed = quota.parse_quota("agy", screen)
        assert parsed["state"] == "available"
        assert parsed["limits"]["daily"]["percent"] == 55
    finally:
        quota.close_persistent_quota_sessions()


def test_diagnostics_reports_process_limits(monkeypatch, tmp_path):
    pm = load_pm(monkeypatch, tmp_path)

    payload = pm.diagnostics_payload("codex", status_provider=lambda tool, num: None)

    assert payload["process_limits"]["supported"] in (True, False)
    assert "launch" in payload["process_limits"]["policies"]
    assert "quota" in payload["process_limits"]["policies"]


def test_runtime_benchmark_quota_parser_outputs_json():
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "benchmark_runtime.py"),
            "--scenario",
            "quota-parser",
            "--iterations",
            "2",
            "--json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert payload["ok"] is True
    assert payload["scenario"] == "quota-parser"
    assert payload["results"][0]["name"] == "quota-parser"
    assert payload["results"][0]["runs"] == 2


def test_horizon_governance_validates_current_horizon_docs():
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "horizon_governance.py"),
            "--json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["ok"] is True
    assert payload["checked"] >= 21
    assert payload["issues"] == []


def test_horizon_governance_collects_redacted_evidence(tmp_path):
    horizon = tmp_path / "H99_Test_Horizon"
    horizon.mkdir()
    (horizon / "V_00_Validation_Plan.md").write_text(
        "\n".join(
            [
                "# V_00 Validation Plan",
                "",
                "```bash",
                f"{sys.executable} -c \"print('user@example.com sk-test-secret')\"",
                "```",
            ]
        ),
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "horizon_governance.py"),
            "--horizon",
            str(horizon),
            "--evidence",
            "--write",
            "--json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    payload = json.loads(completed.stdout)
    evidence = (horizon / "V_99_Automated_Evidence.md").read_text(encoding="utf-8")
    rendered = json.dumps(payload) + evidence
    assert payload["ok"] is True
    assert "[redacted-email]" in rendered
    assert "[redacted-token]" in rendered
    assert "user@example.com" not in rendered
    assert "sk-test-secret" not in rendered


def test_status_table_lines_fit_narrow_width_and_preserve_quota():
    from cli_profile_manager.cli import CLR_RED, CLR_RESET, status_table_lines, visible_len

    statuses = [{
        "profile": "p12",
        "email": f"{CLR_RED}invalid token: Antigravity CLI token is missing token field with long details{CLR_RESET}",
        "has_token": False,
        "token_state": "invalid",
        "label": "very-long-profile-label-for-terminal",
        "home": "/home/example/agy-homes/p12",
        "quota": {
            "state": "available",
            "source_command": "/usage",
            "limits": {
                "gemini_3_5_flash_medium": {"model": "Gemini 3.5 Flash (Medium)", "percent": 94},
            },
        },
    }]

    lines = status_table_lines("agy", statuses, terminal_width=80)

    assert all(visible_len(line) <= 80 for line in lines)
    assert "Quota" in lines[0]
    assert "FM:94%" in lines[2]
    assert "..." in lines[2]


def test_install_script_is_idempotent_and_verifiable(tmp_path):
    env = os.environ.copy()
    env["AI_MAN_INSTALL_BIN_DIR"] = str(tmp_path / "bin")

    for _ in range(2):
        installed = subprocess.run(
            ["bash", str(ROOT / "install.sh")],
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        assert installed.returncode == 0, installed.stderr

    verified = subprocess.run(
        ["bash", str(ROOT / "scripts" / "verify_install.sh")],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert verified.returncode == 0, verified.stderr
    assert "install verification passed" in verified.stdout


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


def test_command_parser_uses_compact_handler_table(monkeypatch, tmp_path):
    pm = load_pm(monkeypatch, tmp_path)

    assert "list" in pm.COMMAND_HANDLERS
    assert "config_show" in pm.COMMAND_HANDLERS
    assert "diagnostics" in pm.COMMAND_HANDLERS

    parser = pm.build_parser()
    cases = {
        ("list", "agy", "--json"): "list",
        ("status", "codex", "p1", "--json"): "status",
        ("diagnostics", "agy", "--json"): "diagnostics",
        ("doctor", "agy", "--json"): "diagnostics",
        ("config", "show", "--json"): "config_show",
        ("config", "health", "--json"): "config_health",
        ("audit", "status", "--json"): "audit",
        ("service", "status", "--json"): "service",
    }

    for argv, handler in cases.items():
        args = parser.parse_args(list(argv))
        assert args.command_handler == handler
        assert not hasattr(args, "func")


def test_dispatch_parsed_args_uses_handler_table(monkeypatch, tmp_path):
    pm = load_pm(monkeypatch, tmp_path)

    called = []
    monkeypatch.setitem(pm.COMMAND_HANDLERS, "fake", lambda args: called.append(args.value) or 17)

    args = types.SimpleNamespace(command_handler="fake", value="ok")

    assert pm.dispatch_parsed_args(args) == 17
    assert called == ["ok"]


def test_runtime_service_paths_are_user_only(monkeypatch, tmp_path):
    load_pm(monkeypatch, tmp_path)
    from cli_profile_manager import runtime_service

    runtime_service.ensure_runtime_dir()
    status = runtime_service.service_status()

    assert status["runtime_dir"] == str(tmp_path / "metadata" / "runtime")
    assert status["runtime_dir_mode"] == "0o700"
    assert status["socket_path"].endswith("service.sock")
    assert status["running"] is False


def test_runtime_service_contract_lists_state_and_invalidation(monkeypatch, tmp_path):
    load_pm(monkeypatch, tmp_path)
    from cli_profile_manager import runtime_service

    status = runtime_service.service_status()
    contract = status["contract"]

    assert "metadata" in contract["state_ownership"]
    assert "raw credential contents" in contract["never_cache"]
    assert "list" in contract["eligible_commands"]
    assert "import" in contract["ineligible_commands"]
    assert contract["mutation_invalidation"]["label"] == ["metadata", "command_snapshot", "diagnostics"]


@pytest.mark.parametrize(
    ("argv", "reason", "domains"),
    [
        (["label", "agy", "p1", "bench"], "label", {"metadata", "command_snapshot"}),
        (["import", "agy", "cred.json"], "import", {"credentials", "profiles"}),
        (["clear", "agy", "p1", "--yes"], "clear", {"credentials", "profiles", "quota"}),
        (["sync", "--source", "wsl"], "sync", {"credentials", "profiles", "metadata"}),
        (["audit", "purge", "--yes"], "audit:purge", {"audit", "diagnostics"}),
        (["audit", "compact"], "audit:compact", {"audit", "diagnostics"}),
    ],
)
def test_runtime_service_mutation_invalidation_contract(argv, reason, domains):
    from cli_profile_manager import runtime_service

    invalidation = runtime_service.mutation_invalidation(argv)

    assert invalidation["reason"] == reason
    assert domains.issubset(set(invalidation["domains"]))


def test_runtime_service_does_not_invalidate_dry_run_mutations():
    from cli_profile_manager import runtime_service

    assert runtime_service.mutation_invalidation(["import", "agy", "cred.json", "--dry-run"]) is None
    assert runtime_service.mutates_runtime_state(["import", "agy", "cred.json", "--dry-run"]) is False


def test_runtime_service_invalidation_is_idempotent_and_diagnostic(monkeypatch, tmp_path):
    load_pm(monkeypatch, tmp_path)
    from cli_profile_manager import runtime_service

    state = runtime_service.RuntimeState()
    first = runtime_service.handle_payload(
        {
            "version": runtime_service.PROTOCOL_VERSION,
            "action": "invalidate",
            "reason": "label",
            "domains": ["metadata", "diagnostics", "metadata"],
            "command": "label",
        },
        state,
    )
    second = runtime_service.handle_payload(
        {
            "version": runtime_service.PROTOCOL_VERSION,
            "action": "invalidate",
            "reason": "label",
            "domains": ["metadata"],
            "command": "label",
        },
        state,
    )
    status = runtime_service.service_status()

    assert first["ok"] is True
    assert second["ok"] is True
    assert second["generation"] == first["generation"] + 1
    assert second["last_invalidation"]["domains"] == ["metadata"]
    assert status["last_invalidation"]["reason"] == "label"


def test_runtime_service_caches_read_only_runs_and_invalidates(monkeypatch, tmp_path):
    load_pm(monkeypatch, tmp_path)
    from cli_profile_manager import runtime_service

    calls = []

    def fake_execute(argv, state=None):
        calls.append(list(argv))
        return {
            "ok": True,
            "returncode": 0,
            "stdout": json.dumps({"call": len(calls)}) + "\n",
            "stderr": "",
        }

    monkeypatch.setattr(runtime_service, "execute_argv", fake_execute)
    state = runtime_service.RuntimeState()
    payload = {
        "version": runtime_service.PROTOCOL_VERSION,
        "action": "run",
        "argv": ["list", "agy", "--json"],
    }

    first = runtime_service.handle_payload(payload, state)
    second = runtime_service.handle_payload(payload, state)
    health = state.health()

    assert first["cache"]["hit"] is False
    assert second["cache"]["hit"] is True
    assert second["stdout"] == first["stdout"]
    assert calls == [["list", "agy", "--json"]]
    assert health["cache"]["entries"] == 1
    assert health["cache"]["hits"] == 1
    assert health["cache"]["misses"] == 1
    assert health["cache"]["last_latency_ms"] is not None

    runtime_service.handle_payload(
        {
            "version": runtime_service.PROTOCOL_VERSION,
            "action": "invalidate",
            "reason": "label",
            "domains": ["metadata", "command_snapshot"],
            "command": "label",
        },
        state,
    )
    third = runtime_service.handle_payload(payload, state)

    assert third["cache"]["hit"] is False
    assert len(calls) == 2
    assert state.health()["cache"]["invalidations"] == 1


def test_runtime_service_reuses_command_snapshot_until_invalidation(monkeypatch, tmp_path):
    load_pm(monkeypatch, tmp_path)
    from cli_profile_manager import operations, runtime_service

    builds = []
    real_snapshot = operations.CommandSnapshot

    class CountingSnapshot(real_snapshot):
        def __init__(self, metadata=None):
            builds.append(metadata)
            super().__init__(metadata)

    monkeypatch.setattr(operations, "CommandSnapshot", CountingSnapshot)
    state = runtime_service.RuntimeState()

    first = state.command_snapshot()
    second = state.command_snapshot()

    assert first is second
    assert len(builds) == 1
    assert state.health()["cache"]["snapshot_cached"] is True
    assert state.health()["cache"]["snapshot_builds"] == 1

    state.invalidate(reason="label", domains=["metadata"], command="label")
    third = state.command_snapshot()

    assert third is not first
    assert len(builds) == 2
    assert state.health()["cache"]["snapshot_builds"] == 2


def test_runtime_service_invalidates_stale_profile_snapshot(monkeypatch, tmp_path):
    load_pm(monkeypatch, tmp_path)
    from cli_profile_manager import runtime_service

    (tmp_path / "codex-homes" / "p1").mkdir(parents=True)
    state = runtime_service.RuntimeState()
    snapshot = state.command_snapshot()

    assert snapshot.status("codex", 1)["has_token"] is False

    state.response_cache[("list", "codex", "--json")] = {"ok": True}
    write_json(
        tmp_path / "codex-homes" / "p1" / "auth.json",
        {"tokens": {"id_token": make_id_token("fresh@example.com")}},
    )

    state.refresh_profile_snapshot()
    refreshed = state.command_snapshot()

    assert refreshed is not snapshot
    assert refreshed.status("codex", 1)["account"] == "fresh@example.com"
    assert state.response_cache == {}
    assert state.last_invalidation["reason"] == "profile_files_changed"


def test_runtime_service_stale_cleanup_reports_recovery(monkeypatch, tmp_path):
    load_pm(monkeypatch, tmp_path)
    from cli_profile_manager import runtime_service

    runtime_service.ensure_runtime_dir()
    runtime_service.pid_path().write_text("99999999", encoding="utf-8")
    runtime_service.socket_path().write_text("", encoding="utf-8")

    status = runtime_service.service_status()
    assert status["stale"] is True
    assert status["unavailable_reason"] == "stale_runtime_files"
    assert status["recovery_hint"]
    assert runtime_service.cleanup_stale_files() is True
    assert runtime_service.service_status()["stale"] is False


def test_service_status_json_and_diagnostics_include_runtime(monkeypatch, tmp_path):
    env = os.environ.copy()
    env.update({
        "AI_MAN_AGY_HOME": str(tmp_path / "agy-homes"),
        "AI_MAN_CODEX_HOME": str(tmp_path / "codex-homes"),
        "AI_MAN_CLAUDE_HOME": str(tmp_path / "claude-homes"),
        "AI_MAN_METADATA_DIR": str(tmp_path / "metadata"),
    })

    status = subprocess.run(
        [sys.executable, str(ROOT / "profile_manager.py"), "service", "status", "--json"],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    diagnostics = subprocess.run(
        [sys.executable, str(ROOT / "profile_manager.py"), "diagnostics", "--json"],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert status.returncode == 0, status.stderr
    assert diagnostics.returncode == 0, diagnostics.stderr
    service_payload = json.loads(status.stdout)
    diagnostics_payload = json.loads(diagnostics.stdout)
    assert service_payload["service"]["running"] is False
    assert diagnostics_payload["service_runtime"]["socket_path"] == service_payload["service"]["socket_path"]
    assert "contract" in diagnostics_payload["service_runtime"]


def test_service_mode_falls_back_when_service_absent(monkeypatch, tmp_path):
    env = os.environ.copy()
    env.update({
        "AI_MAN_SERVICE": "1",
        "AI_MAN_AGY_HOME": str(tmp_path / "agy-homes"),
        "AI_MAN_CODEX_HOME": str(tmp_path / "codex-homes"),
        "AI_MAN_CLAUDE_HOME": str(tmp_path / "claude-homes"),
        "AI_MAN_METADATA_DIR": str(tmp_path / "metadata"),
    })

    completed = subprocess.run(
        [sys.executable, str(ROOT / "profile_manager.py"), "config", "show", "--json"],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout)["ok"] is True


def test_service_backed_output_matches_one_shot(monkeypatch, tmp_path):
    env = os.environ.copy()
    env.update({
        "AI_MAN_AGY_HOME": str(tmp_path / "agy-homes"),
        "AI_MAN_CODEX_HOME": str(tmp_path / "codex-homes"),
        "AI_MAN_CLAUDE_HOME": str(tmp_path / "claude-homes"),
        "AI_MAN_METADATA_DIR": str(tmp_path / "metadata"),
    })
    write_json(tmp_path / "agy-homes" / "p1" / ".gemini" / "oauth_creds.json", {"refresh_token": "r"})
    write_json(tmp_path / "agy-homes" / "p1" / ".gemini" / "google_accounts.json", {"active": "agy@example.com"})

    def comparable_payload(payload):
        payload = json.loads(json.dumps(payload))
        if "audit" in payload:
            payload["audit"].pop("record_count", None)
        payload.pop("generated_at", None)
        return payload

    start = subprocess.run(
        [sys.executable, str(ROOT / "profile_manager.py"), "service", "start", "--json"],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    try:
        assert start.returncode == 0, start.stderr
        start_payload = json.loads(start.stdout)
        assert start_payload["service"]["running"] is True
        assert start_payload["service"]["socket_mode"] == "0o600"

        commands = [
            ["config", "show", "--json"],
            ["list", "agy", "--json"],
            ["status", "agy", "p1", "--json"],
            ["diagnostics", "agy", "--json"],
        ]
        for command in commands:
            one_shot = subprocess.run(
                [sys.executable, str(ROOT / "profile_manager.py"), *command],
                env={**env, "AI_MAN_SERVICE": "0"},
                text=True,
                capture_output=True,
                check=False,
            )
            service_backed = subprocess.run(
                [sys.executable, str(ROOT / "profile_manager.py"), *command],
                env={**env, "AI_MAN_SERVICE": "1"},
                text=True,
                capture_output=True,
                check=False,
            )

            assert one_shot.returncode == 0, one_shot.stderr
            assert service_backed.returncode == 0, service_backed.stderr
            assert comparable_payload(json.loads(service_backed.stdout)) == comparable_payload(json.loads(one_shot.stdout))
    finally:
        subprocess.run(
            [sys.executable, str(ROOT / "profile_manager.py"), "service", "stop", "--json"],
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )


def test_mutating_command_notifies_runtime_invalidation(monkeypatch, tmp_path):
    pm = load_pm(monkeypatch, tmp_path)
    import cli_profile_manager.cli as cli

    calls = []

    class FakeRuntime:
        def service_mode_enabled(self):
            return False

        def eligible_argv(self, argv):
            return False

        def mutates_runtime_state(self, argv):
            return bool(argv and argv[0] == "label")

        def mutation_invalidation(self, argv):
            return {"reason": "label", "domains": ["metadata"], "command": "label"}

        def invalidate_service_for(self, reason=None, domains=(), command=None):
            calls.append((reason, tuple(domains), command))

    monkeypatch.setattr(cli, "_runtime_service", lambda: FakeRuntime())

    rc, _, stderr = run_in_process_command(pm, ["label", "agy", "p1", "bench"])

    assert rc == 0, stderr
    assert calls == [("label", ("metadata",), "label")]


def test_audit_event_redacts_tokens_accounts_and_paths(monkeypatch, tmp_path):
    load_pm(monkeypatch, tmp_path)
    from cli_profile_manager import audit

    event = audit.make_event(
        "credential",
        "attempted",
        command="import",
        tool="codex",
        details={
            "token": "sk-test-secret",
            "account": "user@example.com",
            "path": str(tmp_path / "codex-homes" / "p1" / "auth.json"),
        },
    )

    rendered = json.dumps(event)
    assert event["schema_version"] == 1
    assert event["event_id"]
    assert event["correlation_id"]
    assert "sk-test-secret" not in rendered
    assert "user@example.com" not in rendered
    assert str(tmp_path) not in rendered
    assert "[redacted]" in rendered or "[redacted-token]" in rendered


def test_audit_jsonl_backend_writes_and_skips_malformed_rows(monkeypatch, tmp_path):
    load_pm(monkeypatch, tmp_path)
    from cli_profile_manager import audit

    audit.record("command", "started", command="list", details={"argv": ["list", "agy", "--json"]})
    with open(audit.jsonl_path(), "a", encoding="utf-8") as handle:
        handle.write("{malformed\n")
    events = audit.read_jsonl_events()
    status = audit.status_payload()

    assert len(events) == 1
    assert events[0]["command"] == "list"
    assert status["audit_dir_mode"] == "0o700"
    assert status["path_mode"] == "0o600"


def test_audit_sqlite_backend_writes_and_queries(monkeypatch, tmp_path):
    load_pm(monkeypatch, tmp_path)
    monkeypatch.setenv("AI_MAN_AUDIT_BACKEND", "sqlite")
    from cli_profile_manager import audit

    audit.record("command", "completed", command="status", tool="agy", profile="p1", result="succeeded")
    events = audit.query_events(command="status", tool="agy", profile="p1", result="succeeded")
    status = audit.status_payload()

    assert len(events) == 1
    assert events[0]["category"] == "command"
    assert status["backend"] == "sqlite"
    assert status["record_count"] == 1


def test_audit_cli_records_command_and_supports_query_export_purge(monkeypatch, tmp_path):
    env = os.environ.copy()
    env.update({
        "AI_MAN_AGY_HOME": str(tmp_path / "agy-homes"),
        "AI_MAN_CODEX_HOME": str(tmp_path / "codex-homes"),
        "AI_MAN_CLAUDE_HOME": str(tmp_path / "claude-homes"),
        "AI_MAN_METADATA_DIR": str(tmp_path / "metadata"),
    })

    listed = subprocess.run(
        [sys.executable, str(ROOT / "profile_manager.py"), "list", "agy", "--json"],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    audit_list = subprocess.run(
        [sys.executable, str(ROOT / "profile_manager.py"), "audit", "list", "--json", "--command", "list", "--limit", "20"],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    exported = subprocess.run(
        [sys.executable, str(ROOT / "profile_manager.py"), "audit", "export", "--format", "json"],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    purged = subprocess.run(
        [sys.executable, str(ROOT / "profile_manager.py"), "audit", "purge", "--yes", "--json"],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert listed.returncode == 0, listed.stderr
    assert audit_list.returncode == 0, audit_list.stderr
    events = json.loads(audit_list.stdout)["events"]
    assert any(event["category"] == "command" and event["action"] == "started" for event in events)
    assert any(event["category"] == "command" and event["action"] == "completed" for event in events)
    assert exported.returncode == 0, exported.stderr
    assert json.loads(exported.stdout)["events"]
    assert purged.returncode == 0, purged.stderr
    assert json.loads(purged.stdout)["removed"] >= 1


def test_audit_purge_json_refuses_without_confirmation(monkeypatch, tmp_path):
    env = os.environ.copy()
    env.update({
        "AI_MAN_AGY_HOME": str(tmp_path / "agy-homes"),
        "AI_MAN_CODEX_HOME": str(tmp_path / "codex-homes"),
        "AI_MAN_CLAUDE_HOME": str(tmp_path / "claude-homes"),
        "AI_MAN_METADATA_DIR": str(tmp_path / "metadata"),
    })

    subprocess.run(
        [sys.executable, str(ROOT / "profile_manager.py"), "list", "agy", "--json"],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    refused = subprocess.run(
        [sys.executable, str(ROOT / "profile_manager.py"), "audit", "purge", "--json"],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert refused.returncode == 2
    payload = json.loads(refused.stdout)
    assert payload["ok"] is False
    assert payload["safety"]["preflight"]["operation"] == "audit-purge"
    assert payload["safety"]["result"] == "refused"


def test_audit_diagnostics_report_health(monkeypatch, tmp_path):
    pm = load_pm(monkeypatch, tmp_path)
    from cli_profile_manager import audit

    audit.record("diagnostic", "completed", command="diagnostics")
    payload = pm.diagnostics_payload("codex", status_provider=lambda tool, num: None)

    assert payload["audit"]["enabled"] is True
    assert payload["audit"]["backend"] == "jsonl"
    assert payload["audit"]["record_count"] >= 1
