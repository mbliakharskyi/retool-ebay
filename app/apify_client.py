import os
import httpx

APIFY_BASE = "https://api.apify.com/v2"

def _actor_ref() -> str:
    """
    Returns the canonical actor ref usable in the REST path:
    either 'username~name' or just the ID.
    """
    actor = os.getenv("APIFY_ACTOR", "catawiki")
    if "~" in actor or actor.startswith("act_") or actor.startswith("P"):
        return actor
    username = os.getenv("APIFY_USERNAME")
    if username:
        return f"{username}~{actor}"
    return actor  # hope it's already full ref

async def fetch_catawiki_items(catawiki_url: str) -> list[dict]:
    """
    Runs the existing Catawiki actor and returns its dataset items (JSON array).
    Adjust the input payload key if the actor expects something else.
    """
    token = os.environ["APIFY_TOKEN"]
    actor_ref = _actor_ref()
    endpoint = f"{APIFY_BASE}/acts/{actor_ref}/run-sync-get-dataset-items"
    params = {"format": "json"}

    # IMPORTANT: change 'url' if the actor expects a different input schema
    payload = {"url": catawiki_url}

    async with httpx.AsyncClient(timeout=300) as client:
        r = await client.post(
            endpoint,
            params=params,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        r.raise_for_status()
        data = r.json()
        if isinstance(data, dict) and "items" in data:
            # In rare cases the API wraps items; normalize to list
            return data["items"]
        if isinstance(data, list):
            return data
        return []
