"""Local credential storage for saved login profiles.

Passwords are base64-encoded (obfuscation, not encryption — this is a
single-user local tool; the data lives on the same machine as the MT5 terminal).

The JSON file is stored in the project root (one level above mt5_server/) so
it persists across updates that only replace mt5_server/ contents.

Structure of saved_logins.json:
{
  "ProfileName": { "login": 12345, "server": "...", "password": "<b64>" },
  ...
  "_ct": {
    "ProfileName": { "client_id": "...", "client_secret": "<b64>" },
    ...
  }
}
"""

import base64
import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Project root — survives updates
_DATA_FILE = Path(__file__).resolve().parent.parent / "saved_logins.json"


def _load_all() -> dict:
    try:
        if _DATA_FILE.exists():
            return json.loads(_DATA_FILE.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("Could not read saved_logins.json: %s", exc)
    return {}


def _persist(data: dict) -> None:
    try:
        _DATA_FILE.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception as exc:
        logger.error("Could not write saved_logins.json: %s", exc)


# ── MT5 profiles ──────────────────────────────────────────────────────────────

def list_logins() -> list:
    """Return saved MT5 logins without passwords (safe to send to browser)."""
    data = _load_all()
    return [
        {"name": name, "login": entry["login"], "server": entry["server"]}
        for name, entry in data.items()
        if not name.startswith("_")
    ]


def save_login(name: str, login: int, server: str, password: str) -> None:
    """Save or overwrite an MT5 login profile."""
    data = _load_all()
    data[name] = {
        "login": login,
        "server": server,
        "password": base64.b64encode(password.encode("utf-8")).decode("ascii"),
    }
    _persist(data)


def delete_login(name: str) -> bool:
    """Delete an MT5 login profile. Returns True if it existed."""
    data = _load_all()
    if name not in data:
        return False
    del data[name]
    _persist(data)
    return True


def get_login(name: str) -> Optional[dict]:
    """Return full credentials for a saved MT5 profile, including decoded password."""
    data = _load_all()
    entry = data.get(name)
    if not entry:
        return None
    try:
        password = base64.b64decode(entry["password"].encode("ascii")).decode("utf-8")
    except Exception:
        password = ""
    return {
        "login": entry["login"],
        "server": entry["server"],
        "password": password,
    }


# ── cTrader profiles ──────────────────────────────────────────────────────────

def _ct_section(data: dict) -> dict:
    if "_ct" not in data or not isinstance(data["_ct"], dict):
        data["_ct"] = {}
    return data["_ct"]


def list_ct_logins() -> list:
    """Return saved cTrader profiles without secrets (safe to send to browser)."""
    data = _load_all()
    ct = data.get("_ct", {})
    return [{"name": name, "client_id": entry["client_id"]} for name, entry in ct.items()]


def save_ct_login(name: str, client_id: str, client_secret: str) -> None:
    """Save or overwrite a cTrader profile."""
    data = _load_all()
    ct = _ct_section(data)
    ct[name] = {
        "client_id": client_id,
        "client_secret": base64.b64encode(client_secret.encode("utf-8")).decode("ascii"),
    }
    _persist(data)


def delete_ct_login(name: str) -> bool:
    """Delete a cTrader profile. Returns True if it existed."""
    data = _load_all()
    ct = data.get("_ct", {})
    if name not in ct:
        return False
    del ct[name]
    _persist(data)
    return True


def get_ct_login(name: str) -> Optional[dict]:
    """Return full credentials for a saved cTrader profile."""
    data = _load_all()
    ct = data.get("_ct", {})
    entry = ct.get(name)
    if not entry:
        return None
    try:
        client_secret = base64.b64decode(entry["client_secret"].encode("ascii")).decode("utf-8")
    except Exception:
        client_secret = ""
    return {
        "client_id": entry["client_id"],
        "client_secret": client_secret,
    }

        "password": password,
    }
