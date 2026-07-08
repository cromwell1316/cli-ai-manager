import glob
import logging
import os
import re
import select
import sys
import termios
import threading
import time
import tty

from .cli import (
    CLR_BG_CYAN,
    CLR_BLACK_TEXT,
    CLR_BLUE,
    CLR_BOLD,
    CLR_CYAN,
    CLR_GREEN,
    CLR_MAGENTA,
    CLR_RED,
    CLR_RESET,
    CLR_WHITE,
    CLR_YELLOW,
    EXIT_OK,
    TOOLS,
    account_email_from_google_accounts,
    build_windows_agy_credential,
    credential_path,
    clear_profile_data,
    core_find_windows_user,
    default_export_dir,
    export_credential_file,
    find_windows_user,
    first_free_profile,
    get_display_profiles,
    get_profile_status,
    get_profiles,
    import_credential_file,
    label_profile,
    load_metadata,
    normalize_credential_path,
    parse_profile,
    profile_home,
    read_wsl_agy_oauth,
    resolve_sync_bases,
    run_cli_tool,
    save_metadata,
    quota_payload,
    status_payload,
    sync_profiles_noninteractive,
    quota_summary,
    write_json_atomic,
)

INTERACTIVE_QUOTA_CACHE = {}
INTERACTIVE_QUOTA_LOCK = threading.Lock()
QUOTA_FRESH_SECONDS = 300
ANSI_RE = re.compile(
    r"(?:\x1b\[[0-?]*[ -/]*[@-~]|\x1b\][^\x07]*(?:\x07|\x1b\\)|\x1b[@-_])"
)


def visible_len(text):
    return len(ANSI_RE.sub("", str(text)))


def visible_ljust(text, width):
    text = str(text)
    return text + (" " * max(0, width - visible_len(text)))


def visible_fit(text, width):
    text = str(text)
    if visible_len(text) <= width:
        return visible_ljust(text, width)
    plain = ANSI_RE.sub("", text)
    if width <= 3:
        return plain[:width]
    return plain[:width - 3] + "..."


def interactive_quota_enabled():
    return os.environ.get("AI_MAN_INTERACTIVE_QUOTA", "1").lower() not in ("0", "false", "no", "off")


def interactive_quota_timeout():
    raw = os.environ.get("AI_MAN_INTERACTIVE_QUOTA_TIMEOUT", "8")
    try:
        return max(1.0, float(raw))
    except ValueError:
        return 8.0


def quota_cache_entry(tool_key, profile_num):
    with INTERACTIVE_QUOTA_LOCK:
        return INTERACTIVE_QUOTA_CACHE.get((tool_key, profile_num))


def store_quota_cache(tool_key, profile_num, entry):
    with INTERACTIVE_QUOTA_LOCK:
        INTERACTIVE_QUOTA_CACHE[(tool_key, profile_num)] = entry


def load_quota_background(tool_key, profile_num):
    try:
        quota = quota_payload(tool_key, profile_num, interactive_quota_timeout())["quota"]
    except Exception as e:
        quota = {
            "state": "error",
            "limits": {},
            "warnings": [str(e)],
        }
    quota["fetched_at"] = time.time()
    store_quota_cache(tool_key, profile_num, {
        "state": "ready",
        "quota": quota,
        "fetched_at": quota["fetched_at"],
    })


def ensure_quota_loading(tool_key, profile_num):
    entry = quota_cache_entry(tool_key, profile_num)
    if entry is not None:
        return entry
    entry = {
        "state": "loading",
        "quota": {
            "state": "loading",
            "limits": {},
            "warnings": ["quota is loading"],
        },
        "fetched_at": None,
    }
    store_quota_cache(tool_key, profile_num, entry)
    thread = threading.Thread(
        target=load_quota_background,
        args=(tool_key, profile_num),
        daemon=True,
    )
    entry["thread"] = thread
    thread.start()
    return entry


