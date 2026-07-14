import re
import shutil
import sys


FRAME_BG_BLACK = "\033[48;5;0m"
FRAME_RESET = "\033[0m"
TERMINAL_BG_BLACK = "\033]11;#000000\007"
TERMINAL_BG_RESET = "\033]111\007"
AUTOWRAP_OFF = "\033[?7l"
AUTOWRAP_ON = "\033[?7h"


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


def terminal_size(fallback=(120, 24), stdout=None):
    stdout = sys.stdout if stdout is None else stdout
    try:
        return shutil.get_terminal_size(fallback)
    except OSError:
        return fallback


class TerminalFrameRenderer:
    def __init__(self, stdout=None, cache_key="default", size_provider=None):
        self.stdout = sys.stdout if stdout is None else stdout
        self.cache_key = cache_key
        self.size_provider = size_provider or terminal_size
        self.previous_lines = None
        self.previous_size = None
        self.cursor_hidden = False

    def is_tty(self):
        return bool(getattr(self.stdout, "isatty", lambda: False)())

    def current_size(self):
        try:
            return self.size_provider(stdout=self.stdout)
        except TypeError:
            return self.size_provider()

    def paint(self, lines, force=False):
        text_lines = [str(line) for line in lines]
        if not self.is_tty():
            self.stdout.write("\n".join(text_lines) + "\n")
            self.stdout.flush()
            self.previous_lines = text_lines
            return

        size = self.current_size()
        if not force and self.previous_lines == text_lines and self.previous_size == size:
            return
        resized = self.previous_size is not None and size != self.previous_size
        output = []
        output.append(TERMINAL_BG_BLACK)
        output.append(FRAME_BG_BLACK)
        output.append(AUTOWRAP_OFF)
        if not self.cursor_hidden:
            output.append("\033[?25l")
            self.cursor_hidden = True

        if force or resized or self.previous_lines is None:
            output.append("\033[H\033[J")
            for idx, line in enumerate(text_lines, start=1):
                output.append(f"\033[{idx};1H{line}\033[K")
        else:
            max_lines = max(len(self.previous_lines), len(text_lines))
            for idx in range(max_lines):
                new_line = text_lines[idx] if idx < len(text_lines) else ""
                old_line = self.previous_lines[idx] if idx < len(self.previous_lines) else None
                if new_line == old_line:
                    continue
                output.append(f"\033[{idx + 1};1H{new_line}\033[K")
            if len(text_lines) < len(self.previous_lines):
                output.append(f"\033[{len(text_lines) + 1};1H\033[J")

        self.previous_lines = text_lines
        self.previous_size = size
        self.stdout.write("".join(output))
        self.stdout.flush()

    def reset(self, clear_cache=True):
        if clear_cache:
            self.previous_lines = None
            self.previous_size = None
        if self.is_tty() and self.cursor_hidden:
            self.stdout.write(f"{AUTOWRAP_ON}{TERMINAL_BG_RESET}{FRAME_RESET}\033[?25h")
            self.stdout.flush()
        self.cursor_hidden = False

    def clear(self):
        if self.is_tty():
            self.stdout.write(f"{AUTOWRAP_ON}{TERMINAL_BG_BLACK}{FRAME_BG_BLACK}\033[H\033[J")
            self.stdout.flush()
        self.previous_lines = None
        self.previous_size = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.reset()
        return False
