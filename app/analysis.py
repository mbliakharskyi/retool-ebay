from typing import List, Dict, Any
from statistics import median

def match_top(cw_title: str, ebay_items: List[Dict[str, Any]], top_n=8):
    base = set(cw_title.lower().split())
    def score(e):
        t = set((e.get("title") or "").lower().split())
        return len(base & t)
    return sorted(ebay_items, key=score, reverse=True)[:top_n]

def summarize_prices(items, get_price=lambda x: x.get("price",{}).get("value")):
    vals = []
    for it in items:
        p = get_price(it)
        try:
            vals.append(float(p))
        except (TypeError, ValueError):
            pass
    if not vals:
        return {"n": 0}
    return {"n": len(vals), "min": min(vals), "median": median(vals), "max": max(vals)}

def simple_verdict(catawiki, ebay_stats):
    est_min = catawiki.get("estimatedPriceMin")
    est_max = catawiki.get("estimatedPriceMax")
    med = ebay_stats.get("median")
    if not med or not est_min or not est_max:
        return "unknown"
    if med < est_min: return "underpriced"
    if med > est_max: return "overpriced"
    return "fair"
