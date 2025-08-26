import os
from typing import List, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def gpt_research(title: str, sites: List[str]) -> List[Dict[str, Any]]:
    """
    Returns a list of {title, price, currency, condition, url}.
    Keep it lightweight and limited to the allowed domains.
    """
    if not sites:
        return []

    system = (
        "You are a pricing researcher. "
        "Search ONLY the provided domains. Extract structured facts "
        "(title, price number, currency, condition, url). If a field is missing, omit it. "
        "Return a concise JSON array."
    )
    user = f"Find comparable listings for: {title}. Search only these sites: {', '.join(sites)}."

    # Note: depending on your model access, replace with your browsing/tools call.
    # Here we call a JSON-structured response (pseudo—adapt to your SDK/model):
    resp = client.chat.completions.create(
        model="gpt-4o-mini",  # or model with tools/browsing you have
        temperature=0,
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": user}]
    )
    # Extract JSON from the response text safely:
    text = resp.choices[0].message.content or "[]"
    # Implement a robust JSON extraction if needed
    try:
        import json, re
        # naive extraction
        start = text.find("[")
        end = text.rfind("]")+1
        return json.loads(text[start:end])
    except Exception:
        return []
