import re
import time

from .cli import agy_quota_entries, quota_summary
from .terminal_rendering import terminal_size, visible_fit, visible_len

CLR_RESET = "\033[0m"
CLR_BOLD = "\033[1m"
CLR_RED = "\033[31m"
CLR_GREEN = "\033[32m"
CLR_YELLOW = "\033[33m"
CLR_CYAN = "\033[36m"
CLR_MAGENTA = "\033[35m"
CLR_WHITE = "\033[37m"
CLR_BG_BLACK = "\033[48;5;0m"
CLR_DARK_RED = "\033[38;5;88m"
CLR_BRIGHT_RED = "\033[38;5;196m"

AGY_DEFAULT_QUOTA_COLUMNS = ["FM", "FH", "FL", "PL", "PH", "CS", "CO", "GPT"]
AGY_QUOTA_COLUMN_GROUPS = (
    ("Flash", ("FM", "FH", "FL")),
    ("Pro", ("PL", "PH")),
    ("Claude", ("CS", "CO")),
    ("GPT", ("GPT",)),
)
AGY_QUOTA_COLUMN_LABELS = {
    "FM": "Mdl",
    "FH": "Hgt",
    "FL": "Low",
    "PL": "Low",
    "PH": "Hgt",
    "CS": "Sonnet",
    "CO": "Opus",
    "GPT": "",
}
QUOTA_ACTIVE_JOB_STATES = ("queued", "running")


def header_lines(title="", width=None):
    term_width = terminal_size()[0]
    width = width or min(max(42, visible_len(title) + 10), term_width)
    width = max(1, min(width, term_width))
    divider = "━" * width
    subtitle = f" {title}" if title else ""
    return [
        f"{CLR_BOLD}{CLR_BRIGHT_RED}AI-MAN{CLR_RESET}{CLR_WHITE}{subtitle}{CLR_RESET}",
        f"{CLR_DARK_RED}{divider}{CLR_RESET}",
    ]


def themed_line(text="", width=None):
    width = max(1, width or terminal_size()[0])
    body = str(text).replace(CLR_RESET, CLR_RESET + CLR_BG_BLACK)
    padding = " " * max(0, width - visible_len(body))
    return f"{CLR_BG_BLACK}{body}{padding}{CLR_BG_BLACK}"


def themed_screen_lines(lines, width=None, height=None, top_padding=2, left_padding=None):
    term_width, term_height = terminal_size()
    width = max(1, width or term_width)
    height = max(1, height or term_height)
    if left_padding is None:
        left_padding = 4 if width >= 100 else 2
    left = " " * max(0, min(left_padding, max(0, width - 1)))
    themed = [themed_line(width=width) for _ in range(max(0, top_padding))]
    for line in lines:
        themed.append(themed_line(left + str(line), width))
    while len(themed) < height:
        themed.append(themed_line(width=width))
    return themed


def themed_screen_with_footer_lines(lines, footer_lines, width=None, height=None, top_padding=2, left_padding=None):
    term_width, term_height = terminal_size()
    width = max(1, width or term_width)
    height = max(1, height or term_height)
    footer_lines = [str(line) for line in (footer_lines or [])]
    if not footer_lines:
        return themed_screen_lines(lines, width, height, top_padding, left_padding)
    if left_padding is None:
        left_padding = 4 if width >= 100 else 2
    left = " " * max(0, min(left_padding, max(0, width - 1)))
    themed = [themed_line(width=width) for _ in range(max(0, top_padding))]
    footer_block = ["", *footer_lines]
    content_capacity = max(0, height - len(themed) - len(footer_block))
    for line in list(lines)[:content_capacity]:
        themed.append(themed_line(left + str(line), width))
    while len(themed) < height - len(footer_block):
        themed.append(themed_line(width=width))
    for line in footer_block:
        themed.append(themed_line(left + str(line), width))
    return themed[:height]