def status_with_auto_quota(tool_key, profile_num, metadata):
    status = status_payload(tool_key, profile_num, metadata)
    if not interactive_quota_enabled():
        return status
    if not status["has_token"]:
        status["quota"] = {
            "state": "no_token",
            "limits": {},
            "warnings": ["profile has no token"],
        }
        return status
    entry = ensure_quota_loading(tool_key, profile_num)
    status["quota"] = entry["quota"]
    return status


def color_quota_text(text, status):
    quota = status.get("quota") or {}
    state = quota.get("state")
    if state == "loading":
        return f"{CLR_YELLOW}{text}{CLR_RESET}"
    fetched_at = quota.get("fetched_at")
    if fetched_at is None:
        return f"{CLR_RED}{text}{CLR_RESET}" if state not in ("available", "loading") else text
    color = CLR_GREEN if time.time() - fetched_at <= QUOTA_FRESH_SECONDS else CLR_RED
    return f"{color}{text}{CLR_RESET}"


def quota_text(status, color=True):
    summary = quota_summary(status)
    if summary == "unknown":
        summary = "not parsed"
    text = summary or "quota pending"
    if len(text) > 24:
        text = f"{text[:21]}..."
    return color_quota_text(text, status) if color else text


def invalidate_quota_cache(tool_key=None, profile_num=None):
    with INTERACTIVE_QUOTA_LOCK:
        if tool_key is None:
            INTERACTIVE_QUOTA_CACHE.clear()
            return
        if profile_num is None:
            for key in list(INTERACTIVE_QUOTA_CACHE):
                if key[0] == tool_key:
                    del INTERACTIVE_QUOTA_CACHE[key]
            return
        INTERACTIVE_QUOTA_CACHE.pop((tool_key, profile_num), None)


def any_quota_loading(tool_key=None):
    with INTERACTIVE_QUOTA_LOCK:
        for (entry_tool, _), entry in INTERACTIVE_QUOTA_CACHE.items():
            if tool_key is not None and entry_tool != tool_key:
                continue
            if entry.get("state") == "loading":
                return True
    return False


def read_key_byte(fd=None, timeout=None):
    fd = sys.stdin.fileno() if fd is None else fd
    if timeout is not None:
        ready, _, _ = select.select([fd], [], [], timeout)
        if not ready:
            return None
    data = os.read(fd, 1)
    if not data:
        return None
    return data.decode(errors="ignore")


def key_from_escape_sequence(fd):
    sequence = ""
    deadline = time.monotonic() + 0.5
    while time.monotonic() < deadline:
        ch = read_key_byte(fd, max(0.0, deadline - time.monotonic()))
        if ch is None:
            return None
        sequence += ch
        if ch.isalpha() or ch == "~":
            break

    final = sequence[-1:] if sequence else ""
    if final == 'A':
        return 'up'
    if final == 'B':
        return 'down'
    if final == 'C':
        return 'right'
    if final == 'D':
        return 'left'
    return 'esc'


