import json
import os


METADATA_DIR = os.path.expanduser(os.environ.get("AI_MAN_METADATA_DIR", "~/.config/cli-profile-manager"))
METADATA_PATH = os.path.join(METADATA_DIR, "profiles_metadata.json")


def refresh_from_env():
    global METADATA_DIR, METADATA_PATH
    METADATA_DIR = os.path.expanduser(os.environ.get("AI_MAN_METADATA_DIR", "~/.config/cli-profile-manager"))
    METADATA_PATH = os.path.join(METADATA_DIR, "profiles_metadata.json")


def load_metadata():
    if os.path.exists(METADATA_PATH):
        try:
            with open(METADATA_PATH, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_metadata(data):
    os.makedirs(METADATA_DIR, exist_ok=True)
    with open(METADATA_PATH, "w") as f:
        json.dump(data, f, indent=2)


def label_profile(tool_key, profile_num, label):
    metadata = load_metadata()
    metadata.setdefault(tool_key, {}).setdefault(f"p{profile_num}", {})["label"] = label
    save_metadata(metadata)
