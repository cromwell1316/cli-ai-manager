import base64
import importlib
import json
import os
import subprocess
import sys
import threading
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


def test_interactive_quota_text_marks_unknown_state_as_retrying():
    sys.path.insert(0, str(ROOT))
    import cli_profile_manager.interactive as interactive

    status = {"quota": {"state": "unknown", "limits": {}}}

    assert interactive.quota_text(status, color=False) == "retrying"


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


def test_quota_payload_preserves_missing_cli_diagnostic():
    from cli_profile_manager.quota import QuotaProbeError, quota_payload

    def fake_runner(tool_key, command, env, cwd, timeout_seconds=20):
        raise QuotaProbeError("missing_cli", "agy CLI is not installed or not in PATH")

    payload = quota_payload("agy", "p1", ["agy"], {}, ".", runner=fake_runner)

    assert payload["quota"]["state"] == "missing_cli"
    assert payload["quota"]["warnings"] == ["agy CLI is not installed or not in PATH"]


def test_interactive_uses_longer_agy_quota_timeout(monkeypatch):
    import cli_profile_manager.interactive as interactive

    monkeypatch.delenv("AI_MAN_INTERACTIVE_QUOTA_TIMEOUT", raising=False)
    monkeypatch.delenv("AI_MAN_INTERACTIVE_AGY_QUOTA_TIMEOUT", raising=False)

    assert interactive.interactive_quota_timeout("agy") == 40.0
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
    assert calls == [("agy", 1, 40.0)]


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

    assert sorted(calls) == [("agy", 1, 40.0), ("agy", 2, 40.0)]
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


def test_interactive_stale_quota_survives_failed_refresh(monkeypatch):
    import cli_profile_manager.interactive as interactive

    def fake_quota_payload(tool_key, profile_num, timeout_seconds):
        return {
            "quota": {
                "state": "timeout",
                "limits": {},
                "warnings": ["timeout waiting for CLI output"],
            },
        }

    monkeypatch.setattr(interactive, "quota_payload", fake_quota_payload)
    interactive.invalidate_quota_cache()
    stale_fetched_at = interactive.time.time() - interactive.QUOTA_FRESH_SECONDS - 1
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
    assert refreshed["last_error"]["state"] == "timeout"
    assert "timeout waiting for CLI output" in refreshed["quota"]["warnings"]


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


def test_persistent_quota_runner_reuses_session(monkeypatch, tmp_path):
    import cli_profile_manager.quota as quota

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


def test_persistent_quota_parser_miss_threshold_invalidates_session(monkeypatch, tmp_path):
    import cli_profile_manager.quota as quota

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


def test_interactive_invalidate_closes_matching_persistent_session(monkeypatch, tmp_path):
    import cli_profile_manager.interactive as interactive
    import cli_profile_manager.quota as quota

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
    no_token = {"quota": {"state": "no_token", "limits": {}}}

    assert agy_quota_cells(stale, columns)[0] == "94%~"
    assert agy_quota_cells(failed, columns)[0] == "!"
    assert agy_quota_cells(parser_miss, columns)[0] == "!"
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


@pytest.mark.parametrize("refresh_key", ["r", "R", "ctrl+r", "к", "К"])
def test_interactive_status_refresh_key_invalidates_quota_cache(monkeypatch, refresh_key):
    import cli_profile_manager.interactive as interactive

    rendered = []
    invalidated = []
    keys = iter([refresh_key, "enter"])

    monkeypatch.setattr(interactive, "render_status_screen", lambda tool_key, status_message=None: rendered.append((tool_key, status_message)))
    monkeypatch.setattr(interactive, "get_key", lambda timeout=None: next(keys))
    monkeypatch.setattr(interactive, "next_quota_wake_timeout", lambda tool_key: None)
    monkeypatch.setattr(interactive, "invalidate_quota_cache", lambda tool_key=None, profile_num=None: invalidated.append((tool_key, profile_num)))

    interactive.view_status("agy")

    assert rendered == [("agy", None), ("agy", "Refreshing quota now...")]
    assert invalidated == [("agy", None)]


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
    assert "persistent_sessions" in payload
    assert "user@example.com" not in rendered
    assert "redacted:" in rendered


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
        "AI_MAN_AGY_QUOTA_COMMAND": "sk-test-secret",
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
    assert any("AI_MAN_INTERACTIVE_AGY_QUOTA_CONCURRENCY" in warning for warning in payload["warnings"])
    assert any("AI_MAN_INTERACTIVE_QUOTA_TIMEOUT" in warning for warning in payload["warnings"])
    assert "sk-test-secret" not in completed.stdout
    assert payload["quota"]["commands"]["agy"] == "[redacted-token]"


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
