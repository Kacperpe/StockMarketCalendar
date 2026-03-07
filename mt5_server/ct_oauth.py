"""
cTrader Spotware OAuth2 helpers.

Flow:
  1. get_auth_url(client_id, redirect_uri)  →  send user to Spotware login page
  2. exchange_code(code, …)                 →  access_token + refresh_token
  3. list_accounts(access_token)            →  [{ctidTraderAccountId, brokerName, isLive, balance}]
"""

import logging
from typing import List, Optional, Tuple

import requests

logger = logging.getLogger(__name__)

SPOTWARE_AUTH_BASE  = "https://connect.spotware.com"
SPOTWARE_API_BASE   = "https://api.spotware.com"

# ── 1. Authorization URL ──────────────────────────────────────────────────────

def get_auth_url(client_id: str, redirect_uri: str) -> str:
    """Returns the URL to open in a browser so the user can authorize the app."""
    from urllib.parse import urlencode
    params = urlencode({
        "client_id":     client_id,
        "redirect_uri":  redirect_uri,
        "scope":         "trading",
        "response_type": "code",
    })
    return f"{SPOTWARE_AUTH_BASE}/apps/{client_id}/auth?{params}"


# ── 2. Code → Token ───────────────────────────────────────────────────────────

def exchange_code(
    code: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
) -> Tuple[Optional[str], Optional[str]]:
    """
    Exchanges authorization code for tokens.
    Returns (access_token, error_message).
    """
    try:
        resp = requests.post(
            f"{SPOTWARE_AUTH_BASE}/apps/token",
            data={
                "grant_type":    "authorization_code",
                "code":          code,
                "client_id":     client_id,
                "client_secret": client_secret,
                "redirect_uri":  redirect_uri,
            },
            timeout=10,
        )
        data = resp.json()
        if resp.status_code == 200 and "accessToken" in data:
            return data["accessToken"], None
        err = data.get("error_description") or data.get("error") or str(resp.status_code)
        return None, err
    except Exception as e:
        logger.error(f"CT token exchange error: {e}")
        return None, str(e)


# ── 3. Account list ───────────────────────────────────────────────────────────

def list_accounts(access_token: str) -> Tuple[Optional[List[dict]], Optional[str]]:
    """
    Returns (accounts, error).
    Each account dict: {id, broker, is_live, deposit_currency, balance}
    """
    try:
        resp = requests.get(
            f"{SPOTWARE_API_BASE}/connect/tradingaccounts",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        if resp.status_code != 200:
            return None, f"HTTP {resp.status_code}: {resp.text[:200]}"

        data = resp.json()
        accounts = []
        for acc in data.get("data", []):
            accounts.append({
                "id":               acc.get("ctidTraderAccountId"),
                "broker":           acc.get("brokerName", ""),
                "is_live":          acc.get("live", False),
                "deposit_currency": acc.get("depositCurrency", ""),
                "balance":          acc.get("balance", 0),
            })
        return accounts, None
    except Exception as e:
        logger.error(f"CT accounts list error: {e}")
        return None, str(e)
