# Unified CLI Profile Manager for WSL

A sleek, dependency-free Terminal User Interface (TUI) to manage, label, launch, and import multiple isolated accounts for **Antigravity CLI** (`agy`), **OpenAI Codex CLI** (`codex`), and **Anthropic Claude CLI** (`claude`) under WSL/Linux.

This project is written in pure Python using native terminal bindings (`termios`, `tty`) and ANSI escape sequences. It has **zero external dependencies** and works out of the box on any Linux/WSL distribution with Python 3 installed.

---

## 🚀 Key Features

* **Three-in-One CLI Support**: Manage isolated profiles for `agy`, `codex`, and `claude` all from a single unified menu.
* **Interactive Arrow-Key Selector**: Scroll through your profiles and launch the selected CLI under that account in one keystroke.
* **100% Profile Isolation**: Uses target environment variable overrides (`HOME`, `CODEX_HOME`, and `CLAUDE_CONFIG_DIR`) to keep profiles clean and isolated.
* **Label Management**: Attach custom nicknames to your profiles (e.g. `Work`, `Personal`, `Testing`) independently for each tool.
* **Credential Importers**: 
  * For `agy`: Imports Windows Credential Manager backups (`cred-pN.json`) and converts them to Linux tokens.
  * For `codex` / `claude`: Imports existing credentials files (`auth.json` or `.credentials.json`) by copying them directly to your WSL profiles.

---

## 🛠️ Installation

Run the installation script in the project directory to create the symlinks in your local bin:

```bash
chmod +x install.sh
./install.sh
```

Ensure `~/.local/bin` is in your shell `PATH` (it usually is by default in Ubuntu WSL). You can then run the manager from anywhere using either the long or short command:

```bash
ai-man
# or simply:
pman / profile-man
```

---

## 📖 Usage Guide

```
┌────────────────────────────────────────────────────────────┐
│                  UNIFIED PROFILE MANAGER                   │
└────────────────────────────────────────────────────────────┘

  -->  [1] Antigravity CLI (agy)
       [2] OpenAI Codex CLI
       [3] Anthropic Claude CLI
       [x] Exit
```

1. **Select a Tool**: Choose the CLI tool you want to manage.
2. **Launch Account**: Opens the list of profiles for that tool. Select one with the arrow keys and press `Enter` to run the tool. When you exit, you'll return straight to the manager.
3. **Add New Profile (OAuth)**: Triggers the standard login flow for that CLI tool.
4. **Import Windows Credential**: 
  * Provide the path to the backup file on Windows (e.g., `/mnt/c/Users/Oliver/agy-homes/cred-p1.json` or `C:\Users\Oliver\.claude\.credentials.json`), and the manager will import it into your WSL profile.
5. **Set Profile Label**: Give a profile a custom label (e.g., `Work`) for easy identification.
6. **Detailed Account Status**: Prints a clean grid of all profiles, active accounts, token existence, and labels.

---

## 📂 Project Structure

```
cli-profile-manager/
├── profile_manager.py  # Main Python TUI application
├── install.sh          # Installation & linking script
└── README.md           # This guide
```
