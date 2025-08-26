import os, base64, httpx, time

EBAY_SEARCH = "https://api.ebay.com/buy/browse/v1/item_summary/search"

async def search_ebay(title: str, limit: int = 20) -> list[dict]:
    token = os.environ["EBAY_OAUTH_TOKEN"]
    mp = os.getenv("EBAY_MARKETPLACE_ID", "EBAY_US")
    headers = {
        "Authorization": f"Bearer {token}",
        "X-EBAY-C-MARKETPLACE-ID": mp,
    }
    params = {"q": title, "limit": limit}
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(EBAY_SEARCH, headers=headers, params=params)
        r.raise_for_status()
        return r.json().get("itemSummaries", []) or []

CLIENT_ID = os.getenv("EBAY_CLIENT_ID")
CLIENT_SECRET = os.getenv("EBAY_CLIENT_SECRET")
AUTH = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()

def get_token():
    url = "https://api.ebay.com/identity/v1/oauth2/token"
    data = {
        "grant_type": "client_credentials",
        "scope": "https://api.ebay.com/oauth/api_scope https://api.ebay.com/oauth/api_scope/buy.browse"
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded",
               "Authorization": f"Basic {AUTH}"}
    r = httpx.post(url, data=data, headers=headers)
    r.raise_for_status()
    token = r.json()
    return token["access_token"], time.time() + token["expires_in"]