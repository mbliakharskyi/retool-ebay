import os, time, base64
import httpx
from typing import List, Dict, Any, Tuple

EBAY_OAUTH_URL = "https://api.ebay.com/identity/v1/oauth2/token"
EBAY_BROWSE_SEARCH = "https://api.ebay.com/buy/browse/v1/item_summary/search"

# simple in-process cache for the OAuth token
_token_cache: Tuple[str, float] | None = None  # (access_token, expires_at_epoch)

def _basic_auth_header() -> str:
    cid = os.environ["EBAY_CLIENT_ID"]
    csec = os.environ["EBAY_CLIENT_SECRET"]
    raw = f"{cid}:{csec}".encode("utf-8")
    return base64.b64encode(raw).decode("ascii")

async def _get_app_token() -> str:
    """
    Client-credentials OAuth with base scope only:
    scope=https://api.ebay.com/oauth/api_scope
    """
    global _token_cache
    now = time.time()
    if _token_cache and now < _token_cache[1] - 60:  # 60s safety margin
        return _token_cache[0]

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {_basic_auth_header()}",
    }
    data = {
        "grant_type": "client_credentials",
        "scope": "https://api.ebay.com/oauth/api_scope",
    }
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(EBAY_OAUTH_URL, data=data, headers=headers)
        r.raise_for_status()
        j = r.json()
        token = j["access_token"]
        expires_at = now + int(j.get("expires_in", 7200))
        _token_cache = (token, expires_at)
        return token

async def search_ebay(title: str, limit: int = 20) -> List[Dict[str, Any]]:
    token = await _get_app_token()
    mp = os.getenv("EBAY_MARKETPLACE_ID", "EBAY_US")
    headers = {
        "Authorization": f"Bearer {token}",
        "X-EBAY-C-MARKETPLACE-ID": mp,
    }
    params = {"q": title, "limit": limit}
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(EBAY_BROWSE_SEARCH, headers=headers, params=params)
        r.raise_for_status()
        return r.json().get("itemSummaries", []) or []
