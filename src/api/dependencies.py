# src/api/dependencies.py
from fastapi import Header, HTTPException, Depends
from typing import Optional
import os
import time
from src.core.exceptions import RateLimitExceeded

# Simple in-memory rate limiting store
_rate_limit_store = {}

def check_rate_limit(api_key: str, endpoint: str, limit: int = 10, window: int = 60) -> bool:
    """Check if request is within rate limit"""
    key = f"{api_key}:{endpoint}"
    now = int(time.time())
    window_start = now - window
    
    if key in _rate_limit_store:
        _rate_limit_store[key] = [t for t in _rate_limit_store[key] if t > window_start]
    else:
        _rate_limit_store[key] = []
    
    if len(_rate_limit_store[key]) >= limit:
        return False
    
    _rate_limit_store[key].append(now)
    return True

async def verify_api_key(
    api_key: Optional[str] = Header(None, alias="X-API-Key")
) -> str:
    """Verify API key (optional for MVP)"""
    expected_key = os.getenv("API_KEY", None)
    
    if expected_key and not api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    if expected_key and api_key != expected_key:
        raise HTTPException(status_code=403, detail="Invalid API key")
    
    return api_key or "public"

def get_user_identifier(api_key: str = Depends(verify_api_key)) -> str:
    """Return a unique identifier for rate limiting"""
    return api_key if api_key != "public" else "anonymous"

async def rate_limit_dep(
    api_key: str = Depends(verify_api_key),
    endpoint: str = "generate"
) -> str:
    """Rate limiting dependency"""
    if not check_rate_limit(api_key, endpoint):
        raise RateLimitExceeded(f"Rate limit exceeded for endpoint: {endpoint}")
    return api_key
