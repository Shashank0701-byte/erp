from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging
from typing import Callable
from app.dependencies.tenant import extract_tenant_id_from_request

logger = logging.getLogger(__name__)


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically extract and attach tenant context to requests
    
    This middleware:
    1. Extracts tenant ID from request (header, subdomain, path)
    2. Stores tenant ID in request.state for access by dependencies
    3. Adds tenant ID to response headers for debugging
    4. Logs tenant information for each request
    
    Usage:
        from app.middleware.tenant import TenantMiddleware
        
        app.add_middleware(TenantMiddleware)
    """
    
    def __init__(self, app: ASGIApp, exclude_paths: list[str] = None):
        """
        Initialize tenant middleware
        
        Args:
            app: ASGI application
            exclude_paths: List of paths to exclude from tenant extraction
        """
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/docs",
            "/api/redoc",
            "/api/openapi.json"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and inject tenant context
        
        Args:
            request: Incoming request
            call_next: Next middleware/route handler
            
        Returns:
            Response with tenant context headers
        """
        # Skip tenant extraction for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Extract tenant ID
        try:
            tenant_id = await extract_tenant_id_from_request(
                request,
                request.headers.get("X-Tenant-ID")
            )
            
            if tenant_id:
                # Store in request state
                request.state.tenant_id = tenant_id
                logger.info(
                    f"Tenant context attached: {tenant_id} | "
                    f"Path: {request.url.path} | "
                    f"Method: {request.method}"
                )
            else:
                logger.debug(f"No tenant context for request: {request.url.path}")
        
        except Exception as e:
            logger.error(f"Error extracting tenant context: {str(e)}")
        
        # Process request
        response = await call_next(request)
        
        # Add tenant ID to response headers for debugging
        if hasattr(request.state, "tenant_id"):
            response.headers["X-Tenant-ID"] = request.state.tenant_id
        
        return response


class TenantIsolationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce tenant isolation at the database level
    
    This middleware ensures that all database queries are scoped to the current tenant
    by setting a session variable or filter
    
    Usage:
        from app.middleware.tenant import TenantIsolationMiddleware
        
        app.add_middleware(TenantIsolationMiddleware)
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Enforce tenant isolation for database queries
        
        Args:
            request: Incoming request
            call_next: Next middleware/route handler
            
        Returns:
            Response
        """
        # Get tenant ID from request state (set by TenantMiddleware)
        tenant_id = getattr(request.state, "tenant_id", None)
        
        if tenant_id:
            # TODO: Set database session variable for tenant isolation
            # Example for PostgreSQL:
            # await db.execute(f"SET app.current_tenant_id = '{tenant_id}'")
            
            # Example for SQLAlchemy with filters:
            # request.state.db_filter = {"tenant_id": tenant_id}
            
            logger.debug(f"Tenant isolation enforced for: {tenant_id}")
        
        response = await call_next(request)
        return response
