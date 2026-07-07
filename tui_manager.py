#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import base64
import shutil
import subprocess
from datetime import datetime

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DataTable, Static, Button, Select, Label, Input, Log, RichLog
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen, ModalScreen
from textual import work
from rich.text import Text
from rich.json import JSON as RichJSON

# Import core logic
sys.path.append(os.path.dirname(__file__))
import profile_manager as pm

class ToolSelect(Horizontal):
    def compose(self) -> ComposeResult:
        yield Label("Tool: ", id="tool-select-label")
        yield Select(
            [("Antigravity CLI (agy)", "agy"), ("OpenAI Codex CLI", "codex"), ("Anthropic Claude CLI", "claude")],
            value="agy",
            id="tool-select"
        )

class MainScreen(Screen):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.selected_rows = set()
        self.search_query = ""
        self.last_profile_count = 0

    def compose(self) -> ComposeResult:
        yield Header()
        
        with Horizontal(id="top-bar"):
            yield ToolSelect()
            yield Input(placeholder="Search by email or label...", id="search-input")
            
        with Horizontal(id="main-area"):
            yield DataTable(id="profile-table")
        
        with Horizontal(id="action-bar"):
            yield Button("Launch", id="btn-launch", variant="success")
            yield Button("Details", id="btn-details", variant="warning")
            yield Button("Add New", id="btn-add", variant="primary")
            yield Button("Set Label", id="btn-label")
            yield Button("Magic Import", id="btn-magic")
            yield Button("Export Selected", id="btn-export")
            yield Button("Clear Selected", id="btn-clear", variant="error")
            
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True
        table.add_columns("[ ]", "Profile", "Active Account", "Status", "Label")
        
        self.refresh_table()
        # Live Refresh every 3 seconds
        self.set_interval(3.0, self.live_refresh)

    def live_refresh(self):
        # Do not refresh if any modal is active
        if len(self.app.screen_stack) > 1:
            return
        self.refresh_table(preserve_cursor=True)

    def refresh_table(self, preserve_cursor=False):
        table = self.query_one(DataTable)
        tool_key = self.query_one("#tool-select", Select).value
        
        # Save cursor
        try:
            old_coord = table.cursor_coordinate
            old_row_key = table.coordinate_to_cell_key(old_coord).row_key.value if old_coord else None
        except Exception:
            old_coord = None
            old_row_key = None
            
        table.clear()
        
        metadata = pm.load_metadata()
        profiles = pm.get_profiles(tool_key)
        
        for n in profiles:
            st = pm.get_profile_status(tool_key, n, metadata)
            
            # Search Filter
            search_str = f"{st['email']} {st['label']}".lower()
            if self.search_query and self.search_query not in search_str:
                continue
                
            p_name = f"p{n}"
            email = st["email"]
            
            if st["has_token"]:
                status_txt = Text("Active", style="bold green")
                email_txt = Text(email, style="cyan")
            else:
                status_txt = Text("No Token", style="bold red")
                email_txt = Text(email, style="dim")
                
            label_txt = Text(st["label"], style="yellow") if st["label"] else ""
            
            # Checkbox logic
            checked = "[X]" if n in self.selected_rows else "[ ]"
            check_txt = Text(checked, style="bold magenta" if n in self.selected_rows else "dim")
            
            table.add_row(check_txt, p_name, email_txt, status_txt, label_txt, key=str(n))
            
        if preserve_cursor and old_row_key:
            # Try to restore cursor
            for r in range(table.row_count):
                if table.get_row_at(r)[1] == f"p{old_row_key}":
                    table.move_cursor(row=r)
                    break

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "tool-select":
            self.selected_rows.clear()
            self.refresh_table()
            
    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "search-input":
            self.search_query = event.value.lower()
            self.refresh_table()

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        pass

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        # Toggle selection on Enter or Click
        row_key = int(event.row_key.value)
        if row_key in self.selected_rows:
            self.selected_rows.remove(row_key)
        else:
            self.selected_rows.add(row_key)
        self.refresh_table(preserve_cursor=True)

    def get_token_data(self, tool_key, profile_num):
        tool = pm.TOOLS[tool_key]
        meta = pm.load_metadata()
        st = pm.get_profile_status(tool_key, profile_num, meta)
        cred_path = os.path.join(st["home"], tool["cred_file"])
        
        if not os.path.exists(cred_path):
            return None
            
        try:
            with open(cred_path, "r") as f:
                data = json.load(f)
            return data
        except:
            pass
        return None

    def get_profile_details_text(self, tool_key, p_num):
        tool = pm.TOOLS[tool_key]
        
        meta = pm.load_metadata()
        st = pm.get_profile_status(tool_key, p_num, meta)
        
        info = f"[b]📁 PATH[/b]\n[dim]{st['home']}[/dim]\n\n"
        
        token_data = self.get_token_data(tool_key, p_num)
        if not token_data:
            info += "[red]No valid token file found.[/red]"
            return info
            
        auth_lines = []
        config_lines = []
        stats_lines = []

        if tool_key == "agy":
            auth_lines.append("[cyan]Provider:[/cyan] Google OAuth")
            exp = token_data.get("token", {}).get("expiry")
            if exp:
                try:
                    dt = exp.split('.')[0].replace('T', ' ')
                    auth_lines.append(f"[cyan]Expires:[/cyan] {dt}")
                except:
                    pass
                
            agy_dir = os.path.dirname(os.path.join(st["home"], tool["cred_file"]))
            
            settings_path = os.path.join(agy_dir, "settings.json")
            if os.path.exists(settings_path):
                try:
                    with open(settings_path, "r") as f: sett = json.load(f)
                    config_lines.append(f"[yellow]Model:[/yellow] {sett.get('model', 'Default')}")
                    config_lines.append(f"[yellow]Telemetry:[/yellow] {'Enabled' if sett.get('enableTelemetry') else 'Disabled'}")
                    config_lines.append(f"[yellow]Workspaces:[/yellow] {len(sett.get('trustedWorkspaces', []))}")
                except: pass
                    
            mcp_dir = os.path.join(agy_dir, "mcp")
            if os.path.exists(mcp_dir):
                try:
                    mcp_list = [d for d in os.listdir(mcp_dir) if os.path.isdir(os.path.join(mcp_dir, d))]
                    if mcp_list: stats_lines.append(f"[magenta]MCP Servers:[/magenta] {', '.join(mcp_list)}")
                except: pass
                    
            brain_dir = os.path.join(agy_dir, "brain")
            if os.path.exists(brain_dir):
                try:
                    conv_count = len([d for d in os.listdir(brain_dir) if os.path.isdir(os.path.join(brain_dir, d))])
                    stats_lines.append(f"[magenta]Conversations:[/magenta] {conv_count}")
                except: pass
            
            history_path = os.path.join(agy_dir, "history.jsonl")
            if os.path.exists(history_path):
                try:
                    stats_lines.append(f"[magenta]History Size:[/magenta] {os.path.getsize(history_path) / 1024:.1f} KB")
                    dt = datetime.fromtimestamp(os.path.getmtime(history_path)).strftime('%Y-%m-%d %H:%M')
                    stats_lines.append(f"[magenta]Last Active:[/magenta] {dt}")
                except: pass
                    
        elif tool_key == "codex":
            codex_dir = st["home"]
            auth_mode = token_data.get("auth_mode", "unknown")
            if auth_mode.lower() == "oauth" or "tokens" in token_data:
                auth_lines.append("[cyan]Type:[/cyan] Auth0 JWT")
                acct_id = token_data.get("tokens", {}).get("account_id")
                if acct_id: auth_lines.append(f"[cyan]Account ID:[/cyan] {acct_id.split('-')[0]}...")
                
                idt = token_data.get("tokens", {}).get("id_token")
                if idt:
                    try:
                        payload_b64 = idt.split(".")[1]
                        payload_b64 += "=" * (4 - len(payload_b64) % 4)
                        payload = json.loads(base64.urlsafe_b64decode(payload_b64).decode("utf-8"))
                        if payload.get("exp"):
                            dt = datetime.fromtimestamp(payload.get("exp")).strftime('%Y-%m-%d %H:%M:%S')
                            auth_lines.append(f"[cyan]Expires:[/cyan] {dt}")
                    except: pass
            elif token_data.get("OPENAI_API_KEY"):
                auth_lines.append("[cyan]Type:[/cyan] API Key")
                
            config_path = os.path.join(codex_dir, "config.toml")
            if os.path.exists(config_path):
                import re
                try:
                    with open(config_path, "r") as f: config_content = f.read()
                    model_match = re.search(r'model\s*=\s*"([^"]+)"', config_content)
                    reason_match = re.search(r'model_reasoning_effort\s*=\s*"([^"]+)"', config_content)
                    sandbox_match = re.search(r'sandbox_mode\s*=\s*"([^"]+)"', config_content)
                    approval_match = re.search(r'approval_policy\s*=\s*"([^"]+)"', config_content)
                    
                    if model_match: config_lines.append(f"[yellow]Model:[/yellow] {model_match.group(1)}")
                    if reason_match: config_lines.append(f"[yellow]Reasoning:[/yellow] {reason_match.group(1)}")
                    if sandbox_match: config_lines.append(f"[yellow]Sandbox:[/yellow] {sandbox_match.group(1)}")
                    if approval_match: config_lines.append(f"[yellow]Approval:[/yellow] {approval_match.group(1)}")
                except: pass
            
            sessions_dir = os.path.join(codex_dir, "sessions")
            if os.path.exists(sessions_dir):
                try: stats_lines.append(f"[magenta]Sessions:[/magenta] {len(os.listdir(sessions_dir))}")
                except: pass
                    
            skills_dir = os.path.join(codex_dir, "skills")
            if os.path.exists(skills_dir):
                try:
                    skills_list = [d for d in os.listdir(skills_dir) if os.path.isdir(os.path.join(skills_dir, d))]
                    if skills_list: stats_lines.append(f"[magenta]Skills:[/magenta] {', '.join(skills_list)}")
                except: pass
                    
            rules_dir = os.path.join(codex_dir, "rules")
            if os.path.exists(rules_dir):
                try:
                    rules_list = [f for f in os.listdir(rules_dir) if f.endswith('.md')]
                    if rules_list: stats_lines.append(f"[magenta]Rules:[/magenta] {len(rules_list)}")
                except: pass
                    
            history_path = os.path.join(codex_dir, "history.jsonl")
            if os.path.exists(history_path):
                try:
                    stats_lines.append(f"[magenta]History Size:[/magenta] {os.path.getsize(history_path) / 1024:.1f} KB")
                    dt = datetime.fromtimestamp(os.path.getmtime(history_path)).strftime('%Y-%m-%d %H:%M')
                    stats_lines.append(f"[magenta]Last Active:[/magenta] {dt}")
                except: pass

        elif tool_key == "claude":
            claude_dir = st["home"]
            oauth = token_data.get("claudeAiOauth", {})
            
            auth_lines.append(f"[cyan]Tier:[/cyan] {oauth.get('rateLimitTier', 'N/A')}")
            auth_lines.append(f"[cyan]Sub:[/cyan] {oauth.get('subscriptionType', 'N/A')}")
            
            exp_ms = oauth.get("expiresAt")
            if exp_ms:
                try:
                    dt = datetime.fromtimestamp(exp_ms / 1000.0).strftime('%Y-%m-%d %H:%M:%S')
                    auth_lines.append(f"[cyan]Expires:[/cyan] {dt}")
                except: pass
                    
            scopes = oauth.get("scopes", [])
            if scopes:
                short_scopes = [s.replace('user:', '').replace('sessions:claude_code', 'sessions') for s in scopes]
                auth_lines.append(f"[cyan]Scopes:[/cyan] {', '.join(short_scopes)}")
                
            settings_path = os.path.join(claude_dir, "settings.json")
            if os.path.exists(settings_path):
                try:
                    with open(settings_path, "r") as f: sett = json.load(f)
                    skip_danger = sett.get("skipDangerousModePermissionPrompt", False)
                    config_lines.append(f"[yellow]Auto-Approve:[/yellow] {'Yes' if skip_danger else 'No'}")
                    config_lines.append(f"[yellow]Theme:[/yellow] {sett.get('theme', 'Default')}")
                except: pass
                    
            claude_json_path = os.path.join(claude_dir, ".claude.json")
            if os.path.exists(claude_json_path):
                try:
                    with open(claude_json_path, "r") as f: cjson = json.load(f)
                    stats_lines.append(f"[magenta]Startups (Runs):[/magenta] {cjson.get('numStartups', 0)}")
                    stats_lines.append(f"[magenta]Tracked Projects:[/magenta] {len(cjson.get('projects', {}).keys())}")
                except: pass
                    
            sessions_dir = os.path.join(claude_dir, "sessions")
            if os.path.exists(sessions_dir):
                try: stats_lines.append(f"[magenta]Sessions:[/magenta] {len(os.listdir(sessions_dir))}")
                except: pass
                    
            history_path = os.path.join(claude_dir, "history.jsonl")
            if os.path.exists(history_path):
                try:
                    stats_lines.append(f"[magenta]History Size:[/magenta] {os.path.getsize(history_path) / 1024:.1f} KB")
                    dt = datetime.fromtimestamp(os.path.getmtime(history_path)).strftime('%Y-%m-%d %H:%M')
                    stats_lines.append(f"[magenta]Last Active:[/magenta] {dt}")
                except: pass

        if auth_lines:
            info += "[b]🔑 AUTHENTICATION[/b]\n" + "\n".join(auth_lines) + "\n\n"
        if config_lines:
            info += "[b]⚙️ CONFIGURATION[/b]\n" + "\n".join(config_lines) + "\n\n"
        if stats_lines:
            info += "[b]📈 STATISTICS[/b]\n" + "\n".join(stats_lines) + "\n"

        return info.strip()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        tool_key = self.query_one("#tool-select", Select).value
        table = self.query_one(DataTable)
        
        try:
            row_key = int(table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value)
        except Exception:
            row_key = None

        if button_id == "btn-launch" and row_key:
            await self.launch_profile(tool_key, row_key)
        elif button_id == "btn-add":
            await self.add_profile(tool_key)
        elif button_id == "btn-label" and row_key:
            self.app.push_screen(LabelModal(tool_key, row_key), self.handle_modal_result)
        elif button_id == "btn-clear":
            targets = list(self.selected_rows) if self.selected_rows else ([row_key] if row_key else [])
            if targets:
                self.app.push_screen(ConfirmClearModal(tool_key, targets), self.handle_modal_result)
        elif button_id == "btn-magic":
            self.app.push_screen(MagicImportModal(tool_key), self.handle_modal_result)
        elif button_id == "btn-export":
            targets = list(self.selected_rows) if self.selected_rows else ([row_key] if row_key else [])
            if targets:
                self.app.push_screen(ExportModal(tool_key, targets))
        elif button_id == "btn-details" and row_key:
            self.app.push_screen(ProfileDetailsModal(tool_key, row_key, self))
            
    def handle_modal_result(self, result):
        if result:
            self.selected_rows.clear()
            self.refresh_table()

    async def launch_profile(self, tool_key, profile_num):
        tool = pm.TOOLS[tool_key]
        profile_home = os.path.join(tool["base_dir"], f"p{profile_num}")
        os.makedirs(profile_home, exist_ok=True)
        
        env = os.environ.copy()
        env[tool["env_var"]] = profile_home
        if tool_key == "agy":
            env["HOME"] = profile_home
            
        with self.app.suspend():
            print(f"\n\033[1;36mLAUNCHING {tool['name']} (Profile p{profile_num})\033[0m\n")
            try:
                subprocess.run([tool["cmd"]], env=env)
            except Exception as e:
                print(f"Error launching: {e}")
            print("\nPress Enter to return to TUI...")
            input()
            
    async def add_profile(self, tool_key):
        tool = pm.TOOLS[tool_key]
        profiles = pm.get_profiles(tool_key)
        next_p = (profiles[-1] if profiles else 0) + 1
        profile_home = os.path.join(tool["base_dir"], f"p{next_p}")
        os.makedirs(os.path.join(profile_home, os.path.dirname(tool["cred_file"])), exist_ok=True)
        
        env = os.environ.copy()
        env[tool["env_var"]] = profile_home
        if tool_key == "agy":
            env["HOME"] = profile_home
            
        with self.app.suspend():
            print(f"\n\033[1;36mADD NEW PROFILE: p{next_p} ({tool['cmd']})\033[0m")
            print("Please complete the browser authentication. Exit the tool when done.\n")
            try:
                subprocess.run([tool["cmd"]], env=env)
            except Exception as e:
                print(f"Error launching: {e}")
            print("\nPress Enter to return to TUI...")
            input()
        self.refresh_table()


