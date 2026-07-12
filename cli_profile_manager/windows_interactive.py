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

CLR_RESET = "\033[0m"
CLR_RED = "\033[31m"
CLR_RED_BOLD = "\033[1;31m"
CLR_DIM = "\033[2m"
CLR_WHITE_BOLD = "\033[1;37m"
CLR_CYAN = "\033[36m"
CLR_GREEN = "\033[32m"
CLR_YELLOW = "\033[33m"
CLR_PANEL = "\033[48;5;232m"


def _print(output, text=""):
    output(text)


def _input(prompt, input_func):
    try:
        return input_func(prompt)
    except EOFError:
        return "x"


def _pause(input_func, output):
    _input(f"{CLR_DIM}Press Enter to continue...{CLR_RESET}", input_func)


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
            _print(output, f"{CLR_GREEN}{result.message}{CLR_RESET}")
        elif result.payload:
            _print(output, f"{CLR_GREEN}ok{CLR_RESET}")
        return True
    _print(output, f"{CLR_RED}{result.message or 'operation failed'}{CLR_RESET}")
    return False


def _banner(output, title, subtitle=None):
    width = max(52, len(title) + 12)
    _print(output)
    _print(output, f"{CLR_PANEL}{CLR_RED_BOLD}{'=' * width}{CLR_RESET}")
    _print(output, f"{CLR_PANEL}{CLR_WHITE_BOLD}{title.center(width)}{CLR_RESET}")
    if subtitle:
        _print(output, f"{CLR_PANEL}{CLR_DIM}{subtitle.center(width)}{CLR_RESET}")
    _print(output, f"{CLR_PANEL}{CLR_RED_BOLD}{'=' * width}{CLR_RESET}")


def _menu_item(output, marker, label, selected=False):
    marker_text = f"[{marker}]"
    prefix = f"{CLR_CYAN}-->{CLR_RESET} " if selected else "    "
    color = CLR_RED_BOLD if selected else CLR_WHITE_BOLD
    _print(output, f"{prefix}{color}{marker_text}{CLR_RESET} {label}")


def _hint(output, text):
    _print(output, f"{CLR_DIM}{text}{CLR_RESET}")


def _profile_or_default(raw, default):
    raw = raw.strip()
    if not raw:
        return default
    return parse_profile(raw)


def _profile_status_lines(tool_key, include_quota=False):
    result = list_profiles_operation(tool_key, include_quota=include_quota)
    lines = [f"{CLR_WHITE_BOLD}{TOOLS[tool_key]['name']}{CLR_RESET}", f"{CLR_DIM}Next profile: {result.payload['next_profile']}{CLR_RESET}"]
    for status in result.payload["profiles"]:
        token = status.get("token_state") or ("valid" if status.get("has_token") else "missing")
        account = status.get("email") or status.get("account") or "(unknown)"
        label = status.get("label") or ""
        occupied = "*" if status.get("exists") else "-"
        suffix = f" [{label}]" if label else ""
        token_color = CLR_GREEN if token in ("valid", "active") else CLR_RED
        lines.append(f"{CLR_RED}{occupied}{CLR_RESET} {status['profile']}: {account} token={token_color}{token}{CLR_RESET}{suffix}")
    return lines


def _select_profile(tool_key, input_func, output, default=None):
    default = first_free_profile(tool_key) if default is None else default
    raw = _input(f"{CLR_RED}Profile{CLR_RESET} [p{default}]: ", input_func)
    try:
        return _profile_or_default(raw, default)
    except ValueError as e:
        _print(output, f"{CLR_RED}{e}{CLR_RESET}")
        return None


def _launch_profile(tool_key, input_func, output):
    profile_num = _select_profile(tool_key, input_func, output, default=1)
    if profile_num is None:
        return
    status = profile_status_operation(tool_key, f"p{profile_num}").payload
    if not status.get("has_token"):
        _print(output, f"{CLR_RED}profile p{profile_num} has no token; use login or import first{CLR_RESET}")
        return
    from .cli import run_cli_tool

    code = run_cli_tool(tool_key, profile_num)
    _print(output, f"{CLR_DIM}{tool_key} p{profile_num} exited with code {code}{CLR_RESET}")


