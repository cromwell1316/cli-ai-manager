#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import base64
import subprocess
import termios
import tty
import shutil
import time
import logging
from pathlib import Path
from datetime import datetime

# Setup logging
log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ai-man.log")
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Base configuration paths
METADATA_DIR = os.path.expanduser("~/.config/cli-profile-manager")
METADATA_PATH = os.path.join(METADATA_DIR, "profiles_metadata.json")

# Tool configurations
TOOLS = {
    "agy": {
        "name": "Antigravity CLI (agy)",
        "env_var": "HOME",
        "base_dir": os.path.expanduser("~/agy-homes"),
        "cmd": "agy",
        "cred_file": os.path.join(".gemini", "antigravity-cli", "antigravity-oauth-token"),
        "acct_file": os.path.join(".gemini", "google_accounts.json"),
        "import_help": "Import a Windows Credential Manager backup (.json) file"
    },
    "codex": {
        "name": "OpenAI Codex CLI",
        "env_var": "CODEX_HOME",
        "base_dir": os.path.expanduser("~/codex-homes"),
        "cmd": "codex",
        "cred_file": "auth.json",
        "acct_file": None,
        "import_help": "Import a Codex auth.json file"
    },
    "claude": {
        "name": "Anthropic Claude CLI",
        "env_var": "CLAUDE_CONFIG_DIR",
        "base_dir": os.path.expanduser("~/claude-homes"),
        "cmd": "claude",
        "cred_file": ".credentials.json",
        "acct_file": None,
        "import_help": "Import a Claude .credentials.json file"
    }
}

# ANSI Colors
CLR_RESET = "\033[0m"
CLR_BOLD = "\033[1m"
CLR_RED = "\033[31m"
CLR_GREEN = "\033[32m"
CLR_YELLOW = "\033[33m"
CLR_BLUE = "\033[34m"
CLR_MAGENTA = "\033[35m"
CLR_CYAN = "\033[36m"
CLR_WHITE = "\033[37m"
CLR_BG_CYAN = "\033[46m"
CLR_BLACK_TEXT = "\033[30m"

def clear_screen():
    sys.stdout.write("\033[H\033[J")
    sys.stdout.flush()