class LabelModal(ModalScreen[bool]):
    def __init__(self, tool_key, profile_num, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tool_key = tool_key
        self.profile_num = profile_num

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label(f"Set label for p{self.profile_num}:")
            yield Input(id="label-input", placeholder="Enter label (empty to clear)")
            with Horizontal():
                yield Button("Save", variant="success", id="save")
                yield Button("Cancel", variant="error", id="cancel")

    def on_mount(self):
        meta = pm.load_metadata()
        current = meta.get(self.tool_key, {}).get(f"p{self.profile_num}", {}).get("label", "")
        self.query_one(Input).value = current
        self.query_one(Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            val = self.query_one(Input).value.strip()
            meta = pm.load_metadata()
            if self.tool_key not in meta: meta[self.tool_key] = {}
            if f"p{self.profile_num}" not in meta[self.tool_key]: meta[self.tool_key][f"p{self.profile_num}"] = {}
            meta[self.tool_key][f"p{self.profile_num}"]["label"] = val
            pm.save_metadata(meta)
            self.dismiss(True)
        else:
            self.dismiss(False)


class ConfirmClearModal(ModalScreen[bool]):
    def __init__(self, tool_key, profile_nums, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tool_key = tool_key
        self.profile_nums = profile_nums

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label(f"Are you sure you want to completely clear and delete {len(self.profile_nums)} profile(s)?", id="warn-lbl")
            with Horizontal():
                yield Button("Yes, Delete", variant="error", id="delete")
                yield Button("Cancel", variant="primary", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "delete":
            tool = pm.TOOLS[self.tool_key]
            for p in self.profile_nums:
                profile_home = os.path.join(tool["base_dir"], f"p{p}")
                shutil.rmtree(profile_home, ignore_errors=True)
            self.dismiss(True)
        else:
            self.dismiss(False)


class MagicImportModal(ModalScreen[bool]):
    def __init__(self, tool_key, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tool_key = tool_key
        self.found_files = []

    def compose(self) -> ComposeResult:
        with Vertical(id="magic-dialog"):
            yield Label("Scanning Windows Drives...", id="scan-lbl")
            yield Select([], id="file-select")
            yield Label("Target Profile Number:")
            yield Input(id="profile-num-input")
            with Horizontal():
                yield Button("Import", variant="success", id="import")
                yield Button("Cancel", variant="error", id="cancel")

    def on_mount(self):
        win_user = pm.find_windows_user()
        if self.tool_key == "agy":
            pattern = f"/mnt/c/Users/{win_user}/agy-homes/cred-*.json"
        elif self.tool_key == "codex":
            pattern = f"/mnt/c/Users/{win_user}/codex-homes/p*/auth.json"
        elif self.tool_key == "claude":
            pattern = f"/mnt/c/Users/{win_user}/claude-homes/p*/.credentials.json"
            
        import glob
        self.found_files = glob.glob(pattern)
        sel = self.query_one("#file-select", Select)
        
        if not self.found_files:
            self.query_one("#scan-lbl", Label).update(f"No credentials found for user {win_user}.")
            self.query_one("#import", Button).disabled = True
        else:
            self.query_one("#scan-lbl", Label).update(f"Found credentials for {win_user}:")
            sel.set_options([(os.path.basename(f), f) for f in self.found_files])
            sel.value = self.found_files[0]
            
            profiles = pm.get_profiles(self.tool_key)
            next_p = (profiles[-1] if profiles else 0) + 1
            self.query_one(Input).value = str(next_p)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "import":
            cred_file = self.query_one("#file-select", Select).value
            try:
                target_p = int(self.query_one(Input).value)
            except:
                self.app.notify("Invalid profile number!", severity="error")
                return
                
            tool = pm.TOOLS[self.tool_key]
            wsl_dest_dir = os.path.join(tool["base_dir"], f"p{target_p}")
            wsl_dest_file = os.path.join(wsl_dest_dir, tool["cred_file"])
            os.makedirs(os.path.dirname(wsl_dest_file), exist_ok=True)
            
            try:
                if self.tool_key == "agy":
                    with open(cred_file, "r", encoding="utf-8-sig") as f: data = json.load(f)
                    blob_data = base64.b64decode(data["BlobBase64"]).decode("utf-8")
                    with open(wsl_dest_file, "w") as f: f.write(blob_data)
                    email = data.get("Account")
                    if email:
                        acct_file_path = os.path.join(wsl_dest_dir, tool["acct_file"])
                        os.makedirs(os.path.dirname(acct_file_path), exist_ok=True)
                        with open(acct_file_path, "w") as f: json.dump({"active": email}, f, indent=2)
                else:
                    shutil.copy(cred_file, wsl_dest_file)
                self.app.notify("Imported successfully!", severity="info")
                self.dismiss(True)
            except Exception as e:
                self.app.notify(f"Import error: {e}", severity="error")
        else:
            self.dismiss(False)


class ExportModal(ModalScreen[None]):
    def __init__(self, tool_key, profile_nums, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tool_key = tool_key
        self.profile_nums = profile_nums

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label(f"Exporting {len(self.profile_nums)} profile(s) to Windows...", id="exp-lbl")
            yield Button("Close", variant="primary", id="close")

    def on_mount(self):
        tool = pm.TOOLS[self.tool_key]
        meta = pm.load_metadata()
        
        win_user = pm.find_windows_user()
        export_dir = f"/mnt/c/Users/{win_user}/Downloads"
        if not os.path.exists(export_dir): export_dir = f"/mnt/c/Users/{win_user}/Desktop"
        if not os.path.exists(export_dir): export_dir = "/mnt/c/"
        
        results = []
        for p in self.profile_nums:
            st = pm.get_profile_status(self.tool_key, p, meta)
            cred_path = os.path.join(st["home"], tool["cred_file"])
            if not os.path.exists(cred_path):
                results.append(f"p{p}: No Token")
                continue
                
            try:
                if self.tool_key == "agy":
                    with open(cred_path, "r") as f: token_data = f.read()
                    b64 = base64.b64encode(token_data.encode("utf-8")).decode("utf-8")
                    win_json = {
                        "Target": "gemini:antigravity", "Type": 1, "Persist": 2, "Flags": 0,
                        "UserName": "antigravity", "Account": st["email"] if st["email"] != "logged in" else None,
                        "BlobBase64": b64, "SavedAt": datetime.now().isoformat()
                    }
                    dest_file = os.path.join(export_dir, f"cred-p{p}-exported.json")
                    with open(dest_file, "w") as f: json.dump(win_json, f, indent=2)
                else:
                    dest_file = os.path.join(export_dir, f"{self.tool_key}-p{p}-exported.json")
                    shutil.copy(cred_path, dest_file)
                results.append(f"p{p}: OK")
            except Exception as e:
                results.append(f"p{p}: Error")
                
        self.query_one("#exp-lbl", Label).update(f"Exported to {export_dir}:\n" + "\n".join(results))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(None)


class TokenInspectorModal(ModalScreen[None]):
    def __init__(self, profile_name, token_data, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.profile_name = profile_name
        self.token_data = token_data

    def compose(self) -> ComposeResult:
        with Vertical(id="inspector-dialog"):
            yield Label(f"Raw Token Inspector: {self.profile_name}", id="inspector-title")
            yield RichLog(id="json-log", highlight=True, markup=True)
            yield Button("Close", variant="primary", id="close")

    def on_mount(self):
        log = self.query_one("#json-log", RichLog)
        # Write syntax highlighted JSON
        log.write(RichJSON.from_data(self.token_data))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(None)


class ProfileDetailsModal(ModalScreen[None]):
    def __init__(self, tool_key, profile_num, main_screen, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tool_key = tool_key
        self.profile_num = profile_num
        self.main_screen = main_screen

    def compose(self) -> ComposeResult:
        with Vertical(id="details-dialog"):
            yield Label(f"Profile Details: p{self.profile_num}", id="details-title")
            yield Static(id="details-content")
            with Horizontal():
                yield Button("Inspect Raw Token", variant="warning", id="btn-inspect-token")
                yield Button("Close", variant="primary", id="close")

    def on_mount(self):
        content = self.query_one("#details-content", Static)
        info_text = self.main_screen.get_profile_details_text(self.tool_key, self.profile_num)
        content.update(info_text)
        
        # Disable inspect button if no token data
        token_data = self.main_screen.get_token_data(self.tool_key, self.profile_num)
        if not token_data:
            self.query_one("#btn-inspect-token", Button).disabled = True

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-inspect-token":
            token_data = self.main_screen.get_token_data(self.tool_key, self.profile_num)
            if token_data:
                self.app.push_screen(TokenInspectorModal(f"p{self.profile_num}", token_data))
        else:
            self.dismiss(None)


class AIManagerApp(App):
    TITLE = "AI Profile Manager"
    
    CSS = """
    #top-bar {
        height: 3;
        margin-bottom: 1;
    }
    #tool-select-label {
        padding: 1;
        text-style: bold;
    }
    ToolSelect {
        width: 40;
    }
    #search-input {
        width: 1fr;
        margin-left: 2;
    }
    #main-area {
        height: 1fr;
    }
    DataTable {
        width: 1fr;
        height: 1fr;
    }
    #action-bar {
        height: 3;
        margin-top: 1;
        dock: bottom;
        align: center middle;
    }
    Button {
        margin: 0 1;
    }
    #dialog, #magic-dialog {
        padding: 1 2;
        width: 60;
        height: auto;
        background: $surface;
        border: thick $primary;
    }
    #details-dialog {
        padding: 1 2;
        width: 70;
        height: 80%;
        background: $surface;
        border: thick $secondary;
    }
    #details-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    #details-content {
        height: 1fr;
        overflow-y: auto;
        margin-bottom: 1;
    }
    #inspector-dialog {
        padding: 1 2;
        width: 80;
        height: 80%;
        background: $surface;
        border: thick $secondary;
    }
    #inspector-title {
        text-style: bold;
        margin-bottom: 1;
    }
    #json-log {
        height: 1fr;
        border: solid $primary;
        margin-bottom: 1;
    }
    #warn-lbl {
        color: $error;
        text-style: bold;
        margin-bottom: 1;
    }
    #file-select {
        margin-bottom: 1;
    }
    """
    
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("l", "launch", "Launch"),
        ("d", "details", "Details"),
        ("a", "add", "Add"),
        ("s", "label", "Set Label"),
        ("m", "magic", "Magic Import"),
        ("e", "export", "Export Selected"),
        ("c", "clear", "Clear Selected")
    ]

    def action_launch(self) -> None:
        self.query_one("#btn-launch", Button).press()
    def action_details(self) -> None:
        self.query_one("#btn-details", Button).press()
    def action_add(self) -> None:
        self.query_one("#btn-add", Button).press()
    def action_label(self) -> None:
        self.query_one("#btn-label", Button).press()
    def action_magic(self) -> None:
        self.query_one("#btn-magic", Button).press()
    def action_export(self) -> None:
        self.query_one("#btn-export", Button).press()
    def action_clear(self) -> None:
        self.query_one("#btn-clear", Button).press()

    def on_mount(self) -> None:
        self.push_screen(MainScreen())

if __name__ == "__main__":
    app = AIManagerApp()
    app.run()
