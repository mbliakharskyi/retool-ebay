import os, httpx

APIFY_BASE = "https://api.apify.com/v2"

async def fetch_catawiki_items(catawiki_url: str) -> list[dict]:
    token = os.environ["APIFY_TOKEN"]
    # Run the existing actor and get dataset items directly
    endpoint = f"{APIFY_BASE}/acts/kamil989898~catawiki/run-sync-get-dataset-items"
    params = {"format": "json"}
    # Pass the URL as the actor input (adjust if the actor expects a different key)
    payload = {"url": catawiki_url}
    async with httpx.AsyncClient(timeout=300) as client:
        r = await client.post(endpoint, params=params,
                              headers={"Authorization": f"Bearer {token}",
                                       "Content-Type": "application/json"},
                              json=payload)
        r.raise_for_status()
        return r.json()  # array of items
