from .metadata import load_metadata
from .operations import (
    EXIT_OK,
    TOOLS,
    clear_profile_operation,
    config_show_operation,
    export_credential_operation,
    first_free_profile,
    import_credential_operation,
    label_profile_operation,
    list_profiles_operation,
    parse_profile,
    profile_status_operation,
    sync_profiles_operation,
)


def _print(output, text=""):
    output(text)


def _input(prompt, input_func):
    try:
        return input_func(prompt)
    except EOFError:
        return "x"


def _pause(input_func, output):
    _input("Press Enter to continue...", input_func)


def _choice(prompt, choices, input_func, output):
    valid = {str(key).lower() for key in choices}
    while True:
        value = _input(prompt, input_func).strip().lower()
        if value in valid:
            return value
        _print(output, f"Invalid choice: {value}")


def _print_result(result, output):
    if result.ok:
        if result.message:
            _print(output, result.message)
        elif result.payload:
            _print(output, "ok")
        return True
    _print(output, result.message or "operation failed")
    return False


def _profile_or_default(raw, default):
    raw = raw.strip()
    if not raw:
        return default
    return parse_profile(raw)


def _profile_status_lines(tool_key, include_quota=False):
    result = list_profiles_operation(tool_key, include_quota=include_quota)
    lines = [TOOLS[tool_key]["name"], f"Next profile: {result.payload['next_profile']}"]
    for status in result.payload["profiles"]:
        token = status.get("token_state") or ("valid" if status.get("has_token") else "missing")
        account = status.get("email") or status.get("account") or "(unknown)"
        label = status.get("label") or ""
        occupied = "*" if status.get("exists") else " "
        suffix = f" [{label}]" if label else ""
        lines.append(f"{occupied} {status['profile']}: {account} token={token}{suffix}")
    return lines


def _select_profile(tool_key, input_func, output, default=None):
    default = first_free_profile(tool_key) if default is None else default
    raw = _input(f"Profile [p{default}]: ", input_func)
    try:
        return _profile_or_default(raw, default)
    except ValueError as e:
        _print(output, str(e))
        return None


def _launch_profile(tool_key, input_func, output):
    profile_num = _select_profile(tool_key, input_func, output, default=1)
    if profile_num is None:
        return
    status = profile_status_operation(tool_key, f"p{profile_num}").payload
    if not status.get("has_token"):
        _print(output, f"profile p{profile_num} has no token; use login or import first")
        return
    from .cli import run_cli_tool

    code = run_cli_tool(tool_key, profile_num)
    _print(output, f"{tool_key} p{profile_num} exited with code {code}")


def _login_profile(tool_key, input_func, output):
    profile_num = _select_profile(tool_key, input_func, output)
    if profile_num is None:
        return
    from .cli import run_cli_tool

    code = run_cli_tool(tool_key, profile_num, [], login=True)
    _print(output, f"{tool_key} login p{profile_num} exited with code {code}")


def _import_profile(tool_key, input_func, output):
    path = _input("Credential path: ", input_func).strip()
    if not path:
        _print(output, "import cancelled")
        return
    profile_num = _select_profile(tool_key, input_func, output)
    if profile_num is None:
        return
    result = import_credential_operation(tool_key, path, f"p{profile_num}")
    if _print_result(result, output):
        _print(output, f"imported into {result.payload['profile']}: {result.payload['destination']}")


def _export_profile(tool_key, input_func, output):
    profile_num = _select_profile(tool_key, input_func, output, default=1)
    if profile_num is None:
        return
    target = _input("Destination file or directory [default]: ", input_func).strip() or None
    result = export_credential_operation(tool_key, f"p{profile_num}", target)
    if _print_result(result, output):
        _print(output, f"exported {result.payload['profile']}: {result.payload['destination']}")


def _label_profile(tool_key, input_func, output):
    profile_num = _select_profile(tool_key, input_func, output, default=1)
    if profile_num is None:
        return
    label = _input("Label (empty clears): ", input_func).strip()
    result = label_profile_operation(tool_key, f"p{profile_num}", label)
    if _print_result(result, output):
        _print(output, f"label saved for {result.payload['profile']}")


def _clear_profile(tool_key, input_func, output):
    profile_num = _select_profile(tool_key, input_func, output, default=1)
    if profile_num is None:
        return
    confirm = _input(f"Type yes to clear {tool_key} p{profile_num}: ", input_func).strip().lower()
    if confirm != "yes":
        _print(output, "clear cancelled")
        return
    result = clear_profile_operation(tool_key, f"p{profile_num}")
    if _print_result(result, output):
        _print(output, f"cleared {result.payload['profile']}: {result.payload['cleared']}")