def get_key(timeout=None):
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = read_key_byte(fd, timeout)
        if ch is None:
            return None
        if ch == '\x1b':
            ch2 = read_key_byte(fd, 0.5)
            if ch2 is None:
                return 'esc'
            if ch2 in ('[', 'O'):
                key = key_from_escape_sequence(fd)
                return key or 'esc'
            return 'esc'
        elif ch in ('\n', '\r'):
            return 'enter'
        elif ch == '\x03': # Ctrl+C
            return 'ctrl+c'
        else:
            return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def render_status_screen(tool_key):
    clear_screen()
    tool_name = TOOLS[tool_key]["name"]
    print_header(f"STATUS: {tool_name.upper()}")
    print()

    metadata = load_metadata()
    profiles = get_display_profiles(tool_key)

    widths = {
        "profile": 8,
        "account": 34,
        "status": 10,
        "quota": 24,
        "label": 14,
    }
    print(
        f"{CLR_BOLD}{CLR_WHITE}"
        f"{'Profile':<{widths['profile']}} "
        f"{'Active Account / Tier':<{widths['account']}} "
        f"{'Status':<{widths['status']}} "
        f"{'Quota':<{widths['quota']}} "
        f"{'Label':<{widths['label']}}"
        f"{CLR_RESET}"
    )
    print("-" * (sum(widths.values()) + len(widths) - 1))

    for n in profiles:
        status = status_with_auto_quota(tool_key, n, metadata)
        stat_str = f"{CLR_GREEN}Active{CLR_RESET}" if status["has_token"] else f"{CLR_RED}No Token{CLR_RESET}"
        lbl_str = f"({status['label']})" if status["label"] else ""
        email_color = CLR_CYAN if status["has_token"] else CLR_RESET
        quota = quota_text(status)
        profile = f"p{status['num']}"
        email = f"{email_color}{status['email']}{CLR_RESET}"
        label = f"{CLR_YELLOW}{lbl_str}{CLR_RESET}" if lbl_str else ""
        print(
            f"{visible_fit(profile, widths['profile'])} "
            f"{visible_fit(email, widths['account'])} "
            f"{visible_fit(stat_str, widths['status'])} "
            f"{visible_fit(quota, widths['quota'])} "
            f"{visible_fit(label, widths['label'])}"
        )
    print()
    print("Press Enter to return...")


def view_status(tool_key):
    while True:
        render_status_screen(tool_key)
        key = get_key(timeout=0.5 if any_quota_loading(tool_key) else None)
        if key is None:
            continue
        if key in ("enter", "esc", "q"):
            return
        elif key == "ctrl+c":
            sys.exit(0)


def clear_screen():
    sys.stdout.write("\033[H\033[J")
    sys.stdout.flush()


def print_header(title=""):
    width = 62
    border = "═" * (width - 2)
    print(f"{CLR_BOLD}{CLR_CYAN}╔{border}╗{CLR_RESET}")
    if title:
        padding = (width - 2 - len(title)) // 2
        pad_str = " " * padding
        extra = " " if (width - 2 - len(title)) % 2 != 0 else ""
        print(f"{CLR_BOLD}{CLR_CYAN}║{CLR_RESET}{pad_str}{CLR_BOLD}{CLR_WHITE}{title}{CLR_RESET}{pad_str}{extra}{CLR_BOLD}{CLR_CYAN}║{CLR_RESET}")
    print(f"{CLR_BOLD}{CLR_CYAN}╚{border}╝{CLR_RESET}")

def run_menu(options, title="", shortcuts=None):
    shortcuts = shortcuts or {}
    selected_idx = 0
    while True:
        clear_screen()
        print_header(title)
        print()

        for idx, option in enumerate(options):
            if idx == selected_idx:
                print(f"  {CLR_BOLD}{CLR_CYAN}--> \033[40m\033[1;37m{option}{CLR_RESET}")
            else:
                print(f"      \033[90m{option}{CLR_RESET}")
        print()
        print(f"{CLR_WHITE}Use {CLR_BOLD}↑/↓{CLR_RESET}{CLR_WHITE}, digits/shortcuts, {CLR_BOLD}Enter{CLR_RESET}{CLR_WHITE} to confirm, {CLR_BOLD}Esc/q{CLR_RESET}{CLR_WHITE} to go back.{CLR_RESET}")

        key = get_key()
        if key == 'up':
            selected_idx = (selected_idx - 1) % len(options)
        elif key == 'down':
            selected_idx = (selected_idx + 1) % len(options)
        elif key == 'enter':
            return selected_idx
        elif key.isdigit() and key != "0":
            idx = int(key) - 1
            if 0 <= idx < len(options):
                return idx
        elif key in shortcuts:
            return shortcuts[key]
        elif key in ('esc', 'q'):
            return -1
        elif key == 'ctrl+c':
            sys.exit(0)

