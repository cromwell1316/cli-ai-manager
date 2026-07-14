import os
import sys

from .metadata import load_metadata
from . import interactive_model
from . import interactive_render
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
from .terminal_rendering import TerminalFrameRenderer, visible_len

CLR_RESET = "\033[0m"
CLR_RED = "\033[31m"
CLR_RED_BOLD = "\033[1;31m"
CLR_DIM = "\033[2m"
CLR_WHITE_BOLD = "\033[1;37m"
CLR_CYAN = "\033[36m"
CLR_GREEN = "\033[32m"
CLR_YELLOW = "\033[33m"
CLR_BG_BLACK = interactive_render.CLR_BG_BLACK
CLR_DARK_RED = interactive_render.CLR_DARK_RED
CLR_GRAY = "\033[90m"
CLR_CLEAR = "\033[H\033[2J\033[3J"


def _print(output, text=""):
    output(text)


def _line(text="", width=None):
    width = width or 120
    plain_len = visible_len(text)
    padding = " " * max(0, width - plain_len)
    return f"{CLR_BG_BLACK}{text}{padding}{CLR_BG_BLACK}"


def _input(prompt, input_func):
    try:
        return input_func(prompt)
    except EOFError:
        return "x"


def _read_key(input_func):
    if input_func is input and os.name == "nt":
        import msvcrt

        char = msvcrt.getwch()
        if char in ("\x00", "\xe0"):
            code = msvcrt.getwch()
            return {
                "H": "up",
                "P": "down",
                "K": "left",
                "M": "right",
            }.get(code, "")
        if char in ("\r", "\n"):
            return "enter"
        if char == "\x1b":
            return "esc"
        return char.lower()
    value = _input("", input_func).strip().lower()
    return value or "enter"


def _pause(input_func, output):
    _input(f"{CLR_DIM}Press Enter to continue...{CLR_RESET}", input_func)


def _menu_lines(menu_items, title, selected_idx=0, pre_lines=None):
    return interactive_render.render_menu_lines(
        interactive_model.options(menu_items),
        title,
        selected_idx,
        pre_lines=pre_lines,
    )


def _paint_lines(lines, output, renderer=None):
    if renderer is not None:
        renderer.paint(lines)
        return
    for line in lines:
        output(line)


def _native_renderer(output, cache_key):
    if output is print:
        return TerminalFrameRenderer(stdout=sys.stdout, cache_key=cache_key)
    return None


def _show_startup_splash(input_func, output):
    renderer = _native_renderer(output, "splash")
    try:
        _paint_lines(interactive_render.pilot_splash_lines(), output, renderer)
        while True:
            key = _read_key(input_func)
            if key == "enter":
                return True
            if key in ("q", "esc"):
                return False
    finally:
        if renderer is not None:
            renderer.clear()
            renderer.reset()


def _choose_menu(menu_items, title, input_func, output, pre_lines=None, cancelled_action="back"):
    selected_idx = 0
    renderer = _native_renderer(output, "menu")
    try:
        while True:
            _paint_lines(_menu_lines(menu_items, title, selected_idx, pre_lines), output, renderer)
            key = _read_key(input_func)
            if key == "up":
                selected_idx = (selected_idx - 1) % len(menu_items)
                continue
            if key == "down":
                selected_idx = (selected_idx + 1) % len(menu_items)
                continue
            if key == "enter":
                return interactive_model.action_at(menu_items, selected_idx, cancelled_action=cancelled_action)
            if key in ("esc", "q"):
                return cancelled_action
            action = interactive_model.action_for_choice(menu_items, key, cancelled_action=None)
            if action is not None:
                return action
    finally:
        if renderer is not None:
            renderer.clear()
            renderer.reset()


def _choose_index(options, title, input_func, output, pre_lines=None):
    selected_idx = 0
    renderer = _native_renderer(output, "menu")
    try:
        while True:
            lines = interactive_render.render_menu_lines(options, title, selected_idx, pre_lines=pre_lines)
            _paint_lines(lines, output, renderer)
            key = _read_key(input_func)
            if key == "up":
                selected_idx = (selected_idx - 1) % len(options)
                continue
            if key == "down":
                selected_idx = (selected_idx + 1) % len(options)
                continue
            if key == "enter":
                return selected_idx
            if key.isdigit() and key != "0":
                idx = int(key) - 1
                if 0 <= idx < len(options):
                    return idx
            if key in ("esc", "q"):
                return -1
    finally:
        if renderer is not None:
            renderer.clear()
            renderer.reset()


