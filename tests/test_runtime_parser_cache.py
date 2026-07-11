import contextlib
import io
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_runtime_command_parser_is_cached_but_build_parser_stays_fresh():
    from cli_profile_manager import cli

    cli.reset_runtime_command_parser_cache()

    assert cli.build_parser() is not cli.build_parser()
    assert cli.runtime_command_parser() is cli.runtime_command_parser()


def test_runtime_command_parser_repeated_parses_do_not_leak_state():
    from cli_profile_manager import cli

    cli.reset_runtime_command_parser_cache()
    parser = cli.runtime_command_parser()

    first = parser.parse_args(["list", "agy", "--json"])
    second = parser.parse_args(["status", "codex", "p1", "--json"])
    third = parser.parse_args(["doctor", "agy", "--json"])
    fourth = parser.parse_args(["config", "health", "--json"])

    assert first.command_handler == "list"
    assert first.tool == "agy"
    assert not hasattr(first, "profile")

    assert second.command_handler == "status"
    assert second.tool == "codex"
    assert second.profile == "p1"

    assert third.command_handler == "diagnostics"
    assert third.command == "doctor"
    assert not hasattr(third, "profile")

    assert fourth.command_handler == "config_health"
    assert fourth.config_command == "health"
    assert not hasattr(fourth, "tool")


def test_runtime_service_execute_argv_uses_cached_parser(monkeypatch, tmp_path):
    from cli_profile_manager import cli, runtime_service

    monkeypatch.setenv("AI_MAN_AGY_HOME", str(tmp_path / "agy-homes"))
    monkeypatch.setenv("AI_MAN_CODEX_HOME", str(tmp_path / "codex-homes"))
    monkeypatch.setenv("AI_MAN_CLAUDE_HOME", str(tmp_path / "claude-homes"))
    monkeypatch.setenv("AI_MAN_METADATA_DIR", str(tmp_path / "metadata"))
    monkeypatch.setenv("AI_MAN_WSL_HOME", str(tmp_path / "wsl"))
    monkeypatch.setenv("AI_MAN_WINDOWS_HOME", str(tmp_path / "windows"))

    cli.reset_runtime_command_parser_cache()
    builds = 0
    original_build_parser = cli.build_parser

    def counted_build_parser():
        nonlocal builds
        builds += 1
        return original_build_parser()

    monkeypatch.setattr(cli, "build_parser", counted_build_parser)

    first = runtime_service.execute_argv(["config", "show", "--json"])
    second = runtime_service.execute_argv(["config", "show", "--json"])

    assert first["returncode"] == 0
    assert second["returncode"] == 0
    assert json.loads(first["stdout"])["ok"] is True
    assert json.loads(second["stdout"])["ok"] is True
    assert builds == 1


def test_run_cli_default_path_uses_process_local_parser_cache(monkeypatch, tmp_path):
    from cli_profile_manager import cli

    monkeypatch.setenv("AI_MAN_AGY_HOME", str(tmp_path / "agy-homes"))
    monkeypatch.setenv("AI_MAN_CODEX_HOME", str(tmp_path / "codex-homes"))
    monkeypatch.setenv("AI_MAN_CLAUDE_HOME", str(tmp_path / "claude-homes"))
    monkeypatch.setenv("AI_MAN_METADATA_DIR", str(tmp_path / "metadata"))
    monkeypatch.setenv("AI_MAN_WSL_HOME", str(tmp_path / "wsl"))
    monkeypatch.setenv("AI_MAN_WINDOWS_HOME", str(tmp_path / "windows"))

    builds = 0
    original_build_parser = cli.build_parser

    def counted_build_parser():
        nonlocal builds
        builds += 1
        return original_build_parser()

    monkeypatch.setattr(cli, "build_parser", counted_build_parser)
    cli.reset_runtime_command_parser_cache()

    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        assert cli.run_cli(["config", "show", "--json"]) == 0
        assert cli.run_cli(["config", "show", "--json"]) == 0

    assert builds == 1


def test_run_cli_can_still_use_explicit_fresh_parser_factory(monkeypatch, tmp_path):
    from cli_profile_manager import cli

    monkeypatch.setenv("AI_MAN_AGY_HOME", str(tmp_path / "agy-homes"))
    monkeypatch.setenv("AI_MAN_CODEX_HOME", str(tmp_path / "codex-homes"))
    monkeypatch.setenv("AI_MAN_CLAUDE_HOME", str(tmp_path / "claude-homes"))
    monkeypatch.setenv("AI_MAN_METADATA_DIR", str(tmp_path / "metadata"))
    monkeypatch.setenv("AI_MAN_WSL_HOME", str(tmp_path / "wsl"))
    monkeypatch.setenv("AI_MAN_WINDOWS_HOME", str(tmp_path / "windows"))

    builds = 0
    original_build_parser = cli.build_parser

    def counted_build_parser():
        nonlocal builds
        builds += 1
        return original_build_parser()

    monkeypatch.setattr(cli, "build_parser", counted_build_parser)

    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        assert cli.run_cli(["config", "show", "--json"], parser_factory=cli.build_parser) == 0
        assert cli.run_cli(["config", "show", "--json"], parser_factory=cli.build_parser) == 0

    assert builds == 2