def launch_account(tool_key):
    tool = TOOLS[tool_key]
    metadata = load_metadata()
    while True:
        profiles = get_display_profiles(tool_key)
        options = []
        for n in profiles:
            status = status_with_auto_quota(tool_key, n, metadata)
            lbl = f" ({status['label']})" if status['label'] else ""
            tok = f"{CLR_GREEN}[Active]{CLR_RESET}" if status['has_token'] else f"{CLR_RED}[No Token]{CLR_RESET}"
            quota = quota_text(status)
            options.append(f"p{status['num']:<3} | {status['email']:<28} {tok} {quota:<24}{CLR_YELLOW}{lbl}{CLR_RESET}")

        sel = run_menu(options, f"LAUNCH {tool['name'].upper()}")
        if sel == -1:
            break

        profile_num = profiles[sel]
        status = status_payload(tool_key, profile_num, metadata)
        if not status["has_token"]:
            clear_screen()
            print_header(f"LAUNCH p{profile_num} ({tool['cmd']})")
            print(f"\n{CLR_RED}Profile p{profile_num} has no token. Use login or import first.{CLR_RESET}")
            input("\nPress Enter to continue...")
            continue

        clear_screen()
        print_header(f"LAUNCHING p{profile_num} ({tool['cmd']})")
        print(f"\nConfig directory: {profile_home(tool_key, profile_num)}\n")
        print(f"{CLR_YELLOW}Running CLI... Exit the tool normally to return here.{CLR_RESET}\n")
        code = run_cli_tool(tool_key, profile_num)
        invalidate_quota_cache(tool_key, profile_num)
        if code != EXIT_OK:
            print(f"{CLR_RED}Command exited with code {code}.{CLR_RESET}")
            input("\nPress Enter to continue...")

        # Refresh metadata
        metadata = load_metadata()

def add_account(tool_key):
    tool = TOOLS[tool_key]
    clear_screen()
    print_header(f"ADD NEW PROFILE ({tool['cmd']})")
    print()

    next_p = first_free_profile(tool_key)

    p_num_input = input(f"Enter profile number [Default: {next_p}]: ").strip()
    if p_num_input:
        try:
            next_p = parse_profile(p_num_input)
        except ValueError:
            print(f"{CLR_RED}Invalid profile number!{CLR_RESET}")
            input("\nPress Enter to return...")
            return

    os.makedirs(profile_home(tool_key, next_p), exist_ok=True)

    clear_screen()
    print_header(f"SETUP p{next_p} ({tool['cmd']})")
    print(f"\nConfig directory: {profile_home(tool_key, next_p)}\n")
    print("Launching CLI to sign in.")
    print("Complete the browser authentication flow. Once logged in, exit the tool.\n")
    input("Press Enter to start authentication...")

    logging.info(f"Adding new profile p{next_p} for {tool_key}")
    code = run_cli_tool(tool_key, next_p)
    invalidate_quota_cache(tool_key, next_p)
    if code == EXIT_OK:
        logging.info(f"Successfully configured new profile p{next_p} for {tool_key}")
    else:
        print(f"{CLR_RED}Command exited with code {code}.{CLR_RESET}")

    print(f"\n{CLR_GREEN}Setup finished for p{next_p}!{CLR_RESET}")
    input("Press Enter to return...")

def set_label(tool_key):
    tool = TOOLS[tool_key]
    metadata = load_metadata()
    while True:
        profiles = get_display_profiles(tool_key)
        options = []
        for n in profiles:
            status = status_with_auto_quota(tool_key, n, metadata)
            lbl = f" ({status['label']})" if status['label'] else " (no label)"
            quota = quota_text(status)
            options.append(f"p{status['num']:<3} | {status['email']:<28} {quota:<24} {CLR_YELLOW}{lbl}{CLR_RESET}")

        sel = run_menu(options, f"LABEL {tool['name'].upper()}")
        if sel == -1:
            break

        profile_num = profiles[sel]
        clear_screen()
        print_header(f"LABEL p{profile_num} ({tool['cmd']})")
        print()

        current_lbl = metadata.get(tool_key, {}).get(f"p{profile_num}", {}).get("label", "")
        print(f"Current label: {CLR_YELLOW}{current_lbl or '(none)'}{CLR_RESET}\n")
        new_lbl = input("Enter new label (or empty to clear): ").strip()

        label_profile(tool_key, profile_num, new_lbl)
        metadata = load_metadata()

        print(f"\n{CLR_GREEN}Label updated successfully!{CLR_RESET}")
        input("Press Enter to return...")

