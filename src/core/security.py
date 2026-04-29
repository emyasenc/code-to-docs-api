# src/core/security.py
"""
Security utilities for the Code-to-Docs API.
"""

import os
import hashlib
import hmac
from typing import Optional
from fastapi import HTTPException, status

# In-memory rate limiting store (for MVP)
# In production, replace with Redis.
_rate_limit_store = {}

def verify_api_key(api_key: str, expected_key: Optional[str] = None) -> bool:
    """
    Constant‑time API key verification.
    """
    expected = expected_key or os.getenv("API_KEY")
    if not expected:
        # No key configured → allow all requests (development mode)
        return True
    
    return hmac.compare_digest(api_key, expected)

def get_rate_limit_key(api_key: str, endpoint: str) -> str:
    """
    Generate a unique key for rate limiting.
    """
    return f"ratelimit:{api_key}:{endpoint}"

def rate_limit_check(api_key: str, endpoint: str, limit: int = 10, window: int = 60) -> bool:
    """
    Simple in‑memory rate limiter.
    Returns True if under limit, False if exceeded.
    """
    key = get_rate_limit_key(api_key, endpoint)
    from time import time
    
    now = int(time())
    window_start = now - window
    
    # Clean old entries
    if key in _rate_limit_store:
        _rate_limit_store[key] = [t for t in _rate_limit_store[key] if t > window_start]
    else:
        _rate_limit_store[key] = []
    
    if len(_rate_limit_store[key]) >= limit:
        return False
    
    _rate_limit_store[key].append(now)
    return True

def raise_rate_limit_exceeded(limit: int, window: int) -> None:
    """
    Raise a standardized rate limit error.
    """
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail={
            "error": "RATE_LIMIT_EXCEEDED",
            "message": f"Limit of {limit} requests per {window} seconds exceeded.",
            "retry_after": window
        }
    )