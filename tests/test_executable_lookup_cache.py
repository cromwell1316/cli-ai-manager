from cli_profile_manager import executable_lookup


def test_executable_lookup_cache_hits_for_same_path(monkeypatch):
    calls = []

    def fake_which(command, path=None):
        calls.append((command, path))
        return f"/bin/{command}"

    executable_lookup.reset_executable_lookup_cache()
    monkeypatch.setenv("PATH", "/bin")
    monkeypatch.setattr(executable_lookup.shutil, "which", fake_which)

    assert executable_lookup.executable_path("agy") == "/bin/agy"
    assert executable_lookup.executable_path("agy") == "/bin/agy"
    assert calls == [("agy", None)]
    executable_lookup.reset_executable_lookup_cache()


def test_executable_lookup_cache_preserves_missing_results(monkeypatch):
    calls = []

    def fake_which(command, path=None):
        calls.append((command, path))
        return None

    executable_lookup.reset_executable_lookup_cache()
    monkeypatch.setenv("PATH", "/missing")
    monkeypatch.setattr(executable_lookup.shutil, "which", fake_which)

    assert executable_lookup.executable_path("missing-cli") is None
    assert executable_lookup.executable_path("missing-cli") is None
    assert calls == [("missing-cli", None)]
    executable_lookup.reset_executable_lookup_cache()


def test_executable_lookup_cache_key_tracks_path(monkeypatch):
    calls = []

    def fake_which(command, path=None):
        calls.append((command, path))
        return f"{executable_lookup.os.environ.get('PATH')}/{command}"

    executable_lookup.reset_executable_lookup_cache()
    monkeypatch.setattr(executable_lookup.shutil, "which", fake_which)
    monkeypatch.setenv("PATH", "/first")
    assert executable_lookup.executable_path("tmux") == "/first/tmux"
    monkeypatch.setenv("PATH", "/second")
    assert executable_lookup.executable_path("tmux") == "/second/tmux"
    assert calls == [("tmux", None), ("tmux", None)]
    executable_lookup.reset_executable_lookup_cache()


def test_executable_lookup_explicit_paths_are_not_cached(monkeypatch):
    calls = []

    def fake_which(command, path=None):
        calls.append((command, path))
        return command

    executable_lookup.reset_executable_lookup_cache()
    monkeypatch.setattr(executable_lookup.shutil, "which", fake_which)

    assert executable_lookup.executable_path("/opt/bin/agy") == "/opt/bin/agy"
    assert executable_lookup.executable_path("/opt/bin/agy") == "/opt/bin/agy"
    assert calls == [("/opt/bin/agy", None), ("/opt/bin/agy", None)]
    executable_lookup.reset_executable_lookup_cache()
