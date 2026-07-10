import os
import ntpath
from pathlib import Path


DISPLAY_SLOT_COUNT = 12
WINDOWS_USER_EXCLUSIONS = {
    "Public",
    "Default",
    "Default User",
    "All Users",
    "desktop.ini",
    "Все пользователи",
}
WINDOWS_PROFILE_MARKERS = (
    "agy-homes",
    "codex-homes",
    "claude-homes",
    os.path.join(".config", "cli-profile-manager"),
)


TOOLS = {
    "agy": {
        "name": "Antigravity CLI (agy)",
        "env_var": "HOME",
        "base_dir": os.path.expanduser(os.environ.get("AI_MAN_AGY_HOME", "~/agy-homes")),
        "cmd": "agy",
        "cred_file": os.path.join(".gemini", "oauth_creds.json"),
        "acct_file": os.path.join(".gemini", "google_accounts.json"),
        "import_help": "Import a Windows Credential Manager backup (.json) file",
    },
    "codex": {
        "name": "OpenAI Codex CLI",
        "env_var": "CODEX_HOME",
        "base_dir": os.path.expanduser(os.environ.get("AI_MAN_CODEX_HOME", "~/codex-homes")),
        "cmd": "codex",
        "cred_file": "auth.json",
        "acct_file": None,
        "import_help": "Import a Codex auth.json file",
    },
    "claude": {
        "name": "Anthropic Claude CLI",
        "env_var": "CLAUDE_CONFIG_DIR",
        "base_dir": os.path.expanduser(os.environ.get("AI_MAN_CLAUDE_HOME", "~/claude-homes")),
        "cmd": "claude",
        "cred_file": ".credentials.json",
        "acct_file": None,
        "import_help": "Import a Claude .credentials.json file",
    },
}


def refresh_from_env():
    TOOLS["agy"]["base_dir"] = os.path.expanduser(os.environ.get("AI_MAN_AGY_HOME", "~/agy-homes"))
    TOOLS["codex"]["base_dir"] = os.path.expanduser(os.environ.get("AI_MAN_CODEX_HOME", "~/codex-homes"))
    TOOLS["claude"]["base_dir"] = os.path.expanduser(os.environ.get("AI_MAN_CLAUDE_HOME", "~/claude-homes"))


def parse_profile(value):
    raw = str(value).strip().lower()
    if raw.startswith("p"):
        raw = raw[1:]
    if not raw.isdigit():
        raise ValueError(f"invalid profile '{value}': expected pN with a positive integer")
    num = int(raw)
    if num <= 0:
        raise ValueError(f"invalid profile '{value}': profile number must be positive")
    return num


def get_occupied_profiles(tool_key):
    base_dir = TOOLS[tool_key]["base_dir"]
    if not os.path.exists(base_dir):
        os.makedirs(base_dir, exist_ok=True)

    profiles = set()
    for d in os.listdir(base_dir):
        if d.startswith("p") and d[1:].isdigit():
            profiles.add(int(d[1:]))
        elif os.name == "nt" and tool_key == "agy" and d.startswith("cred-p") and d.endswith(".json"):
            num_part = d[6:-5]
            if num_part.isdigit():
                profiles.add(int(num_part))
    return sorted(profiles)


def get_display_profiles(tool_key):
    profiles = set(get_occupied_profiles(tool_key))
    profiles.update(range(1, DISPLAY_SLOT_COUNT + 1))
    return sorted(profiles)


def first_free_profile(tool_key):
    occupied = set(get_occupied_profiles(tool_key))
    n = 1
    while n in occupied:
        n += 1
    return n


def is_valid_display_profile(tool_key, n):
    return n in get_display_profiles(tool_key)


def normalize_credential_path(tool_key, cred_file, platform_name=None):
    platform_name = os.name if platform_name is None else platform_name
    cred_file = cred_file.strip()
    if (cred_file.startswith('"') and cred_file.endswith('"')) or (cred_file.startswith("'") and cred_file.endswith("'")):
        cred_file = cred_file[1:-1]
    if platform_name != "nt" and len(cred_file) >= 3 and cred_file[1:3] == ":\\":
        drive = cred_file[0].lower()
        cred_file = f"/mnt/{drive}/" + cred_file[3:].replace("\\", "/")
    cred_file = os.path.expanduser(cred_file)
    if os.path.isdir(cred_file):
        if tool_key == "codex":
            cred_file = os.path.join(cred_file, "auth.json")
        elif tool_key == "claude":
            cred_file = os.path.join(cred_file, ".credentials.json")
    return cred_file


def profile_home(tool_key, n):
    return os.path.join(TOOLS[tool_key]["base_dir"], f"p{n}")


def credential_path(tool_key, n):
    tool = TOOLS[tool_key]
    return os.path.join(profile_home(tool_key, n), tool["cred_file"])


def agy_windows_credential_path(n, base_dir=None):
    base = base_dir or TOOLS["agy"]["base_dir"]
    return os.path.join(str(base), f"cred-p{n}.json")


def make_tool_env(tool_key, n):
    tool = TOOLS[tool_key]
    home = profile_home(tool_key, n)
    env = os.environ.copy()
    env[tool["env_var"]] = home
    if tool_key == "agy":
        env["HOME"] = home
    return env


def windows_user_score(user_home):
    score = 0
    for marker in WINDOWS_PROFILE_MARKERS:
        marker_path = user_home / marker
        if marker_path.exists():
            score += 10
    agy_home = user_home / "agy-homes"
    if agy_home.exists():
        try:
            if any(child.name.startswith("cred-p") or (child.name.startswith("p") and child.name[1:].isdigit()) for child in agy_home.iterdir()):
                score += 20
        except OSError:
            pass
    config = user_home / ".config" / "cli-profile-manager" / "profiles_metadata.json"
    if config.exists():
        score += 10
    return score


def find_windows_user(users_base="/mnt/c/Users"):
    env_userprofile = os.environ.get("USERPROFILE")
    if env_userprofile:
        candidate = ntpath.basename(env_userprofile.rstrip("\\/")) or Path(env_userprofile).name
        if candidate and candidate not in WINDOWS_USER_EXCLUSIONS:
            return candidate
    try:
        users_base = Path(users_base)
        candidates = []
        for user_path in users_base.iterdir():
            user = user_path.name
            if user in WINDOWS_USER_EXCLUSIONS or not user_path.is_dir():
                continue
            candidates.append((windows_user_score(user_path), user.lower(), user))
        if candidates:
            candidates.sort(key=lambda item: (-item[0], item[1]))
            return candidates[0][2]
    except Exception:
        pass
    return "Oliver"


def resolve_sync_bases(direction):
    override_wsl = os.environ.get("AI_MAN_WSL_HOME")
    override_win = os.environ.get("AI_MAN_WINDOWS_HOME")
    if os.name == "nt":
        win_home = Path(override_win or os.environ.get("USERPROFILE", r"C:\Users\Oliver"))
        if override_wsl:
            wsl_home = Path(override_wsl)
        else:
            wsl_home = Path(r"\\wsl.localhost\Ubuntu\home\olivercromwell")
        if not override_wsl and not wsl_home.exists():
            wsl_home = Path(r"\\wsl$\Ubuntu\home\olivercromwell")
    else:
        wsl_home = Path(override_wsl or os.path.expanduser("~"))
        win_home = Path(override_win or f"/mnt/c/Users/{find_windows_user()}")
    src_base = wsl_home if direction == "wsl" else win_home
    dst_base = win_home if direction == "wsl" else wsl_home
    return src_base, dst_base
