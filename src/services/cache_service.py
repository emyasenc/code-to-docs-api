# src/services/cache_service.py
"""
Cache service for storing generated documentation.
Saves costs by avoiding duplicate LLM calls.
"""

import os
import json
import hashlib
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class CacheService:
    """Simple file-based cache for generated documentation"""
    
    def __init__(self, cache_dir: str = "./data/cache", ttl_seconds: int = 86400):
        """
        Initialize cache service.
        
        Args:
            cache_dir: Directory to store cache files
            ttl_seconds: Time to live in seconds (default 24 hours)
        """
        self.cache_dir = Path(cache_dir)
        self.ttl_seconds = ttl_seconds
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Cache service initialized at {self.cache_dir}")
    
    def _get_cache_key(self, github_url: str, include_readme: bool, 
                       include_openapi: bool, include_contributing: bool,
                       include_architecture: bool) -> str:
        """Generate a unique cache key from request parameters"""
        data = f"{github_url}:{include_readme}:{include_openapi}:{include_contributing}:{include_architecture}"
        return hashlib.md5(data.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get file path for a cache key"""
        return self.cache_dir / f"{cache_key}.json"
    
    def get(self, github_url: str, include_readme: bool = True,
            include_openapi: bool = False, include_contributing: bool = False,
            include_architecture: bool = False) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached response if it exists and hasn't expired.
        
        Returns:
            Cached response dict or None if not found/expired
        """
        cache_key = self._get_cache_key(github_url, include_readme, include_openapi,
                                        include_contributing, include_architecture)
        cache_path = self._get_cache_path(cache_key)
        
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'r') as f:
                cached = json.load(f)
            
            # Check if cache is expired
            cached_time = datetime.fromisoformat(cached.get('cached_at', '2000-01-01'))
            if datetime.now() - cached_time > timedelta(seconds=self.ttl_seconds):
                logger.info(f"Cache expired for {github_url}")
                return None
            
            logger.info(f"Cache hit for {github_url}")
            return cached.get('response')
        except Exception as e:
            logger.error(f"Cache read failed: {e}")
            return None
    
    def set(self, github_url: str, response: Dict[str, Any],
            include_readme: bool = True, include_openapi: bool = False,
            include_contributing: bool = False, include_architecture: bool = False) -> bool:
        """
        Store response in cache.
        
        Returns:
            True if successful, False otherwise
        """
        cache_key = self._get_cache_key(github_url, include_readme, include_openapi,
                                        include_contributing, include_architecture)
        cache_path = self._get_cache_path(cache_key)
        
        try:
            cache_data = {
                'cached_at': datetime.now().isoformat(),
                'github_url': github_url,
                'response': response,
                'ttl_seconds': self.ttl_seconds
            }
            with open(cache_path, 'w') as f:
                json.dump(cache_data, f, indent=2)
            logger.info(f"Cached response for {github_url}")
            return True
        except Exception as e:
            logger.error(f"Cache write failed: {e}")
            return False
    
    def invalidate(self, github_url: str) -> bool:
        """Delete cached response for a specific repo"""
        # Delete all cache keys that might match this repo (simple approach)
        deleted = 0
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    if data.get('github_url') == github_url:
                        cache_file.unlink()
                        deleted += 1
            except:
                pass
        
        logger.info(f"Invalidated {deleted} cache entries for {github_url}")
        return deleted > 0
    
    def clear_all(self) -> int:
        """Clear entire cache"""
        deleted = 0
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
                deleted += 1
            except:
                pass
        logger.info(f"Cleared {deleted} cache entries")
        return deleted
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        files = list(self.cache_dir.glob("*.json"))
        return {
            'cache_dir': str(self.cache_dir),
            'total_entries': len(files),
            'ttl_seconds': self.ttl_seconds,
            'ttl_hours': self.ttl_seconds / 3600
        }