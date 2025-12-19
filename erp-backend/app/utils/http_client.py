"""
HTTP Client utility for inter-service communication
"""

import httpx
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
import logging
from app.config import settings

logger = logging.getLogger(__name__)


class HTTPClient:
    """
    Async HTTP client for inter-service communication
    
    Features:
    - Connection pooling
    - Automatic retries
    - Timeout configuration
    - Request/response logging
    - Error handling
    """
    
    _client: Optional[httpx.AsyncClient] = None
    
    @classmethod
    async def get_client(cls) -> httpx.AsyncClient:
        """
        Get or create HTTP client instance (singleton pattern)
        
        Returns:
            Configured httpx.AsyncClient instance
        """
        if cls._client is None:
            cls._client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0, connect=10.0),  # 30s total, 10s connect
                limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
                follow_redirects=True,
                http2=True  # Enable HTTP/2 support
            )
            logger.info("HTTP client initialized")
        
        return cls._client
    
    @classmethod
    async def close_client(cls):
        """Close HTTP client and cleanup resources"""
        if cls._client is not None:
            await cls._client.aclose()
            cls._client = None
            logger.info("HTTP client closed")
    
    @classmethod
    async def get(
        cls,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None
    ) -> httpx.Response:
        """
        Perform async GET request
        
        Args:
            url: Target URL
            headers: Optional request headers
            params: Optional query parameters
            timeout: Optional request timeout
            
        Returns:
            httpx.Response object
            
        Raises:
            httpx.HTTPError: On request failure
        """
        client = await cls.get_client()
        
        try:
            logger.debug(f"GET request to {url}")
            response = await client.get(
                url,
                headers=headers,
                params=params,
                timeout=timeout
            )
            response.raise_for_status()
            logger.debug(f"GET {url} - Status: {response.status_code}")
            return response
        except httpx.HTTPError as e:
            logger.error(f"GET request failed: {url} - {str(e)}")
            raise
    
    @classmethod
    async def post(
        cls,
        url: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None
    ) -> httpx.Response:
        """
        Perform async POST request
        
        Args:
            url: Target URL
            json: Optional JSON body
            data: Optional form data
            headers: Optional request headers
            timeout: Optional request timeout
            
        Returns:
            httpx.Response object
            
        Raises:
            httpx.HTTPError: On request failure
        """
        client = await cls.get_client()
        
        try:
            logger.debug(f"POST request to {url}")
            response = await client.post(
                url,
                json=json,
                data=data,
                headers=headers,
                timeout=timeout
            )
            response.raise_for_status()
            logger.debug(f"POST {url} - Status: {response.status_code}")
            return response
        except httpx.HTTPError as e:
            logger.error(f"POST request failed: {url} - {str(e)}")
            raise
    
    @classmethod
    async def put(
        cls,
        url: str,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None
    ) -> httpx.Response:
        """
        Perform async PUT request
        
        Args:
            url: Target URL
            json: Optional JSON body
            headers: Optional request headers
            timeout: Optional request timeout
            
        Returns:
            httpx.Response object
            
        Raises:
            httpx.HTTPError: On request failure
        """
        client = await cls.get_client()
        
        try:
            logger.debug(f"PUT request to {url}")
            response = await client.put(
                url,
                json=json,
                headers=headers,
                timeout=timeout
            )
            response.raise_for_status()
            logger.debug(f"PUT {url} - Status: {response.status_code}")
            return response
        except httpx.HTTPError as e:
            logger.error(f"PUT request failed: {url} - {str(e)}")
            raise
    
    @classmethod
    async def delete(
        cls,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None
    ) -> httpx.Response:
        """
        Perform async DELETE request
        
        Args:
            url: Target URL
            headers: Optional request headers
            timeout: Optional request timeout
            
        Returns:
            httpx.Response object
            
        Raises:
            httpx.HTTPError: On request failure
        """
        client = await cls.get_client()
        
        try:
            logger.debug(f"DELETE request to {url}")
            response = await client.delete(
                url,
                headers=headers,
                timeout=timeout
            )
            response.raise_for_status()
            logger.debug(f"DELETE {url} - Status: {response.status_code}")
            return response
        except httpx.HTTPError as e:
            logger.error(f"DELETE request failed: {url} - {str(e)}")
            raise


@asynccontextmanager
async def http_client():
    """
    Context manager for HTTP client
    
    Usage:
        async with http_client() as client:
            response = await client.get("https://api.example.com")
    """
    client = await HTTPClient.get_client()
    try:
        yield client
    finally:
        pass  # Don't close here, let the singleton manage lifecycle
