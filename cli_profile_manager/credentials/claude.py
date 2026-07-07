from .common import read_json_object


def account_summary(path):
    data = read_json_object(path)
    oauth = data.get("claudeAiOauth", {})
    sub = oauth.get("subscriptionType")
    tier = oauth.get("rateLimitTier")
    if sub and tier:
        return f"Logged in ({sub}/{tier})"
    if sub:
        return f"Logged in ({sub})"
    return "Logged in"

