from dataclasses import dataclass


@dataclass(frozen=True)
class MenuItem:
    action: str
    marker: str
    label: str
    aliases: tuple[str, ...] = ()

    @property
    def option(self):
        return f"[{self.marker}] {self.label}"


ROOT_MENU = (
    MenuItem("agy", "1", "Antigravity CLI (agy)", ("@",)),
    MenuItem("codex", "2", "OpenAI Codex CLI", ("$",)),
    MenuItem("claude", "3", "Anthropic Claude CLI", ("^",)),
    MenuItem("sync", "4", "Sync Profiles (WSL <-> Windows)", ("~",)),
    MenuItem("settings", "5", "Settings", ("!",)),
    MenuItem("exit", "0", "Exit", ("x",)),
)

TOOL_MENU = (
    MenuItem("launch", "1", "Launch Account", (">",)),
    MenuItem("login", "2", "Login / Re-authenticate", ("+", "a", "l")),
    MenuItem("status", "3", "Detailed Account Status", ("i", "s")),
    MenuItem("label", "4", "Set Profile Label", ("#",)),
    MenuItem("credential_sync", "5", "Credential Sync / Recovery", ("~", "*", "r")),
    MenuItem("clear", "6", "Clear / Logout Profile", ("-", "c")),
    MenuItem("back", "0", "Back to main menu", ("x", "b")),
)

WINDOWS_TOOL_MENU = tuple(
    MenuItem(item.action, item.marker, "Back" if item.action == "back" else item.label, item.aliases)
    for item in TOOL_MENU
)

CREDENTIAL_SYNC_MENU = (
    MenuItem("magic_import", "1", "Magic Import from Windows", ("*", "m")),
    MenuItem("manual_import", "2", "Import Windows Credential (Manual)", ("<", "i")),
    MenuItem("export", "3", "Export Credential to Windows", ("^", "e")),
    MenuItem("back", "0", "Back", ("x", "b")),
)

SYNC_DIRECTION_MENU = (
    MenuItem("wsl", "1", "WSL -> Windows", (">",)),
    MenuItem("windows", "2", "Windows -> WSL", ("<",)),
    MenuItem("back", "0", "Back", ("x", "b")),
)

SYNC_MODE_MENU = (
    MenuItem("soft", "1", "Soft", ("~",)),
    MenuItem("hard", "2", "Hard", ("!",)),
)


def options(items):
    return [item.option for item in items]


def shortcuts(items, include_digits=True):
    mapping = {}
    for idx, item in enumerate(items):
        keys = (item.marker, *item.aliases)
        for key in keys:
            if key.isdigit() and not include_digits:
                continue
            mapping[key.lower()] = idx
    return mapping


def action_at(items, index, cancelled_action="back"):
    if index == -1:
        return cancelled_action
    if 0 <= index < len(items):
        return items[index].action
    return cancelled_action


def action_for_choice(items, choice, cancelled_action="back"):
    normalized = str(choice).strip().lower()
    for item in items:
        keys = (item.marker, *item.aliases)
        if normalized in {key.lower() for key in keys}:
            return item.action
    return cancelled_action


def choice_keys(items):
    keys = set()
    for item in items:
        keys.add(item.marker)
        keys.update(item.aliases)
    return keys


def contract_snapshot():
    def snapshot_items(items):
        return [
            {
                "action": item.action,
                "marker": item.marker,
                "label": item.label,
                "aliases": list(item.aliases),
                "option": item.option,
            }
            for item in items
        ]

    return {
        "root": snapshot_items(ROOT_MENU),
        "tool": snapshot_items(TOOL_MENU),
        "windows_tool": snapshot_items(WINDOWS_TOOL_MENU),
        "credential_sync": snapshot_items(CREDENTIAL_SYNC_MENU),
        "sync_direction": snapshot_items(SYNC_DIRECTION_MENU),
        "sync_mode": snapshot_items(SYNC_MODE_MENU),
        "shortcuts_without_legacy_digits": {
            "root": shortcuts(ROOT_MENU, include_digits=False),
            "tool": shortcuts(TOOL_MENU, include_digits=False),
            "credential_sync": shortcuts(CREDENTIAL_SYNC_MENU, include_digits=False),
        },
    }
