from pydantic import BaseModel
from typing import Optional, List, Any

class CompareRequest(BaseModel):
    catawiki_url: str
    include_research: bool = True

class CatawikiItem(BaseModel):
    id: Optional[int] = None
    title: str
    subtitle: Optional[str] = ""
    url: Optional[str] = ""
    imageUrl: Optional[str] = ""
    category: Optional[str] = ""
    condition: Optional[str] = ""
    estimatedPriceMin: Optional[float] = None
    estimatedPriceMax: Optional[float] = None
    finalPrice: Optional[float] = None

class CompareResult(BaseModel):
    source: Any
    ebay: List[Any]
    research: List[Any]
    analysis: Any