def find_windows_user():
    return core_find_windows_user()

def magic_import(tool_key):
    tool = TOOLS[tool_key]
    clear_screen()
    print_header(f"MAGIC IMPORT: {tool['name'].upper()}")
    print()

    win_user = find_windows_user()
    print(f"Scanning Windows drives for user: {win_user}...\n")

    found_files = []
    if tool_key == "agy":
        pattern = f"/mnt/c/Users/{win_user}/agy-homes/cred-*.json"
        found_files.extend(glob.glob(pattern))
    elif tool_key == "codex":
        pattern = f"/mnt/c/Users/{win_user}/codex-homes/p*/auth.json"
        found_files.extend(glob.glob(pattern))
    elif tool_key == "claude":
        pattern = f"/mnt/c/Users/{win_user}/claude-homes/p*/.credentials.json"
        found_files.extend(glob.glob(pattern))

    if not found_files:
        print(f"{CLR_YELLOW}No Windows credentials found automatically.{CLR_RESET}")
        input("\nPress Enter to return...")
        return

    options = []
    for f in found_files:
        options.append(f)

    sel = run_menu(options, "SELECT FILE TO IMPORT")
    if sel == -1:
        return

    cred_file = found_files[sel]

    next_p = first_free_profile(tool_key)

    p_num_input = input(f"\nSelected: {cred_file}\nEnter target profile number [Default: {next_p}]: ").strip()
    if p_num_input:
        try:
            next_p = parse_profile(p_num_input)
        except ValueError:
            print(f"\n{CLR_RED}Invalid profile number!{CLR_RESET}")
            input("\nPress Enter to return...")
            return

    print(f"\nImporting into profile p{next_p}...")

    try:
        _, dest_file = import_credential_file(tool_key, cred_file, next_p)
        invalidate_quota_cache(tool_key, next_p)
        print(f"\n{CLR_GREEN}Successfully imported credential to {dest_file}!{CLR_RESET}")
    except Exception as e:
        print(f"\n{CLR_RED}Import error: {e}{CLR_RESET}")

    input("\nPress Enter to return...")

def export_credential(tool_key):
    tool = TOOLS[tool_key]
    metadata = load_metadata()
    while True:
        profiles = get_profiles(tool_key)
        options = []
        valid_profiles = []
        for n in profiles:
            status = status_with_auto_quota(tool_key, n, metadata)
            if status['has_token']:
                lbl = f" ({status['label']})" if status['label'] else ""
                quota = quota_text(status)
                options.append(f"p{status['num']:<3} | {status['email']:<28} {CLR_GREEN}[Active]{CLR_RESET} {quota:<24}{CLR_YELLOW}{lbl}{CLR_RESET}")
                valid_profiles.append(n)

        if not valid_profiles:
            clear_screen()
            print_header(f"EXPORT {tool['name'].upper()}")
            print(f"\n{CLR_YELLOW}No active profiles to export.{CLR_RESET}")
            input("\nPress Enter to return...")
            break

        sel = run_menu(options, f"EXPORT {tool['name'].upper()}")
        if sel == -1:
            break

        profile_num = valid_profiles[sel]
        try:
            dest_file = export_credential_file(tool_key, profile_num)
            print(f"\n{CLR_GREEN}Successfully exported to Windows: {dest_file}{CLR_RESET}")
        except Exception as e:
            print(f"\n{CLR_RED}Export error: {e}{CLR_RESET}")

        input("\nPress Enter to return...")

