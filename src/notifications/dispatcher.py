import logging
import asyncio
from typing import Dict, Any
from src.database.client import get_service_client
from src.notifications.webhook_sender import send_webhook
from src.notifications.email_sender import EmailSender

logger = logging.getLogger(__name__)

class NotificationDispatcher:
    def __init__(self):
        self.email_sender = EmailSender()
        self.supabase = get_service_client()

    async def dispatch(self, user_id: str, event_type: str, payload: Dict[str, Any]):
        """Dispatches an event to all registered channels for a user."""
        logger.info(f"Dispatching event '{event_type}' for user {user_id}")
        
        # 1. Fetch user email (for primary alerts)
        try:
            # We assume the user's email is available in auth.users
            # Since we can't easily query auth.users from client without special permissions,
            # we might want a 'user_profiles' table or just use the session if available.
            # For now, we'll skip direct auth query and assume webhooks are the primary programmatic channel.
            pass
        except Exception as e:
            logger.error(f"Failed to fetch user email: {e}")

        # 2. Webhooks
        try:
            res = self.supabase.table('webhooks').select('*').eq('user_id', user_id).eq('is_active', True).execute()
            webhooks = res.data
            for wh in webhooks:
                if event_type in wh.get('events', []):
                    # Prepare webhook payload
                    wh_payload = {
                        "event": event_type,
                        "timestamp": "now()",
                        "data": payload
                    }
                    # Run async
                    asyncio.create_task(send_webhook(wh['id'], wh['url'], wh_payload, wh['secret']))
        except Exception as e:
            logger.error(f"Error dispatching webhooks: {e}")

        # 3. Special handling for critical alerts
        if event_type == "alert" and payload.get('status') == 'EMERGING_CRISIS':
            # Here we would send the email
            # self.email_sender.send_alert_email(...)
            pass
