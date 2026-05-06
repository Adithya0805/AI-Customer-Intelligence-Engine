import hashlib
from fastapi import Request, HTTPException, Security
from fastapi.security import APIKeyHeader
from src.database.client import get_service_client

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_user_from_api_key(api_key: str = Security(api_key_header)):
    if not api_key:
        raise HTTPException(status_code=401, detail="X-API-Key header missing")
    
    # Hash the key to compare with stored hashes
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    
    supabase = get_service_client()
    try:
        res = supabase.table('api_keys').select('user_id').eq('key_hash', key_hash).eq('is_active', True).execute()
        if res.data:
            user_id = res.data[0]['user_id']
            # Update last_used_at
            supabase.table('api_keys').update({"last_used_at": "now()"}).eq('key_hash', key_hash).execute()
            return user_id
    except Exception as e:
        print(f"Auth error: {e}")
        
    raise HTTPException(status_code=401, detail="Invalid or inactive API key")