def clear_profile(tool_key):
    tool = TOOLS[tool_key]
    metadata = load_metadata()
    while True:
        profiles = get_display_profiles(tool_key)
        options = []
        for n in profiles:
            status = status_with_auto_quota(tool_key, n, metadata)
            lbl = f" ({status['label']})" if status['label'] else ""
            tok = f"{CLR_GREEN}[Active]{CLR_RESET}" if status['has_token'] else f"{CLR_RED}[No Token]{CLR_RESET}"
            quota = quota_text(status)
            options.append(f"p{status['num']:<3} | {status['email']:<28} {tok} {quota:<24}{CLR_YELLOW}{lbl}{CLR_RESET}")

        sel = run_menu(options, f"CLEAR PROFILE: {tool['name'].upper()}")
        if sel == -1:
            break

        profile_num = profiles[sel]
        home = profile_home(tool_key, profile_num)

        clear_screen()
        print_header(f"CLEAR p{profile_num}")
        print(f"\n{CLR_RED}WARNING: This will completely delete the profile folder and log you out!{CLR_RESET}")
        print(f"Path: {home}")
        confirm = input("\nType 'yes' to confirm deletion: ").strip().lower()
        if confirm == 'yes':
            logging.info(f"Clearing profile p{profile_num} for {tool_key} at {home}")
            try:
                clear_profile_data(tool_key, profile_num)
                invalidate_quota_cache(tool_key, profile_num)
                print(f"\n{CLR_GREEN}Profile p{profile_num} has been cleared.{CLR_RESET}")
                logging.info(f"Successfully cleared profile p{profile_num}")
            except Exception as e:
                logging.error(f"Error clearing profile p{profile_num}: {e}")
                print(f"\n{CLR_RED}Error clearing profile: {e}{CLR_RESET}")
        else:
            print("\nOperation cancelled.")

        input("\nPress Enter to return...")

def import_credential(tool_key):
    tool = TOOLS[tool_key]
    clear_screen()
    print_header(f"IMPORT CREDENTIAL: {tool['name'].upper()}")
    print()

    print(f"{CLR_WHITE}{tool['import_help']}{CLR_RESET}\n")

    cred_file = input("Enter path to file to import: ").strip()

    cred_file = normalize_credential_path(tool_key, cred_file)

    if not os.path.exists(cred_file):
        print(f"\n{CLR_RED}Error: File '{cred_file}' not found.{CLR_RESET}")
        input("\nPress Enter to return...")
        return

    next_p = first_free_profile(tool_key)

    p_num_input = input(f"Enter target profile number [Default: {next_p}]: ").strip()
    if p_num_input:
        try:
            next_p = parse_profile(p_num_input)
        except ValueError:
            print(f"\n{CLR_RED}Invalid profile number!{CLR_RESET}")
            input("\nPress Enter to return...")
            return

    print(f"\nImporting into profile p{next_p}...")

    try:
        _, dest_file = import_credential_file(tool_key, cred_file, next_p)
        invalidate_quota_cache(tool_key, next_p)
        print(f"\n{CLR_GREEN}Successfully imported credential to {dest_file}!{CLR_RESET}")

    except Exception as e:
        print(f"\n{CLR_RED}Import error: {e}{CLR_RESET}")

    input("\nPress Enter to return...")

def run_tool_manager(tool_key):
    tool = TOOLS[tool_key]
    menu_options = [
        "[>] Launch Account",
        "[+] Add New Profile (OAuth)",
        "[*] Magic Import from Windows",
        "[<] Import Windows Credential (Manual)",
        "[^] Export Credential to Windows",
        "[-] Clear / Logout Profile",
        "[#] Set Profile Label",
        "[i] Detailed Account Status",
        "[x] Back to main menu"
    ]

    while True:
        shortcuts = {
            ">": 0,
            "+": 1,
            "a": 1,
            "*": 2,
            "i": 3,
            "<": 3,
            "e": 4,
            "^": 4,
            "c": 5,
            "-": 5,
            "l": 6,
            "#": 6,
            "s": 7,
        }
        sel = run_menu(menu_options, tool["name"].upper(), shortcuts)
        if sel == 0:
            launch_account(tool_key)
        elif sel == 1:
            add_account(tool_key)
        elif sel == 2:
            magic_import(tool_key)
        elif sel == 3:
            import_credential(tool_key)
        elif sel == 4:
            export_credential(tool_key)
        elif sel == 5:
            clear_profile(tool_key)
        elif sel == 6:
            set_label(tool_key)
        elif sel == 7:
            view_status(tool_key)
        elif sel in (8, -1):
            break

