# app/ebay_client.py
import os, time, base64
from typing import List, Dict, Any, Tuple, Optional
import httpx
from dotenv import load_dotenv

load_dotenv()
# ----- Environment selection -----
EBAY_ENV = (os.getenv("EBAY_ENV", "PRODUCTION") or "PRODUCTION").upper()
IS_SANDBOX = EBAY_ENV == "SANDBOX"

EBAY_OAUTH_URL = (
    "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
    if IS_SANDBOX else
    "https://api.ebay.com/identity/v1/oauth2/token"
)

EBAY_BROWSE_SEARCH = (
    "https://api.sandbox.ebay.com/buy/browse/v1/item_summary/search"
    if IS_SANDBOX else
    "https://api.ebay.com/buy/browse/v1/item_summary/search"
)

DEFAULT_MARKETPLACE = os.getenv("EBAY_MARKETPLACE_ID", "EBAY_US")

# simple in-process cache for the OAuth token
_token_cache: Optional[Tuple[str, float]] = None  # (access_token, expires_at_epoch)

def _require_env(name: str) -> str:
    val = os.getenv(name)
    if not val:
        raise RuntimeError(
            f"Missing environment variable: {name}. "
            f"Set it in your .env or hosting environment."
        )
    return val

def _basic_auth_header() -> str:
    cid = _require_env("EBAY_CLIENT_ID")        # App ID (for current env)
    csec = _require_env("EBAY_CLIENT_SECRET")   # Cert ID (for current env)
    raw = f"{cid}:{csec}".encode("utf-8")
    return base64.b64encode(raw).decode("ascii")

async def _get_app_token() -> str:
    """
    Client-credentials OAuth with the base scope:
      scope=https://api.ebay.com/oauth/api_scope
    Works for both Sandbox and Production (URL changes by env).
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

    # small retry loop to be resilient to transient failures
    for attempt in range(2):
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                r = await client.post(EBAY_OAUTH_URL, data=data, headers=headers)
        except httpx.HTTPError as e:
            if attempt == 1:
                raise RuntimeError(f"EBAY OAUTH network error: {e}") from e
            await _sleep(0.5)
            continue

        if r.status_code >= 400:
            # Surface eBay's error text to logs for fast diagnosis
            raise RuntimeError(
                f"EBAY OAUTH {r.status_code}: {r.text} "
                f"(env={EBAY_ENV}, url={EBAY_OAUTH_URL})"
            )

        j = r.json()
        token = j["access_token"]
        expires_at = now + int(j.get("expires_in", 7200))
        _token_cache = (token, expires_at)
        return token

    # should never reach here
    raise RuntimeError("Failed to obtain eBay OAuth token after retries")

async def _sleep(seconds: float):
    # tiny helper to avoid importing asyncio at module top if you prefer
    import asyncio
    await asyncio.sleep(seconds)

async def search_ebay(title: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Search the Browse API for item summaries by title.
    Uses the marketplace header (default EBAY_US or env EBAY_MARKETPLACE_ID).
    """
    if not title:
        return []

    token = await _get_app_token()
    mp = DEFAULT_MARKETPLACE
    headers = {
        "Authorization": f"Bearer {token}",
        "X-EBAY-C-MARKETPLACE-ID": mp,
    }
    params = {"q": title, "limit": limit}

    for attempt in range(2):
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                r = await client.get(EBAY_BROWSE_SEARCH, headers=headers, params=params)
        except httpx.HTTPError as e:
            if attempt == 1:
                raise RuntimeError(f"EBAY BROWSE network error: {e}") from e
            await _sleep(0.5)
            continue

        if r.status_code >= 400:
            raise RuntimeError(f"EBAY BROWSE {r.status_code}: {r.text}")

        data = r.json()
        return data.get("itemSummaries", []) or []

    return []