def _login_profile(tool_key, input_func, output):
    profile_num = _select_profile(tool_key, input_func, output)
    if profile_num is None:
        return
    from .cli import run_cli_tool

    code = run_cli_tool(tool_key, profile_num, [], login=True)
    _print(output, f"{CLR_DIM}{tool_key} login p{profile_num} exited with code {code}{CLR_RESET}")


def _import_profile(tool_key, input_func, output):
    path = _input("Credential path: ", input_func).strip()
    if not path:
        _print(output, f"{CLR_DIM}import cancelled{CLR_RESET}")
        return
    profile_num = _select_profile(tool_key, input_func, output)
    if profile_num is None:
        return
    result = import_credential_operation(tool_key, path, f"p{profile_num}")
    if _print_result(result, output):
        _print(output, f"{CLR_GREEN}imported into {result.payload['profile']}: {result.payload['destination']}{CLR_RESET}")


def _export_profile(tool_key, input_func, output):
    profile_num = _select_profile(tool_key, input_func, output, default=1)
    if profile_num is None:
        return
    target = _input("Destination file or directory [default]: ", input_func).strip() or None
    result = export_credential_operation(tool_key, f"p{profile_num}", target)
    if _print_result(result, output):
        _print(output, f"{CLR_GREEN}exported {result.payload['profile']}: {result.payload['destination']}{CLR_RESET}")


def _label_profile(tool_key, input_func, output):
    profile_num = _select_profile(tool_key, input_func, output, default=1)
    if profile_num is None:
        return
    label = _input("Label (empty clears): ", input_func).strip()
    result = label_profile_operation(tool_key, f"p{profile_num}", label)
    if _print_result(result, output):
        _print(output, f"{CLR_GREEN}label saved for {result.payload['profile']}{CLR_RESET}")


def _clear_profile(tool_key, input_func, output):
    profile_num = _select_profile(tool_key, input_func, output, default=1)
    if profile_num is None:
        return
    confirm = _input(f"Type yes to clear {tool_key} p{profile_num}: ", input_func).strip().lower()
    if confirm != "yes":
        _print(output, f"{CLR_DIM}clear cancelled{CLR_RESET}")
        return
    result = clear_profile_operation(tool_key, f"p{profile_num}")
    if _print_result(result, output):
        _print(output, f"{CLR_GREEN}cleared {result.payload['profile']}: {result.payload['cleared']}{CLR_RESET}")


def _credential_sync_menu(tool_key, input_func, output):
    while True:
        _banner(output, f"{TOOLS[tool_key]['name'].upper()} CREDENTIAL SYNC / RECOVERY")
        _menu_item(output, "*", "Magic Import from Windows", selected=True)
        _menu_item(output, "<", "Import Windows Credential (Manual)")
        _menu_item(output, "^", "Export Credential to Windows")
        _menu_item(output, "x", "Back")
        _hint(output, "Use *, <, ^, x. Legacy m/i/e shortcuts also work.")
        choice = _choice(
            f"{CLR_RED}>{CLR_RESET} ",
            {"*", "m", "<", "i", "^", "e", "x", "b"},
            input_func,
            output,
        )
        if choice in ("*", "m"):
            _print(output, f"{CLR_YELLOW}Magic import is available in WSL interactive mode; use manual import here.{CLR_RESET}")
        elif choice in ("<", "i"):
            _import_profile(tool_key, input_func, output)
        elif choice in ("^", "e"):
            _export_profile(tool_key, input_func, output)
        elif choice in ("x", "b"):
            return
        _pause(input_func, output)


