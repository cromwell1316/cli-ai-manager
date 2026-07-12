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
    MenuItem("agy", "@", "Antigravity CLI (agy)", ("1",)),
    MenuItem("codex", "$", "OpenAI Codex CLI", ("2",)),
    MenuItem("claude", "^", "Anthropic Claude CLI", ("3",)),
    MenuItem("sync", "~", "Sync Profiles (WSL <-> Windows)", ("4",)),
    MenuItem("settings", "!", "Settings", ("5",)),
    MenuItem("exit", "x", "Exit"),
)

TOOL_MENU = (
    MenuItem("launch", ">", "Launch Account", ("1",)),
    MenuItem("login", "+", "Login / Re-authenticate", ("a", "l", "2")),
    MenuItem("status", "i", "Detailed Account Status", ("s", "3")),
    MenuItem("label", "#", "Set Profile Label", ("4",)),
    MenuItem("credential_sync", "~", "Credential Sync / Recovery", ("*", "r", "5")),
    MenuItem("clear", "-", "Clear / Logout Profile", ("c", "6")),
    MenuItem("back", "x", "Back to main menu", ("b",)),
)

WINDOWS_TOOL_MENU = tuple(
    MenuItem(item.action, item.marker, "Back" if item.action == "back" else item.label, item.aliases)
    for item in TOOL_MENU
)

CREDENTIAL_SYNC_MENU = (
    MenuItem("magic_import", "*", "Magic Import from Windows", ("m",)),
    MenuItem("manual_import", "<", "Import Windows Credential (Manual)", ("i",)),
    MenuItem("export", "^", "Export Credential to Windows", ("e",)),
    MenuItem("back", "x", "Back", ("b",)),
)

SYNC_DIRECTION_MENU = (
    MenuItem("wsl", ">", "WSL -> Windows", ("1",)),
    MenuItem("windows", "<", "Windows -> WSL", ("2",)),
    MenuItem("back", "x", "Back", ("b",)),
)

SYNC_MODE_MENU = (
    MenuItem("soft", "~", "Soft", ("1",)),
    MenuItem("hard", "!", "Hard", ("2",)),
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
