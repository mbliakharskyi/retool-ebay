import asyncio
from fastapi import FastAPI, HTTPException
from app.schemas import CompareRequest, CompareResult, CatawikiItem
from app.apify_client import fetch_catawiki_items
from app.ebay_client import search_ebay
from app.analysis import match_top, summarize_prices, simple_verdict
from app.sites import sites_for_category
from app.research import gpt_research
from dotenv import load_dotenv

app = FastAPI()

load_dotenv()

@app.get("/")
async def hello():
    ebay_raw = await search_ebay("test")
    print("ebay::", ebay_raw)
    return {"ok": True}

@app.post("/compare")
async def compare(req: CompareRequest):
    if not req.catawiki_url:
        raise HTTPException(status_code=400, detail="catawiki_url is required")

    items = await fetch_catawiki_items(req.catawiki_url)
    if not items:
        return {"items": [], "notes": "No items found from Catawiki"}

    # pick just the first item for testing
    first = items[0]

    async def run_item(raw: dict):
        cw = CatawikiItem(**raw)
        ebay_raw = await search_ebay(cw.title)
        ebay_top = match_top(cw.title, ebay_raw)
        ebay_stats = summarize_prices(ebay_top, lambda x: x.get("price", {}).get("value"))

        research = []
        # leave include_research as-is; it can be False for Phase 1
        if req.include_research:
            allowed = sites_for_category(cw.category or "")
            research = await gpt_research(cw.title, allowed)

        verdict = simple_verdict(raw, ebay_stats)
        analysis = {
            "verdict": verdict,
            "confidence": 0.6 if ebay_stats.get("n", 0) >= 5 else 0.4,
            "price_summary": {
                "catawiki": {
                    "estimateMin": raw.get("estimatedPriceMin"),
                    "estimateMax": raw.get("estimatedPriceMax"),
                },
                "ebay": ebay_stats,
                "research": {},
            },
            "key_differences": [],
            "recommendation": "buy" if verdict == "underpriced" else ("watch" if verdict != "overpriced" else "skip"),
            "notes": "Heuristic verdict using eBay median vs Catawiki estimate.",
        }

        return CompareResult(source=raw, ebay=ebay_top, research=research, analysis=analysis).model_dump()

    one_result = await run_item(first)
    return {"items": [one_result]}  # << return list for consistency