def sync_profiles():
    clear_screen()
    print_header("SYNC PROFILES (WSL <-> WINDOWS)")
    print()

    options = [
        "1. [SOFT] WSL -> Windows (Update newer files only)",
        "2. [SOFT] Windows -> WSL (Update newer files only)",
        "3. [HARD] WSL -> Windows (Exact mirror, delete extra files)",
        "4. [HARD] Windows -> WSL (Exact mirror, delete extra files)",
        "5. Cancel"
    ]

    sel = run_menu(options, "SYNC DIRECTION & MODE")
    if sel in (4, -1):
        return

    is_hard = sel in (2, 3)
    is_wsl_to_win = sel in (0, 2)
    direction = "wsl" if is_wsl_to_win else "windows"
    mode = "hard" if is_hard else "soft"
    src_base, dst_base = resolve_sync_bases(direction)

    clear_screen()
    print_header("SYNCHRONIZING...")
    print()

    print(f"Mode:  {'HARD (Mirror)' if is_hard else 'SOFT (Incremental)'}")
    print(f"Source: {src_base}")
    print(f"Dest:   {dst_base}\n")

    if is_hard:
        try:
            preflight = sync_profiles_noninteractive(direction, mode, dry_run=True, yes=True)
            print(f"Hard-delete preflight: {preflight['would_delete']} destination paths would be removed.")
            for path in preflight["delete_paths"]:
                print(f"  {path}")
        except Exception as e:
            print(f"{CLR_RED}Preflight failed: {e}{CLR_RESET}")
            input("\nPress Enter to return...")
            return
        print(f"{CLR_RED}WARNING: Hard sync will DELETE extra files in Dest that are not in Source.{CLR_RESET}")
        confirm = input("Type 'yes' to proceed: ").strip().lower()
        if confirm != 'yes':
            print("Operation cancelled.")
            input("\nPress Enter to return...")
            return

    try:
        result = sync_profiles_noninteractive(direction, mode, dry_run=False, yes=True)
    except Exception as e:
        logging.error(f"Sync failed: {e}")
        print(f"{CLR_RED}Sync failed: {e}{CLR_RESET}")
        input("\nPress Enter to return...")
        return

    logging.info(f"Sync completed successfully: {result}")
    invalidate_quota_cache()
    print(
        f"{CLR_GREEN}Updated {result['copied']} files, skipped {result['skipped']}, "
        f"converted {result['converted']} agy credentials, invalid {result['invalid']}.{CLR_RESET}"
    )
    print(f"\n{CLR_CYAN}Sync Complete!{CLR_RESET}")
    input("\nPress Enter to return...")


def run_interactive_main():
    while True:
        options = [
            "[1] Antigravity CLI (agy)",
            "[2] OpenAI Codex CLI",
            "[3] Anthropic Claude CLI",
            "[4] Sync Profiles (WSL <-> Windows)",
            "[x] Exit",
        ]
        sel = run_menu(options, "UNIFIED PROFILE MANAGER")
        if sel == 0:
            run_tool_manager("agy")
        elif sel == 1:
            run_tool_manager("codex")
        elif sel == 2:
            run_tool_manager("claude")
        elif sel == 3:
            sync_profiles()
        elif sel in (4, -1):
            clear_screen()
            print("Exiting Profile Manager. Goodbye!")
            break
    return EXIT_OK
