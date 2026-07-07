import base64
import json

from .common import read_json_object


def account_from_auth(path):
    data = read_json_object(path)
    idt = data.get("tokens", {}).get("id_token")
    if idt:
        payload_b64 = idt.split(".")[1]
        payload_b64 += "=" * (4 - len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64).decode("utf-8"))
        return payload.get("email") or payload.get("https://api.openai.com/profile", {}).get("email") or "logged in"
    if data.get("OPENAI_API_KEY"):
        return "API Key"
    return "logged in"

