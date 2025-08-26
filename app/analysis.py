from typing import List, Dict, Any
from statistics import median
import re

def _norm_tokens(text: str) -> set[str]:
    text = (text or "").lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return set(t for t in text.split() if t)

def match_top(cw_title: str, ebay_items: List[Dict[str, Any]], top_n=8):
    base = _norm_tokens(cw_title)
    def score(e):
        t = _norm_tokens(e.get("title") or "")
        return len(base & t)
    return sorted(ebay_items, key=score, reverse=True)[:top_n]

def summarize_prices(items, get_price=lambda x: x.get("price", {}).get("value")):
    vals: List[float] = []
    for it in items:
        p = get_price(it)
        try:
            vals.append(float(p))
        except (TypeError, ValueError):
            pass
    if not vals:
        return {"n": 0}
    return {"n": len(vals), "min": min(vals), "median": median(vals), "max": max(vals)}

def simple_verdict(catawiki: Dict[str, Any], ebay_stats: Dict[str, Any]) -> str:
    est_min = catawiki.get("estimatedPriceMin")
    est_max = catawiki.get("estimatedPriceMax")
    med = ebay_stats.get("median")
    if not med or not est_min or not est_max:
        return "unknown"
    if med < est_min:
        return "underpriced"
    if med > est_max:
        return "overpriced"
    return "fair"
