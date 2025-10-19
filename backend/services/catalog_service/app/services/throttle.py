"""
Throttled Pantheon API Client
Max 5 requests/second with ETag/If-Modified-Since caching
"""
import asyncio
import time
from typing import Optional, Dict, Any
from datetime import datetime

import httpx
from app_common.logging import get_logger

logger = get_logger(__name__)

class ThrottledPantheonClient:
    """
    Pantheon API client with rate limiting (max 5 req/s)
    Implements ETag and If-Modified-Since caching
    """
    
    def __init__(self, base_url: str, api_key: str, username: str, password: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.username = username
        self.password = password
        
        # Rate limiting: max 5 requests per second
        self.max_requests_per_second = 5
        self.min_interval = 1.0 / self.max_requests_per_second  # 0.2 seconds
        self.last_request_time = 0.0
        
        # ETag cache
        self.etag_cache: Dict[str, str] = {}
        self.last_modified_cache: Dict[str, str] = {}
        
        # HTTP client with timeout
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "X-API-Key": self.api_key,
                "User-Agent": "MagacinTrack/1.0"
            }
        )
    
    async def _throttle(self):
        """
        Enforce rate limiting: wait if necessary
        """
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        
        if elapsed < self.min_interval:
            wait_time = self.min_interval - elapsed
            logger.debug(f"throttle.wait", wait_time=wait_time)
            await asyncio.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    async def get_articles(
        self, 
        time_chg_ts: Optional[datetime] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get articles from Pantheon GetArticleWMS
        
        Args:
            time_chg_ts: Filter by modification timestamp
            use_cache: Use ETag/If-Modified-Since caching
            
        Returns:
            {
                "items": [...],
                "cached": bool,
                "etag": str,
                "count": int
            }
        """
        await self._throttle()
        
        url = f"{self.base_url}/GetArticleWMS"
        headers = {}
        
        # Add caching headers
        cache_key = "GetArticleWMS"
        if use_cache and cache_key in self.etag_cache:
            headers["If-None-Match"] = self.etag_cache[cache_key]
        
        if use_cache and time_chg_ts:
            headers["If-Modified-Since"] = time_chg_ts.strftime("%a, %d %b %Y %H:%M:%S GMT")
        
        params = {}
        if time_chg_ts:
            params["time_chg_ts"] = time_chg_ts.isoformat()
        
        logger.info("pantheon.get_articles", url=url, use_cache=use_cache, time_chg_ts=str(time_chg_ts))
        
        try:
            response = await self.client.get(
                url,
                params=params,
                headers=headers,
                auth=(self.username, self.password) if self.username else None
            )
            
            # Handle 304 Not Modified (cached)
            if response.status_code == 304:
                logger.info("pantheon.cache_hit", endpoint="GetArticleWMS")
                return {
                    "items": [],
                    "cached": True,
                    "etag": self.etag_cache.get(cache_key),
                    "count": 0
                }
            
            response.raise_for_status()
            
            # Store ETag for future requests
            if "ETag" in response.headers:
                self.etag_cache[cache_key] = response.headers["ETag"]
            
            if "Last-Modified" in response.headers:
                self.last_modified_cache[cache_key] = response.headers["Last-Modified"]
            
            data = response.json()
            items = data.get("items", []) if isinstance(data, dict) else data
            
            logger.info("pantheon.success", endpoint="GetArticleWMS", count=len(items))
            
            return {
                "items": items,
                "cached": False,
                "etag": self.etag_cache.get(cache_key),
                "count": len(items)
            }
            
        except httpx.HTTPError as e:
            logger.error("pantheon.error", endpoint="GetArticleWMS", error=str(e))
            raise
    
    async def get_subjects(
        self,
        time_chg_ts: Optional[datetime] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get subjects/partners from Pantheon GetSubjectWMS
        """
        await self._throttle()
        
        url = f"{self.base_url}/GetSubjectWMS"
        headers = {}
        
        cache_key = "GetSubjectWMS"
        if use_cache and cache_key in self.etag_cache:
            headers["If-None-Match"] = self.etag_cache[cache_key]
        
        params = {}
        if time_chg_ts:
            params["time_chg_ts"] = time_chg_ts.isoformat()
        
        try:
            response = await self.client.get(
                url,
                params=params,
                headers=headers,
                auth=(self.username, self.password) if self.username else None
            )
            
            if response.status_code == 304:
                return {"items": [], "cached": True, "count": 0}
            
            response.raise_for_status()
            
            if "ETag" in response.headers:
                self.etag_cache[cache_key] = response.headers["ETag"]
            
            data = response.json()
            items = data.get("items", []) if isinstance(data, dict) else data
            
            return {
                "items": items,
                "cached": False,
                "count": len(items)
            }
            
        except httpx.HTTPError as e:
            logger.error("pantheon.error", endpoint="GetSubjectWMS", error=str(e))
            raise
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