def _profile_action_post_lines(profiles, selected_idx):
    selected = profiles[selected_idx] if profiles and 0 <= selected_idx < len(profiles) else None
    if not selected:
        selected_line = f"{CLR_GRAY}Selected: none{CLR_RESET}"
    else:
        label = selected.get("label") or "none"
        account = selected.get("email") or selected.get("account") or "unknown"
        selected_line = (
            f"{CLR_GRAY}Selected: {CLR_RED_BOLD}p{selected.get('num')}{CLR_RESET}{CLR_BG_BLACK}{CLR_GRAY} "
            f"{account} | label: {CLR_YELLOW}{label}{CLR_RESET}{CLR_BG_BLACK}{CLR_GRAY} | "
            f"{CLR_RED_BOLD}Enter{CLR_RESET}{CLR_BG_BLACK}{CLR_GRAY} launch{CLR_RESET}"
        )
    return ["", selected_line, f"{CLR_GRAY}1-9 launch profile{CLR_RESET}"]


def _profile_action_footer_lines():
    return [
        (
            f"{CLR_GRAY}↑/↓ select   "
            f"{CLR_RED_BOLD}Enter{CLR_RESET}{CLR_BG_BLACK}{CLR_GRAY} launch   "
            f"{CLR_RED}Esc{CLR_RESET}{CLR_BG_BLACK}{CLR_GRAY} back{CLR_RESET}"
        ),
        (
            f"{CLR_GRAY}{CLR_RED}a{CLR_RESET}{CLR_BG_BLACK}{CLR_GRAY} add/login   "
            f"{CLR_RED}l{CLR_RESET}{CLR_BG_BLACK}{CLR_GRAY} label   "
            f"{CLR_DARK_RED}d{CLR_RESET}{CLR_BG_BLACK}{CLR_GRAY} clear/logout   "
            f"{CLR_RED}~{CLR_RESET}{CLR_BG_BLACK}{CLR_GRAY} sync/recovery{CLR_RESET}"
        ),
    ]


def _choose_profile_action(options, profiles, title, input_func, output, pre_lines=None):
    selected_idx = 0
    renderer = _native_renderer(output, "menu")
    try:
        while True:
            lines = interactive_render.render_menu_lines(
                options,
                title,
                selected_idx,
                pre_lines=pre_lines,
                post_lines=_profile_action_post_lines(profiles, selected_idx),
                footer_lines=_profile_action_footer_lines(),
            )
            _paint_lines(lines, output, renderer)
            key = _read_key(input_func)
            if key == "up":
                selected_idx = (selected_idx - 1) % len(options)
                continue
            if key == "down":
                selected_idx = (selected_idx + 1) % len(options)
                continue
            if key == "enter":
                return "launch", selected_idx
            if key.isdigit() and key != "0":
                idx = int(key) - 1
                if 0 <= idx < len(options):
                    return "launch", idx
            if key in ("a", "+"):
                return "login", selected_idx
            if key in ("l", "#"):
                return "label", selected_idx
            if key in ("d", "c", "-"):
                return "clear", selected_idx
            if key in ("~", "m"):
                return "credential_sync", selected_idx
            if key in ("esc", "q", "x", "b"):
                return "back", -1
    finally:
        if renderer is not None:
            renderer.clear()
            renderer.reset()


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
    heading = f"{CLR_RED_BOLD}{subtitle or 'AI-MAN'}{CLR_RESET}{CLR_BG_BLACK} {CLR_WHITE_BOLD}{title}{CLR_RESET}{CLR_BG_BLACK}"
    width = max(52, visible_len(heading))
    term_width = 120
    _print(output, f"{CLR_CLEAR}{_line('', width=term_width)}")
    _print(output, _line(heading, width=term_width))
    _print(output, _line(f"{CLR_RED_BOLD}{'-' * width}{CLR_RESET}{CLR_BG_BLACK}", width=term_width))
    _print(output, _line("", width=term_width))
    return 4


def _menu_item(output, marker, label, selected=False):
    marker_text = f"[{marker}]"
    prefix = f"{CLR_RED_BOLD}|{CLR_RESET}{CLR_BG_BLACK}  " if selected else "   "
    color = CLR_RED_BOLD if selected else CLR_WHITE_BOLD
    label_color = CLR_WHITE_BOLD if selected else CLR_GRAY
    _print(output, _line(f"{prefix}{color}{marker_text}{CLR_RESET}{CLR_BG_BLACK} {label_color}{label}{CLR_RESET}{CLR_BG_BLACK}"))
    return 1


def _hint(output, text):
    _print(output, _line(""))
    _print(output, _line(f"{CLR_GRAY}{text}{CLR_RESET}{CLR_BG_BLACK}"))
    return 2


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


def _select_profile_from_table(tool_key, input_func, output, title):
    action, profile_num = _select_profile_action_from_table(tool_key, input_func, output, title)
    return profile_num if action == "launch" else None


def _select_profile_action_from_table(tool_key, input_func, output, title):
    result = list_profiles_operation(tool_key, include_quota=False)
    profiles = result.payload["profiles"]
    for status in profiles:
        if status.get("has_token"):
            status.setdefault("quota", {"state": "startup_pending", "limits": {}})
        else:
            status.setdefault("quota", {"state": "no_token", "limits": {}})
    pre_lines, rows = interactive_render.launch_account_table(tool_key, profiles)
    action, sel = _choose_profile_action(rows, profiles, title, input_func, output, pre_lines=pre_lines)
    if sel == -1:
        return action, None
    return action, int(profiles[sel]["num"])


