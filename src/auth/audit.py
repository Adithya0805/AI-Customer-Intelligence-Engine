import logging
from typing import Optional, Dict, Any
from src.database.client import get_service_client

logger = logging.getLogger(__name__)

def log_action(user_id: Optional[str], action: str, resource_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
    """
    Logs an enterprise audit event to the database.
    """
    try:
        supabase = get_service_client()
        supabase.table('audit_logs').insert({
            "user_id": user_id,
            "action": action,
            "resource_id": resource_id,
            "metadata": metadata or {}
        }).execute()
        logger.info(f"Audit log: {action} by {user_id}")
    except Exception as e:
        logger.error(f"Failed to write audit log: {e}")
