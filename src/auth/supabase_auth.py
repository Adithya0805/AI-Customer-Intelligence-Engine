import streamlit as st
import logging
from typing import Optional, Dict
from src.database.client import get_supabase_client

logger = logging.getLogger(__name__)

def signup(email: str, password: str) -> Dict:
    """Signs up a new user via Supabase."""
    try:
        supabase = get_supabase_client()
        res = supabase.auth.sign_up({
            "email": email,
            "password": password,
        })
        return {"status": "success", "user": res.user}
    except Exception as e:
        logger.error(f"Signup error: {e}")
        return {"status": "error", "message": str(e)}

def login(email: str, password: str) -> Dict:
    """Logs in an existing user via Supabase."""
    try:
        supabase = get_supabase_client()
        res = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password,
        })
        if res.user:
            st.session_state.user = res.user
            st.session_state.access_token = res.session.access_token
            return {"status": "success", "user": res.user}
        return {"status": "error", "message": "Login failed"}
    except Exception as e:
        logger.error(f"Login error: {e}")
        return {"status": "error", "message": str(e)}

def logout():
    """Logs out the current user."""
    try:
        supabase = get_supabase_client()
        supabase.auth.sign_out()
        if 'user' in st.session_state:
            del st.session_state.user
        if 'access_token' in st.session_state:
            del st.session_state.access_token
        st.rerun()
    except Exception as e:
        logger.error(f"Logout error: {e}")

def get_current_user():
    """Returns the current logged in user from session state."""
    return st.session_state.get('user')

def is_authenticated() -> bool:
    """Checks if a user is currently logged in."""
    return 'user' in st.session_state and st.session_state.user is not None