def _launch_selected_profile(tool_key, profile_num, output):
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


def _login_selected_profile(tool_key, profile_num, output):
    if tool_key == "agy":
        _state, lines = _windows_agy_session_lines(profile_num, login=True)
        for line in lines:
            _print(output, line)
    from .cli import run_cli_tool

    code = run_cli_tool(tool_key, profile_num, [], login=True)
    _print(output, f"{CLR_DIM}{tool_key} login p{profile_num} exited with code {code}{CLR_RESET}")


def _label_selected_profile(tool_key, profile_num, input_func, output):
    label = _input("Label (empty clears): ", input_func).strip()
    result = label_profile_operation(tool_key, f"p{profile_num}", label)
    if _print_result(result, output):
        _print(output, f"{CLR_GREEN}label saved for {result.payload['profile']}{CLR_RESET}")


def _clear_selected_profile(tool_key, profile_num, input_func, output):
    confirm = _input(f"Type yes to clear {tool_key} p{profile_num}: ", input_func).strip().lower()
    if confirm != "yes":
        _print(output, f"{CLR_DIM}clear cancelled{CLR_RESET}")
        return
    result = clear_profile_operation(tool_key, f"p{profile_num}")
    if _print_result(result, output):
        _print(output, f"{CLR_GREEN}cleared {result.payload['profile']}: {result.payload['cleared']}{CLR_RESET}")


def _launch_profile(tool_key, input_func, output):
    while True:
        action, profile_num = _select_profile_action_from_table(
            tool_key,
            input_func,
            output,
            f"LAUNCH {TOOLS[tool_key]['name'].upper()}",
        )
        if action == "back":
            return
        if action == "launch":
            _launch_selected_profile(tool_key, profile_num, output)
        elif action == "login":
            _login_selected_profile(tool_key, profile_num, output)
        elif action == "label":
            _label_selected_profile(tool_key, profile_num, input_func, output)
        elif action == "clear":
            _clear_selected_profile(tool_key, profile_num, input_func, output)
        elif action == "credential_sync":
            _credential_sync_menu(tool_key, input_func, output)
        _pause(input_func, output)


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
        action = _choose_menu(
            menu_items,
            f"{TOOLS[tool_key]['name'].upper()} CREDENTIAL SYNC / RECOVERY",
            input_func,
            output,
        )
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
        action = _choose_menu(
            menu_items,
            TOOLS[tool_key]["name"].upper(),
            input_func,
            output,
        )
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
    direction_action = _choose_menu(direction_items, "SYNC PROFILES", input_func, output)
    if direction_action == "back":
        return
    direction = direction_action
    mode = _choose_menu(mode_items, "SYNC MODE", input_func, output)
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
    used = _banner(output, "AI-MAN SETTINGS")
    _print(output, _line(f"{CLR_WHITE_BOLD}Profile roots:{CLR_RESET}{CLR_BG_BLACK}"))
    used += 1
    for tool_key, root in payload["profile_roots"].items():
        _print(output, _line(f"  {tool_key}: {root}"))
        used += 1
    _print(output, _line(f"Metadata: {payload['metadata_dir']}"))
    used += 1
    _print(output, _line(f"Sync roots: wsl={payload['sync_roots']['wsl']} windows={payload['sync_roots']['windows']}"))
    used += 1
    quota = payload["quota"]
    _print(output, _line(f"Quota: enabled={quota['interactive_enabled']} timeout={quota['interactive_timeout']} agy_timeout={quota['interactive_agy_timeout']}"))
    used += 1
    if payload.get("warnings"):
        _print(output, _line("Warnings:"))
        used += 1
        for warning in payload["warnings"]:
            _print(output, _line(f"  {warning}"))
            used += 1
    for line in interactive_render.themed_screen_lines([], top_padding=0)[used:]:
        _print(output, line)


def run_windows_interactive_main(input_func=input, output_func=print):
    load_metadata()
    if input_func is input and output_func is print and not _show_startup_splash(input_func, output_func):
        _print(output_func, f"{CLR_RESET}Exiting Profile Manager. Goodbye!")
        return EXIT_OK
    menu_items = interactive_model.ROOT_MENU
    while True:
        action = _choose_menu(
            menu_items,
            "UNIFIED PROFILE MANAGER",
            input_func,
            output_func,
            cancelled_action="exit",
        )
        if action == "agy":
            _launch_profile("agy", input_func, output_func)
        elif action == "codex":
            _launch_profile("codex", input_func, output_func)
        elif action == "claude":
            _launch_profile("claude", input_func, output_func)
        elif action == "sync":
            _sync_menu(input_func, output_func)
            _pause(input_func, output_func)
        elif action == "settings":
            _settings_menu(input_func, output_func)
            _pause(input_func, output_func)
        elif action == "exit":
            _print(output_func, f"{CLR_RESET}Exiting Profile Manager. Goodbye!")
            return EXIT_OK
