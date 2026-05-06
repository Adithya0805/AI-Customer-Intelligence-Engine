import hmac
import hashlib
import json
import httpx
import logging
from typing import Dict, Any
from src.database.client import get_service_client

logger = logging.getLogger(__name__)

async def send_webhook(webhook_id: str, url: str, payload: Dict[str, Any], secret: str):
    """Sends a signed webhook payload with retry logic."""
    data = json.dumps(payload)
    signature = hmac.new(secret.encode(), data.encode(), hashlib.sha256).hexdigest()
    
    headers = {
        "Content-Type": "application/json",
        "X-Hub-Signature-256": f"sha256={signature}"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, content=data, headers=headers, timeout=10.0)
            status_code = response.status_code
            logger.info(f"Webhook {webhook_id} sent to {url}, status: {status_code}")
        except Exception as e:
            logger.error(f"Webhook {webhook_id} failed: {e}")
            status_code = 0
            
        # Log delivery
        try:
            supabase = get_service_client()
            supabase.table('webhook_deliveries').insert({
                "webhook_id": webhook_id,
                "event_type": payload.get("event", "unknown"),
                "payload": payload,
                "response_code": status_code
            }).execute()
        except Exception as ex:
            logger.error(f"Failed to log webhook delivery: {ex}")
