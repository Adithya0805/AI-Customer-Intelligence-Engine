import logging
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from typing import List, Dict, Optional
from src.api.schemas import AnalyzeRequest, AnalyzeResponse, WebhookRegisterRequest
from src.api.auth_middleware import get_user_from_api_key
from src.processing.pipeline import IntelligencePipeline
from src.database.client import get_service_client
import secrets

app = FastAPI(title="AI Customer Intelligence API", version="1.0.0")
logger = logging.getLogger(__name__)

# Initialize pipeline once
pipeline = IntelligencePipeline()

@app.get("/api/v1/health")
async def health_check():
    return {"status": "healthy", "service": "ai-intel-api"}

@app.post("/api/v1/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest, user_id: str = Depends(get_user_from_api_key)):
    """Synchronous analysis endpoint."""
    try:
        if request.url:
            res = pipeline.run(str(request.url), user_id=user_id)
        elif request.text:
            res = pipeline.run_from_text(request.text, user_id=user_id)
        else:
            raise HTTPException(status_code=400, detail="Either url or text must be provided")

        if res['status'] == 'success':
            # Calculate distribution
            import pandas as pd
            df = pd.DataFrame(res['processed_data'])
            sent_dist = df['sentiment'].value_counts().to_dict()
            
            return {
                "status": "success",
                "processed_count": res['processed_count'],
                "executive_summary": res['executive_summary'],
                "sentiment_distribution": sent_dist,
                "aspects": res['aspects'],
                "alerts": res['alerts']
            }
        else:
            raise HTTPException(status_code=500, detail=res['message'])
    except Exception as e:
        logger.error(f"API Analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/reviews")
async def get_reviews(limit: int = 100, user_id: str = Depends(get_user_from_api_key)):
    supabase = get_service_client()
    res = supabase.table('reviews').select('*').eq('user_id', user_id).order('date', desc=True).limit(limit).execute()
    return res.data

@app.post("/api/v1/webhooks/register")
async def register_webhook(request: WebhookRegisterRequest, user_id: str = Depends(get_user_from_api_key)):
    supabase = get_service_client()
    secret = secrets.token_urlsafe(32)
    try:
        res = supabase.table('webhooks').insert({
            "user_id": user_id,
            "url": str(request.url),
            "events": request.events,
            "secret": secret
        }).execute()
        return {"status": "success", "webhook_id": res.data[0]['id'], "secret": secret}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
