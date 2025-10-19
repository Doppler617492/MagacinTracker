"""
Pantheon API Client
Enterprise-grade HTTP client with JWT auth, rate limiting, circuit breaker, and retry logic
"""
from __future__ import annotations

import asyncio
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from enum import Enum

import httpx
from app_common.logging import get_logger
from app_common.pantheon_config import pantheon_config

logger = get_logger(__name__)


class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"       # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class PantheonCircuitBreaker:
    """Circuit breaker for Pantheon API"""
    
    def __init__(self):
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.threshold = pantheon_config.circuit_breaker_threshold
        self.timeout = pantheon_config.circuit_breaker_timeout_s
    
    def record_success(self):
        """Record successful request"""
        if self.state == CircuitBreakerState.HALF_OPEN:
            logger.info("Circuit breaker: recovered, closing circuit")
            self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
    
    def record_failure(self):
        """Record failed request"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.threshold:
            logger.warning(
                f"Circuit breaker: threshold reached ({self.failure_count} failures), "
                f"opening circuit for {self.timeout}s"
            )
            self.state = CircuitBreakerState.OPEN
    
    def can_attempt(self) -> bool:
        """Check if request can be attempted"""
        if self.state == CircuitBreakerState.CLOSED:
            return True
        
        if self.state == CircuitBreakerState.OPEN:
            # Check if timeout expired
            if self.last_failure_time:
                elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
                if elapsed >= self.timeout:
                    logger.info("Circuit breaker: timeout expired, entering half-open state")
                    self.state = CircuitBreakerState.HALF_OPEN
                    return True
            return False
        
        # HALF_OPEN: allow one test request
        return True


class PantheonAPIClient:
    """
    Enterprise Pantheon API Client with:
    - JWT authentication with auto-refresh
    - Rate limiting (1 RPS)
    - Circuit breaker pattern
    - Exponential backoff retry
    - Request correlation IDs
    """
    
    def __init__(self):
        self.base_url = pantheon_config.base_url
        self.username = pantheon_config.username
        self.password = pantheon_config.password
        self.rate_limit_rps = pantheon_config.rate_limit_rps
        self.timeout_ms = pantheon_config.timeout_ms / 1000.0  # Convert to seconds
        self.retry_max = pantheon_config.retry_max
        
        self._token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        self._last_request_time: float = 0
        self._circuit_breaker = PantheonCircuitBreaker()
        self._client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout_ms,
            headers={"Content-Type": "application/json"}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self._client:
            await self._client.aclose()
    
    async def _wait_for_rate_limit(self):
        """Enforce rate limiting (1 RPS)"""
        now = time.time()
        elapsed = now - self._last_request_time
        min_interval = 1.0 / self.rate_limit_rps
        
        if elapsed < min_interval:
            wait_time = min_interval - elapsed
            logger.debug(f"Rate limit: waiting {wait_time:.3f}s")
            await asyncio.sleep(wait_time)
        
        self._last_request_time = time.time()
    
    async def authenticate(self) -> bool:
        """
        Authenticate with Pantheon API
        Response format: {"status": 0, "token": "<JWT>"}
        Returns: True if successful, False otherwise
        """
        try:
            logger.info(f"🔐 Authenticating with Pantheon API: {self.username} @ {self.base_url}")
            
            response = await self._client.post(
                "/login",
                json={
                    "username": self.username,
                    "password": self.password
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # CORRECTED: Pantheon returns {"message": "Login successful", "token": "..."}
                token = data.get("token")
                if token:
                    self._token = token
                    
                    # JWT tokens typically expire in 1 hour, refresh 5 min before
                    self._token_expires_at = datetime.utcnow() + timedelta(
                        minutes=55
                    )
                    
                    logger.info(f"✅ Authentication successful, token expires at {self._token_expires_at}")
                    self._circuit_breaker.record_success()
                    return True
                else:
                    logger.error(f"❌ Authentication failed: no token in response={data}")
                    self._circuit_breaker.record_failure()
                    return False
            else:
                logger.error(f"❌ Authentication failed: {response.status_code} {response.text}")
                self._circuit_breaker.record_failure()
                return False
                
        except Exception as e:
            logger.error(f"❌ Authentication exception: {e}")
            self._circuit_breaker.record_failure()
            return False
    
    async def _ensure_authenticated(self) -> bool:
        """Ensure we have a valid token, refresh if needed"""
        # No token yet
        if not self._token or not self._token_expires_at:
            return await self.authenticate()
        
        # Token about to expire (within 5 minutes)
        buffer = timedelta(minutes=pantheon_config.token_refresh_buffer_minutes)
        if datetime.utcnow() >= (self._token_expires_at - buffer):
            logger.info("Token expiring soon, refreshing...")
            return await self.authenticate()
        
        return True
    
    async def _request_with_retry(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Make HTTP request with retry logic and exponential backoff
        """
        # Check circuit breaker
        if not self._circuit_breaker.can_attempt():
            logger.warning("Circuit breaker OPEN, rejecting request")
            return None
        
        # Ensure authenticated
        if not await self._ensure_authenticated():
            logger.error("Failed to authenticate")
            return None
        
        # Add authorization header
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self._token}"
        
        # Retry loop with exponential backoff
        for attempt in range(self.retry_max):
            try:
                # Rate limiting
                await self._wait_for_rate_limit()
                
                # Make request
                logger.debug(f"Request {method} {endpoint} (attempt {attempt + 1}/{self.retry_max})")
                
                response = await self._client.request(
                    method,
                    endpoint,
                    headers=headers,
                    **kwargs
                )
                
                # Success
                if response.status_code == 200:
                    self._circuit_breaker.record_success()
                    data = response.json()
                    
                    # CORRECTED: Pantheon returns array directly, not {"items": [...]}
                    if isinstance(data, list):
                        return {
                            "items": data,
                            "total": len(data)  # Pantheon doesn't return total count
                        }
                    else:
                        return data
                
                # No data found (acceptable)
                elif response.status_code == 204:
                    logger.debug(f"No data found for {endpoint}")
                    self._circuit_breaker.record_success()
                    return {"items": [], "total": 0}
                
                # Unauthorized - try to re-authenticate
                elif response.status_code == 401:
                    logger.warning(f"401 Unauthorized, re-authenticating...")
                    if await self.authenticate():
                        headers["Authorization"] = f"Bearer {self._token}"
                        continue
                    else:
                        self._circuit_breaker.record_failure()
                        return None
                
                # Rate limit exceeded
                elif response.status_code == 429:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"429 Rate limit exceeded, waiting {wait_time}s")
                    await asyncio.sleep(wait_time)
                    continue
                
                # Server error - retry
                elif response.status_code >= 500:
                    wait_time = 2 ** attempt
                    logger.warning(f"5xx Server error, waiting {wait_time}s before retry")
                    await asyncio.sleep(wait_time)
                    continue
                
                # Other errors
                else:
                    logger.error(f"Request failed: {response.status_code} {response.text}")
                    self._circuit_breaker.record_failure()
                    return None
                    
            except httpx.TimeoutException:
                wait_time = 2 ** attempt
                logger.warning(f"Request timeout, waiting {wait_time}s before retry")
                await asyncio.sleep(wait_time)
                continue
                
            except Exception as e:
                logger.error(f"Request exception: {e}")
                self._circuit_breaker.record_failure()
                return None
        
        # All retries exhausted
        logger.error(f"All {self.retry_max} retries exhausted for {endpoint}")
        self._circuit_breaker.record_failure()
        return None
    
    # =========================================================================
    # PUBLIC API METHODS
    # =========================================================================
    
    async def get_ident_wms(
        self,
        ad_time_chg: Optional[str] = None,
        limit: int = 1000,
        offset: int = 0
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch articles from Pantheon (getIdentWMS method via POST /get)
        
        Args:
            ad_time_chg: Optional timestamp for delta sync (ISO format)
            limit: Page size
            offset: Page offset
        
        Returns:
            Dict with 'items' (list of articles) and 'total' (count)
        """
        body = {
            "method": "getIdentWMS",
            "offset": offset,
            "limit": limit
        }
        
        if ad_time_chg:
            body["filters"] = {
                "adTimeChg": {
                    "operator": ">=",
                    "value": ad_time_chg
                }
            }
        
        return await self._request_with_retry("POST", "/get", json=body)
    
    async def get_subject_wms(
        self,
        ad_time_chg: Optional[str] = None,
        limit: int = 1000,
        offset: int = 0
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch subjects/partners from Pantheon (GetSubjectWMS method via POST /get)
        """
        body = {
            "method": "GetSubjectWMS",
            "offset": offset,
            "limit": limit
        }
        
        if ad_time_chg:
            body["filters"] = {
                "c.adTimeChg": {
                    "operator": ">",
                    "value": ad_time_chg
                }
            }
        
        return await self._request_with_retry("POST", "/get", json=body)
    
    async def get_issue_doc_wms(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: int = 1000,
        offset: int = 0
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch outbound/issue documents from Pantheon (GetIssueDocWMS method via POST /get)
        """
        body = {
            "method": "GetIssueDocWMS",
            "offset": offset,
            "limit": limit
        }
        
        if date_from:
            body["filters"] = {
                "m.adDate": {
                    "operator": ">",
                    "value": date_from
                }
            }
        
        return await self._request_with_retry("POST", "/get", json=body)
    
    async def get_receipt_doc_wms(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: int = 1000,
        offset: int = 0
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch inbound/receipt documents from Pantheon (GetReceiptDocWMS method via POST /get)
        """
        body = {
            "method": "GetReceiptDocWMS",
            "offset": offset,
            "limit": limit
        }
        
        if date_from:
            body["filters"] = {
                "m.adDate": {
                    "operator": ">",
                    "value": date_from
                }
            }
        
        return await self._request_with_retry("POST", "/get", json=body)


# Global client factory
async def get_pantheon_client() -> PantheonAPIClient:
    """Factory function for Pantheon API client"""
    return PantheonAPIClient()

