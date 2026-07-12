import os
import shutil
from dataclasses import dataclass
from pathlib import Path

from .credentials.agy import (
    account_email_from_profile,
    build_windows_credential,
    decode_windows_credential,
    read_wsl_oauth,
)
from .credentials.common import write_json_atomic


DEFAULT_DIRS_TO_SYNC = ["agy-homes", "codex-homes", "claude-homes", ".config/cli-profile-manager"]
PROFILE_SYNC_FILES = {
    "agy-homes": (
        Path(".gemini") / "oauth_creds.json",
        Path(".gemini") / "google_accounts.json",
    ),
    "codex-homes": (Path("auth.json"),),
    "claude-homes": (Path(".credentials.json"),),
}
CONFIG_SYNC_FILES = {
    ".config/cli-profile-manager": (Path("profiles_metadata.json"),),
}
PRUNED_DIR_NAMES = {
    ".cache",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tempmediaStorage",
    ".tox",
    ".venv",
    "__pycache__",
    "cache",
    "dist",
    "log",
    "logs",
    "node_modules",
    "site-packages",
    "venv",
}


@dataclass(frozen=True)
class SyncManifestEntry:
    rel_path: Path
    path: Path
    size: int
    mtime_ns: int
    entry_type: str = "file"

    def same_content_facts(self, other):
        return (
            other is not None
            and self.entry_type == other.entry_type
            and self.size == other.size
            and self.mtime_ns == other.mtime_ns
        )


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
        dirs[:] = [d for d in dirs if d not in PRUNED_DIR_NAMES]
        for file_name in files:
            paths.append(str(Path(root) / file_name))
        for dir_name in dirs:
            dir_path = Path(root) / dir_name
            if not any(dir_path.iterdir()):
                paths.append(str(dir_path))
    if not paths:
        paths.append(str(path))
    return sorted(paths)


def manifest_entry(path, rel_path):
    path = Path(path)
    stat = path.stat()
    return SyncManifestEntry(Path(rel_path), path, stat.st_size, stat.st_mtime_ns)


def build_sync_manifest(base, name):
    if name in PROFILE_SYNC_FILES:
        if not base.exists():
            return {}
        manifest = {}
        for profile_dir in base.iterdir():
            if not profile_dir.is_dir() or profile_number_from_dir_name(profile_dir.name) is None:
                continue
            for rel_file in PROFILE_SYNC_FILES[name]:
                candidate = profile_dir / rel_file
                if candidate.exists() and candidate.is_file() and not candidate.is_symlink():
                    rel_path = Path(profile_dir.name) / rel_file
                    manifest[rel_path] = manifest_entry(candidate, rel_path)
                elif candidate.is_symlink():
                    rel_path = Path(profile_dir.name) / rel_file
                    manifest[rel_path] = SyncManifestEntry(rel_path, candidate, 0, 0, "symlink")
        return dict(sorted(manifest.items()))
    if name in CONFIG_SYNC_FILES:
        manifest = {}
        for rel_file in CONFIG_SYNC_FILES[name]:
            candidate = base / rel_file
            if candidate.exists() and candidate.is_file() and not candidate.is_symlink():
                manifest[rel_file] = manifest_entry(candidate, rel_file)
            elif candidate.is_symlink():
                manifest[rel_file] = SyncManifestEntry(rel_file, candidate, 0, 0, "symlink")
        return dict(sorted(manifest.items()))
    return build_sync_manifest_by_walk(base)


def build_sync_manifest_by_walk(base):
    if not base.exists():
        return {}
    manifest = {}
    for root, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if d not in PRUNED_DIR_NAMES]
        rel_root = Path(root).relative_to(base)
        for file_name in files:
            path = Path(root) / file_name
            rel_path = rel_root / file_name
            if path.is_symlink():
                manifest[rel_path] = SyncManifestEntry(rel_path, path, 0, 0, "symlink")
            elif path.is_file():
                manifest[rel_path] = manifest_entry(path, rel_path)
    return dict(sorted(manifest.items()))


def sync_file_rel_paths(base, name):
    return sorted(build_sync_manifest(base, name))


def sync_file_rel_paths_by_walk(base):
    return sorted(build_sync_manifest_by_walk(base))


def managed_destination_manifest(base, name):
    return build_sync_manifest(base, name)


def managed_destination_rel_paths(base, name):
    return sorted(managed_destination_manifest(base, name))


def remove_empty_parents(path, stop_at):
    stop_at = stop_at.resolve()
    current = path.parent
    while current != stop_at and path_is_within(current, stop_at):
        try:
            current.rmdir()
        except OSError:
            return
        current = current.parent


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
                account = account_email_from_profile(str(profile_dir))
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
        src_manifest = build_sync_manifest(src, name)
        dst_manifest = managed_destination_manifest(dst, name) if dst.exists() else {}
        if hard_mode and dst.exists():
            src_rel_set = set(src_manifest)
            for rel_path in sorted(set(dst_manifest) - src_rel_set):
                dst_file = dst / rel_path
                delete_paths.append(str(dst_file))
                if not dry_run:
                    try:
                        dst_file.unlink()
                    except FileNotFoundError:
                        pass
                    remove_empty_parents(dst_file, dst)
        if not dry_run and src_manifest:
            dst.mkdir(parents=True, exist_ok=True)
        for rel_path, src_entry in src_manifest.items():
            src_file = src_entry.path
            file_name = src_file.name
            if direction == "windows" and name == "agy-homes" and is_windows_agy_backup_name(file_name):
                skipped += 1
                skipped_items.append({"source": str(src_file), "reason": "windows-agy-backup-converted"})
                continue
            if src_file.is_symlink():
                skipped += 1
                skipped_items.append({"source": str(src_file), "reason": "symlink"})
                continue
            dst_file = dst / rel_path
            dst_entry = dst_manifest.get(rel_path)
            should_copy = (
                dst_entry is None
                or dst_entry.entry_type != "file"
                or (
                    not src_entry.same_content_facts(dst_entry)
                    if hard_mode
                    else src_entry.size != dst_entry.size or src_entry.mtime_ns > dst_entry.mtime_ns
                )
            )
            if should_copy:
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
        "sync_roots": {
            "source": {
                "platform": direction,
                "base": str(src_base),
            },
            "destination": {
                "platform": "windows" if direction == "wsl" else "wsl",
                "base": str(dst_base),
            },
            "dirs": list(dirs_to_sync),
        },
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
