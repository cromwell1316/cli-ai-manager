import os
import shutil
from pathlib import Path

from .credentials.agy import (
    account_email_from_google_accounts,
    build_windows_credential,
    decode_windows_credential,
    read_wsl_oauth,
)
from .credentials.common import write_json_atomic


DEFAULT_DIRS_TO_SYNC = ["agy-homes", "codex-homes", "claude-homes", ".config/cli-profile-manager"]


def profile_number_from_dir_name(name):
    if name.startswith("p") and name[1:].isdigit():
        return int(name[1:])
    return None


def is_windows_agy_backup_name(name):
    return name.startswith("cred-p") and name.endswith(".json") and name[6:-5].isdigit()


def path_is_within(child, parent):
    child = Path(child).resolve()
    parent = Path(parent).resolve()
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def deletion_preflight_paths(path):
    if not path.exists():
        return []
    paths = []
    for root, dirs, files in os.walk(path):
        for file_name in files:
            paths.append(str(Path(root) / file_name))
        for dir_name in dirs:
            dir_path = Path(root) / dir_name
            if not any(dir_path.iterdir()):
                paths.append(str(dir_path))
    if not paths:
        paths.append(str(path))
    return sorted(paths)


def sync_agy_credentials_between_bases(src_base, dst_base, direction, dry_run=False):
    result = {"converted": 0, "invalid": 0, "items": []}
    src_agy = Path(src_base) / "agy-homes"
    dst_agy = Path(dst_base) / "agy-homes"
    if not src_agy.exists():
        return result

    if direction == "wsl":
        for profile_dir in src_agy.iterdir():
            if not profile_dir.is_dir():
                continue
            n = profile_number_from_dir_name(profile_dir.name)
            if n is None:
                continue
            token_path = profile_dir / ".gemini" / "oauth_creds.json"
            if not token_path.exists():
                continue
            dest = dst_agy / f"cred-p{n}.json"
            try:
                token_data = read_wsl_oauth(str(token_path))
                account = account_email_from_google_accounts(str(profile_dir))
            except Exception as e:
                result["invalid"] += 1
                result["items"].append({"source": str(token_path), "destination": str(dest), "status": "invalid", "error": str(e)})
                continue
            result["converted"] += 1
            result["items"].append({"source": str(token_path), "destination": str(dest), "status": "converted"})
            if not dry_run:
                write_json_atomic(str(dest), build_windows_credential(token_data, account))
    else:
        for cred_path in src_agy.glob("cred-p*.json"):
            stem = cred_path.stem
            num_text = stem[6:]
            if not num_text.isdigit():
                continue
            n = int(num_text)
            dest_profile = dst_agy / f"p{n}"
            dest = dest_profile / ".gemini" / "oauth_creds.json"
            try:
                token_data, account = decode_windows_credential(str(cred_path))
            except Exception as e:
                result["invalid"] += 1
                result["items"].append({"source": str(cred_path), "destination": str(dest), "status": "invalid", "error": str(e)})
                continue
            result["converted"] += 1
            result["items"].append({"source": str(cred_path), "destination": str(dest), "status": "converted"})
            if not dry_run:
                write_json_atomic(str(dest), token_data)
                if account:
                    write_json_atomic(str(dest_profile / ".gemini" / "google_accounts.json"), {"active": account})
    return result


def sync_profiles_between_bases(src_base, dst_base, direction, mode, dry_run=False, yes=False, dirs_to_sync=None):
    dirs_to_sync = dirs_to_sync or DEFAULT_DIRS_TO_SYNC
    hard_mode = mode == "hard"
    if hard_mode and not yes and not dry_run:
        raise PermissionError("hard sync requires --yes")
    src_base = Path(src_base)
    dst_base = Path(dst_base)
    if not src_base.exists():
        raise FileNotFoundError(f"source path not found: {src_base}")
    if not dst_base.exists():
        raise FileNotFoundError(f"destination path not found: {dst_base}")

    copied = 0
    skipped = 0
    delete_paths = []
    copied_items = []
    skipped_items = []
    for name in dirs_to_sync:
        src = src_base / name
        dst = dst_base / name
        if not src.exists():
            continue
        if not path_is_within(dst, dst_base):
            raise PermissionError(f"refusing to sync unsafe destination path: {dst}")
        if hard_mode and dst.exists():
            delete_paths.extend(deletion_preflight_paths(dst))
        if hard_mode and dst.exists() and not dry_run:
            shutil.rmtree(dst)
        if not dry_run:
            dst.mkdir(parents=True, exist_ok=True)
        for root, dirs, files in os.walk(src):
            dirs[:] = [d for d in dirs if d not in ("cache", "log", ".tempmediaStorage", ".venv", "node_modules")]
            rel_root = Path(root).relative_to(src)
            if not dry_run:
                (dst / rel_root).mkdir(parents=True, exist_ok=True)
            for file_name in files:
                src_file = Path(root) / file_name
                if direction == "windows" and name == "agy-homes" and is_windows_agy_backup_name(file_name):
                    skipped += 1
                    skipped_items.append({"source": str(src_file), "reason": "windows-agy-backup-converted"})
                    continue
                if src_file.is_symlink():
                    skipped += 1
                    skipped_items.append({"source": str(src_file), "reason": "symlink"})
                    continue
                dst_file = dst / rel_root / file_name
                if hard_mode or not dst_file.exists() or src_file.stat().st_mtime > dst_file.stat().st_mtime:
                    copied += 1
                    copied_items.append({"source": str(src_file), "destination": str(dst_file)})
                    if not dry_run:
                        dst_file.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src_file, dst_file)
                else:
                    skipped += 1
                    skipped_items.append({"source": str(src_file), "destination": str(dst_file), "reason": "up-to-date"})
    conversion = sync_agy_credentials_between_bases(src_base, dst_base, direction, dry_run)
    return {
        "ok": True,
        "direction": direction,
        "mode": mode,
        "dry_run": dry_run,
        "source_base": str(src_base),
        "destination_base": str(dst_base),
        "files": copied,
        "copied": copied,
        "skipped": skipped,
        "converted": conversion["converted"],
        "invalid": conversion["invalid"],
        "would_delete": len(delete_paths),
        "delete_paths": delete_paths,
        "copied_items": copied_items,
        "skipped_items": skipped_items,
        "conversion_items": conversion["items"],
    }
