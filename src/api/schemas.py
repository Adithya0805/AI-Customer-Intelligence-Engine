from pydantic import BaseModel, HttpUrl
from typing import List, Dict, Optional, Any
from datetime import datetime

class AnalyzeRequest(BaseModel):
    url: Optional[HttpUrl] = None
    text: Optional[str] = None
    source: Optional[str] = "api_request"

class AnalyzeResponse(BaseModel):
    status: str
    processed_count: int
    executive_summary: str
    sentiment_distribution: Dict[str, int]
    aspects: List[Dict[str, Any]]
    alerts: List[Dict[str, Any]]

class ReviewResponse(BaseModel):
    id: str
    original_text: str
    sentiment: str
    source: str
    date: datetime

class WebhookRegisterRequest(BaseModel):
    url: HttpUrl
    events: List[str] = ["alert", "new_review"]
