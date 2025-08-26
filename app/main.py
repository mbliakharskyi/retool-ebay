import os, asyncio, orjson
from fastapi import FastAPI, HTTPException
from app.schemas import CompareRequest, CompareResult, CatawikiItem
from app.apify_client import fetch_catawiki_items
from app.ebay_client import search_ebay
from app.analysis import match_top, summarize_prices, simple_verdict

app = FastAPI()

@app.get("/health")
def health(): return {"ok": True}

@app.post("/compare")
async def compare(req: CompareRequest):
    if not req.catawiki_url:
        raise HTTPException(400, "catawiki_url is required")

    # 1) pull items from Apify
    items = await fetch_catawiki_items(req.catawiki_url)
    if not items:
        return {"items": [], "notes": "No items found from Catawiki"}

    # 2) fan-out: ebay + (optional) research
    async def run_item(raw):
        research = []
        if req.include_research:
            research = await gpt_research(cw.title, sites_for_category(cw.category or ""))

        analysis = {
        "verdict": simple_verdict(raw, ebay_stats),
        "confidence": 0.6 if ebay_stats.get("n",0) >= 5 else 0.4,
        "price_summary": {
            "catawiki": {"estimateMin": raw.get("estimatedPriceMin"), "estimateMax": raw.get("estimatedPriceMax")},
            "ebay": ebay_stats,
            "research": summarize_prices(research, lambda x: x.get("price"))
        },
        "key_differences": [],
        "recommendation": "buy" if simple_verdict(raw, ebay_stats) == "underpriced" else "watch",
        "notes": "Heuristic verdict using eBay median vs Catawiki estimate, plus optional research."
        }
        cw = CatawikiItem(**raw)
        ebay_raw = await search_ebay(cw.title)
        ebay_top = match_top(cw.title, ebay_raw)
        ebay_stats = summarize_prices(ebay_top, lambda x: x.get("price",{}).get("value"))

        analysis = {
            "verdict": simple_verdict(raw, ebay_stats),
            "confidence": 0.6 if ebay_stats.get("n",0) >= 5 else 0.4,
            "price_summary": {
                "catawiki": {"estimateMin": raw.get("estimatedPriceMin"), "estimateMax": raw.get("estimatedPriceMax")},
                "ebay": ebay_stats,
                "research": {}  # fill later if you add GPT research
            },
            "key_differences": [],
            "recommendation": "buy" if simple_verdict(raw, ebay_stats)=="underpriced" else "watch",
            "notes": "Heuristic verdict using eBay median vs Catawiki estimate."
        }
        return {
        "source": raw,
        "ebay": ebay_top,
        "research": research,
        "analysis": analysis
        }
        return CompareResult(source=raw, ebay=ebay_top, research=[], analysis=analysis).model_dump()

    results = await asyncio.gather(*[run_item(i) for i in items])
    return {"items": results}
