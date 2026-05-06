import os
import logging
import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Singleton instances
_client = None
_service_client = None

def get_supabase_client() -> Client:
    """
    Returns a Supabase client. 
    If a user is logged in (Streamlit session), returns a client scoped to that user.
    Otherwise, returns a generic anon client.
    """
    # Check for authenticated session in Streamlit
    if 'access_token' in st.session_state:
        return get_auth_client(st.session_state.access_token)
    
    global _client
    if _client is None:
        url: str = os.getenv("SUPABASE_URL")
        key: str = os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise ValueError("Missing Supabase credentials (URL/KEY) in .env file")
        _client = create_client(url, key)
    return _client

def get_auth_client(access_token: str) -> Client:
    """Returns a Supabase client scoped to a specific user's session."""
    url: str = os.getenv("SUPABASE_URL")
    if not url:
        raise ValueError("Missing SUPABASE_URL in .env file")
    # We create a new client with the access token in headers for RLS
    return create_client(url, os.getenv("SUPABASE_KEY"), options={"headers": {"Authorization": f"Bearer {access_token}"}})

def get_service_client() -> Client:
    """Returns a singleton Supabase client using the service role key for write operations."""
    global _service_client
    if _service_client is None:
        url: str = os.getenv("SUPABASE_URL")
        key: str = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise ValueError("Missing Supabase credentials in .env file")
        _service_client = create_client(url, key)
    return _service_client

def test_connection() -> bool:
    """Tests the database connection with a simple query."""
    try:
        client = get_supabase_client()
        # Simple query to check connectivity
        client.table('reviews').select('id', count='exact').limit(1).execute()
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False