def _tool_menu(tool_key, input_func, output):
    while True:
        _print(output)
        for line in _profile_status_lines(tool_key):
            _print(output, line)
        _print(output, "")
        _print(output, "[1] Launch")
        _print(output, "[2] Login/Add")
        _print(output, "[3] Import")
        _print(output, "[4] Export")
        _print(output, "[5] Label")
        _print(output, "[6] Clear")
        _print(output, "[b] Back")
        choice = _choice("> ", {"1", "2", "3", "4", "5", "6", "b"}, input_func, output)
        if choice == "1":
            _launch_profile(tool_key, input_func, output)
        elif choice == "2":
            _login_profile(tool_key, input_func, output)
        elif choice == "3":
            _import_profile(tool_key, input_func, output)
        elif choice == "4":
            _export_profile(tool_key, input_func, output)
        elif choice == "5":
            _label_profile(tool_key, input_func, output)
        elif choice == "6":
            _clear_profile(tool_key, input_func, output)
        elif choice == "b":
            return
        _pause(input_func, output)


def _sync_menu(input_func, output):
    _print(output, "[1] WSL -> Windows")
    _print(output, "[2] Windows -> WSL")
    _print(output, "[b] Back")
    direction_choice = _choice("> ", {"1", "2", "b"}, input_func, output)
    if direction_choice == "b":
        return
    direction = "wsl" if direction_choice == "1" else "windows"
    _print(output, "[1] Soft")
    _print(output, "[2] Hard")
    mode_choice = _choice("> ", {"1", "2"}, input_func, output)
    mode = "soft" if mode_choice == "1" else "hard"
    dry_run = _input("Dry run? [Y/n]: ", input_func).strip().lower() not in ("n", "no")
    yes = False
    if mode == "hard" and not dry_run:
        yes = _input("Type yes to confirm hard sync: ", input_func).strip().lower() == "yes"
        if not yes:
            _print(output, "sync cancelled")
            return
    result = sync_profiles_operation(direction, mode, dry_run=dry_run, yes=yes)
    if _print_result(result, output):
        payload = result.payload
        _print(output, f"sync {payload['direction']} {payload['mode']} dry_run={payload['dry_run']}")
        _print(output, f"copied={payload['copied']} skipped={payload['skipped']} converted={payload['converted']} invalid={payload['invalid']}")
        if payload.get("would_delete"):
            _print(output, f"would_delete={payload['would_delete']}")


def _settings_menu(input_func, output):
    result = config_show_operation(include_sources=True)
    if not result.ok:
        _print_result(result, output)
        return
    payload = result.payload
    _print(output, "Profile roots:")
    for tool_key, root in payload["profile_roots"].items():
        _print(output, f"  {tool_key}: {root}")
    _print(output, f"Metadata: {payload['metadata_dir']}")
    _print(output, f"Sync roots: wsl={payload['sync_roots']['wsl']} windows={payload['sync_roots']['windows']}")
    quota = payload["quota"]
    _print(output, f"Quota: enabled={quota['interactive_enabled']} timeout={quota['interactive_timeout']} agy_timeout={quota['interactive_agy_timeout']}")
    if payload.get("warnings"):
        _print(output, "Warnings:")
        for warning in payload["warnings"]:
            _print(output, f"  {warning}")


def run_windows_interactive_main(input_func=input, output_func=print):
    load_metadata()
    while True:
        _print(output_func)
        _print(output_func, "UNIFIED PROFILE MANAGER")
        _print(output_func, "[1] Antigravity CLI (agy)")
        _print(output_func, "[2] OpenAI Codex CLI")
        _print(output_func, "[3] Anthropic Claude CLI")
        _print(output_func, "[4] Sync Profiles (WSL <-> Windows)")
        _print(output_func, "[5] Settings")
        _print(output_func, "[x] Exit")
        choice = _choice("> ", {"1", "2", "3", "4", "5", "x"}, input_func, output_func)
        if choice == "1":
            _tool_menu("agy", input_func, output_func)
        elif choice == "2":
            _tool_menu("codex", input_func, output_func)
        elif choice == "3":
            _tool_menu("claude", input_func, output_func)
        elif choice == "4":
            _sync_menu(input_func, output_func)
            _pause(input_func, output_func)
        elif choice == "5":
            _settings_menu(input_func, output_func)
            _pause(input_func, output_func)
        elif choice == "x":
            _print(output_func, "Exiting Profile Manager.")
            return EXIT_OK
