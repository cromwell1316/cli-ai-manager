from .metadata import load_metadata
from . import interactive_model
from . import windows_support
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


def _windows_agy_session_lines(profile_num, login=False):
    state = windows_support.windows_agy_session_state(
        TOOLS["agy"]["base_dir"],
        profile_num,
        login=login,
        native_windows=True,
    )
    color = CLR_YELLOW if state["ready"] else CLR_RED
    lines = [f"{CLR_WHITE_BOLD}Windows AGY shared slot:{CLR_RESET} {state['live_slot']['target']}"]
    lines.extend(f"{color}{line}{CLR_RESET}" for line in windows_support.windows_agy_guardrail_lines(state))
    if not state["ready"]:
        lines.extend(f"{CLR_RED}{line}{CLR_RESET}" for line in state["blockers"])
        lines.extend(f"{CLR_DIM}{line}{CLR_RESET}" for line in windows_support.windows_agy_recovery_hint_lines(state))
    return state, lines


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
    if tool_key == "agy":
        state, lines = _windows_agy_session_lines(profile_num, login=False)
        for line in lines:
            _print(output, line)
        if not state["ready"]:
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
    if tool_key == "agy":
        _state, lines = _windows_agy_session_lines(profile_num, login=True)
        for line in lines:
            _print(output, line)
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
    menu_items = interactive_model.CREDENTIAL_SYNC_MENU
    while True:
        _banner(output, f"{TOOLS[tool_key]['name'].upper()} CREDENTIAL SYNC / RECOVERY")
        for idx, item in enumerate(menu_items):
            _menu_item(output, item.marker, item.label, selected=(idx == 0))
        _hint(output, "Use *, <, ^, x. Legacy m/i/e shortcuts also work.")
        choice = _choice(
            f"{CLR_RED}>{CLR_RESET} ",
            interactive_model.choice_keys(menu_items),
            input_func,
            output,
        )
        action = interactive_model.action_for_choice(menu_items, choice)
        if action == "magic_import":
            _print(output, f"{CLR_YELLOW}Magic import is available in WSL interactive mode; use manual import here.{CLR_RESET}")
        elif action == "manual_import":
            _import_profile(tool_key, input_func, output)
        elif action == "export":
            _export_profile(tool_key, input_func, output)
        elif action == "back":
            return
        _pause(input_func, output)


def _tool_menu(tool_key, input_func, output):
    menu_items = interactive_model.WINDOWS_TOOL_MENU
    while True:
        _banner(output, TOOLS[tool_key]["name"].upper())
        for line in _profile_status_lines(tool_key):
            _print(output, line)
        _print(output, "")
        for idx, item in enumerate(menu_items):
            _menu_item(output, item.marker, item.label, selected=(idx == 0))
        _hint(output, "Use symbols/shortcuts, Enter confirms typed command.")
        choice = _choice(
            f"{CLR_RED}>{CLR_RESET} ",
            interactive_model.choice_keys(menu_items),
            input_func,
            output,
        )
        action = interactive_model.action_for_choice(menu_items, choice)
        if action == "launch":
            _launch_profile(tool_key, input_func, output)
        elif action == "login":
            _login_profile(tool_key, input_func, output)
        elif action == "status":
            for line in _profile_status_lines(tool_key, include_quota=True):
                _print(output, line)
        elif action == "label":
            _label_profile(tool_key, input_func, output)
        elif action == "credential_sync":
            _credential_sync_menu(tool_key, input_func, output)
        elif action == "clear":
            _clear_profile(tool_key, input_func, output)
        elif action == "back":
            return
        _pause(input_func, output)


def _sync_menu(input_func, output):
    direction_items = interactive_model.SYNC_DIRECTION_MENU
    mode_items = interactive_model.SYNC_MODE_MENU
    _banner(output, "SYNC PROFILES")
    for idx, item in enumerate(direction_items):
        _menu_item(output, item.marker, item.label, selected=(idx == 0))
    direction_choice = _choice(f"{CLR_RED}>{CLR_RESET} ", interactive_model.choice_keys(direction_items), input_func, output)
    direction_action = interactive_model.action_for_choice(direction_items, direction_choice)
    if direction_action == "back":
        return
    direction = direction_action
    for item in mode_items:
        _menu_item(output, item.marker, item.label)
    mode_choice = _choice(f"{CLR_RED}>{CLR_RESET} ", interactive_model.choice_keys(mode_items), input_func, output)
    mode = interactive_model.action_for_choice(mode_items, mode_choice)
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
    menu_items = interactive_model.ROOT_MENU
    while True:
        _banner(output_func, "UNIFIED PROFILE MANAGER", "AI-MAN")
        for idx, item in enumerate(menu_items):
            _menu_item(output_func, item.marker, item.label, selected=(idx == 0))
        _hint(output_func, "Use @, $, ^, ~, !, x. Legacy digits still work.")
        choice = _choice(f"{CLR_RED}>{CLR_RESET} ", interactive_model.choice_keys(menu_items), input_func, output_func)
        action = interactive_model.action_for_choice(menu_items, choice, cancelled_action="exit")
        if action == "agy":
            _tool_menu("agy", input_func, output_func)
        elif action == "codex":
            _tool_menu("codex", input_func, output_func)
        elif action == "claude":
            _tool_menu("claude", input_func, output_func)
        elif action == "sync":
            _sync_menu(input_func, output_func)
            _pause(input_func, output_func)
        elif action == "settings":
            _settings_menu(input_func, output_func)
            _pause(input_func, output_func)
        elif action == "exit":
            _print(output_func, f"{CLR_RESET}Exiting Profile Manager.")
            return EXIT_OK