def _tool_menu(tool_key, input_func, output):
    while True:
        _banner(output, TOOLS[tool_key]["name"].upper())
        for line in _profile_status_lines(tool_key):
            _print(output, line)
        _print(output, "")
        _menu_item(output, ">", "Launch Account", selected=True)
        _menu_item(output, "+", "Login / Re-authenticate")
        _menu_item(output, "i", "Detailed Account Status")
        _menu_item(output, "#", "Set Profile Label")
        _menu_item(output, "~", "Credential Sync / Recovery")
        _menu_item(output, "-", "Clear / Logout Profile")
        _menu_item(output, "x", "Back")
        _hint(output, "Use symbols/shortcuts, Enter confirms typed command.")
        choice = _choice(
            f"{CLR_RED}>{CLR_RESET} ",
            {">", "+", "a", "l", "i", "s", "#", "~", "*", "r", "-", "c", "x", "b", "1", "2", "3", "4", "5", "6"},
            input_func,
            output,
        )
        if choice in (">", "1"):
            _launch_profile(tool_key, input_func, output)
        elif choice in ("+", "a", "l", "2"):
            _login_profile(tool_key, input_func, output)
        elif choice in ("i", "s", "3"):
            for line in _profile_status_lines(tool_key, include_quota=True):
                _print(output, line)
        elif choice in ("#", "4"):
            _label_profile(tool_key, input_func, output)
        elif choice in ("~", "*", "r", "5"):
            _credential_sync_menu(tool_key, input_func, output)
        elif choice in ("-", "c", "6"):
            _clear_profile(tool_key, input_func, output)
        elif choice in ("x", "b"):
            return
        _pause(input_func, output)


def _sync_menu(input_func, output):
    _banner(output, "SYNC PROFILES")
    _menu_item(output, ">", "WSL -> Windows", selected=True)
    _menu_item(output, "<", "Windows -> WSL")
    _menu_item(output, "x", "Back")
    direction_choice = _choice(f"{CLR_RED}>{CLR_RESET} ", {">", "<", "x", "b", "1", "2"}, input_func, output)
    if direction_choice in ("x", "b"):
        return
    direction = "wsl" if direction_choice in (">", "1") else "windows"
    _menu_item(output, "~", "Soft")
    _menu_item(output, "!", "Hard")
    mode_choice = _choice(f"{CLR_RED}>{CLR_RESET} ", {"~", "!", "1", "2"}, input_func, output)
    mode = "soft" if mode_choice in ("~", "1") else "hard"
    dry_run = _input("Dry run? [Y/n]: ", input_func).strip().lower() not in ("n", "no")
    yes = False
    if mode == "hard" and not dry_run:
        yes = _input("Type yes to confirm hard sync: ", input_func).strip().lower() == "yes"
        if not yes:
            _print(output, f"{CLR_DIM}sync cancelled{CLR_RESET}")
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
    _banner(output, "AI-MAN SETTINGS")
    _print(output, f"{CLR_WHITE_BOLD}Profile roots:{CLR_RESET}")
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
        _banner(output_func, "UNIFIED PROFILE MANAGER", "AI-MAN")
        _menu_item(output_func, "@", "Antigravity CLI (agy)", selected=True)
        _menu_item(output_func, "$", "OpenAI Codex CLI")
        _menu_item(output_func, "^", "Anthropic Claude CLI")
        _menu_item(output_func, "~", "Sync Profiles (WSL <-> Windows)")
        _menu_item(output_func, "!", "Settings")
        _menu_item(output_func, "x", "Exit")
        _hint(output_func, "Use @, $, ^, ~, !, x. Legacy digits still work.")
        choice = _choice(f"{CLR_RED}>{CLR_RESET} ", {"@", "$", "^", "~", "!", "x", "1", "2", "3", "4", "5"}, input_func, output_func)
        if choice in ("@", "1"):
            _tool_menu("agy", input_func, output_func)
        elif choice in ("$", "2"):
            _tool_menu("codex", input_func, output_func)
        elif choice in ("^", "3"):
            _tool_menu("claude", input_func, output_func)
        elif choice in ("~", "4"):
            _sync_menu(input_func, output_func)
            _pause(input_func, output_func)
        elif choice in ("!", "5"):
            _settings_menu(input_func, output_func)
            _pause(input_func, output_func)
        elif choice == "x":
            _print(output_func, f"{CLR_RESET}Exiting Profile Manager.")
            return EXIT_OK
