RISK_READ_ONLY = "read_only"
RISK_LOW = "low_mutation"
RISK_CREDENTIAL = "credential_movement"
RISK_DESTRUCTIVE = "destructive"
RISK_EXTERNAL = "external_process"


POLICIES = {
    "clear": {
        "risk": RISK_DESTRUCTIVE,
        "requires_confirmation": True,
        "confirmation_flag": "--yes",
        "dry_run_supported": False,
        "summary": "delete one profile directory",
        "recovery": "restore the profile directory from backup or re-import credentials",
    },
    "sync-hard": {
        "risk": RISK_DESTRUCTIVE,
        "requires_confirmation": True,
        "confirmation_flag": "--yes",
        "dry_run_supported": True,
        "summary": "replace destination profile directories during hard sync",
        "recovery": "review dry-run delete_paths and restore destination files from backup if needed",
    },
    "sync-soft": {
        "risk": RISK_LOW,
        "requires_confirmation": False,
        "confirmation_flag": None,
        "dry_run_supported": True,
        "summary": "copy newer profile files without deleting destination directories",
        "recovery": "rerun sync in the opposite direction or restore overwritten files from backup",
    },
    "import": {
        "risk": RISK_CREDENTIAL,
        "requires_confirmation": False,
        "confirmation_flag": None,
        "dry_run_supported": True,
        "summary": "copy credential material into a managed profile",
        "recovery": "clear the affected profile or re-import the previous credential",
    },
    "export": {
        "risk": RISK_CREDENTIAL,
        "requires_confirmation": False,
        "confirmation_flag": None,
        "dry_run_supported": True,
        "summary": "copy credential material out of a managed profile",
        "recovery": "delete the exported credential file if it was written to the wrong location",
    },
    "label": {
        "risk": RISK_LOW,
        "requires_confirmation": False,
        "confirmation_flag": None,
        "dry_run_supported": False,
        "summary": "update profile metadata label",
        "recovery": "set the label again or clear it with an empty value",
    },
    "login": {
        "risk": RISK_EXTERNAL,
        "requires_confirmation": False,
        "confirmation_flag": None,
        "dry_run_supported": False,
        "summary": "launch native CLI login flow",
        "recovery": "close the native CLI session or clear the profile if credentials were changed",
    },
    "launch": {
        "risk": RISK_EXTERNAL,
        "requires_confirmation": False,
        "confirmation_flag": None,
        "dry_run_supported": True,
        "summary": "launch a native external CLI under a managed profile",
        "recovery": "exit the native CLI; no profile files are changed by the wrapper itself",
    },
    "audit-purge": {
        "risk": RISK_DESTRUCTIVE,
        "requires_confirmation": True,
        "confirmation_flag": "--yes",
        "dry_run_supported": False,
        "summary": "delete local audit events",
        "recovery": "audit events cannot be recovered unless backed up externally",
    },
    "audit-compact": {
        "risk": RISK_DESTRUCTIVE,
        "requires_confirmation": False,
        "confirmation_flag": None,
        "dry_run_supported": False,
        "summary": "delete audit events outside retention settings",
        "recovery": "audit events cannot be recovered unless backed up externally",
    },
    "service-start": {
        "risk": RISK_EXTERNAL,
        "requires_confirmation": False,
        "confirmation_flag": None,
        "dry_run_supported": False,
        "summary": "start a local runtime service process",
        "recovery": "stop the service with ai-man service stop",
    },
    "service-stop": {
        "risk": RISK_LOW,
        "requires_confirmation": False,
        "confirmation_flag": None,
        "dry_run_supported": False,
        "summary": "stop the local runtime service process",
        "recovery": "start the service again with ai-man service start",
    },
    "service-restart": {
        "risk": RISK_EXTERNAL,
        "requires_confirmation": False,
        "confirmation_flag": None,
        "dry_run_supported": False,
        "summary": "restart the local runtime service process",
        "recovery": "stop or start the service explicitly if restart fails",
    },
}


def command_inventory():
    return {name: dict(policy) for name, policy in sorted(POLICIES.items())}


def operation_descriptor(name, command=None, tool=None, profile=None, target=None, facts=None):
    if name not in POLICIES:
        raise ValueError(f"unknown sensitive operation: {name}")
    policy = POLICIES[name]
    return {
        "operation": name,
        "command": command or name.split("-", 1)[0],
        "risk": policy["risk"],
        "summary": policy["summary"],
        "tool": tool,
        "profile": profile,
        "target": target,
        "facts": facts or {},
        "recovery": policy["recovery"],
        "requires_confirmation": policy["requires_confirmation"],
        "confirmation_flag": policy["confirmation_flag"],
        "dry_run_supported": policy["dry_run_supported"],
    }


def evaluate(descriptor, yes=False, dry_run=False):
    requires_confirmation = bool(descriptor["requires_confirmation"] and not dry_run)
    confirmed = bool(yes) if requires_confirmation else True
    allowed = not requires_confirmation or confirmed
    result = "confirmed" if allowed and requires_confirmation else "not_required"
    if dry_run:
        result = "dry_run"
    if not allowed:
        result = "refused"
    return {
        "ok": allowed,
        "result": result,
        "dry_run": bool(dry_run),
        "confirmed": confirmed,
        "required_confirmation": requires_confirmation,
        "confirmation_flag": descriptor.get("confirmation_flag"),
        "preflight": descriptor,
        "message": refusal_message(descriptor) if not allowed else None,
    }


def refusal_message(descriptor):
    flag = descriptor.get("confirmation_flag") or "confirmation"
    if descriptor.get("dry_run_supported"):
        return f"refusing {descriptor['operation']} without {flag}; run with --dry-run first to inspect the preflight"
    return f"refusing {descriptor['operation']} without {flag}"


def payload(decision):
    return {
        "ok": decision["ok"],
        "result": decision["result"],
        "dry_run": decision["dry_run"],
        "confirmed": decision["confirmed"],
        "required_confirmation": decision["required_confirmation"],
        "confirmation_flag": decision["confirmation_flag"],
        "preflight": decision["preflight"],
        "message": decision["message"],
    }


def audit_decision(audit_module, decision):
    preflight = decision["preflight"]
    audit_module.record(
        "safety",
        "decision",
        command=preflight.get("command"),
        tool=preflight.get("tool"),
        profile=preflight.get("profile"),
        result=decision["result"],
        details=payload(decision),
    )