def get_key():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == '\x1b':
            ch2 = sys.stdin.read(1)
            if ch2 == '[':
                ch3 = sys.stdin.read(1)
                if ch3 == 'A': return 'up'
                elif ch3 == 'B': return 'down'
                elif ch3 == 'C': return 'right'
                elif ch3 == 'D': return 'left'
            return 'esc'
        elif ch in ('\n', '\r'):
            return 'enter'
        elif ch == '\x03': # Ctrl+C
            return 'ctrl+c'
        else:
            return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def load_metadata():
    if os.path.exists(METADATA_PATH):
        try:
            with open(METADATA_PATH, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_metadata(data):
    os.makedirs(METADATA_DIR, exist_ok=True)
    try:
        with open(METADATA_PATH, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving metadata: {e}")

def get_profiles(tool_key):
    base_dir = TOOLS[tool_key]["base_dir"]
    if not os.path.exists(base_dir):
        os.makedirs(base_dir, exist_ok=True)
    
    profiles = set()
    for d in os.listdir(base_dir):
        if d.startswith("p") and d[1:].isdigit():
            profiles.add(int(d[1:]))
        # For Windows agy, the profile might just be a cred-pN.json file
        elif tool_key == "agy" and d.startswith("cred-p") and d.endswith(".json"):
            num_part = d[6:-5]
            if num_part.isdigit():
                profiles.add(int(num_part))
    
    # Guarantee at least 1..12 are available/listed
    for i in range(1, 13):
        profiles.add(i)
            
    profiles = list(profiles)
    profiles.sort()
    return profiles

def generate_win_cred_from_linux_token(token_path, win_cred_path, profile_home, tool):
    try:
        with open(token_path, "r", encoding="utf-8") as f:
            token_content = f.read().strip()
        if not token_content:
            return False
            
        # Try to find email
        email = "logged in"
        ga_path = os.path.join(profile_home, tool["acct_file"])
        if os.path.exists(ga_path):
            try:
                with open(ga_path, "r") as f:
                    ga = json.load(f)
                    email = ga.get("active", "logged in").rstrip(",")
            except Exception:
                pass
                
        if email in ("(no login)", "logged in"):
            log_dir = os.path.join(profile_home, ".gemini", "antigravity-cli", "log")
            if os.path.exists(log_dir):
                try:
                    for log_file in sorted(os.listdir(log_dir), reverse=True):
                        if log_file.startswith("cli-") and log_file.endswith(".log"):
                            log_path = os.path.join(log_dir, log_file)
                            with open(log_path, "r", errors="ignore") as lf:
                                for line in lf:
                                    if "email=" in line:
                                        parts = line.split("email=")
                                        if len(parts) > 1:
                                            email = parts[1].split()[0].strip().rstrip(",")
                                            break
                        if email not in ("(no login)", "logged in"):
                            break
                except Exception:
                    pass
                    
        blob_size = len(token_content.encode("utf-8"))
        blob_b64 = base64.b64encode(token_content.encode("utf-8")).decode("utf-8")
        
        cred_data = {
            "Target": "gemini:antigravity",
            "Type": 1,
            "Persist": 2,
            "Flags": 0,
            "UserName": "antigravity",
            "Account": email,
            "BlobBase64": blob_b64,
            "BlobSize": blob_size,
            "SavedAt": datetime.now().isoformat()
        }
        
        with open(win_cred_path, "w", encoding="utf-8") as f:
            json.dump(cred_data, f, indent=4)
            
        logging.info(f"Generated Windows credential {win_cred_path} for account {email}")
        return True
    except Exception as e:
        logging.error(f"Failed to generate Windows cred from Linux token: {e}")
        return False

def get_profile_status(tool_key, n, metadata):
    tool = TOOLS[tool_key]
    profile_home = os.path.join(tool["base_dir"], f"p{n}")
    cred_path = os.path.join(profile_home, tool["cred_file"])
    
    email = "(no login)"
    has_token = False
    
    # Windows native token checking for agy
    is_windows_agy = (tool_key == "agy" and os.name == "nt")
    win_cred_path = os.path.join(tool["base_dir"], f"cred-p{n}.json")
    
    if is_windows_agy:
        # Auto-generate Windows cred if missing but Linux token file was synced
        if not os.path.exists(win_cred_path) and os.path.exists(cred_path):
            generate_win_cred_from_linux_token(cred_path, win_cred_path, profile_home, tool)
            
        if os.path.exists(win_cred_path):
            has_token = True
            try:
                with open(win_cred_path, "r", encoding="utf-8-sig") as f:
                    cdata = json.load(f)
                    acct = cdata.get("Account")
                    if acct and acct != "(no login)":
                        email = acct.rstrip(",")
            except Exception:
                pass
        
        # Fallback to google_accounts.json if email is still not found
        ga_path = os.path.join(profile_home, tool["acct_file"])
        if os.path.exists(ga_path):
            try:
                with open(ga_path, "r") as f:
                    ga = json.load(f)
                    email = ga.get("active", "(no login)").rstrip(",")
            except Exception:
                pass
        
        # Fallback: scan log files for email if missing
        if email in ("(no login)", "logged in") and has_token:
            log_dir = os.path.join(profile_home, ".gemini", "antigravity-cli", "log")
            if os.path.exists(log_dir):
                try:
                    for log_file in sorted(os.listdir(log_dir), reverse=True):
                        if log_file.startswith("cli-") and log_file.endswith(".log"):
                            log_path = os.path.join(log_dir, log_file)
                            with open(log_path, "r", errors="ignore") as lf:
                                for line in lf:
                                    if "email=" in line:
                                        parts = line.split("email=")
                                        if len(parts) > 1:
                                            email = parts[1].split()[0].strip().rstrip(",")
                                            break
                            if email not in ("(no login)", "logged in"):
                                break
                except Exception:
                    pass
                    
        if email in ("(no login)", "logged in") and has_token:
            email = "logged in"
            
    elif tool_key == "codex":
        if has_token:
            try:
                with open(cred_path, "r") as f:
                    data = json.load(f)
                idt = data.get("tokens", {}).get("id_token")
                if idt:
                    payload_b64 = idt.split(".")[1]
                    payload_b64 += "=" * (4 - len(payload_b64) % 4)
                    payload = json.loads(base64.urlsafe_b64decode(payload_b64).decode("utf-8"))
                    email = payload.get("email") or payload.get("https://api.openai.com/profile", {}).get("email") or "logged in"
                elif data.get("OPENAI_API_KEY"):
                    email = "API Key"
            except Exception:
                email = "logged in"
                
    elif tool_key == "claude":
        if has_token:
            try:
                with open(cred_path, "r") as f:
                    data = json.load(f)
                oauth = data.get("claudeAiOauth", {})
                sub = oauth.get("subscriptionType")
                tier = oauth.get("rateLimitTier")
                if sub and tier:
                    email = f"Logged in ({sub}/{tier})"
                elif sub:
                    email = f"Logged in ({sub})"
                else:
                    email = "Logged in"
            except Exception:
                email = "Logged in"
                
    label = metadata.get(tool_key, {}).get(f"p{n}", {}).get("label", "")
    return {
        "num": n,
        "email": email,
        "has_token": has_token,
        "label": label,
        "home": profile_home
    }

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

def run_menu(options, title=""):
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
        print(f"{CLR_WHITE}Use {CLR_BOLD}↑/↓{CLR_RESET}{CLR_WHITE} arrows to select, {CLR_BOLD}Enter{CLR_RESET}{CLR_WHITE} to confirm, {CLR_BOLD}Esc/q{CLR_RESET}{CLR_WHITE} to go back.{CLR_RESET}")
        
        key = get_key()
        if key == 'up':
            selected_idx = (selected_idx - 1) % len(options)
        elif key == 'down':
            selected_idx = (selected_idx + 1) % len(options)
        elif key == 'enter':
            return selected_idx
        elif key in ('esc', 'q'):
            return -1
        elif key == 'ctrl+c':
            sys.exit(0)

def view_status(tool_key):
    clear_screen()
    tool_name = TOOLS[tool_key]["name"]
    print_header(f"STATUS: {tool_name.upper()}")
    print()
    
    metadata = load_metadata()
    profiles = get_profiles(tool_key)
    
    print(f"{CLR_BOLD}{CLR_WHITE}{'Profile':<9} {'Active Account / Tier':<30} {'Status':<12} {'Label':<12}{CLR_RESET}")
    print("-" * 64)
    
    for n in profiles:
        status = get_profile_status(tool_key, n, metadata)
        stat_str = f"{CLR_GREEN}Active{CLR_RESET}" if status["has_token"] else f"{CLR_RED}No Token{CLR_RESET}"
        lbl_str = f"({status['label']})" if status["label"] else ""
        email_color = CLR_CYAN if status["has_token"] else CLR_RESET
        print(f"p{status['num']:<7} {email_color}{status['email']:<30}{CLR_RESET} {stat_str:<12} {CLR_YELLOW}{lbl_str:<12}{CLR_RESET}")
        
    print()
    input("Press Enter to return...")

def launch_account(tool_key):
    tool = TOOLS[tool_key]
    metadata = load_metadata()
    while True:
        profiles = get_profiles(tool_key)
        options = []
        for n in profiles:
            status = get_profile_status(tool_key, n, metadata)
            lbl = f" ({status['label']})" if status['label'] else ""
            tok = f"{CLR_GREEN}[Active]{CLR_RESET}" if status['has_token'] else f"{CLR_RED}[No Token]{CLR_RESET}"
            options.append(f"p{status['num']:<3} | {status['email']:<28} {tok}{CLR_YELLOW}{lbl}{CLR_RESET}")
            
        sel = run_menu(options, f"LAUNCH {tool['name'].upper()}")
        if sel == -1:
            break
            
        profile_num = profiles[sel]
        profile_home = os.path.join(tool["base_dir"], f"p{profile_num}")
        os.makedirs(profile_home, exist_ok=True)
        
        clear_screen()
        print_header(f"LAUNCHING p{profile_num} ({tool['cmd']})")
        print(f"\nConfig directory: {profile_home}\n")
        print(f"{CLR_YELLOW}Running CLI... Exit the tool normally to return here.{CLR_RESET}\n")
        
        # Build environment
        env = os.environ.copy()
        env[tool["env_var"]] = profile_home
        
        # Specialized env override for tools like agy that read HOME
        if tool_key == "agy":
            env["HOME"] = profile_home
            
        logging.info(f"Launching {tool_key} profile p{profile_num} interactively")
        try:
            # Launch CLI interactively
            subprocess.run([tool["cmd"]], env=env)
            logging.info(f"Exited {tool_key} profile p{profile_num}")
        except FileNotFoundError:
            logging.error(f"Failed to launch {tool['cmd']}: Executable not found")
            print(f"{CLR_RED}Error: {tool['cmd']} CLI is not installed or not in PATH.{CLR_RESET}")
            input("\nPress Enter to continue...")
        except KeyboardInterrupt:
            pass
        
        # Refresh metadata
        metadata = load_metadata()

def add_account(tool_key):
    tool = TOOLS[tool_key]
    clear_screen()
    print_header(f"ADD NEW PROFILE ({tool['cmd']})")
    print()
    
    profiles = get_profiles(tool_key)
    last_p = profiles[-1] if profiles else 0
    next_p = last_p + 1
    
    p_num_input = input(f"Enter profile number [Default: {next_p}]: ").strip()
    if p_num_input:
        try:
            next_p = int(p_num_input)
        except ValueError:
            print(f"{CLR_RED}Invalid profile number!{CLR_RESET}")
            input("\nPress Enter to return...")
            return
            
    profile_home = os.path.join(tool["base_dir"], f"p{next_p}")
    os.makedirs(os.path.join(profile_home, os.path.dirname(tool["cred_file"])), exist_ok=True)
    
    clear_screen()
    print_header(f"SETUP p{next_p} ({tool['cmd']})")
    print(f"\nConfig directory: {profile_home}\n")
    print("Launching CLI to sign in.")
    print("Complete the browser authentication flow. Once logged in, exit the tool.\n")
    input("Press Enter to start authentication...")
    
    env = os.environ.copy()
    env[tool["env_var"]] = profile_home
    if tool_key == "agy":
        env["HOME"] = profile_home
        
    logging.info(f"Adding new profile p{next_p} for {tool_key}")
    try:
        if tool_key == "claude":
            subprocess.run([tool["cmd"]], env=env)
        elif tool_key == "codex":
            subprocess.run([tool["cmd"]], env=env)
        else:
            subprocess.run([tool["cmd"]], env=env)
        logging.info(f"Successfully configured new profile p{next_p} for {tool_key}")
    except FileNotFoundError:
        logging.error(f"Failed to add profile: {tool['cmd']} executable not found")
        print(f"{CLR_RED}Error: {tool['cmd']} CLI is not installed or not in PATH.{CLR_RESET}")
    except KeyboardInterrupt:
        pass
        
    print(f"\n{CLR_GREEN}Setup finished for p{next_p}!{CLR_RESET}")
    input("Press Enter to return...")

def set_label(tool_key):
    tool = TOOLS[tool_key]
    metadata = load_metadata()
    while True:
        profiles = get_profiles(tool_key)
        options = []
        for n in profiles:
            status = get_profile_status(tool_key, n, metadata)
            lbl = f" ({status['label']})" if status['label'] else " (no label)"
            options.append(f"p{status['num']:<3} | {status['email']:<28} {CLR_YELLOW}{lbl}{CLR_RESET}")
            
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
        
        if tool_key not in metadata:
            metadata[tool_key] = {}
        if f"p{profile_num}" not in metadata[tool_key]:
            metadata[tool_key][f"p{profile_num}"] = {}
            
        metadata[tool_key][f"p{profile_num}"]["label"] = new_lbl
        save_metadata(metadata)
        
        print(f"\n{CLR_GREEN}Label updated successfully!{CLR_RESET}")
        input("Press Enter to return...")

import glob

def find_windows_user():
    try:
        users = os.listdir("/mnt/c/Users")
        for u in users:
            if u not in ["Public", "Default", "Default User", "All Users", "desktop.ini"]:
                return u
    except Exception:
        pass
    return "Oliver"

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
    
    profiles = get_profiles(tool_key)
    next_p = (profiles[-1] if profiles else 0) + 1
    
    p_num_input = input(f"\nSelected: {cred_file}\nEnter target profile number [Default: {next_p}]: ").strip()
    if p_num_input:
        try:
            next_p = int(p_num_input)
        except ValueError:
            print(f"\n{CLR_RED}Invalid profile number!{CLR_RESET}")
            input("\nPress Enter to return...")
            return
            
    print(f"\nImporting into profile p{next_p}...")
    
    try:
        wsl_dest_dir = os.path.join(tool["base_dir"], f"p{next_p}")
        wsl_dest_file = os.path.join(wsl_dest_dir, tool["cred_file"])
        os.makedirs(os.path.dirname(wsl_dest_file), exist_ok=True)
        
        if tool_key == "agy":
            with open(cred_file, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
            blob_data = base64.b64decode(data["BlobBase64"]).decode("utf-8")
            with open(wsl_dest_file, "w") as f:
                f.write(blob_data)
            email = data.get("Account")
            if email:
                acct_file_path = os.path.join(wsl_dest_dir, tool["acct_file"])
                os.makedirs(os.path.dirname(acct_file_path), exist_ok=True)
                with open(acct_file_path, "w") as f:
                    json.dump({"active": email}, f, indent=2)
            print(f"\n{CLR_GREEN}Successfully imported credential for agy! (Account: {email or 'Unknown'}){CLR_RESET}")
        else:
            shutil.copy(cred_file, wsl_dest_file)
            print(f"\n{CLR_GREEN}Successfully copied credential file!{CLR_RESET}")
            
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
            status = get_profile_status(tool_key, n, metadata)
            if status['has_token']:
                lbl = f" ({status['label']})" if status['label'] else ""
                options.append(f"p{status['num']:<3} | {status['email']:<28} {CLR_GREEN}[Active]{CLR_RESET}{CLR_YELLOW}{lbl}{CLR_RESET}")
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
        status = get_profile_status(tool_key, profile_num, metadata)
        cred_path = os.path.join(status["home"], tool["cred_file"])
        
        win_user = find_windows_user()
        export_dir = f"/mnt/c/Users/{win_user}/Downloads"
        if not os.path.exists(export_dir):
            export_dir = f"/mnt/c/Users/{win_user}/Desktop"
            if not os.path.exists(export_dir):
                export_dir = "/mnt/c/"
            
        if tool_key == "agy":
            try:
                with open(cred_path, "r") as f:
                    token_data = f.read()
                b64 = base64.b64encode(token_data.encode("utf-8")).decode("utf-8")
                
                win_json = {
                    "Target": "gemini:antigravity",
                    "Type": 1,
                    "Persist": 2,
                    "Flags": 0,
                    "UserName": "antigravity",
                    "Account": status["email"] if status["email"] != "logged in" else None,
                    "BlobBase64": b64,
                    "SavedAt": datetime.now().isoformat()
                }
                
                dest_file = os.path.join(export_dir, f"cred-p{profile_num}-exported.json")
                with open(dest_file, "w") as f:
                    json.dump(win_json, f, indent=2)
                print(f"\n{CLR_GREEN}Successfully exported to Windows: {dest_file}{CLR_RESET}")
            except Exception as e:
                print(f"\n{CLR_RED}Export error: {e}{CLR_RESET}")
        else:
            dest_file = os.path.join(export_dir, f"{tool_key}-p{profile_num}-exported.json")
            try:
                shutil.copy(cred_path, dest_file)
                print(f"\n{CLR_GREEN}Successfully exported to Windows: {dest_file}{CLR_RESET}")
            except Exception as e:
                print(f"\n{CLR_RED}Export error: {e}{CLR_RESET}")
                
        input("\nPress Enter to return...")

def clear_profile(tool_key):
    tool = TOOLS[tool_key]
    metadata = load_metadata()
    while True:
        profiles = get_profiles(tool_key)
        options = []
        for n in profiles:
            status = get_profile_status(tool_key, n, metadata)
            lbl = f" ({status['label']})" if status['label'] else ""
            tok = f"{CLR_GREEN}[Active]{CLR_RESET}" if status['has_token'] else f"{CLR_RED}[No Token]{CLR_RESET}"
            options.append(f"p{status['num']:<3} | {status['email']:<28} {tok}{CLR_YELLOW}{lbl}{CLR_RESET}")
            
        sel = run_menu(options, f"CLEAR PROFILE: {tool['name'].upper()}")
        if sel == -1:
            break
            
        profile_num = profiles[sel]
        profile_home = os.path.join(tool["base_dir"], f"p{profile_num}")
        
        clear_screen()
        print_header(f"CLEAR p{profile_num}")
        print(f"\n{CLR_RED}WARNING: This will completely delete the profile folder and log you out!{CLR_RESET}")
        print(f"Path: {profile_home}")
        confirm = input("\nType 'yes' to confirm deletion: ").strip().lower()
        if confirm == 'yes':
            logging.info(f"Clearing profile p{profile_num} for {tool_key} at {profile_home}")
            try:
                shutil.rmtree(profile_home, ignore_errors=True)
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
    
    # Strip quotes
    if (cred_file.startswith('"') and cred_file.endswith('"')) or (cred_file.startswith("'") and cred_file.endswith("'")):
        cred_file = cred_file[1:-1]
    
    # Auto-convert Windows paths to WSL paths
    if len(cred_file) >= 3 and cred_file[1:3] == ":\\":
        drive = cred_file[0].lower()
        cred_file = f"/mnt/{drive}/" + cred_file[3:].replace("\\", "/")
        
    cred_file = os.path.expanduser(cred_file)
    
    # If the provided path is a directory, append the default credential file name
    if os.path.isdir(cred_file):
        if tool_key == "codex":
            cred_file = os.path.join(cred_file, "auth.json")
        elif tool_key == "claude":
            cred_file = os.path.join(cred_file, ".credentials.json")
    
    if not os.path.exists(cred_file):
        print(f"\n{CLR_RED}Error: File '{cred_file}' not found.{CLR_RESET}")
        input("\nPress Enter to return...")
        return
        
    profiles = get_profiles(tool_key)
    last_p = profiles[-1] if profiles else 0
    next_p = last_p + 1
    
    p_num_input = input(f"Enter target profile number [Default: {next_p}]: ").strip()
    if p_num_input:
        try:
            next_p = int(p_num_input)
        except ValueError:
            print(f"\n{CLR_RED}Invalid profile number!{CLR_RESET}")
            input("\nPress Enter to return...")
            return
            
    print(f"\nImporting into profile p{next_p}...")
    
    try:
        wsl_dest_dir = os.path.join(tool["base_dir"], f"p{next_p}")
        wsl_dest_file = os.path.join(wsl_dest_dir, tool["cred_file"])
        os.makedirs(os.path.dirname(wsl_dest_file), exist_ok=True)
        
        if tool_key == "agy":
            # agy Windows Credential Manager JSON decoding
            with open(cred_file, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
                
            blob_data = base64.b64decode(data["BlobBase64"]).decode("utf-8")
            
            with open(wsl_dest_file, "w") as f:
                f.write(blob_data)
                
            email = data.get("Account")
            if email:
                acct_file_path = os.path.join(wsl_dest_dir, tool["acct_file"])
                os.makedirs(os.path.dirname(acct_file_path), exist_ok=True)
                with open(acct_file_path, "w") as f:
                    json.dump({"active": email}, f, indent=2)
            print(f"\n{CLR_GREEN}Successfully imported credential for agy! (Account: {email or 'Unknown'}){CLR_RESET}")
        else:
            # Codex / Claude raw copy-import
            shutil.copy(cred_file, wsl_dest_file)
            print(f"\n{CLR_GREEN}Successfully copied credential file to {wsl_dest_file}!{CLR_RESET}")
            
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
        sel = run_menu(menu_options, tool["name"].upper())
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
    
    DIRS_TO_SYNC = ["agy-homes", "codex-homes", "claude-homes", ".config/cli-profile-manager"]
    
    if os.name == 'nt':
        win_home = Path(os.environ.get("USERPROFILE", r"C:\Users\Oliver"))
        wsl_home = Path(r"\\wsl.localhost\Ubuntu\home\olivercromwell")
        # Fallback if wsl.localhost doesn't work
        if not wsl_home.exists():
            wsl_home = Path(r"\\wsl$\Ubuntu\home\olivercromwell")
    else:
        wsl_home = Path(os.path.expanduser("~"))
        win_user = find_windows_user()
        win_home = Path(f"/mnt/c/Users/{win_user}")
        
    if not wsl_home.exists():
        print(f"{CLR_RED}Error: Cannot access WSL path: {wsl_home}{CLR_RESET}")
        input("\nPress Enter to return...")
        return
        
    if not win_home.exists():
        print(f"{CLR_RED}Error: Cannot access Windows path: {win_home}{CLR_RESET}")
        input("\nPress Enter to return...")
        return
        
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
    
    clear_screen()
    print_header("SYNCHRONIZING...")
    print()
    
    src_base = wsl_home if is_wsl_to_win else win_home
    dst_base = win_home if is_wsl_to_win else wsl_home
    
    print(f"Mode:  {'HARD (Mirror)' if is_hard else 'SOFT (Incremental)'}")
    print(f"Source: {src_base}")
    print(f"Dest:   {dst_base}\n")
    
    if is_hard:
        print(f"{CLR_RED}WARNING: Hard sync will DELETE extra files in Dest that are not in Source.{CLR_RESET}")
        confirm = input("Type 'yes' to proceed: ").strip().lower()
        if confirm != 'yes':
            print("Operation cancelled.")
            input("\nPress Enter to return...")
            return
            
    logging.info(f"Starting sync. Mode: {'HARD' if is_hard else 'SOFT'}, Source: {src_base}, Dest: {dst_base}")
    
    def sync_dir(src: Path, dst: Path, hard_mode: bool):
        if not src.exists():
            return
        
        # Hard sync: remove destination first to ensure exact mirror
        if hard_mode and dst.exists():
            try:
                shutil.rmtree(dst, ignore_errors=True)
                logging.info(f"Hard sync: Cleared destination {dst}")
            except Exception as e:
                logging.error(f"Hard sync clear failed for {dst}: {e}")
                print(f"{CLR_RED}Failed to clear {dst}: {e}{CLR_RESET}")
                
        dst.mkdir(parents=True, exist_ok=True)
        copied = 0
        scanned_dirs = 0
        for root, dirs, files in os.walk(src):
            scanned_dirs += 1
            # Exclude heavy/unnecessary directories to speed up network sync
            dirs[:] = [d for d in dirs if d not in ('cache', 'log', '.tempmediaStorage', '.venv', 'node_modules')]
            
            print(f"\r  -> Scanning dir #{scanned_dirs}: {Path(root).name[:40]:<40}", end="", flush=True)
            
            # Ensure the directory itself is created even if it has no files
            rel_root = Path(root).relative_to(src)
            (dst / rel_root).mkdir(parents=True, exist_ok=True)
            
            for file in files:
                src_file = Path(root) / file
                rel_path = src_file.relative_to(src)
                dst_file = dst / rel_path
                dst_file.parent.mkdir(parents=True, exist_ok=True)
                
                try:
                    if src_file.is_symlink():
                        continue
                        
                    if not src_file.exists():
                        continue
                        
                    if hard_mode or not dst_file.exists() or src_file.stat().st_mtime > dst_file.stat().st_mtime:
                        shutil.copy2(src_file, dst_file)
                        copied += 1
                except FileNotFoundError:
                    pass
                except Exception as e:
                    if not str(src_file).endswith(".log"):
                        logging.warning(f"Failed to copy {rel_path}: {e}")
                        # Don't print to avoid breaking the carriage return progress bar
                        
        print("\r" + " " * 80 + "\r", end="", flush=True) # Clear progress line
        if copied > 0:
            logging.info(f"Synced {src.name}: {copied} files {'mirrored' if hard_mode else 'updated'}.")
            print(f"{CLR_GREEN}Synced {src.name}: {copied} files {'mirrored' if hard_mode else 'updated'}.{CLR_RESET}")
            
    for d in DIRS_TO_SYNC:
        print(f"Scanning {d}...")
        sync_dir(src_base / d, dst_base / d, is_hard)
        
    # Generate Windows credentials directly after sync
    if is_wsl_to_win:
        print("Finalizing profile credentials...")
        src_agy = src_base / "agy-homes"
        dst_agy = dst_base / "agy-homes"
        if src_agy.exists():
            for d in os.listdir(src_agy):
                if d.startswith("p") and d[1:].isdigit():
                    token_path = src_agy / d / ".gemini" / "antigravity-cli" / "antigravity-oauth-token"
                    win_cred_path = dst_agy / f"cred-{d}.json"
                    profile_home = src_agy / d
                    if token_path.exists():
                        generate_win_cred_from_linux_token(
                            str(token_path), 
                            str(win_cred_path), 
                            str(profile_home), 
                            TOOLS["agy"]
                        )
                        
    logging.info("Sync completed successfully.")
    print(f"\n{CLR_CYAN}Sync Complete!{CLR_RESET}")
    input("\nPress Enter to return...")

def main():
    while True:
        options = [
            "[1] Antigravity CLI (agy)",
            "[2] OpenAI Codex CLI",
            "[3] Anthropic Claude CLI",
            "[4] Sync Profiles (WSL <-> Windows)",
            "[x] Exit"
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

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        clear_screen()
        sys.exit(0)
