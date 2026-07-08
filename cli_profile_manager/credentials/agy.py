import base64
import json
import os
from datetime import datetime

from .common import read_json_object, write_json_atomic


WINDOWS_TARGET = "gemini:antigravity"
WINDOWS_USERNAME = "antigravity"
GOOGLE_ACCOUNTS_FILE = os.path.join(".gemini", "google_accounts.json")
WSL_OAUTH_FILE = os.path.join(".gemini", "oauth_creds.json")
AGY_CLI_TOKEN_FILE = os.path.join(".gemini", "antigravity-cli", "antigravity-oauth-token")


def account_email_from_google_accounts(profile_home, account_file=GOOGLE_ACCOUNTS_FILE):
    ga_path = os.path.join(profile_home, account_file)
    if not os.path.exists(ga_path):
        return None
    try:
        data = read_json_object(ga_path)
    except Exception:
        return None
    email = data.get("active")
    if isinstance(email, str) and email.strip():
        return email.strip().rstrip(",")
    return None


def decode_windows_credential(win_cred_path):
    data = read_json_object(win_cred_path, encoding="utf-8-sig")
    target = data.get("Target")
    if target and target != WINDOWS_TARGET:
        raise ValueError(f"unexpected Windows credential target: {target}")
    blob_b64 = data.get("BlobBase64")
    if not isinstance(blob_b64, str) or not blob_b64:
        raise ValueError("Windows credential is missing BlobBase64")
    try:
        token_text = base64.b64decode(blob_b64).decode("utf-8")
        token_data = json.loads(token_text)
    except Exception as e:
        raise ValueError(f"Windows credential BlobBase64 is not valid OAuth JSON: {e}") from e
    if not isinstance(token_data, dict):
        raise ValueError("Windows credential token payload must be a JSON object")
    account = data.get("Account")
    if isinstance(account, str):
        account = account.strip().rstrip(",") or None
    else:
        account = None
    return token_data, account


def read_wsl_oauth(token_path):
    return read_json_object(token_path)


def read_agy_cli_token(profile_home, token_file=AGY_CLI_TOKEN_FILE):
    token_path = os.path.join(profile_home, token_file)
    data = read_json_object(token_path)
    token = data.get("token")
    auth_method = data.get("auth_method")
    if not isinstance(token, str) or not token:
        raise ValueError("Antigravity CLI token is missing token")
    if auth_method is not None and not isinstance(auth_method, str):
        raise ValueError("Antigravity CLI token auth_method must be a string")
    return data


def build_windows_credential(token_data, account=None):
    token_text = json.dumps(token_data, indent=2)
    token_bytes = token_text.encode("utf-8")
    return {
        "Target": WINDOWS_TARGET,
        "Type": 1,
        "Persist": 2,
        "Flags": 0,
        "UserName": WINDOWS_USERNAME,
        "Account": account,
        "BlobBase64": base64.b64encode(token_bytes).decode("utf-8"),
        "BlobSize": len(token_bytes),
        "SavedAt": datetime.now().isoformat(),
    }


def import_windows_credential(win_cred_path, dest_home, dest_file, account_file=GOOGLE_ACCOUNTS_FILE):
    token_data, account = decode_windows_credential(win_cred_path)
    write_json_atomic(dest_file, token_data)
    if account:
        write_json_atomic(os.path.join(dest_home, account_file), {"active": account})
    return dest_file


def export_wsl_credential(token_path, profile_home, win_cred_path, account_file=GOOGLE_ACCOUNTS_FILE):
    token_data = read_wsl_oauth(token_path)
    account = account_email_from_google_accounts(profile_home, account_file)
    write_json_atomic(win_cred_path, build_windows_credential(token_data, account))
    return win_cred_path