def _center_splash_line(text, width):
    pad = max(0, (width - visible_len(text)) // 2)
    return themed_line((" " * pad) + text, width)


def pilot_splash_lines(size=None):
    width, height = size or terminal_size()
    width = max(1, width)
    height = max(1, height)
    content = [
        f"{CLR_BOLD}{CLR_BRIGHT_RED}AI-MAN{CLR_RESET}",
        f"{CLR_WHITE}Profile control deck{CLR_RESET}",
        f"{CLR_DARK_RED}{'━' * min(32, width)}{CLR_RESET}",
        f"{CLR_BRIGHT_RED}AGY{CLR_RESET}{CLR_WHITE} · {CLR_RED}Codex{CLR_RESET}{CLR_WHITE} · {CLR_DARK_RED}Claude{CLR_RESET}",
        "",
        f"{CLR_BOLD}{CLR_BRIGHT_RED}Enter{CLR_RESET}{CLR_WHITE} to continue · {CLR_RED}q/Esc{CLR_RESET}{CLR_WHITE} to exit{CLR_RESET}",
    ]
    top_padding = max(1, (height - len(content)) // 3)
    lines = [themed_line(width=width) for _ in range(top_padding)]
    lines.extend(_center_splash_line(line, width) if line else themed_line(width=width) for line in content)
    while len(lines) < height:
        lines.append(themed_line(width=width))
    return lines[:height]


def render_menu_lines(options, title="", selected_idx=0, pre_lines=None, post_lines=None, footer_lines=None):
    lines = header_lines(title)
    lines.append("")
    if pre_lines:
        lines.extend(str(line) for line in pre_lines)
    for idx, option in enumerate(options):
        if idx == selected_idx:
            lines.append(f"{CLR_BRIGHT_RED}▌{CLR_RESET} {CLR_BOLD}{CLR_WHITE}{option}{CLR_RESET}")
        else:
            lines.append(f"  \033[90m{option}{CLR_RESET}")
    if post_lines:
        lines.extend(str(line) for line in post_lines)
    if footer_lines is None:
        footer_lines = [
            (
                f"\033[90m↑/↓ move   digits/shortcuts   "
                f"{CLR_BRIGHT_RED}Enter{CLR_RESET}{CLR_BG_BLACK}\033[90m select   "
                f"{CLR_RED}Esc/q{CLR_RESET}{CLR_BG_BLACK}\033[90m back{CLR_RESET}"
            )
        ]
    if footer_lines:
        return themed_screen_with_footer_lines(lines, footer_lines)
    return themed_screen_lines(lines)


def quota_text(status, color=True, width=24, quota_fresh_seconds=600.0):
    summary = quota_summary(status)
    if summary == "unknown":
        summary = "retrying"
    text = summary or "quota pending"
    if len(text) > width:
        text = f"{text[:max(0, width - 3)]}..."
    return color_quota_text(text, status, quota_fresh_seconds) if color else text


def color_quota_text(text, status, quota_fresh_seconds=600.0):
    quota = status.get("quota") or {}
    state = quota.get("state")
    if state == "loading":
        return f"{CLR_YELLOW}{text}{CLR_RESET}"
    fetched_at = quota.get("fetched_at")
    if fetched_at is None:
        return f"{CLR_RED}{text}{CLR_RESET}" if state not in ("available", "loading") else text
    color = CLR_GREEN if time.time() - fetched_at <= quota_fresh_seconds else CLR_WHITE
    return f"{color}{text}{CLR_RESET}"


def agy_quota_cell_map(status):
    quota = status.get("quota") or {}
    if quota.get("state") != "available":
        return {}
    return dict(agy_quota_entries(quota))


def agy_status_quota_columns(statuses):
    columns = list(AGY_DEFAULT_QUOTA_COLUMNS)
    for status in statuses:
        for label in agy_quota_cell_map(status):
            if label not in columns:
                columns.append(label)
    return columns


def agy_quota_cells(status, columns):
    cells = agy_quota_cell_map(status)
    quota = status.get("quota") or {}
    job_state = quota.get("job_state") or status.get("job_state")
    if cells:
        return [cells.get(column, "") for column in columns]
    state = quota.get("state")
    marker = ""
    if state == "no_token":
        marker = ""
    elif job_state in QUOTA_ACTIVE_JOB_STATES or state in ("loading", "startup_pending", None):
        marker = "..."
    elif job_state in ("retryable", "failed") or state in (
        "unknown",
        "error",
        "timeout",
        "exception",
        "auth_required",
        "missing_cli",
        "empty_output",
        "parser_miss",
        "process_exit",
        "tty_unavailable",
        "account_ineligible",
        "resource_exhausted",
        "pty_failure",
        "resource_limited",
    ):
        marker = "!"
    return [marker if idx == 0 else "" for idx, _ in enumerate(columns)]


def quota_cell_percent(cell):
    match = re.search(r"(\d{1,3}(?:\.\d+)?)\s*%", str(cell))
    if not match:
        return None
    return float(match.group(1))


def agy_quota_fresh(status, quota_fresh_seconds=600.0):
    quota = status.get("quota") or {}
    fetched_at = quota.get("fetched_at")
    if fetched_at is None:
        return True
    return time.time() - fetched_at <= quota_fresh_seconds


def color_agy_quota_cell(cell, status, quota_fresh_seconds=600.0):
    if not cell:
        return cell
    if cell == "...":
        return f"{CLR_YELLOW}{cell}{CLR_RESET}"
    if cell == "!":
        return f"{CLR_RED}{cell}{CLR_RESET}"
    value = quota_cell_percent(cell)
    if value is None:
        return cell
    if not agy_quota_fresh(status, quota_fresh_seconds):
        return f"{CLR_WHITE}{cell}{CLR_RESET}"
    if value <= 20:
        color = CLR_RED
    elif value <= 40:
        color = CLR_YELLOW
    else:
        color = CLR_GREEN
    return f"{color}{cell}{CLR_RESET}"


def agy_quota_header_lines(columns, quota_width):
    column_groups = []
    used = set()
    for title, group_columns in AGY_QUOTA_COLUMN_GROUPS:
        present = [column for column in group_columns if column in columns]
        if not present:
            continue
        used.update(present)
        span_width = (quota_width * len(present)) + max(0, len(present) - 1)
        column_groups.append((title, span_width))
    other_columns = [column for column in columns if column not in used]
    if other_columns:
        span_width = (quota_width * len(other_columns)) + max(0, len(other_columns) - 1)
        column_groups.append(("Other", span_width))
    group_header = " ".join(visible_fit(title.center(width), width) for title, width in column_groups)
    column_header = " ".join(visible_fit(AGY_QUOTA_COLUMN_LABELS.get(column, column), quota_width) for column in columns)
    return group_header, column_header


def status_has_issue(status):
    email = str(status.get("email") or "")
    token_state = status.get("token_state")
    return (
        not status.get("has_token")
        or token_state in ("invalid", "missing", "error")
        or email.startswith("invalid token:")
    )


def status_profile_text(status):
    profile = f"p{status['num']}"
    if not status_has_issue(status):
        return profile
    return f"{CLR_RED}{profile}{CLR_RESET}"


def color_email_parts(value):
    text = str(value)
    match = re.fullmatch(r"([^@\s]+)(@[^@\s]+)", text)
    if not match:
        return text
    local, domain = match.groups()
    pieces = []
    for char in local:
        if char.isalpha():
            pieces.append(f"{CLR_CYAN}{char}{CLR_RESET}")
        elif char.isdigit():
            pieces.append(f"{CLR_YELLOW}{char}{CLR_RESET}")
        else:
            pieces.append(f"{CLR_WHITE}{char}{CLR_RESET}")
    pieces.append(f"{CLR_MAGENTA}{domain}{CLR_RESET}")
    return "".join(pieces)


def normalized_launch_statuses(statuses):
    normalized = []
    for status in statuses:
        item = dict(status)
        if not item.get("has_token"):
            item.setdefault("quota", {"state": "no_token", "limits": {}})
        elif "quota" not in item:
            item["quota"] = {"state": "startup_pending", "limits": {}}
        normalized.append(item)
    return normalized


def launch_account_table(tool_key, statuses, quota_fresh_seconds=600.0):
    statuses = normalized_launch_statuses(statuses)
    if tool_key == "agy":
        quota_columns = agy_status_quota_columns(statuses)
        widths = {
            "profile": 6,
            "account": 30,
            "status": 10,
            "quota": 6,
            "label": 14,
        }
        quota_header = agy_quota_header_lines(quota_columns, widths["quota"])
        major_gap = "  "
        quota_gap = " "
        total_width = widths["profile"] + widths["account"] + widths["status"] + widths["label"]
        total_width += (widths["quota"] * len(quota_columns)) + (len(quota_columns) - 1)
        total_width += len(major_gap) * 4
    else:
        quota_columns = []
        major_gap = "  "
        quota_gap = " "
        widths = {
            "profile": 6,
            "account": 30,
            "status": 10,
            "quota": 28,
            "label": 14,
        }
        quota_header = f"{'Quota':<{widths['quota']}}"
        total_width = sum(widths.values()) + len(major_gap) * 4

    prefix = "      "
    row_prefix = "    "
    if isinstance(quota_header, tuple):
        quota_group_header, quota_column_header = quota_header
        headers = [
            (
                f"{prefix}{CLR_BOLD}{CLR_WHITE}"
                f"{'Profile':<{widths['profile']}}{major_gap}"
                f"{'Account':<{widths['account']}}{major_gap}"
                f"{'Status':<{widths['status']}}{major_gap}"
                f"{quota_group_header}{major_gap}"
                f"{'Label':<{widths['label']}}"
                f"{CLR_RESET}"
            ),
            (
                f"{prefix}{CLR_BOLD}{CLR_WHITE}"
                f"{'':<{widths['profile']}}{major_gap}"
                f"{'':<{widths['account']}}{major_gap}"
                f"{'':<{widths['status']}}{major_gap}"
                f"{quota_column_header}{major_gap}"
                f"{'':<{widths['label']}}"
                f"{CLR_RESET}"
            ),
        ]
    else:
        headers = [
            (
                f"{prefix}{CLR_BOLD}{CLR_WHITE}"
                f"{'Profile':<{widths['profile']}}{major_gap}"
                f"{'Account':<{widths['account']}}{major_gap}"
                f"{'Status':<{widths['status']}}{major_gap}"
                f"{quota_header}{major_gap}"
                f"{'Label':<{widths['label']}}"
                f"{CLR_RESET}"
            )
        ]
    separator = f"{prefix}{'-' * total_width}"
    rows = []
    for status in statuses:
        label_text = f"({status['label']})" if status.get("label") else ""
        state_text = f"{CLR_GREEN}Active{CLR_RESET}" if status.get("has_token") else f"{CLR_RED}No Token{CLR_RESET}"
        display_account = status.get("email", "")
        quota_account = (status.get("quota") or {}).get("account")
        if quota_account and (tool_key == "agy" or display_account in ("logged in", "(no login)")):
            display_account = quota_account
        account = color_email_parts(display_account) if status.get("has_token") else f"{CLR_RED}{display_account}{CLR_RESET}"
        if tool_key == "agy":
            quota_text_value = quota_gap.join(
                visible_fit(color_agy_quota_cell(cell, status, quota_fresh_seconds), widths["quota"])
                for cell in agy_quota_cells(status, quota_columns)
            )
        else:
            quota_text_value = visible_fit(quota_text(status, width=widths["quota"], quota_fresh_seconds=quota_fresh_seconds), widths["quota"])
        profile_text = status_profile_text(status)
        label = f"{CLR_YELLOW}{label_text}{CLR_RESET}" if label_text else ""
        rows.append(
            f"{row_prefix}"
            f"{visible_fit(profile_text, widths['profile'])}{major_gap}"
            f"{visible_fit(account, widths['account'])}{major_gap}"
            f"{visible_fit(state_text, widths['status'])}{major_gap}"
            f"{quota_text_value}{major_gap}"
            f"{visible_fit(label, widths['label'])}"
        )
    return headers + [separator], rows
